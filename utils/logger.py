import asyncio
import logging
import json
import os
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from logging.handlers import RotatingFileHandler
import sys

class Logger:
    def __init__(self):
        self.log_dir = Path.home() / '.local' / 'log' / 'asahi_healer'
        self.log_file = self.log_dir / 'asahi_healer.log'
        self.audit_log_file = self.log_dir / 'audit.log'
        self.error_log_file = self.log_dir / 'error.log'
        self.performance_log_file = self.log_dir / 'performance.log'
        
        self.logger = None
        self.audit_logger = None
        self.error_logger = None
        self.performance_logger = None
        
    async def initialize(self) -> bool:
        """Initialize logging system"""
        try:
            # Create log directory
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            # Setup main logger
            self.logger = logging.getLogger('asahi_healer')
            self.logger.setLevel(logging.INFO)
            
            # Clear any existing handlers
            self.logger.handlers.clear()
            
            # Create formatters
            detailed_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            simple_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Setup main log file handler with rotation
            main_handler = RotatingFileHandler(
                self.log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            main_handler.setLevel(logging.INFO)
            main_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(main_handler)
            
            # Setup console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.WARNING)
            console_handler.setFormatter(simple_formatter)
            self.logger.addHandler(console_handler)
            
            # Setup audit logger (for security and important events)
            self.audit_logger = logging.getLogger('asahi_healer.audit')
            self.audit_logger.setLevel(logging.INFO)
            self.audit_logger.propagate = False
            
            audit_handler = RotatingFileHandler(
                self.audit_log_file,
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=10,
                encoding='utf-8'
            )
            audit_handler.setLevel(logging.INFO)
            audit_handler.setFormatter(detailed_formatter)
            self.audit_logger.addHandler(audit_handler)
            
            # Setup error logger (for detailed error tracking)
            self.error_logger = logging.getLogger('asahi_healer.error')
            self.error_logger.setLevel(logging.ERROR)
            self.error_logger.propagate = False
            
            error_handler = RotatingFileHandler(
                self.error_log_file,
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=10,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(detailed_formatter)
            self.error_logger.addHandler(error_handler)
            
            # Setup performance logger (for timing and metrics)
            self.performance_logger = logging.getLogger('asahi_healer.performance')
            self.performance_logger.setLevel(logging.INFO)
            self.performance_logger.propagate = False
            
            perf_handler = RotatingFileHandler(
                self.performance_log_file,
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=5,
                encoding='utf-8'
            )
            perf_handler.setLevel(logging.INFO)
            perf_formatter = logging.Formatter(
                '%(asctime)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            perf_handler.setFormatter(perf_formatter)
            self.performance_logger.addHandler(perf_handler)
            
            # Log initialization
            self.info("Logger initialized successfully")
            await self._log_system_info()
            
            # Setup log rotation cleanup
            asyncio.create_task(self._periodic_cleanup())
            
            return True
            
        except Exception as e:
            print(f"Failed to initialize logger: {e}")
            return False
    
    def debug(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log debug message"""
        if self.logger:
            msg = self._format_message(message, extra_data)
            self.logger.debug(msg)
    
    def info(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log info message"""
        if self.logger:
            msg = self._format_message(message, extra_data)
            self.logger.info(msg)
    
    def warning(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log warning message"""
        if self.logger:
            msg = self._format_message(message, extra_data)
            self.logger.warning(msg)
    
    def error(self, message: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = True):
        """Log error message"""
        if self.logger:
            msg = self._format_message(message, extra_data)
            self.logger.error(msg, exc_info=exc_info)
        
        # Also log to error-specific log
        if self.error_logger:
            error_details = {
                'timestamp': datetime.now().isoformat(),
                'message': message,
                'extra_data': extra_data or {}
            }
            self.error_logger.error(json.dumps(error_details, default=str))
    
    def critical(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log critical message"""
        if self.logger:
            msg = self._format_message(message, extra_data)
            self.logger.critical(msg)
        
        # Also audit critical events
        self.audit_event('critical_error', {'message': message, 'extra_data': extra_data})
    
    def audit_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log audit event"""
        if self.audit_logger:
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'hostname': os.uname().nodename,
                'user': os.getenv('USER', 'unknown'),
                'pid': os.getpid(),
                'data': event_data
            }
            self.audit_logger.info(json.dumps(audit_entry, default=str))
    
    def performance_metric(self, metric_name: str, value: float, unit: str = 'seconds', extra_data: Optional[Dict[str, Any]] = None):
        """Log performance metric"""
        if self.performance_logger:
            metric_entry = {
                'timestamp': datetime.now().isoformat(),
                'metric': metric_name,
                'value': value,
                'unit': unit,
                'extra_data': extra_data or {}
            }
            self.performance_logger.info(json.dumps(metric_entry, default=str))
    
    def scan_started(self, scan_type: str, scan_params: Dict[str, Any]):
        """Log scan start"""
        self.audit_event('scan_started', {
            'scan_type': scan_type,
            'parameters': scan_params
        })
        self.info(f"Started {scan_type} scan", scan_params)
    
    def scan_completed(self, scan_type: str, duration: float, results_summary: Dict[str, Any]):
        """Log scan completion"""
        self.audit_event('scan_completed', {
            'scan_type': scan_type,
            'duration': duration,
            'results': results_summary
        })
        self.performance_metric(f'{scan_type}_scan_duration', duration)
        self.info(f"Completed {scan_type} scan in {duration:.2f} seconds", results_summary)
    
    def fix_applied(self, fix_id: str, fix_details: Dict[str, Any], result: str):
        """Log fix application"""
        self.audit_event('fix_applied', {
            'fix_id': fix_id,
            'fix_details': fix_details,
            'result': result
        })
        self.info(f"Applied fix {fix_id}: {result}", fix_details)
    
    def fix_failed(self, fix_id: str, fix_details: Dict[str, Any], error: str):
        """Log fix failure"""
        self.audit_event('fix_failed', {
            'fix_id': fix_id,
            'fix_details': fix_details,
            'error': error
        })
        self.error(f"Fix {fix_id} failed: {error}", fix_details)
    
    def security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related event"""
        self.audit_event(f'security_{event_type}', details)
        self.warning(f"Security event: {event_type}", details)
    
    def command_executed(self, command: str, returncode: int, duration: float):
        """Log command execution"""
        self.audit_event('command_executed', {
            'command': command,
            'returncode': returncode,
            'duration': duration
        })
        
        if returncode == 0:
            self.debug(f"Command executed successfully: {command}")
        else:
            self.warning(f"Command failed (code {returncode}): {command}")
        
        self.performance_metric('command_execution_time', duration, extra_data={'command': command})
    
    def ai_request(self, provider: str, model: str, prompt_length: int, response_length: int, duration: float):
        """Log AI API request"""
        self.audit_event('ai_request', {
            'provider': provider,
            'model': model,
            'prompt_length': prompt_length,
            'response_length': response_length,
            'duration': duration
        })
        
        self.performance_metric(f'{provider}_request_duration', duration, extra_data={
            'model': model,
            'prompt_length': prompt_length,
            'response_length': response_length
        })
    
    def scheduled_task_run(self, task_id: str, task_type: str, result: str, duration: float):
        """Log scheduled task execution"""
        self.audit_event('scheduled_task', {
            'task_id': task_id,
            'task_type': task_type,
            'result': result,
            'duration': duration
        })
        
        self.info(f"Scheduled task {task_id} ({task_type}) completed: {result}")
        self.performance_metric('scheduled_task_duration', duration, extra_data={
            'task_id': task_id,
            'task_type': task_type
        })
    
    def backup_created(self, backup_path: str, backup_size: int):
        """Log backup creation"""
        self.audit_event('backup_created', {
            'backup_path': backup_path,
            'backup_size': backup_size
        })
        self.info(f"Backup created: {backup_path} ({backup_size} bytes)")
    
    def backup_restored(self, backup_path: str, restore_result: str):
        """Log backup restoration"""
        self.audit_event('backup_restored', {
            'backup_path': backup_path,
            'result': restore_result
        })
        self.info(f"Backup restored from {backup_path}: {restore_result}")
    
    def _format_message(self, message: str, extra_data: Optional[Dict[str, Any]] = None) -> str:
        """Format log message with extra data"""
        if extra_data:
            # Sanitize extra data to remove sensitive information
            sanitized_data = self._sanitize_data(extra_data)
            return f"{message} | {json.dumps(sanitized_data, default=str)}"
        return message
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data to remove sensitive information"""
        sensitive_keys = ['password', 'api_key', 'token', 'secret', 'auth', 'credential']
        
        def sanitize_recursive(obj):
            if isinstance(obj, dict):
                sanitized = {}
                for key, value in obj.items():
                    if any(sensitive in key.lower() for sensitive in sensitive_keys):
                        sanitized[key] = '[REDACTED]'
                    else:
                        sanitized[key] = sanitize_recursive(value)
                return sanitized
            elif isinstance(obj, list):
                return [sanitize_recursive(item) for item in obj]
            else:
                return obj
        
        return sanitize_recursive(data)
    
    async def _log_system_info(self):
        """Log system information at startup"""
        try:
            import psutil
            import platform
            
            system_info = {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'hostname': os.uname().nodename,
                'kernel': os.uname().release,
                'cpu_count': psutil.cpu_count(),
                'memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'disk_usage_gb': round(psutil.disk_usage('/').total / (1024**3), 2)
            }
            
            self.audit_event('system_startup', system_info)
            
        except Exception as e:
            self.error(f"Failed to log system info: {e}")
    
    async def _periodic_cleanup(self):
        """Periodically clean up old log files"""
        while True:
            try:
                await asyncio.sleep(24 * 3600)  # Run daily
                await self._cleanup_old_logs()
            except Exception as e:
                self.error(f"Log cleanup failed: {e}")
    
    async def _cleanup_old_logs(self):
        """Clean up old log files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)  # Keep 30 days
            
            for log_file in self.log_dir.glob('*.log.*'):
                try:
                    if log_file.stat().st_mtime < cutoff_date.timestamp():
                        # Compress old log files before deletion
                        if not log_file.name.endswith('.gz'):
                            compressed_path = f"{log_file}.gz"
                            with open(log_file, 'rb') as f_in:
                                with gzip.open(compressed_path, 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                            log_file.unlink()
                            self.debug(f"Compressed and removed old log file: {log_file}")
                        
                        # Remove very old compressed files (90 days)
                        very_old_cutoff = datetime.now() - timedelta(days=90)
                        if log_file.stat().st_mtime < very_old_cutoff.timestamp():
                            log_file.unlink()
                            self.debug(f"Removed very old log file: {log_file}")
                            
                except Exception as e:
                    self.warning(f"Failed to cleanup log file {log_file}: {e}")
                    
        except Exception as e:
            self.error(f"Log cleanup process failed: {e}")
    
    async def get_recent_logs(self, log_type: str = 'main', hours: int = 24) -> List[str]:
        """Get recent log entries"""
        try:
            log_files = {
                'main': self.log_file,
                'audit': self.audit_log_file,
                'error': self.error_log_file,
                'performance': self.performance_log_file
            }
            
            if log_type not in log_files:
                return []
            
            log_file = log_files[log_type]
            if not log_file.exists():
                return []
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_entries = []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        # Extract timestamp from log line
                        if ' - ' in line:
                            timestamp_str = line.split(' - ')[0]
                            log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                            
                            if log_time >= cutoff_time:
                                recent_entries.append(line.strip())
                    except ValueError:
                        # Skip lines that don't match expected format
                        continue
            
            return recent_entries[-100:]  # Return last 100 entries
            
        except Exception as e:
            self.error(f"Failed to get recent logs: {e}")
            return []
    
    async def get_log_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        try:
            stats = {
                'log_files': {},
                'total_size': 0,
                'oldest_entry': None,
                'newest_entry': None
            }
            
            log_files = {
                'main': self.log_file,
                'audit': self.audit_log_file,
                'error': self.error_log_file,
                'performance': self.performance_log_file
            }
            
            for name, log_file in log_files.items():
                if log_file.exists():
                    stat = log_file.stat()
                    stats['log_files'][name] = {
                        'size_bytes': stat.st_size,
                        'size_mb': round(stat.st_size / (1024**2), 2),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'entries': await self._count_log_entries(log_file)
                    }
                    stats['total_size'] += stat.st_size
            
            stats['total_size_mb'] = round(stats['total_size'] / (1024**2), 2)
            
            return stats
            
        except Exception as e:
            self.error(f"Failed to get log stats: {e}")
            return {}
    
    async def _count_log_entries(self, log_file: Path) -> int:
        """Count entries in a log file"""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except:
            return 0
    
    async def export_logs(self, export_path: str, log_types: List[str] = None, hours: int = 24) -> bool:
        """Export recent logs to a file"""
        try:
            if log_types is None:
                log_types = ['main', 'audit', 'error', 'performance']
            
            export_data = {
                'export_time': datetime.now().isoformat(),
                'hostname': os.uname().nodename,
                'export_period_hours': hours,
                'logs': {}
            }
            
            for log_type in log_types:
                entries = await self.get_recent_logs(log_type, hours)
                export_data['logs'][log_type] = entries
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.info(f"Logs exported to {export_path}")
            return True
            
        except Exception as e:
            self.error(f"Failed to export logs: {e}")
            return False
    
    def set_log_level(self, level: str):
        """Set logging level"""
        try:
            level_map = {
                'DEBUG': logging.DEBUG,
                'INFO': logging.INFO,
                'WARNING': logging.WARNING,
                'ERROR': logging.ERROR,
                'CRITICAL': logging.CRITICAL
            }
            
            if level.upper() in level_map:
                if self.logger:
                    self.logger.setLevel(level_map[level.upper()])
                self.info(f"Log level set to {level.upper()}")
            else:
                self.warning(f"Invalid log level: {level}")
                
        except Exception as e:
            self.error(f"Failed to set log level: {e}")
    
    async def cleanup(self):
        """Cleanup logging resources"""
        try:
            if self.logger:
                for handler in self.logger.handlers[:]:
                    handler.close()
                    self.logger.removeHandler(handler)
            
            if self.audit_logger:
                for handler in self.audit_logger.handlers[:]:
                    handler.close()
                    self.audit_logger.removeHandler(handler)
            
            if self.error_logger:
                for handler in self.error_logger.handlers[:]:
                    handler.close()
                    self.error_logger.removeHandler(handler)
            
            if self.performance_logger:
                for handler in self.performance_logger.handlers[:]:
                    handler.close()
                    self.performance_logger.removeHandler(handler)
                    
        except Exception as e:
            print(f"Logger cleanup error: {e}")