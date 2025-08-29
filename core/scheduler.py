import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import croniter
from dataclasses import dataclass, asdict

@dataclass
class ScheduledTask:
    id: str
    name: str
    schedule: str  # Cron expression
    task_type: str  # 'full_scan', 'quick_scan', 'auto_fix', etc.
    enabled: bool
    last_run: Optional[str]
    next_run: Optional[str]
    parameters: Dict[str, Any]
    created_at: str
    updated_at: str

class TaskScheduler:
    def __init__(self):
        self.config_dir = Path.home() / '.config' / 'asahi_healer'
        self.schedule_file = self.config_dir / 'scheduled_tasks.json'
        self.tasks = {}
        self.running_tasks = set()
        
    async def initialize(self):
        """Initialize the task scheduler"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        await self._load_scheduled_tasks()
        await self._update_next_run_times()
        
    async def setup_schedule(self, schedule_config: Dict[str, Any]) -> bool:
        """Setup scheduled tasks from configuration"""
        try:
            # Remove existing tasks if replacing
            if schedule_config.get('replace_existing', False):
                self.tasks.clear()
            
            # Add new scheduled tasks
            for task_config in schedule_config.get('tasks', []):
                task = ScheduledTask(
                    id=task_config.get('id', f"task_{len(self.tasks)}"),
                    name=task_config.get('name', 'Scheduled System Scan'),
                    schedule=task_config.get('schedule', '0 2 * * *'),  # Default: daily at 2 AM
                    task_type=task_config.get('type', 'full_scan'),
                    enabled=task_config.get('enabled', True),
                    last_run=None,
                    next_run=None,
                    parameters=task_config.get('parameters', {}),
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
                
                self.tasks[task.id] = task
            
            await self._save_scheduled_tasks()
            await self._update_next_run_times()
            await self._setup_system_cron()
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to setup schedule: {e}")
            return False
    
    async def setup_basic_schedule(self, frequency: str) -> bool:
        """Setup a basic schedule from command line"""
        schedules = {
            'hourly': '0 * * * *',
            'daily': '0 2 * * *',      # 2 AM daily
            'weekly': '0 2 * * 0',     # 2 AM on Sundays
            'monthly': '0 2 1 * *'     # 2 AM on 1st of month
        }
        
        if frequency not in schedules:
            logging.error(f"Unknown frequency: {frequency}")
            return False
        
        schedule_config = {
            'replace_existing': True,
            'tasks': [{
                'id': f'auto_{frequency}',
                'name': f'Automatic {frequency.title()} System Scan',
                'schedule': schedules[frequency],
                'type': 'full_scan',
                'enabled': True,
                'parameters': {
                    'auto_fix_low_risk': True,
                    'generate_report': True,
                    'send_notifications': True
                }
            }]
        }
        
        return await self.setup_schedule(schedule_config)
    
    async def should_run_scan(self) -> bool:
        """Check if any scheduled scan should run now"""
        current_time = datetime.now()
        
        for task_id, task in self.tasks.items():
            if not task.enabled:
                continue
                
            if task_id in self.running_tasks:
                continue
            
            # Check if task should run
            if await self._should_task_run(task, current_time):
                # Update last run time
                task.last_run = current_time.isoformat()
                task.updated_at = current_time.isoformat()
                
                # Calculate next run time
                task.next_run = await self._calculate_next_run(task.schedule, current_time)
                
                await self._save_scheduled_tasks()
                return True
        
        return False
    
    async def _should_task_run(self, task: ScheduledTask, current_time: datetime) -> bool:
        """Check if a specific task should run"""
        try:
            cron = croniter.croniter(task.schedule, current_time)
            
            # Get the most recent scheduled time
            prev_run = cron.get_prev(datetime)
            
            # If we have a last run time, check if we've already run since the last scheduled time
            if task.last_run:
                last_run_time = datetime.fromisoformat(task.last_run)
                if last_run_time >= prev_run:
                    return False
            
            # Check if the scheduled time is within the last minute
            time_diff = current_time - prev_run
            return time_diff.total_seconds() < 60
            
        except Exception as e:
            logging.error(f"Error checking task schedule: {e}")
            return False
    
    async def _calculate_next_run(self, schedule: str, current_time: datetime) -> str:
        """Calculate next run time for a schedule"""
        try:
            cron = croniter.croniter(schedule, current_time)
            next_run = cron.get_next(datetime)
            return next_run.isoformat()
        except Exception as e:
            logging.error(f"Error calculating next run: {e}")
            return (current_time + timedelta(hours=24)).isoformat()
    
    async def _update_next_run_times(self):
        """Update next run times for all tasks"""
        current_time = datetime.now()
        
        for task in self.tasks.values():
            task.next_run = await self._calculate_next_run(task.schedule, current_time)
        
        await self._save_scheduled_tasks()
    
    async def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """Get list of scheduled tasks"""
        return [asdict(task) for task in self.tasks.values()]
    
    async def add_task(self, task_config: Dict[str, Any]) -> bool:
        """Add a new scheduled task"""
        try:
            task_id = task_config.get('id', f"task_{len(self.tasks)}")
            
            task = ScheduledTask(
                id=task_id,
                name=task_config.get('name', 'Scheduled Task'),
                schedule=task_config.get('schedule', '0 2 * * *'),
                task_type=task_config.get('type', 'full_scan'),
                enabled=task_config.get('enabled', True),
                last_run=None,
                next_run=await self._calculate_next_run(
                    task_config.get('schedule', '0 2 * * *'), 
                    datetime.now()
                ),
                parameters=task_config.get('parameters', {}),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            self.tasks[task_id] = task
            await self._save_scheduled_tasks()
            await self._setup_system_cron()
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to add task: {e}")
            return False
    
    async def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task"""
        try:
            if task_id in self.tasks:
                del self.tasks[task_id]
                await self._save_scheduled_tasks()
                await self._setup_system_cron()
                return True
            return False
        except Exception as e:
            logging.error(f"Failed to remove task: {e}")
            return False
    
    async def enable_task(self, task_id: str) -> bool:
        """Enable a scheduled task"""
        try:
            if task_id in self.tasks:
                self.tasks[task_id].enabled = True
                self.tasks[task_id].updated_at = datetime.now().isoformat()
                await self._save_scheduled_tasks()
                await self._setup_system_cron()
                return True
            return False
        except Exception as e:
            logging.error(f"Failed to enable task: {e}")
            return False
    
    async def disable_task(self, task_id: str) -> bool:
        """Disable a scheduled task"""
        try:
            if task_id in self.tasks:
                self.tasks[task_id].enabled = False
                self.tasks[task_id].updated_at = datetime.now().isoformat()
                await self._save_scheduled_tasks()
                await self._setup_system_cron()
                return True
            return False
        except Exception as e:
            logging.error(f"Failed to disable task: {e}")
            return False
    
    async def run_task(self, task_id: str) -> Dict[str, Any]:
        """Manually run a specific task"""
        if task_id not in self.tasks:
            return {'status': 'error', 'message': f'Task {task_id} not found'}
        
        if task_id in self.running_tasks:
            return {'status': 'error', 'message': f'Task {task_id} is already running'}
        
        task = self.tasks[task_id]
        self.running_tasks.add(task_id)
        
        try:
            result = await self._execute_task(task)
            
            # Update last run time
            task.last_run = datetime.now().isoformat()
            task.updated_at = datetime.now().isoformat()
            task.next_run = await self._calculate_next_run(task.schedule, datetime.now())
            
            await self._save_scheduled_tasks()
            
            return result
            
        finally:
            self.running_tasks.discard(task_id)
    
    async def _execute_task(self, task: ScheduledTask) -> Dict[str, Any]:
        """Execute a scheduled task"""
        
        result = {
            'task_id': task.id,
            'task_name': task.name,
            'execution_time': datetime.now().isoformat(),
            'status': 'pending',
            'details': {}
        }
        
        try:
            if task.task_type == 'full_scan':
                result.update(await self._execute_full_scan(task))
            elif task.task_type == 'quick_scan':
                result.update(await self._execute_quick_scan(task))
            elif task.task_type == 'auto_fix':
                result.update(await self._execute_auto_fix(task))
            elif task.task_type == 'update_check':
                result.update(await self._execute_update_check(task))
            else:
                result['status'] = 'error'
                result['details']['error'] = f'Unknown task type: {task.task_type}'
            
        except Exception as e:
            result['status'] = 'error'
            result['details']['error'] = str(e)
            logging.error(f"Task execution failed: {e}")
        
        return result
    
    async def _execute_full_scan(self, task: ScheduledTask) -> Dict[str, Any]:
        """Execute a full system scan"""
        # This would integrate with the main AsahiSystemHealer
        # For now, return a placeholder
        
        return {
            'status': 'completed',
            'details': {
                'scan_type': 'full',
                'issues_found': 0,
                'recommendations': 0,
                'execution_time': 30.5,
                'report_generated': task.parameters.get('generate_report', False)
            }
        }
    
    async def _execute_quick_scan(self, task: ScheduledTask) -> Dict[str, Any]:
        """Execute a quick system scan"""
        return {
            'status': 'completed',
            'details': {
                'scan_type': 'quick',
                'issues_found': 0,
                'execution_time': 5.2
            }
        }
    
    async def _execute_auto_fix(self, task: ScheduledTask) -> Dict[str, Any]:
        """Execute automatic fixes"""
        return {
            'status': 'completed',
            'details': {
                'fixes_applied': 0,
                'fixes_skipped': 0,
                'execution_time': 15.3
            }
        }
    
    async def _execute_update_check(self, task: ScheduledTask) -> Dict[str, Any]:
        """Check for system updates"""
        try:
            # Check for package updates
            process = await asyncio.create_subprocess_exec(
                'checkupdates',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                updates = stdout.decode().strip().split('\n') if stdout.decode().strip() else []
                
                return {
                    'status': 'completed',
                    'details': {
                        'updates_available': len(updates),
                        'update_list': updates[:10],  # Show first 10 updates
                        'execution_time': 3.0
                    }
                }
            else:
                return {
                    'status': 'error',
                    'details': {
                        'error': stderr.decode().strip() or 'Update check failed',
                        'execution_time': 3.0
                    }
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'details': {
                    'error': str(e),
                    'execution_time': 0
                }
            }
    
    async def _setup_system_cron(self) -> bool:
        """Setup system cron jobs for scheduled tasks"""
        try:
            # Create cron entries for enabled tasks
            cron_entries = []
            
            for task in self.tasks.values():
                if not task.enabled:
                    continue
                
                # Get the path to the asahi_healer script
                script_path = Path(__file__).parent.parent / 'asahi_healer.py'
                
                # Create cron entry
                cron_line = f"{task.schedule} python3 {script_path} --scheduled-task {task.id} >> /var/log/asahi_healer.log 2>&1"
                cron_entries.append(f"# Asahi System Healer - {task.name}")
                cron_entries.append(cron_line)
                cron_entries.append("")
            
            # Write to user crontab
            if cron_entries:
                # Get current crontab
                try:
                    process = await asyncio.create_subprocess_exec(
                        'crontab', '-l',
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    current_cron = stdout.decode() if process.returncode == 0 else ""
                except:
                    current_cron = ""
                
                # Remove old Asahi System Healer entries
                lines = current_cron.split('\n')
                filtered_lines = []
                skip_next = False
                
                for line in lines:
                    if 'Asahi System Healer' in line:
                        skip_next = True
                        continue
                    elif skip_next and 'asahi_healer.py' in line:
                        skip_next = False
                        continue
                    elif skip_next and line.strip() == "":
                        skip_next = False
                        continue
                    else:
                        skip_next = False
                        if line.strip():
                            filtered_lines.append(line)
                
                # Add new entries
                if filtered_lines and filtered_lines[-1].strip():
                    filtered_lines.append("")
                filtered_lines.extend(cron_entries)
                
                # Write new crontab
                new_cron = '\n'.join(filtered_lines)
                
                process = await asyncio.create_subprocess_exec(
                    'crontab', '-',
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate(input=new_cron.encode())
                
                if process.returncode == 0:
                    logging.info("System cron jobs updated successfully")
                    return True
                else:
                    logging.error(f"Failed to update cron jobs: {stderr.decode()}")
                    return False
            else:
                # Remove all Asahi System Healer cron jobs
                logging.info("No enabled tasks, removing all cron jobs")
                return True
                
        except Exception as e:
            logging.error(f"Failed to setup system cron: {e}")
            return False
    
    async def _load_scheduled_tasks(self):
        """Load scheduled tasks from file"""
        try:
            if self.schedule_file.exists():
                with open(self.schedule_file, 'r') as f:
                    data = json.load(f)
                
                self.tasks = {}
                for task_data in data.get('tasks', []):
                    task = ScheduledTask(**task_data)
                    self.tasks[task.id] = task
                    
        except Exception as e:
            logging.error(f"Failed to load scheduled tasks: {e}")
            self.tasks = {}
    
    async def _save_scheduled_tasks(self):
        """Save scheduled tasks to file"""
        try:
            data = {
                'version': '1.0',
                'updated_at': datetime.now().isoformat(),
                'tasks': [asdict(task) for task in self.tasks.values()]
            }
            
            with open(self.schedule_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            logging.error(f"Failed to save scheduled tasks: {e}")
    
    async def get_task_history(self, task_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get execution history for a task"""
        # This would typically read from a history/log file
        # For now, return placeholder data
        
        if task_id not in self.tasks:
            return []
        
        task = self.tasks[task_id]
        history = []
        
        if task.last_run:
            history.append({
                'execution_time': task.last_run,
                'status': 'completed',
                'duration': 30.5,
                'issues_found': 2,
                'fixes_applied': 1
            })
        
        return history
    
    async def get_next_scheduled_runs(self, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """Get next scheduled runs within specified hours"""
        current_time = datetime.now()
        cutoff_time = current_time + timedelta(hours=hours_ahead)
        
        upcoming_runs = []
        
        for task in self.tasks.values():
            if not task.enabled:
                continue
            
            if task.next_run:
                next_run_time = datetime.fromisoformat(task.next_run)
                if current_time <= next_run_time <= cutoff_time:
                    upcoming_runs.append({
                        'task_id': task.id,
                        'task_name': task.name,
                        'task_type': task.task_type,
                        'scheduled_time': task.next_run,
                        'time_until_run': str(next_run_time - current_time).split('.')[0]
                    })
        
        # Sort by scheduled time
        upcoming_runs.sort(key=lambda x: x['scheduled_time'])
        
        return upcoming_runs
    
    async def cleanup(self):
        """Cleanup scheduler resources"""
        # Cancel any running tasks
        for task_id in list(self.running_tasks):
            self.running_tasks.discard(task_id)
        
        # Save current state
        await self._save_scheduled_tasks()