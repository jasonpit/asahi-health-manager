import asyncio
import subprocess
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import tempfile

class AutoFixer:
    def __init__(self):
        self.dry_run = False
        self.backup_dir = Path.home() / '.asahi_healer_backups'
        self.execution_log = []
        
    async def initialize(self):
        """Initialize the auto-fixer"""
        self.backup_dir.mkdir(exist_ok=True)
        
    async def fix_all(self, recommendations: List[Dict[str, Any]], dry_run: bool = False) -> Dict[str, Any]:
        """Apply all recommended fixes"""
        self.dry_run = dry_run
        
        results = {
            'total_fixes': len(recommendations),
            'successful_fixes': 0,
            'failed_fixes': 0,
            'skipped_fixes': 0,
            'execution_results': [],
            'backup_location': str(self.backup_dir) if not dry_run else None,
            'execution_time': datetime.now().isoformat()
        }
        
        # Sort by severity (critical first)
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        sorted_recommendations = sorted(
            recommendations, 
            key=lambda x: severity_order.get(x.get('severity', 'medium'), 2)
        )
        
        for rec in sorted_recommendations:
            try:
                fix_result = await self._apply_fix(rec)
                results['execution_results'].append(fix_result)
                
                if fix_result['status'] == 'success':
                    results['successful_fixes'] += 1
                elif fix_result['status'] == 'failed':
                    results['failed_fixes'] += 1
                else:
                    results['skipped_fixes'] += 1
                    
            except Exception as e:
                error_result = {
                    'recommendation_id': rec.get('id', 'unknown'),
                    'title': rec.get('title', 'Unknown Fix'),
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                results['execution_results'].append(error_result)
                results['failed_fixes'] += 1
        
        return results
    
    async def fix_selected(self, selected_recommendations: List[Dict[str, Any]], dry_run: bool = False) -> Dict[str, Any]:
        """Apply only selected fixes"""
        return await self.fix_all(selected_recommendations, dry_run)
    
    async def _apply_fix(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a single fix recommendation"""
        
        fix_result = {
            'recommendation_id': recommendation.get('id', 'unknown'),
            'title': recommendation.get('title', 'Unknown Fix'),
            'status': 'pending',
            'commands_executed': [],
            'outputs': [],
            'backup_created': False,
            'backup_path': None,
            'verification_results': [],
            'timestamp': datetime.now().isoformat(),
            'execution_time': 0,
            'errors': []
        }
        
        start_time = datetime.now()
        
        try:
            # Pre-flight checks
            if not await self._pre_flight_check(recommendation):
                fix_result['status'] = 'skipped'
                fix_result['errors'].append('Pre-flight check failed')
                return fix_result
            
            # Create backup if recommended
            if recommendation.get('backup_recommended', False) and not self.dry_run:
                backup_path = await self._create_backup(recommendation)
                if backup_path:
                    fix_result['backup_created'] = True
                    fix_result['backup_path'] = str(backup_path)
            
            # Execute fix commands
            fix_commands = recommendation.get('fix_commands', [])
            
            for i, command in enumerate(fix_commands):
                if not command.strip():
                    continue
                
                # Skip dangerous commands in certain conditions
                if await self._is_command_safe(command, recommendation):
                    cmd_result = await self._execute_command(command, f"fix_step_{i+1}")
                    
                    fix_result['commands_executed'].append(command)
                    fix_result['outputs'].append({
                        'command': command,
                        'returncode': cmd_result['returncode'],
                        'stdout': cmd_result.get('stdout', ''),
                        'stderr': cmd_result.get('stderr', ''),
                        'execution_time': cmd_result.get('execution_time', 0)
                    })
                    
                    # If command failed and is critical, stop execution
                    if cmd_result['returncode'] != 0 and not await self._is_error_acceptable(command, cmd_result):
                        fix_result['status'] = 'failed'
                        fix_result['errors'].append(f"Command failed: {command}")
                        fix_result['errors'].append(f"Error: {cmd_result.get('stderr', 'Unknown error')}")
                        return fix_result
                else:
                    fix_result['errors'].append(f"Command deemed unsafe and skipped: {command}")
            
            # Run verification commands
            verification_commands = recommendation.get('verification_commands', [])
            for verification_cmd in verification_commands:
                if verification_cmd.strip():
                    verify_result = await self._execute_command(verification_cmd, "verification")
                    fix_result['verification_results'].append({
                        'command': verification_cmd,
                        'returncode': verify_result['returncode'],
                        'output': verify_result.get('stdout', ''),
                        'successful': verify_result['returncode'] == 0
                    })
            
            # Determine overall success
            if not fix_result['errors']:
                fix_result['status'] = 'success'
            else:
                fix_result['status'] = 'partial_success'
                
        except Exception as e:
            fix_result['status'] = 'error'
            fix_result['errors'].append(f"Unexpected error: {str(e)}")
            logging.error(f"Fix execution error for {recommendation.get('title', 'unknown')}: {e}")
        
        finally:
            end_time = datetime.now()
            fix_result['execution_time'] = (end_time - start_time).total_seconds()
        
        return fix_result
    
    async def _pre_flight_check(self, recommendation: Dict[str, Any]) -> bool:
        """Perform pre-flight safety checks"""
        
        # Check if system has sufficient resources
        if not await self._check_system_resources():
            logging.warning("Insufficient system resources for safe execution")
            return False
        
        # Check if we have necessary permissions
        commands = recommendation.get('fix_commands', [])
        for command in commands:
            if 'sudo' in command and not await self._check_sudo_access():
                logging.warning("Sudo access required but not available")
                return False
        
        # Check for conflicting operations
        if await self._check_for_conflicts(recommendation):
            logging.warning("Conflicting operations detected")
            return False
        
        # Check system state requirements
        if recommendation.get('requires_reboot', False):
            # In automatic mode, we don't want to automatically reboot
            # This would need user confirmation
            logging.info("Fix requires reboot - will need manual reboot after execution")
        
        return True
    
    async def _check_system_resources(self) -> bool:
        """Check if system has sufficient resources"""
        try:
            import psutil
            
            # Check available memory (should have at least 500MB free)
            memory = psutil.virtual_memory()
            if memory.available < 500 * 1024 * 1024:  # 500MB
                return False
            
            # Check disk space (should have at least 1GB free)
            disk = psutil.disk_usage('/')
            if disk.free < 1024 * 1024 * 1024:  # 1GB
                return False
            
            # Check CPU load (shouldn't be too high)
            load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            cpu_count = psutil.cpu_count()
            if load_avg > cpu_count * 2:  # Load average shouldn't be too high
                return False
            
            return True
            
        except Exception:
            # If we can't check resources, err on the side of caution
            return False
    
    async def _check_sudo_access(self) -> bool:
        """Check if we have sudo access"""
        try:
            result = await self._execute_command('sudo -n true', 'sudo_check')
            return result['returncode'] == 0
        except:
            return False
    
    async def _check_for_conflicts(self, recommendation: Dict[str, Any]) -> bool:
        """Check for conflicting operations"""
        
        # Check if package manager is already running
        commands = recommendation.get('fix_commands', [])
        
        for command in commands:
            # Check for package manager conflicts
            if any(pm in command for pm in ['pacman', 'dnf', 'apt', 'yum']):
                if await self._is_package_manager_busy():
                    return True
            
            # Check for systemctl conflicts
            if 'systemctl' in command and 'restart' in command:
                # Check if there are other systemctl operations running
                result = await self._execute_command('pgrep -f systemctl', 'conflict_check')
                if result['returncode'] == 0 and result.get('stdout', '').strip():
                    return True
        
        return False
    
    async def _is_package_manager_busy(self) -> bool:
        """Check if package manager is busy"""
        try:
            # Check for common package managers
            managers_to_check = [
                ('pacman', '/var/lib/pacman/db.lck'),
                ('dnf', '/var/run/dnf.pid'),
                ('apt', '/var/lib/dpkg/lock'),
                ('yum', '/var/run/yum.pid')
            ]
            
            for manager, lock_file in managers_to_check:
                if Path(lock_file).exists():
                    return True
                
                # Also check running processes
                result = await self._execute_command(f'pgrep -f {manager}', 'package_manager_check')
                if result['returncode'] == 0 and result.get('stdout', '').strip():
                    return True
            
            return False
            
        except:
            return True  # Assume busy if we can't check
    
    async def _create_backup(self, recommendation: Dict[str, Any]) -> Optional[Path]:
        """Create backup of system state"""
        
        if self.dry_run:
            return None
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            rec_id = recommendation.get('id', 'unknown').replace('/', '_')
            backup_name = f"{rec_id}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)
            
            # Create backup manifest
            manifest = {
                'recommendation': recommendation,
                'backup_time': datetime.now().isoformat(),
                'system_info': await self._get_system_snapshot(),
                'files_backed_up': []
            }
            
            # Backup critical system files that might be affected
            critical_files = [
                '/etc/systemd/system',
                '/etc/pacman.conf',
                '/etc/fstab',
                '/etc/hosts',
                '/home/*/.config',  # User configs
            ]
            
            for file_pattern in critical_files:
                try:
                    if '*' in file_pattern:
                        # Handle glob patterns
                        import glob
                        for file_path in glob.glob(file_pattern):
                            if Path(file_path).exists():
                                await self._backup_file(file_path, backup_path)
                                manifest['files_backed_up'].append(file_path)
                    else:
                        if Path(file_pattern).exists():
                            await self._backup_file(file_pattern, backup_path)
                            manifest['files_backed_up'].append(file_pattern)
                except Exception as e:
                    logging.warning(f"Failed to backup {file_pattern}: {e}")
            
            # Save manifest
            with open(backup_path / 'manifest.json', 'w') as f:
                json.dump(manifest, f, indent=2, default=str)
            
            logging.info(f"Backup created at {backup_path}")
            return backup_path
            
        except Exception as e:
            logging.error(f"Failed to create backup: {e}")
            return None
    
    async def _backup_file(self, source_path: str, backup_dir: Path):
        """Backup a single file or directory"""
        try:
            source = Path(source_path)
            if not source.exists():
                return
            
            # Create relative path structure in backup
            if source.is_absolute():
                relative_path = source.relative_to(source.anchor)
            else:
                relative_path = source
            
            backup_target = backup_dir / relative_path
            backup_target.parent.mkdir(parents=True, exist_ok=True)
            
            if source.is_file():
                shutil.copy2(source, backup_target)
            elif source.is_dir():
                shutil.copytree(source, backup_target, dirs_exist_ok=True)
        except Exception as e:
            logging.warning(f"Failed to backup {source_path}: {e}")
    
    async def _get_system_snapshot(self) -> Dict[str, Any]:
        """Get current system state snapshot"""
        snapshot = {}
        
        try:
            # Basic system info
            snapshot['timestamp'] = datetime.now().isoformat()
            snapshot['kernel'] = os.uname().release
            snapshot['hostname'] = os.uname().nodename
            
            # Package versions (for Arch Linux)
            result = await self._execute_command('pacman -Q', 'package_snapshot')
            if result['returncode'] == 0:
                packages = {}
                for line in result.get('stdout', '').split('\n'):
                    if ' ' in line:
                        name, version = line.split(' ', 1)
                        packages[name] = version
                snapshot['installed_packages'] = packages
            
            # Running services
            result = await self._execute_command('systemctl list-units --type=service --state=running --no-legend', 'services_snapshot')
            if result['returncode'] == 0:
                services = []
                for line in result.get('stdout', '').split('\n'):
                    if line.strip():
                        services.append(line.split()[0])
                snapshot['running_services'] = services
            
        except Exception as e:
            logging.warning(f"Failed to create system snapshot: {e}")
            snapshot['error'] = str(e)
        
        return snapshot
    
    async def _is_command_safe(self, command: str, recommendation: Dict[str, Any]) -> bool:
        """Check if a command is safe to execute"""
        
        # Commands that are never safe to auto-execute
        dangerous_commands = [
            'rm -rf /',
            'mkfs',
            'fdisk',
            'parted',
            'dd if=',
            'curl | sh',
            'wget | sh',
            'format',
            'del /s',
            '> /dev/'
        ]
        
        command_lower = command.lower()
        for dangerous in dangerous_commands:
            if dangerous.lower() in command_lower:
                logging.error(f"Dangerous command blocked: {command}")
                return False
        
        # Commands that require special handling
        if 'reboot' in command_lower or 'shutdown' in command_lower:
            logging.warning(f"Reboot/shutdown command requires manual execution: {command}")
            return False
        
        # Check risk level from recommendation
        risk_level = recommendation.get('risk_level', 'medium').lower()
        if risk_level in ['critical', 'high'] and not self._user_confirmed_high_risk():
            logging.warning(f"High-risk command requires confirmation: {command}")
            return False
        
        return True
    
    def _user_confirmed_high_risk(self) -> bool:
        """Check if user has confirmed high-risk operations"""
        # This would integrate with the UI to get user confirmation
        # For now, assume no confirmation in automated mode
        return False
    
    async def _execute_command(self, command: str, operation_type: str = "unknown") -> Dict[str, Any]:
        """Execute a system command"""
        
        if self.dry_run:
            return {
                'returncode': 0,
                'stdout': f'DRY RUN: Would execute: {command}',
                'stderr': '',
                'execution_time': 0,
                'dry_run': True
            }
        
        start_time = datetime.now()
        
        try:
            # Log command execution
            logging.info(f"Executing ({operation_type}): {command}")
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300  # 5 minute timeout
            )
            
            result = {
                'returncode': process.returncode,
                'stdout': stdout.decode('utf-8', errors='ignore'),
                'stderr': stderr.decode('utf-8', errors='ignore'),
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'command': command,
                'operation_type': operation_type
            }
            
            # Log execution to internal log
            self.execution_log.append(result)
            
            if result['returncode'] != 0:
                logging.warning(f"Command failed with code {result['returncode']}: {command}")
                logging.warning(f"stderr: {result['stderr']}")
            else:
                logging.info(f"Command completed successfully: {command}")
            
            return result
            
        except asyncio.TimeoutError:
            logging.error(f"Command timed out: {command}")
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timed out after 300 seconds',
                'execution_time': 300,
                'command': command,
                'operation_type': operation_type,
                'timeout': True
            }
        except Exception as e:
            logging.error(f"Command execution failed: {command}, error: {e}")
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'command': command,
                'operation_type': operation_type,
                'error': True
            }
    
    async def _is_error_acceptable(self, command: str, cmd_result: Dict[str, Any]) -> bool:
        """Determine if a command error is acceptable to continue"""
        
        returncode = cmd_result.get('returncode', 0)
        stderr = cmd_result.get('stderr', '').lower()
        
        # Some commands are expected to fail in certain conditions
        acceptable_failures = [
            # systemctl reset-failed can fail if no services are failed
            ('systemctl reset-failed', 'no failed units'),
            # Package cache cleaning might fail if cache is empty
            ('pacman -Sc', 'nothing to do'),
            # Service restart might fail if service doesn't exist
            ('systemctl restart', 'unit not found'),
        ]
        
        for cmd_pattern, error_pattern in acceptable_failures:
            if cmd_pattern in command.lower() and error_pattern in stderr:
                return True
        
        # Exit codes that might be acceptable
        acceptable_codes = [
            1,  # General error, might be acceptable depending on context
            130,  # Interrupted by user (Ctrl+C)
        ]
        
        if returncode in acceptable_codes:
            return True
        
        return False
    
    async def restore_backup(self, backup_path: str) -> Dict[str, Any]:
        """Restore system from backup"""
        
        restore_result = {
            'status': 'pending',
            'files_restored': [],
            'errors': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            backup_dir = Path(backup_path)
            
            if not backup_dir.exists():
                restore_result['status'] = 'failed'
                restore_result['errors'].append(f"Backup directory not found: {backup_path}")
                return restore_result
            
            # Load manifest
            manifest_path = backup_dir / 'manifest.json'
            if not manifest_path.exists():
                restore_result['status'] = 'failed'
                restore_result['errors'].append("Backup manifest not found")
                return restore_result
            
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Restore files
            for original_file in manifest.get('files_backed_up', []):
                try:
                    backup_file = backup_dir / Path(original_file).relative_to(Path(original_file).anchor)
                    
                    if backup_file.exists():
                        # Create destination directory if needed
                        Path(original_file).parent.mkdir(parents=True, exist_ok=True)
                        
                        if backup_file.is_file():
                            shutil.copy2(backup_file, original_file)
                        elif backup_file.is_dir():
                            if Path(original_file).exists():
                                shutil.rmtree(original_file)
                            shutil.copytree(backup_file, original_file)
                        
                        restore_result['files_restored'].append(original_file)
                        
                except Exception as e:
                    restore_result['errors'].append(f"Failed to restore {original_file}: {str(e)}")
            
            if not restore_result['errors']:
                restore_result['status'] = 'success'
            else:
                restore_result['status'] = 'partial_success'
                
        except Exception as e:
            restore_result['status'] = 'failed'
            restore_result['errors'].append(f"Restore failed: {str(e)}")
        
        return restore_result
    
    async def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get execution log"""
        return self.execution_log.copy()
    
    async def cleanup(self):
        """Cleanup auto-fixer resources"""
        # Clean up old backups (keep last 10)
        try:
            if self.backup_dir.exists():
                backups = sorted(
                    [d for d in self.backup_dir.iterdir() if d.is_dir()],
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )
                
                # Keep only the 10 most recent backups
                for old_backup in backups[10:]:
                    shutil.rmtree(old_backup)
                    logging.info(f"Cleaned up old backup: {old_backup}")
                    
        except Exception as e:
            logging.error(f"Cleanup failed: {e}")