import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import yaml

@dataclass
class APIConfig:
    claude_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    claude_model: str = 'claude-3-sonnet-20240229'
    openai_model: str = 'gpt-4-turbo-preview'
    max_tokens: int = 4000
    timeout: int = 60

@dataclass
class ScanConfig:
    enable_deep_scan: bool = True
    scan_timeout: int = 300
    parallel_scans: bool = True
    include_logs: bool = True
    include_hardware: bool = True
    include_network: bool = True
    asahi_specific_checks: bool = True

@dataclass
class FixConfig:
    auto_fix_enabled: bool = False
    auto_fix_severity_limit: str = 'low'  # Only auto-fix up to this severity
    create_backups: bool = True
    backup_retention_days: int = 30
    dry_run_by_default: bool = True
    require_confirmation_high_risk: bool = True

@dataclass
class ReportingConfig:
    generate_detailed_reports: bool = True
    report_format: str = 'json'  # json, html, markdown
    keep_report_history: int = 10
    include_system_snapshot: bool = True
    anonymize_sensitive_data: bool = True

@dataclass
class NotificationConfig:
    enabled: bool = False
    critical_only: bool = True
    email_enabled: bool = False
    email_address: Optional[str] = None
    webhook_enabled: bool = False
    webhook_url: Optional[str] = None

@dataclass
class SchedulingConfig:
    enabled: bool = False
    default_schedule: str = '0 2 * * *'  # Daily at 2 AM
    auto_fix_scheduled: bool = False
    max_concurrent_tasks: int = 1

class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / '.config' / 'asahi_healer'
        self.config_file = self.config_dir / 'config.yaml'
        self.api_config = APIConfig()
        self.scan_config = ScanConfig()
        self.fix_config = FixConfig()
        self.reporting_config = ReportingConfig()
        self.notification_config = NotificationConfig()
        self.scheduling_config = SchedulingConfig()
        
    async def load(self) -> bool:
        """Load configuration from file"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            if not self.config_file.exists():
                await self._create_default_config()
                return True
            
            with open(self.config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Load API configuration
            if 'api' in config_data:
                api_data = config_data['api']
                self.api_config = APIConfig(**api_data)
            
            # Load scan configuration
            if 'scanning' in config_data:
                scan_data = config_data['scanning']
                self.scan_config = ScanConfig(**scan_data)
            
            # Load fix configuration
            if 'fixing' in config_data:
                fix_data = config_data['fixing']
                self.fix_config = FixConfig(**fix_data)
            
            # Load reporting configuration
            if 'reporting' in config_data:
                reporting_data = config_data['reporting']
                self.reporting_config = ReportingConfig(**reporting_data)
            
            # Load notification configuration
            if 'notifications' in config_data:
                notification_data = config_data['notifications']
                self.notification_config = NotificationConfig(**notification_data)
            
            # Load scheduling configuration
            if 'scheduling' in config_data:
                scheduling_data = config_data['scheduling']
                self.scheduling_config = SchedulingConfig(**scheduling_data)
            
            # Override with environment variables
            await self._load_env_overrides()
            
            logging.info("Configuration loaded successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            await self._create_default_config()
            return False
    
    async def save(self) -> bool:
        """Save configuration to file"""
        try:
            config_data = {
                'api': asdict(self.api_config),
                'scanning': asdict(self.scan_config),
                'fixing': asdict(self.fix_config),
                'reporting': asdict(self.reporting_config),
                'notifications': asdict(self.notification_config),
                'scheduling': asdict(self.scheduling_config)
            }
            
            with open(self.config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            logging.info("Configuration saved successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
            return False
    
    async def _create_default_config(self):
        """Create default configuration file"""
        try:
            # Load API keys from environment if available
            self.api_config.claude_api_key = os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
            self.api_config.openai_api_key = os.getenv('OPENAI_API_KEY')
            
            # Create config with safe defaults
            config_data = {
                'api': asdict(self.api_config),
                'scanning': asdict(self.scan_config),
                'fixing': asdict(self.fix_config),
                'reporting': asdict(self.reporting_config),
                'notifications': asdict(self.notification_config),
                'scheduling': asdict(self.scheduling_config)
            }
            
            with open(self.config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            # Create README for configuration
            readme_path = self.config_dir / 'README.md'
            with open(readme_path, 'w') as f:
                f.write(self._get_config_readme())
            
            logging.info(f"Default configuration created at {self.config_file}")
            
        except Exception as e:
            logging.error(f"Failed to create default configuration: {e}")
    
    async def _load_env_overrides(self):
        """Load configuration overrides from environment variables"""
        
        # API configuration overrides
        if os.getenv('CLAUDE_API_KEY'):
            self.api_config.claude_api_key = os.getenv('CLAUDE_API_KEY')
        if os.getenv('ANTHROPIC_API_KEY'):
            self.api_config.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        if os.getenv('OPENAI_API_KEY'):
            self.api_config.openai_api_key = os.getenv('OPENAI_API_KEY')
        if os.getenv('CLAUDE_MODEL'):
            self.api_config.claude_model = os.getenv('CLAUDE_MODEL')
        if os.getenv('OPENAI_MODEL'):
            self.api_config.openai_model = os.getenv('OPENAI_MODEL')
        
        # Scan configuration overrides
        if os.getenv('ASAHI_HEALER_DEEP_SCAN'):
            self.scan_config.enable_deep_scan = os.getenv('ASAHI_HEALER_DEEP_SCAN').lower() == 'true'
        if os.getenv('ASAHI_HEALER_SCAN_TIMEOUT'):
            self.scan_config.scan_timeout = int(os.getenv('ASAHI_HEALER_SCAN_TIMEOUT'))
        
        # Fix configuration overrides
        if os.getenv('ASAHI_HEALER_AUTO_FIX'):
            self.fix_config.auto_fix_enabled = os.getenv('ASAHI_HEALER_AUTO_FIX').lower() == 'true'
        if os.getenv('ASAHI_HEALER_DRY_RUN'):
            self.fix_config.dry_run_by_default = os.getenv('ASAHI_HEALER_DRY_RUN').lower() == 'true'
    
    def get_api_config(self) -> APIConfig:
        """Get API configuration"""
        return self.api_config
    
    def get_scan_config(self) -> ScanConfig:
        """Get scan configuration"""
        return self.scan_config
    
    def get_fix_config(self) -> FixConfig:
        """Get fix configuration"""
        return self.fix_config
    
    def get_reporting_config(self) -> ReportingConfig:
        """Get reporting configuration"""
        return self.reporting_config
    
    def get_notification_config(self) -> NotificationConfig:
        """Get notification configuration"""
        return self.notification_config
    
    def get_scheduling_config(self) -> SchedulingConfig:
        """Get scheduling configuration"""
        return self.scheduling_config
    
    async def update_api_config(self, updates: Dict[str, Any]) -> bool:
        """Update API configuration"""
        try:
            for key, value in updates.items():
                if hasattr(self.api_config, key):
                    setattr(self.api_config, key, value)
            
            return await self.save()
        except Exception as e:
            logging.error(f"Failed to update API config: {e}")
            return False
    
    async def update_scan_config(self, updates: Dict[str, Any]) -> bool:
        """Update scan configuration"""
        try:
            for key, value in updates.items():
                if hasattr(self.scan_config, key):
                    setattr(self.scan_config, key, value)
            
            return await self.save()
        except Exception as e:
            logging.error(f"Failed to update scan config: {e}")
            return False
    
    async def update_fix_config(self, updates: Dict[str, Any]) -> bool:
        """Update fix configuration"""
        try:
            for key, value in updates.items():
                if hasattr(self.fix_config, key):
                    setattr(self.fix_config, key, value)
            
            return await self.save()
        except Exception as e:
            logging.error(f"Failed to update fix config: {e}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration"""
        validation_results = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Validate API configuration
        if not self.api_config.claude_api_key and not self.api_config.openai_api_key:
            validation_results['warnings'].append("No AI API keys configured - AI features will be disabled")
        
        if self.api_config.max_tokens < 1000:
            validation_results['warnings'].append("Max tokens is very low - AI responses may be truncated")
        
        if self.api_config.timeout < 10:
            validation_results['warnings'].append("API timeout is very low - requests may fail frequently")
        
        # Validate scan configuration
        if self.scan_config.scan_timeout < 60:
            validation_results['warnings'].append("Scan timeout is very low - scans may not complete")
        
        # Validate fix configuration
        if self.fix_config.auto_fix_enabled and not self.fix_config.create_backups:
            validation_results['warnings'].append("Auto-fix enabled without backups - this is risky")
        
        if self.fix_config.auto_fix_enabled and self.fix_config.auto_fix_severity_limit in ['critical', 'high']:
            validation_results['warnings'].append("Auto-fix severity limit is high - this may make dangerous changes")
        
        # Validate notification configuration
        if self.notification_config.email_enabled and not self.notification_config.email_address:
            validation_results['errors'].append("Email notifications enabled but no email address configured")
        
        if self.notification_config.webhook_enabled and not self.notification_config.webhook_url:
            validation_results['errors'].append("Webhook notifications enabled but no webhook URL configured")
        
        # Check if there are any errors
        if validation_results['errors']:
            validation_results['valid'] = False
        
        return validation_results
    
    async def setup_wizard(self) -> bool:
        """Interactive setup wizard"""
        try:
            print("Asahi System Healer Configuration Setup")
            print("==========================================")
            print()
            
            # API Configuration
            print("API Configuration")
            print("-------------------")
            
            claude_key = input("Claude API Key (optional): ").strip()
            if claude_key:
                self.api_config.claude_api_key = claude_key
            
            openai_key = input("OpenAI API Key (optional): ").strip()
            if openai_key:
                self.api_config.openai_api_key = openai_key
            
            if not claude_key and not openai_key:
                print("[!] No API keys provided - AI features will be disabled")
            
            print()
            
            # Scan Configuration
            print("Scan Configuration")
            print("--------------------")
            
            deep_scan = input("Enable deep system scanning? (y/N): ").lower().strip()
            self.scan_config.enable_deep_scan = deep_scan in ['y', 'yes']
            
            include_logs = input("Include log analysis? (Y/n): ").lower().strip()
            self.scan_config.include_logs = include_logs not in ['n', 'no']
            
            print()
            
            # Fix Configuration
            print("Fix Configuration")
            print("--------------------")
            
            auto_fix = input("Enable automatic fixing of low-risk issues? (y/N): ").lower().strip()
            self.fix_config.auto_fix_enabled = auto_fix in ['y', 'yes']
            
            if self.fix_config.auto_fix_enabled:
                severity_limit = input("Auto-fix severity limit (low/medium/high): ").lower().strip()
                if severity_limit in ['low', 'medium', 'high']:
                    self.fix_config.auto_fix_severity_limit = severity_limit
            
            create_backups = input("Create backups before making changes? (Y/n): ").lower().strip()
            self.fix_config.create_backups = create_backups not in ['n', 'no']
            
            print()
            
            # Scheduling Configuration
            print("⏰ Scheduling Configuration")
            print("-------------------------")
            
            enable_scheduling = input("Enable scheduled scans? (y/N): ").lower().strip()
            self.scheduling_config.enabled = enable_scheduling in ['y', 'yes']
            
            if self.scheduling_config.enabled:
                print("Schedule options:")
                print("1. Daily at 2 AM")
                print("2. Weekly on Sunday at 2 AM")
                print("3. Custom schedule")
                
                schedule_choice = input("Choice (1-3): ").strip()
                
                schedules = {
                    '1': '0 2 * * *',
                    '2': '0 2 * * 0'
                }
                
                if schedule_choice in schedules:
                    self.scheduling_config.default_schedule = schedules[schedule_choice]
                elif schedule_choice == '3':
                    custom_schedule = input("Enter cron expression: ").strip()
                    if custom_schedule:
                        self.scheduling_config.default_schedule = custom_schedule
            
            print()
            
            # Save configuration
            if await self.save():
                print("[+] Configuration saved successfully!")
                
                # Validate configuration
                validation = self.validate_config()
                if validation['warnings']:
                    print("\n[!] Configuration Warnings:")
                    for warning in validation['warnings']:
                        print(f"  • {warning}")
                
                if validation['errors']:
                    print("\n[!] Configuration Errors:")
                    for error in validation['errors']:
                        print(f"  • {error}")
                
                print(f"\nConfiguration saved to: {self.config_file}")
                print("You can edit this file manually or run the setup wizard again.")
                
                return validation['valid']
            else:
                print("[-] Failed to save configuration")
                return False
                
        except KeyboardInterrupt:
            print("\n\nSetup cancelled")
            return False
        except Exception as e:
            print(f"\n[-] Setup failed: {e}")
            return False
    
    def _get_config_readme(self) -> str:
        """Get configuration README content"""
        return """# Asahi System Healer Configuration

This directory contains configuration files for the Asahi System Healer.

## Files

- `config.yaml` - Main configuration file
- `scheduled_tasks.json` - Scheduled task definitions
- `README.md` - This file

## Configuration Sections

### API Configuration
- `claude_api_key` - Your Claude/Anthropic API key
- `openai_api_key` - Your OpenAI API key
- `claude_model` - Claude model to use (default: claude-3-sonnet-20240229)
- `openai_model` - OpenAI model to use (default: gpt-4-turbo-preview)

### Scanning Configuration
- `enable_deep_scan` - Enable comprehensive system scanning
- `scan_timeout` - Maximum time for scans in seconds
- `parallel_scans` - Enable parallel scanning for better performance
- `include_logs` - Include log file analysis
- `asahi_specific_checks` - Enable Asahi Linux specific checks

### Fix Configuration
- `auto_fix_enabled` - Enable automatic fixing of issues
- `auto_fix_severity_limit` - Maximum severity to auto-fix (low/medium/high)
- `create_backups` - Create backups before making changes
- `dry_run_by_default` - Run in dry-run mode by default

### Reporting Configuration
- `generate_detailed_reports` - Generate comprehensive reports
- `report_format` - Report format (json/html/markdown)
- `keep_report_history` - Number of reports to keep
- `anonymize_sensitive_data` - Remove sensitive information from reports

### Notification Configuration
- `enabled` - Enable notifications
- `critical_only` - Only notify for critical issues
- `email_enabled` - Enable email notifications
- `webhook_enabled` - Enable webhook notifications

### Scheduling Configuration
- `enabled` - Enable scheduled scans
- `default_schedule` - Default cron schedule
- `auto_fix_scheduled` - Enable auto-fix for scheduled scans

## Environment Variable Overrides

The following environment variables can override config file settings:

- `CLAUDE_API_KEY` or `ANTHROPIC_API_KEY` - Claude API key
- `OPENAI_API_KEY` - OpenAI API key
- `ASAHI_HEALER_DEEP_SCAN` - Enable deep scanning (true/false)
- `ASAHI_HEALER_AUTO_FIX` - Enable auto-fix (true/false)
- `ASAHI_HEALER_DRY_RUN` - Enable dry-run mode (true/false)

## Security Notes

- API keys are stored in plain text - ensure this directory has appropriate permissions
- Consider using environment variables for sensitive information
- Regularly rotate your API keys

## Getting Help

Run `python3 asahi_healer.py --help` for command-line options
Visit: https://github.com/your-repo/asahi-ai-system-manager for documentation
"""
    
    def get_config_path(self) -> Path:
        """Get configuration file path"""
        return self.config_file
    
    def get_config_dir(self) -> Path:
        """Get configuration directory path"""
        return self.config_dir
    
    async def export_config(self, export_path: str) -> bool:
        """Export configuration to a file"""
        try:
            export_data = {
                'version': '1.0',
                'exported_at': os.uname().nodename,
                'exported_by': 'Asahi System Healer',
                'config': {
                    'api': asdict(self.api_config),
                    'scanning': asdict(self.scan_config),
                    'fixing': asdict(self.fix_config),
                    'reporting': asdict(self.reporting_config),
                    'notifications': asdict(self.notification_config),
                    'scheduling': asdict(self.scheduling_config)
                }
            }
            
            # Remove sensitive data
            if 'claude_api_key' in export_data['config']['api']:
                export_data['config']['api']['claude_api_key'] = '[REDACTED]'
            if 'openai_api_key' in export_data['config']['api']:
                export_data['config']['api']['openai_api_key'] = '[REDACTED]'
            if 'email_address' in export_data['config']['notifications']:
                export_data['config']['notifications']['email_address'] = '[REDACTED]'
            if 'webhook_url' in export_data['config']['notifications']:
                export_data['config']['notifications']['webhook_url'] = '[REDACTED]'
            
            with open(export_path, 'w') as f:
                yaml.dump(export_data, f, default_flow_style=False, indent=2)
            
            logging.info(f"Configuration exported to {export_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to export configuration: {e}")
            return False
    
    async def import_config(self, import_path: str) -> bool:
        """Import configuration from a file"""
        try:
            with open(import_path, 'r') as f:
                import_data = yaml.safe_load(f)
            
            if 'config' not in import_data:
                logging.error("Invalid configuration file format")
                return False
            
            config = import_data['config']
            
            # Import configuration sections
            if 'api' in config:
                # Don't import redacted API keys
                api_config = config['api']
                for key, value in api_config.items():
                    if value != '[REDACTED]' and hasattr(self.api_config, key):
                        setattr(self.api_config, key, value)
            
            if 'scanning' in config:
                scan_config = config['scanning']
                for key, value in scan_config.items():
                    if hasattr(self.scan_config, key):
                        setattr(self.scan_config, key, value)
            
            # Import other sections similarly...
            
            return await self.save()
            
        except Exception as e:
            logging.error(f"Failed to import configuration: {e}")
            return False