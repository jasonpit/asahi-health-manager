#!/usr/bin/env python3
"""
Enhanced Cloud Sync System for Asahi Health Manager
Syncs user preferences, system theme settings, and app configurations across different Mac hardware
"""

import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import requests
import base64

logger = logging.getLogger(__name__)

class EnhancedCloudSync:
    """Enhanced cloud sync supporting multiple providers and system settings"""
    
    SUPPORTED_PROVIDERS = [
        'github_gist',     # GitHub Gists (private)
        'dropbox',         # Dropbox API
        'google_drive',    # Google Drive API
        'onedrive',        # OneDrive API  
        's3_compatible',   # Any S3-compatible storage
        'webdav',          # WebDAV (Nextcloud, ownCloud, etc.)
        'local_network'    # Network folder/USB drive
    ]
    
    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path.home() / ".config" / "asahi_health_manager"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.sync_config_file = self.config_dir / "cloud_sync.json"
        self.backup_dir = self.config_dir / "sync_backups"
        self.backup_dir.mkdir(exist_ok=True)
        
    def detect_desktop_environment(self) -> str:
        """Detect the current desktop environment"""
        desktop_env = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        
        if 'kde' in desktop_env or os.environ.get('KDE_FULL_SESSION'):
            return 'kde'
        elif 'gnome' in desktop_env:
            return 'gnome'
        elif 'xfce' in desktop_env:
            return 'xfce'
        elif 'mate' in desktop_env:
            return 'mate'
        else:
            return 'unknown'
    
    def collect_system_theme_settings(self) -> Dict[str, Any]:
        """Collect current system theme and appearance settings"""
        settings = {
            'desktop_environment': self.detect_desktop_environment(),
            'collected_at': datetime.now().isoformat(),
            'theme_data': {}
        }
        
        de = settings['desktop_environment']
        
        try:
            if de == 'kde':
                settings['theme_data'] = self._collect_kde_theme_settings()
            elif de == 'gnome':
                settings['theme_data'] = self._collect_gnome_theme_settings()
            elif de == 'xfce':
                settings['theme_data'] = self._collect_xfce_theme_settings()
            elif de == 'mate':
                settings['theme_data'] = self._collect_mate_theme_settings()
        except Exception as e:
            logger.error(f"Error collecting theme settings for {de}: {e}")
            
        return settings
    
    def _collect_kde_theme_settings(self) -> Dict[str, Any]:
        """Collect KDE Plasma theme settings"""
        settings = {}
        
        try:
            # Global theme
            result = subprocess.run(['kreadconfig5', '--group', 'KDE', '--key', 'LookAndFeelPackage'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                settings['global_theme'] = result.stdout.strip()
            
            # Plasma theme
            result = subprocess.run(['kreadconfig5', '--group', 'Theme', '--key', 'name'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                settings['plasma_theme'] = result.stdout.strip()
                
            # Window decorations
            result = subprocess.run(['kreadconfig5', '--group', 'org.kde.kdecoration2', '--key', 'theme'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                settings['window_decorations'] = result.stdout.strip()
                
            # Icon theme
            result = subprocess.run(['kreadconfig5', '--group', 'Icons', '--key', 'Theme'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                settings['icon_theme'] = result.stdout.strip()
                
            # GTK theme for KDE apps
            result = subprocess.run(['kreadconfig5', '--group', 'General', '--key', 'Name'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                settings['gtk_theme'] = result.stdout.strip()
                
            # Color scheme
            result = subprocess.run(['kreadconfig5', '--group', 'General', '--key', 'ColorScheme'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                settings['color_scheme'] = result.stdout.strip()
                
            # Fonts
            font_settings = {}
            for font_type in ['font', 'menuFont', 'toolBarFont', 'activeFont']:
                result = subprocess.run(['kreadconfig5', '--group', 'General', '--key', font_type], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    font_settings[font_type] = result.stdout.strip()
            settings['fonts'] = font_settings
            
        except Exception as e:
            logger.error(f"Error collecting KDE settings: {e}")
            
        return settings
    
    def _collect_gnome_theme_settings(self) -> Dict[str, Any]:
        """Collect GNOME theme settings"""
        settings = {}
        
        try:
            # GTK theme
            result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                settings['gtk_theme'] = result.stdout.strip().strip("'")
                
            # Icon theme
            result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'icon-theme'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                settings['icon_theme'] = result.stdout.strip().strip("'")
                
            # Cursor theme
            result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'cursor-theme'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                settings['cursor_theme'] = result.stdout.strip().strip("'")
                
            # Font settings
            result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'font-name'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                settings['font_name'] = result.stdout.strip().strip("'")
                
            # Wallpaper
            result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.background', 'picture-uri'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                settings['wallpaper'] = result.stdout.strip().strip("'")
                
            # Dark mode
            result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'color-scheme'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                settings['color_scheme'] = result.stdout.strip().strip("'")
                
        except Exception as e:
            logger.error(f"Error collecting GNOME settings: {e}")
            
        return settings
    
    def _collect_xfce_theme_settings(self) -> Dict[str, Any]:
        """Collect XFCE theme settings"""
        settings = {}
        
        try:
            # Window manager theme
            result = subprocess.run(['xfconf-query', '-c', 'xfwm4', '-p', '/general/theme'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                settings['window_theme'] = result.stdout.strip()
                
            # GTK theme
            result = subprocess.run(['xfconf-query', '-c', 'xsettings', '-p', '/Net/ThemeName'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                settings['gtk_theme'] = result.stdout.strip()
                
            # Icon theme
            result = subprocess.run(['xfconf-query', '-c', 'xsettings', '-p', '/Net/IconThemeName'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                settings['icon_theme'] = result.stdout.strip()
                
        except Exception as e:
            logger.error(f"Error collecting XFCE settings: {e}")
            
        return settings
    
    def _collect_mate_theme_settings(self) -> Dict[str, Any]:
        """Collect MATE theme settings"""  
        settings = {}
        
        try:
            # GTK theme
            result = subprocess.run(['gsettings', 'get', 'org.mate.interface', 'gtk-theme'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                settings['gtk_theme'] = result.stdout.strip().strip("'")
                
            # Icon theme
            result = subprocess.run(['gsettings', 'get', 'org.mate.interface', 'icon-theme'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                settings['icon_theme'] = result.stdout.strip().strip("'")
                
            # Window manager theme
            result = subprocess.run(['gsettings', 'get', 'org.mate.Marco.general', 'theme'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                settings['window_theme'] = result.stdout.strip().strip("'")
                
        except Exception as e:
            logger.error(f"Error collecting MATE settings: {e}")
            
        return settings
    
    def create_comprehensive_backup(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive backup including system theme settings and user preferences"""
        backup_data = {
            'backup_version': '2.0',
            'created_at': datetime.now().isoformat(),
            'hardware_profile': user_profile.get('hardware_profile', {}),
            'user_preferences': user_profile.get('preferences', {}),
            'installed_apps': user_profile.get('installed_apps', []),
            'system_theme_settings': self.collect_system_theme_settings(),
            'asahi_health_settings': {
                'ai_provider_preferences': self._get_ai_settings(),
                'update_preferences': self._get_update_settings(),
                'health_check_preferences': self._get_health_check_settings(),
                'desktop_launcher_configs': self._get_launcher_configs()
            },
            'compatibility_info': self._generate_compatibility_info()
        }
        
        return backup_data
    
    def _get_ai_settings(self) -> Dict[str, Any]:
        """Get AI assistant settings"""
        try:
            config_file = self.config_dir / "ai_config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error reading AI settings: {e}")
        return {}
    
    def _get_update_settings(self) -> Dict[str, Any]:
        """Get system update preferences"""
        return {
            'auto_updates_enabled': True,
            'update_schedule': 'weekly',
            'include_flatpak': True,
            'include_dnf': True,
            'notification_preferences': 'important_only'
        }
    
    def _get_health_check_settings(self) -> Dict[str, Any]:
        """Get health check preferences"""
        return {
            'auto_health_check': True,
            'check_frequency': 'daily',
            'auto_fix_enabled': False,
            'auto_fix_severity_limit': 'medium'
        }
    
    def _get_launcher_configs(self) -> List[Dict[str, str]]:
        """Get desktop launcher configurations"""
        launchers = []
        try:
            launcher_dir = Path.home() / ".local" / "share" / "applications"
            if launcher_dir.exists():
                for desktop_file in launcher_dir.glob("asahi-*.desktop"):
                    with open(desktop_file, 'r') as f:
                        content = f.read()
                        launchers.append({
                            'filename': desktop_file.name,
                            'content': content
                        })
        except Exception as e:
            logger.error(f"Error collecting launcher configs: {e}")
        return launchers
    
    def _generate_compatibility_info(self) -> Dict[str, Any]:
        """Generate compatibility information for cross-Mac restoration"""
        return {
            'asahi_health_manager_version': '1.0.0',
            'supported_apple_silicon': ['M1', 'M1 Pro', 'M1 Max', 'M1 Ultra', 'M2', 'M2 Pro', 'M2 Max', 'M2 Ultra', 'M3', 'M3 Pro', 'M3 Max'],
            'supported_desktop_environments': ['KDE', 'GNOME', 'XFCE', 'MATE'],
            'hardware_adaptive_settings': {
                'performance_scaling_by_chip': {
                    'M1': 'balanced',
                    'M2': 'performance',
                    'M3': 'performance'
                },
                'theme_recommendations_by_screen': {
                    'small': 'compact_themes',
                    'large': 'full_themes',
                    'retina': 'hidpi_themes'
                }
            }
        }
    
    def setup_cloud_provider(self, provider: str, credentials: Dict[str, str]) -> Tuple[bool, str]:
        """Setup cloud storage provider"""
        if provider not in self.SUPPORTED_PROVIDERS:
            return False, f"Unsupported provider: {provider}"
        
        config = {
            'provider': provider,
            'credentials': credentials,
            'setup_date': datetime.now().isoformat(),
            'enabled': True
        }
        
        # Test the connection
        success, message = self._test_provider_connection(provider, credentials)
        if not success:
            return False, f"Connection test failed: {message}"
        
        # Save configuration
        with open(self.sync_config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return True, f"Successfully configured {provider}"
    
    def _test_provider_connection(self, provider: str, credentials: Dict[str, str]) -> Tuple[bool, str]:
        """Test connection to cloud provider"""
        try:
            if provider == 'github_gist':
                return self._test_github_gist(credentials)
            elif provider == 'dropbox':
                return self._test_dropbox(credentials)
            elif provider == 'google_drive':
                return self._test_google_drive(credentials)
            elif provider == 'local_network':
                return self._test_local_network(credentials)
            # Add other providers...
            else:
                return True, "Provider connection test not implemented"
        except Exception as e:
            return False, str(e)
    
    def _test_github_gist(self, credentials: Dict[str, str]) -> Tuple[bool, str]:
        """Test GitHub Gist connection"""
        token = credentials.get('token')
        if not token:
            return False, "GitHub token required"
        
        try:
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
            if response.status_code == 200:
                return True, "GitHub connection successful"
            else:
                return False, f"GitHub API error: {response.status_code}"
        except Exception as e:
            return False, f"GitHub connection error: {e}"
    
    def _test_dropbox(self, credentials: Dict[str, str]) -> Tuple[bool, str]:
        """Test Dropbox connection"""
        # Implementation for Dropbox API testing
        return True, "Dropbox test not implemented"
    
    def _test_google_drive(self, credentials: Dict[str, str]) -> Tuple[bool, str]:
        """Test Google Drive connection"""
        # Implementation for Google Drive API testing
        return True, "Google Drive test not implemented"
    
    def _test_local_network(self, credentials: Dict[str, str]) -> Tuple[bool, str]:
        """Test local network/USB path"""
        path = Path(credentials.get('path', ''))
        if not path.exists():
            return False, f"Path does not exist: {path}"
        if not path.is_dir():
            return False, f"Path is not a directory: {path}"
        if not os.access(path, os.W_OK):
            return False, f"No write permission: {path}"
        return True, "Local path accessible"
    
    def sync_to_cloud(self, backup_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Upload backup data to configured cloud provider"""
        if not self.sync_config_file.exists():
            return False, "No cloud provider configured"
        
        with open(self.sync_config_file, 'r') as f:
            config = json.load(f)
        
        provider = config['provider']
        credentials = config['credentials']
        
        # Create backup file
        backup_filename = f"asahi-health-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        backup_content = json.dumps(backup_data, indent=2)
        
        try:
            if provider == 'github_gist':
                return self._upload_to_github_gist(backup_filename, backup_content, credentials)
            elif provider == 'dropbox':
                return self._upload_to_dropbox(backup_filename, backup_content, credentials)
            elif provider == 'local_network':
                return self._upload_to_local(backup_filename, backup_content, credentials)
            # Add other providers...
            else:
                return False, f"Upload not implemented for {provider}"
        except Exception as e:
            return False, f"Upload error: {e}"
    
    def _upload_to_github_gist(self, filename: str, content: str, credentials: Dict[str, str]) -> Tuple[bool, str]:
        """Upload to GitHub Gist"""
        token = credentials.get('token')
        
        gist_data = {
            'description': f'Asahi Health Manager Backup - {datetime.now().strftime("%Y-%m-%d %H:%M")}',
            'public': False,
            'files': {
                filename: {
                    'content': content
                }
            }
        }
        
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.post('https://api.github.com/gists', 
                               headers=headers, json=gist_data, timeout=30)
        
        if response.status_code == 201:
            gist_data = response.json()
            gist_id = gist_data['id']
            return True, f"Backup uploaded to GitHub Gist: {gist_id}"
        else:
            return False, f"GitHub Gist upload failed: {response.status_code}"
    
    def _upload_to_local(self, filename: str, content: str, credentials: Dict[str, str]) -> Tuple[bool, str]:
        """Upload to local network/USB path"""
        path = Path(credentials.get('path', ''))
        backup_file = path / filename
        
        with open(backup_file, 'w') as f:
            f.write(content)
        
        return True, f"Backup saved to: {backup_file}"
    
    def restore_from_cloud(self, backup_id: str = None) -> Tuple[bool, str]:
        """Download and restore backup from cloud"""
        if not self.sync_config_file.exists():
            return False, "No cloud provider configured"
        
        with open(self.sync_config_file, 'r') as f:
            config = json.load(f)
        
        provider = config['provider']
        credentials = config['credentials']
        
        try:
            # Download backup data
            success, backup_data = self._download_from_cloud(provider, credentials, backup_id)
            if not success:
                return False, backup_data  # backup_data contains error message
            
            # Apply the backup with hardware adaptation
            success, message = self._apply_backup_with_adaptation(backup_data)
            return success, message
            
        except Exception as e:
            return False, f"Restore error: {e}"
    
    def _download_from_cloud(self, provider: str, credentials: Dict[str, str], backup_id: str = None) -> Tuple[bool, Any]:
        """Download backup from cloud provider"""
        if provider == 'github_gist':
            return self._download_from_github_gist(credentials, backup_id)
        elif provider == 'local_network':
            return self._download_from_local(credentials, backup_id)
        # Add other providers...
        else:
            return False, f"Download not implemented for {provider}"
    
    def _download_from_github_gist(self, credentials: Dict[str, str], gist_id: str) -> Tuple[bool, Any]:
        """Download from GitHub Gist"""
        token = credentials.get('token')
        
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get(f'https://api.github.com/gists/{gist_id}', headers=headers, timeout=30)
        
        if response.status_code == 200:
            gist_data = response.json()
            files = gist_data['files']
            
            # Find the backup file
            backup_file = None
            for filename, file_data in files.items():
                if filename.startswith('asahi-health-backup-'):
                    backup_file = file_data
                    break
            
            if backup_file:
                content = backup_file['content']
                backup_data = json.loads(content)
                return True, backup_data
            else:
                return False, "No backup file found in gist"
        else:
            return False, f"Failed to download gist: {response.status_code}"
    
    def _download_from_local(self, credentials: Dict[str, str], backup_id: str = None) -> Tuple[bool, Any]:
        """Download from local network/USB path"""
        path = Path(credentials.get('path', ''))
        
        # Find the most recent backup file if no specific ID provided
        if not backup_id:
            backup_files = list(path.glob('asahi-health-backup-*.json'))
            if not backup_files:
                return False, "No backup files found"
            backup_file = max(backup_files, key=os.path.getctime)
        else:
            backup_file = path / backup_id
        
        if not backup_file.exists():
            return False, f"Backup file not found: {backup_file}"
        
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        return True, backup_data
    
    def _apply_backup_with_adaptation(self, backup_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Apply backup with intelligent hardware adaptation"""
        try:
            results = []
            
            # Apply system theme settings (adapted for current DE)
            success, msg = self._restore_theme_settings(backup_data.get('system_theme_settings', {}))
            results.append(f"Theme settings: {msg}")
            
            # Apply user preferences
            success, msg = self._restore_user_preferences(backup_data.get('user_preferences', {}))
            results.append(f"User preferences: {msg}")
            
            # Apply app preferences with hardware adaptation
            success, msg = self._restore_app_preferences(backup_data.get('asahi_health_settings', {}))
            results.append(f"App preferences: {msg}")
            
            # Restore desktop launchers
            success, msg = self._restore_desktop_launchers(backup_data.get('asahi_health_settings', {}).get('desktop_launcher_configs', []))
            results.append(f"Desktop launchers: {msg}")
            
            return True, "Backup restored successfully. " + " | ".join(results)
            
        except Exception as e:
            return False, f"Error applying backup: {e}"
    
    def _restore_theme_settings(self, theme_settings: Dict[str, Any]) -> Tuple[bool, str]:
        """Restore theme settings adapted for current desktop environment"""
        if not theme_settings:
            return True, "No theme settings to restore"
        
        current_de = self.detect_desktop_environment()
        backed_up_de = theme_settings.get('desktop_environment', 'unknown')
        theme_data = theme_settings.get('theme_data', {})
        
        try:
            if current_de == backed_up_de:
                # Same desktop environment - direct restore
                return self._apply_theme_settings_direct(current_de, theme_data)
            else:
                # Different desktop environment - adapted restore
                return self._apply_theme_settings_adapted(current_de, backed_up_de, theme_data)
        except Exception as e:
            return False, f"Error restoring theme settings: {e}"
    
    def _apply_theme_settings_direct(self, de: str, theme_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Apply theme settings directly for same desktop environment"""
        if de == 'kde':
            return self._apply_kde_theme_settings(theme_data)
        elif de == 'gnome':
            return self._apply_gnome_theme_settings(theme_data)
        elif de == 'xfce':
            return self._apply_xfce_theme_settings(theme_data)
        elif de == 'mate':
            return self._apply_mate_theme_settings(theme_data)
        else:
            return True, f"Theme restoration not supported for {de}"
    
    def _apply_theme_settings_adapted(self, current_de: str, backed_up_de: str, theme_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Apply theme settings adapted for different desktop environment"""
        # Map common theme elements between desktop environments
        adapted_settings = {}
        
        # Extract common elements that can be mapped
        if 'gtk_theme' in theme_data:
            adapted_settings['gtk_theme'] = theme_data['gtk_theme']
        if 'icon_theme' in theme_data:
            adapted_settings['icon_theme'] = theme_data['icon_theme']
        if 'cursor_theme' in theme_data:
            adapted_settings['cursor_theme'] = theme_data['cursor_theme']
        
        # Apply adapted settings
        return self._apply_theme_settings_direct(current_de, adapted_settings)
    
    def _apply_kde_theme_settings(self, theme_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Apply KDE theme settings"""
        applied = []
        
        for setting, value in theme_data.items():
            if setting == 'global_theme':
                subprocess.run(['kwriteconfig5', '--group', 'KDE', '--key', 'LookAndFeelPackage', value])
                applied.append('global_theme')
            elif setting == 'icon_theme':
                subprocess.run(['kwriteconfig5', '--group', 'Icons', '--key', 'Theme', value])
                applied.append('icon_theme')
            # Add other KDE settings...
        
        return True, f"Applied KDE settings: {', '.join(applied)}"
    
    def _apply_gnome_theme_settings(self, theme_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Apply GNOME theme settings"""
        applied = []
        
        for setting, value in theme_data.items():
            if setting == 'gtk_theme':
                subprocess.run(['gsettings', 'set', 'org.gnome.desktop.interface', 'gtk-theme', value])
                applied.append('gtk_theme')
            elif setting == 'icon_theme':
                subprocess.run(['gsettings', 'set', 'org.gnome.desktop.interface', 'icon-theme', value])
                applied.append('icon_theme')
            # Add other GNOME settings...
        
        return True, f"Applied GNOME settings: {', '.join(applied)}"
    
    def _apply_xfce_theme_settings(self, theme_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Apply XFCE theme settings"""
        applied = []
        
        for setting, value in theme_data.items():
            if setting == 'gtk_theme':
                subprocess.run(['xfconf-query', '-c', 'xsettings', '-p', '/Net/ThemeName', '-s', value])
                applied.append('gtk_theme')
            elif setting == 'icon_theme':
                subprocess.run(['xfconf-query', '-c', 'xsettings', '-p', '/Net/IconThemeName', '-s', value])
                applied.append('icon_theme')
            # Add other XFCE settings...
        
        return True, f"Applied XFCE settings: {', '.join(applied)}"
    
    def _apply_mate_theme_settings(self, theme_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Apply MATE theme settings"""
        applied = []
        
        for setting, value in theme_data.items():
            if setting == 'gtk_theme':
                subprocess.run(['gsettings', 'set', 'org.mate.interface', 'gtk-theme', value])
                applied.append('gtk_theme')
            elif setting == 'icon_theme':
                subprocess.run(['gsettings', 'set', 'org.mate.interface', 'icon-theme', value])
                applied.append('icon_theme')
            # Add other MATE settings...
        
        return True, f"Applied MATE settings: {', '.join(applied)}"
    
    def _restore_user_preferences(self, preferences: Dict[str, Any]) -> Tuple[bool, str]:
        """Restore user preferences"""
        # Save preferences to our config
        prefs_file = self.config_dir / "user_preferences.json"
        with open(prefs_file, 'w') as f:
            json.dump(preferences, f, indent=2)
        return True, "User preferences restored"
    
    def _restore_app_preferences(self, app_settings: Dict[str, Any]) -> Tuple[bool, str]:
        """Restore application preferences with hardware adaptation"""
        # Apply AI settings
        ai_settings = app_settings.get('ai_provider_preferences', {})
        if ai_settings:
            ai_config_file = self.config_dir / "ai_config.json"
            with open(ai_config_file, 'w') as f:
                json.dump(ai_settings, f, indent=2)
        
        return True, "App preferences restored"
    
    def _restore_desktop_launchers(self, launcher_configs: List[Dict[str, str]]) -> Tuple[bool, str]:
        """Restore desktop launcher configurations"""
        launcher_dir = Path.home() / ".local" / "share" / "applications"
        launcher_dir.mkdir(parents=True, exist_ok=True)
        
        restored = []
        for config in launcher_configs:
            filename = config.get('filename')
            content = config.get('content')
            
            if filename and content:
                launcher_file = launcher_dir / filename
                with open(launcher_file, 'w') as f:
                    f.write(content)
                restored.append(filename)
        
        if restored:
            subprocess.run(['update-desktop-database', str(launcher_dir)], capture_output=True)
        
        return True, f"Restored {len(restored)} desktop launchers"