#!/usr/bin/env python3
"""
User Profile and Cloud Sync System for Asahi Health Manager
Allows users to save their configuration and sync it across devices with intelligent adaptation
"""

import json
import hashlib
import platform
import subprocess
import base64
import getpass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class HardwareProfile:
    """Hardware information for intelligent adaptation"""
    cpu_model: str
    cpu_arch: str
    apple_silicon_model: str  # M1, M2, M3, etc.
    ram_gb: int
    screen_resolution: str
    desktop_environment: str
    asahi_version: str
    kernel_version: str
    system_id: str  # Unique system identifier

@dataclass
class UserPreferences:
    """User preferences and settings"""
    preferred_apps: List[str]
    favorite_categories: List[str]
    theme_preferences: Dict[str, str]
    audio_settings: Dict[str, Any]
    performance_profile: str  # power_save, balanced, performance
    auto_update_settings: Dict[str, bool]
    notification_preferences: Dict[str, bool]
    privacy_settings: Dict[str, bool]

@dataclass
class UserProfile:
    """Complete user profile"""
    profile_id: str
    username: str
    email: Optional[str]
    created_date: str
    last_updated: str
    hardware_profile: HardwareProfile
    preferences: UserPreferences
    installed_apps: List[str]
    custom_configurations: Dict[str, Any]
    sync_settings: Dict[str, Any]
    version: str = "1.0"

class CloudStorageProvider:
    """Abstract base for cloud storage providers"""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
    
    def upload(self, data: str, filename: str) -> Tuple[bool, str]:
        """Upload data to cloud storage"""
        raise NotImplementedError
    
    def download(self, filename: str) -> Tuple[bool, str]:
        """Download data from cloud storage"""
        raise NotImplementedError
    
    def list_files(self) -> List[str]:
        """List available files"""
        raise NotImplementedError

class GitHubGistProvider(CloudStorageProvider):
    """GitHub Gist storage provider"""
    
    def __init__(self, token: Optional[str] = None):
        super().__init__("GitHub Gist")
        self.token = token
        self.base_url = "https://api.github.com/gists"
    
    def upload(self, data: str, filename: str = "asahi-health-profile.json") -> Tuple[bool, str]:
        """Upload profile to GitHub Gist"""
        if not self.token:
            return False, "GitHub token required"
        
        try:
            import requests
            
            gist_data = {
                "description": "Asahi Health Manager User Profile",
                "public": False,
                "files": {
                    filename: {
                        "content": data
                    }
                }
            }
            
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.post(self.base_url, json=gist_data, headers=headers)
            
            if response.status_code == 201:
                gist_info = response.json()
                gist_id = gist_info['id']
                return True, f"Profile uploaded to Gist ID: {gist_id}"
            else:
                return False, f"Upload failed: {response.text}"
                
        except ImportError:
            return False, "requests library required for GitHub Gist sync"
        except Exception as e:
            return False, f"Upload error: {str(e)}"
    
    def download(self, gist_id: str) -> Tuple[bool, str]:
        """Download profile from GitHub Gist"""
        try:
            import requests
            
            headers = {}
            if self.token:
                headers["Authorization"] = f"token {self.token}"
            
            response = requests.get(f"{self.base_url}/{gist_id}", headers=headers)
            
            if response.status_code == 200:
                gist_data = response.json()
                files = gist_data.get('files', {})
                
                # Find the profile file
                for filename, file_info in files.items():
                    if 'asahi-health-profile' in filename:
                        return True, file_info['content']
                
                return False, "Profile file not found in Gist"
            else:
                return False, f"Download failed: {response.text}"
                
        except ImportError:
            return False, "requests library required for GitHub Gist sync"
        except Exception as e:
            return False, f"Download error: {str(e)}"

class LocalFileProvider(CloudStorageProvider):
    """Local file storage provider (for USB drives, network shares, etc.)"""
    
    def __init__(self, storage_path: Path):
        super().__init__("Local File")
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def upload(self, data: str, filename: str = "asahi-health-profile.json") -> Tuple[bool, str]:
        """Save profile to local storage"""
        try:
            file_path = self.storage_path / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(data)
            return True, f"Profile saved to {file_path}"
        except Exception as e:
            return False, f"Save error: {str(e)}"
    
    def download(self, filename: str = "asahi-health-profile.json") -> Tuple[bool, str]:
        """Load profile from local storage"""
        try:
            file_path = self.storage_path / filename
            with open(file_path, 'r', encoding='utf-8') as f:
                data = f.read()
            return True, data
        except Exception as e:
            return False, f"Load error: {str(e)}"
    
    def list_files(self) -> List[str]:
        """List available profile files"""
        try:
            return [f.name for f in self.storage_path.glob("*.json")]
        except Exception:
            return []

class UserProfileManager:
    """Manages user profiles with cloud sync capabilities"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "asahi_healer"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.profile_file = self.config_dir / "user_profile.json"
        self.current_profile: Optional[UserProfile] = None
        
        # Available cloud providers
        self.cloud_providers: Dict[str, CloudStorageProvider] = {}
        
        # Load existing profile
        self.load_profile()
    
    def detect_hardware_profile(self) -> HardwareProfile:
        """Detect current hardware configuration"""
        try:
            # CPU information
            cpu_info = platform.processor() or "Unknown"
            cpu_arch = platform.machine()
            
            # Detect Apple Silicon model
            apple_silicon = "Unknown"
            try:
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    brand = result.stdout.strip()
                    if "Apple" in brand:
                        if "M1" in brand:
                            apple_silicon = "M1"
                        elif "M2" in brand:
                            apple_silicon = "M2"
                        elif "M3" in brand:
                            apple_silicon = "M3"
                        elif "M4" in brand:
                            apple_silicon = "M4"
            except Exception:
                pass
            
            # RAM information
            ram_gb = 8  # Default assumption
            try:
                result = subprocess.run(
                    ["free", "-g"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Mem:' in line:
                            ram_gb = int(line.split()[1])
                            break
            except Exception:
                pass
            
            # Screen resolution
            screen_res = "1920x1080"  # Default
            try:
                result = subprocess.run(
                    ["xrandr"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if '*' in line:  # Current resolution
                            parts = line.strip().split()
                            for part in parts:
                                if 'x' in part and part.replace('x', '').replace('.', '').isdigit():
                                    screen_res = part.split('.')[0]
                                    break
            except Exception:
                pass
            
            # Desktop Environment
            de = "Unknown"
            de_env = os.environ.get('XDG_CURRENT_DESKTOP', '')
            if de_env:
                de = de_env
            else:
                session = os.environ.get('DESKTOP_SESSION', '')
                if session:
                    de = session
            
            # Asahi version
            asahi_version = "Unknown"
            try:
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('PRETTY_NAME'):
                            asahi_version = line.split('=')[1].strip('"')
                            break
            except Exception:
                pass
            
            # Kernel version
            kernel_version = platform.release()
            
            # Generate unique system ID
            system_data = f"{cpu_info}-{platform.node()}-{cpu_arch}"
            system_id = hashlib.md5(system_data.encode()).hexdigest()[:12]
            
            return HardwareProfile(
                cpu_model=cpu_info,
                cpu_arch=cpu_arch,
                apple_silicon_model=apple_silicon,
                ram_gb=ram_gb,
                screen_resolution=screen_res,
                desktop_environment=de,
                asahi_version=asahi_version,
                kernel_version=kernel_version,
                system_id=system_id
            )
            
        except Exception as e:
            logger.error(f"Hardware detection failed: {e}")
            # Return minimal profile
            return HardwareProfile(
                cpu_model="Unknown",
                cpu_arch=platform.machine(),
                apple_silicon_model="Unknown",
                ram_gb=8,
                screen_resolution="1920x1080",
                desktop_environment="Unknown",
                asahi_version="Unknown",
                kernel_version=platform.release(),
                system_id=hashlib.md5("unknown".encode()).hexdigest()[:12]
            )
    
    def create_new_profile(self, username: str, email: Optional[str] = None) -> UserProfile:
        """Create a new user profile"""
        profile_id = hashlib.md5(f"{username}-{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        hardware = self.detect_hardware_profile()
        
        preferences = UserPreferences(
            preferred_apps=[],
            favorite_categories=[],
            theme_preferences={},
            audio_settings={},
            performance_profile="balanced",
            auto_update_settings={
                "security_updates": True,
                "app_updates": False,
                "firmware_updates": True
            },
            notification_preferences={
                "update_notifications": True,
                "security_alerts": True,
                "installation_complete": True
            },
            privacy_settings={
                "collect_usage_stats": False,
                "share_hardware_info": True,
                "cloud_sync_enabled": False
            }
        )
        
        profile = UserProfile(
            profile_id=profile_id,
            username=username,
            email=email,
            created_date=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            hardware_profile=hardware,
            preferences=preferences,
            installed_apps=[],
            custom_configurations={},
            sync_settings={}
        )
        
        self.current_profile = profile
        return profile
    
    def save_profile(self) -> bool:
        """Save current profile to local storage"""
        if not self.current_profile:
            return False
        
        try:
            self.current_profile.last_updated = datetime.now().isoformat()
            
            # Convert to dict and save
            profile_data = asdict(self.current_profile)
            
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2)
            
            logger.info(f"Profile saved: {self.profile_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save profile: {e}")
            return False
    
    def load_profile(self) -> bool:
        """Load profile from local storage"""
        try:
            if not self.profile_file.exists():
                return False
            
            with open(self.profile_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert back to dataclasses
            hardware_data = data.get('hardware_profile', {})
            hardware = HardwareProfile(**hardware_data)
            
            preferences_data = data.get('preferences', {})
            preferences = UserPreferences(**preferences_data)
            
            self.current_profile = UserProfile(
                profile_id=data.get('profile_id', ''),
                username=data.get('username', ''),
                email=data.get('email'),
                created_date=data.get('created_date', ''),
                last_updated=data.get('last_updated', ''),
                hardware_profile=hardware,
                preferences=preferences,
                installed_apps=data.get('installed_apps', []),
                custom_configurations=data.get('custom_configurations', {}),
                sync_settings=data.get('sync_settings', {}),
                version=data.get('version', '1.0')
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load profile: {e}")
            return False
    
    def update_installed_apps(self, installed_apps: List[str]):
        """Update the list of installed apps in profile"""
        if self.current_profile:
            self.current_profile.installed_apps = installed_apps
            self.save_profile()
    
    def update_preferences(self, **kwargs):
        """Update user preferences"""
        if self.current_profile:
            for key, value in kwargs.items():
                if hasattr(self.current_profile.preferences, key):
                    setattr(self.current_profile.preferences, key, value)
            self.save_profile()
    
    def setup_cloud_sync(self, provider_type: str, **kwargs) -> Tuple[bool, str]:
        """Setup cloud synchronization"""
        try:
            if provider_type == "github":
                token = kwargs.get('token')
                if not token:
                    return False, "GitHub token required"
                
                provider = GitHubGistProvider(token)
                self.cloud_providers['github'] = provider
                
                # Update sync settings
                if self.current_profile:
                    self.current_profile.sync_settings = {
                        'provider': 'github',
                        'enabled': True,
                        'last_sync': None
                    }
                    self.save_profile()
                
                return True, "GitHub Gist sync configured"
                
            elif provider_type == "local":
                storage_path = kwargs.get('path', Path.home() / "Documents" / "AsahiHealthManager")
                provider = LocalFileProvider(storage_path)
                self.cloud_providers['local'] = provider
                
                if self.current_profile:
                    self.current_profile.sync_settings = {
                        'provider': 'local',
                        'path': str(storage_path),
                        'enabled': True,
                        'last_sync': None
                    }
                    self.save_profile()
                
                return True, f"Local sync configured: {storage_path}"
                
            else:
                return False, f"Unknown provider type: {provider_type}"
                
        except Exception as e:
            return False, f"Cloud sync setup failed: {str(e)}"
    
    def sync_to_cloud(self) -> Tuple[bool, str]:
        """Sync current profile to cloud storage"""
        if not self.current_profile:
            return False, "No profile to sync"
        
        sync_settings = self.current_profile.sync_settings
        if not sync_settings.get('enabled'):
            return False, "Cloud sync not enabled"
        
        provider_name = sync_settings.get('provider')
        if provider_name not in self.cloud_providers:
            return False, f"Cloud provider '{provider_name}' not configured"
        
        provider = self.cloud_providers[provider_name]
        
        try:
            # Create sync data
            profile_data = asdict(self.current_profile)
            profile_json = json.dumps(profile_data, indent=2)
            
            # Upload to cloud
            success, message = provider.upload(profile_json)
            
            if success:
                self.current_profile.sync_settings['last_sync'] = datetime.now().isoformat()
                self.save_profile()
            
            return success, message
            
        except Exception as e:
            return False, f"Sync failed: {str(e)}"
    
    def sync_from_cloud(self, identifier: str = None) -> Tuple[bool, str]:
        """Sync profile from cloud storage"""
        sync_settings = self.current_profile.sync_settings if self.current_profile else {}
        
        if not sync_settings.get('enabled'):
            return False, "Cloud sync not enabled"
        
        provider_name = sync_settings.get('provider')
        if provider_name not in self.cloud_providers:
            return False, f"Cloud provider '{provider_name}' not configured"
        
        provider = self.cloud_providers[provider_name]
        
        try:
            # Download from cloud
            if identifier:
                success, data = provider.download(identifier)
            else:
                success, data = provider.download()
            
            if not success:
                return False, data
            
            # Parse and adapt profile
            profile_data = json.loads(data)
            adapted_profile = self.adapt_profile_to_hardware(profile_data)
            
            # Create new profile from synced data
            hardware_data = adapted_profile.get('hardware_profile', {})
            hardware = HardwareProfile(**hardware_data)
            
            preferences_data = adapted_profile.get('preferences', {})
            preferences = UserPreferences(**preferences_data)
            
            synced_profile = UserProfile(
                profile_id=adapted_profile.get('profile_id', ''),
                username=adapted_profile.get('username', ''),
                email=adapted_profile.get('email'),
                created_date=adapted_profile.get('created_date', ''),
                last_updated=datetime.now().isoformat(),
                hardware_profile=hardware,
                preferences=preferences,
                installed_apps=adapted_profile.get('installed_apps', []),
                custom_configurations=adapted_profile.get('custom_configurations', {}),
                sync_settings=adapted_profile.get('sync_settings', {}),
                version=adapted_profile.get('version', '1.0')
            )
            
            self.current_profile = synced_profile
            self.save_profile()
            
            return True, "Profile synced successfully with hardware adaptations"
            
        except Exception as e:
            return False, f"Sync failed: {str(e)}"
    
    def adapt_profile_to_hardware(self, profile_data: Dict) -> Dict:
        """Intelligently adapt profile to current hardware"""
        current_hw = self.detect_hardware_profile()
        synced_hw = profile_data.get('hardware_profile', {})
        
        # Update hardware profile to current system
        profile_data['hardware_profile'] = asdict(current_hw)
        
        # Adapt preferences based on hardware differences
        preferences = profile_data.get('preferences', {})
        
        # Performance profile adaptation
        synced_apple_silicon = synced_hw.get('apple_silicon_model', 'Unknown')
        current_apple_silicon = current_hw.apple_silicon_model
        
        if synced_apple_silicon != current_apple_silicon:
            # Adapt performance settings for different Apple Silicon
            if current_apple_silicon in ['M1']:
                # M1 might need more conservative settings
                if preferences.get('performance_profile') == 'performance':
                    preferences['performance_profile'] = 'balanced'
            elif current_apple_silicon in ['M3', 'M4']:
                # Newer chips can handle more aggressive settings
                pass
        
        # RAM-based adaptations
        synced_ram = synced_hw.get('ram_gb', 8)
        current_ram = current_hw.ram_gb
        
        if current_ram < synced_ram:
            # Less RAM - be more conservative
            preferences['auto_update_settings'] = preferences.get('auto_update_settings', {})
            preferences['auto_update_settings']['app_updates'] = False
        
        # Desktop environment adaptations
        synced_de = synced_hw.get('desktop_environment', '')
        current_de = current_hw.desktop_environment
        
        if synced_de != current_de:
            # Different DE might need different theme preferences
            theme_prefs = preferences.get('theme_preferences', {})
            if current_de.lower() in ['kde', 'plasma']:
                theme_prefs['style_preference'] = 'plasma_compatible'
            elif current_de.lower() in ['gnome']:
                theme_prefs['style_preference'] = 'gtk_compatible'
        
        return profile_data
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        if not self.current_profile:
            return {'enabled': False, 'status': 'No profile'}
        
        sync_settings = self.current_profile.sync_settings
        
        return {
            'enabled': sync_settings.get('enabled', False),
            'provider': sync_settings.get('provider'),
            'last_sync': sync_settings.get('last_sync'),
            'status': 'Configured' if sync_settings.get('enabled') else 'Disabled'
        }

import os