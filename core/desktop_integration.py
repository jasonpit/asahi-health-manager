#!/usr/bin/env python3
"""
Desktop Integration Manager
Creates desktop entries and launcher icons for installed applications
"""

import os
import subprocess
import logging
from typing import Dict, Optional, List
from pathlib import Path
from core.app_manager import Application, AppCategory

logger = logging.getLogger(__name__)


class DesktopIntegration:
    """Manages desktop integration for installed applications"""
    
    def __init__(self):
        self.desktop_dir = Path.home() / '.local' / 'share' / 'applications'
        self.icon_dir = Path.home() / '.local' / 'share' / 'icons' / 'hicolor'
        self.desktop_dir.mkdir(parents=True, exist_ok=True)
        self.icon_dir.mkdir(parents=True, exist_ok=True)
        
        # Icon mapping for applications that might not have proper desktop entries
        self.icon_mappings = self._initialize_icon_mappings()
        
        # Category mappings for desktop entries
        self.category_mappings = {
            AppCategory.DEVELOPMENT: ["Development", "IDE", "Programming"],
            AppCategory.PRODUCTIVITY: ["Office", "Productivity", "TextEditor"],
            AppCategory.MULTIMEDIA: ["AudioVideo", "Multimedia", "Player"],
            AppCategory.GAMING: ["Game", "Amusement"],
            AppCategory.COMMUNICATION: ["Network", "Communication", "Chat"],
            AppCategory.SYSTEM: ["System", "Settings", "Utility"],
            AppCategory.GRAPHICS: ["Graphics", "Photography", "2DGraphics"],
            AppCategory.THEMES: ["Settings", "DesktopSettings", "Appearance"],
            AppCategory.NETWORK: ["Network", "Internet"],
            AppCategory.EDUCATION: ["Education", "Science"],
            AppCategory.UTILITIES: ["Utility", "Accessories"]
        }
    
    def _initialize_icon_mappings(self) -> Dict[str, str]:
        """Initialize icon name mappings for applications with terminal-themed icons"""
        base_dir = Path(__file__).parent.parent
        
        return {
            # Development - Use terminal-themed icons where available
            "vscode": str(base_dir / "icons/terminal-theme/vscode.svg"),
            "code": str(base_dir / "icons/terminal-theme/vscode.svg"),
            "neovim": str(base_dir / "icons/terminal-theme/vim.svg"),
            "nvim": str(base_dir / "icons/terminal-theme/vim.svg"),
            "vim": str(base_dir / "icons/terminal-theme/vim.svg"),
            "git": str(base_dir / "icons/terminal-theme/git.svg"),
            "docker": str(base_dir / "icons/terminal-theme/docker.svg"),
            "python3-pip": str(base_dir / "icons/terminal-theme/python.svg"),
            "pip3": str(base_dir / "icons/terminal-theme/python.svg"),
            "python3": str(base_dir / "icons/terminal-theme/python.svg"),
            "rust": str(base_dir / "icons/terminal-theme/rust.svg"),
            "rustc": str(base_dir / "icons/terminal-theme/rust.svg"),
            "cargo": str(base_dir / "icons/terminal-theme/rust.svg"),
            "nodejs": "nodejs",
            "node": "nodejs",
            
            # Productivity
            "firefox": str(base_dir / "icons/terminal-theme/firefox.svg"),
            "chromium": "chromium-browser",
            "thunderbird": "thunderbird",
            "libreoffice": "libreoffice-startcenter",
            "obsidian": "obsidian",
            
            # Multimedia  
            "vlc": str(base_dir / "icons/terminal-theme/vlc.svg"),
            "mpv": "io.mpv.Mpv",
            "spotify": "spotify",
            "audacity": "audacity",
            
            # Graphics
            "gimp": "org.gimp.GIMP",
            "inkscape": "org.inkscape.Inkscape",
            "krita": str(base_dir / "icons/terminal-theme/krita.svg"),
            "blender": str(base_dir / "icons/terminal-theme/blender.svg"),
            
            # Communication
            "discord": "discord",
            "slack": "com.slack.Slack",
            "signal": "org.signal.Signal",
            
            # System Tools
            "asahi-audio": str(base_dir / "icons/terminal-theme/asahi-audio.svg"),
            "htop": "utilities-system-monitor",
            "neofetch": "utilities-system-monitor",
            "timeshift": "org.teejee2008.Timeshift",
            "gparted": "gparted",
            
            # Gaming
            "wine": "wine",
            "lutris": "net.lutris.Lutris",
            "steam": str(base_dir / "icons/terminal-theme/steam.svg"),
            "bottles": "com.usebottles.bottles",
            "supertuxkart": "supertuxkart",
            "minetest": "net.minetest.Minetest",
            
            # Utilities
            "keepassxc": "org.keepassxc.KeePassXC",
            "flameshot": "org.flameshot.Flameshot",
            "rclone": "folder-cloud"
        }
    
    def create_desktop_entry(self, app: Application) -> bool:
        """Create a desktop entry for an application"""
        try:
            # Check if the application already has a proper desktop entry
            if self._has_existing_desktop_entry(app):
                logger.debug(f"Desktop entry already exists for {app.display_name}")
                return True
            
            desktop_file_path = self.desktop_dir / f"asahi-{app.name}.desktop"
            
            # Get icon name
            icon_name = self._get_icon_name(app)
            
            # Get categories
            categories = self._get_desktop_categories(app)
            
            # Generate executable command
            exec_command = self._get_exec_command(app)
            if not exec_command:
                logger.warning(f"No executable found for {app.display_name}")
                return False
            
            # Create desktop entry content
            desktop_content = self._generate_desktop_content(app, icon_name, categories, exec_command)
            
            # Write desktop file
            with open(desktop_file_path, 'w') as f:
                f.write(desktop_content)
            
            # Make executable
            os.chmod(desktop_file_path, 0o755)
            
            logger.info(f"Created desktop entry for {app.display_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create desktop entry for {app.display_name}: {e}")
            return False
    
    def _has_existing_desktop_entry(self, app: Application) -> bool:
        """Check if application already has a desktop entry"""
        # Check system locations
        system_locations = [
            Path('/usr/share/applications'),
            Path('/usr/local/share/applications'),
            Path.home() / '.local' / 'share' / 'applications'
        ]
        
        possible_names = [
            f"{app.name}.desktop",
            f"{app.package_name}.desktop",
            f"{app.display_name.lower().replace(' ', '-')}.desktop"
        ]
        
        for location in system_locations:
            if location.exists():
                for name in possible_names:
                    if (location / name).exists():
                        return True
        return False
    
    def _get_icon_name(self, app: Application) -> str:
        """Get appropriate icon name for the application"""
        # Try mapped icon first
        if app.name in self.icon_mappings:
            return self.icon_mappings[app.name]
        
        # Try package name
        if app.package_name in self.icon_mappings:
            return self.icon_mappings[app.package_name]
        
        # Try to find icon by common patterns
        icon_search_names = [
            app.name,
            app.package_name,
            app.display_name.lower().replace(' ', '-'),
            app.display_name.lower().replace(' ', '_')
        ]
        
        for name in icon_search_names:
            if self._icon_exists(name):
                return name
        
        # Fallback to terminal-themed category icons
        base_dir = Path(__file__).parent.parent
        category_icons = {
            AppCategory.DEVELOPMENT: str(base_dir / "icons/terminal-theme/development.svg"),
            AppCategory.PRODUCTIVITY: str(base_dir / "icons/terminal-theme/productivity.svg"),
            AppCategory.MULTIMEDIA: str(base_dir / "icons/terminal-theme/multimedia.svg"),
            AppCategory.GAMING: str(base_dir / "icons/terminal-theme/gaming.svg"),
            AppCategory.COMMUNICATION: str(base_dir / "icons/terminal-theme/productivity.svg"),
            AppCategory.SYSTEM: str(base_dir / "icons/terminal-theme/system.svg"),
            AppCategory.GRAPHICS: str(base_dir / "icons/terminal-theme/multimedia.svg"),
            AppCategory.THEMES: str(base_dir / "icons/terminal-theme/themes.svg"),
            AppCategory.NETWORK: str(base_dir / "icons/terminal-theme/system.svg"),
            AppCategory.EDUCATION: str(base_dir / "icons/terminal-theme/productivity.svg"),
            AppCategory.UTILITIES: str(base_dir / "icons/terminal-theme/system.svg")
        }
        
        return category_icons.get(app.category, str(base_dir / "icons/terminal-theme/system.svg"))
    
    def _icon_exists(self, icon_name: str) -> bool:
        """Check if an icon exists in the system"""
        # Check common icon locations directly
        icon_locations = [
            Path('/usr/share/icons'),
            Path('/usr/share/pixmaps'),
            Path('/usr/share/icons/hicolor'),
            self.icon_dir
        ]
        
        # Also check subdirectories in hicolor theme
        hicolor_subdirs = ['scalable/apps', '48x48/apps', '32x32/apps', '24x24/apps', '16x16/apps']
        
        for location in icon_locations:
            if location.exists():
                # Check root directory
                for ext in ['svg', 'png', 'xpm']:
                    if (location / f"{icon_name}.{ext}").exists():
                        return True
                
                # Check hicolor subdirectories if this is an icon directory
                if 'icons' in str(location):
                    for subdir in hicolor_subdirs:
                        subdir_path = location / subdir
                        if subdir_path.exists():
                            for ext in ['svg', 'png', 'xpm']:
                                if (subdir_path / f"{icon_name}.{ext}").exists():
                                    return True
        
        return False
    
    def _get_desktop_categories(self, app: Application) -> str:
        """Get desktop categories for the application"""
        base_categories = self.category_mappings.get(app.category, ["Application"])
        
        # Add additional categories based on app type
        if any(keyword in app.description.lower() for keyword in ['terminal', 'command', 'cli']):
            base_categories.append("TerminalEmulator")
        
        if any(keyword in app.description.lower() for keyword in ['editor', 'ide']):
            base_categories.append("TextEditor")
        
        return ";".join(base_categories) + ";"
    
    def _get_exec_command(self, app: Application) -> Optional[str]:
        """Get the executable command for the application"""
        # For Flatpak apps
        if app.package_manager.value == "flatpak":
            return f"flatpak run {app.package_name}"
        
        # For source/special apps
        if app.package_manager.value == "source":
            if app.name == "theme-manager":
                return f"python3 {Path(__file__).parent.parent}/ui/theme_manager_ui.py"
            elif app.name == "rust":
                return "rustc"
            elif app.name == "box64":
                return "box64"
        
        # Try common executable names
        possible_executables = [
            app.name,
            app.package_name,
            app.name.replace('-', ''),
            app.display_name.lower().replace(' ', '-')
        ]
        
        for exe in possible_executables:
            if self._command_exists(exe):
                return exe
        
        return None
    
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH"""
        try:
            result = subprocess.run(
                ["which", command],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except:
            return False
    
    def _generate_desktop_content(self, app: Application, icon_name: str, 
                                 categories: str, exec_command: str) -> str:
        """Generate desktop entry content"""
        content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={app.display_name}
GenericName={app.display_name}
Comment={app.description}
Icon={icon_name}
Exec={exec_command}
Terminal=false
Categories={categories}
Keywords={app.name};{app.package_name};{app.category.value.lower()};
StartupNotify=true
"""
        
        # Add web browser specific fields
        if app.category == AppCategory.PRODUCTIVITY and "browser" in app.description.lower():
            content += "MimeType=text/html;text/xml;application/xhtml+xml;x-scheme-handler/http;x-scheme-handler/https;\n"
        
        # Add development specific fields
        if app.category == AppCategory.DEVELOPMENT:
            content += "Keywords=development;programming;coding;ide;\n"
        
        # Add terminal flag for CLI tools
        if any(keyword in app.description.lower() for keyword in ['terminal', 'command', 'cli']):
            content = content.replace("Terminal=false", "Terminal=true")
        
        return content
    
    def remove_desktop_entry(self, app: Application) -> bool:
        """Remove desktop entry for an application"""
        try:
            desktop_file_path = self.desktop_dir / f"asahi-{app.name}.desktop"
            if desktop_file_path.exists():
                desktop_file_path.unlink()
                logger.info(f"Removed desktop entry for {app.display_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove desktop entry for {app.display_name}: {e}")
            return False
    
    def update_desktop_database(self) -> bool:
        """Update the desktop database"""
        try:
            if self._command_exists("update-desktop-database"):
                subprocess.run(
                    ["update-desktop-database", str(self.desktop_dir)],
                    capture_output=True,
                    timeout=10
                )
                logger.info("Updated desktop database")
                return True
        except Exception as e:
            logger.warning(f"Failed to update desktop database: {e}")
        return False
    
    def create_desktop_entries_for_installed_apps(self, installed_apps: List[str], 
                                                 apps_database: Dict[str, Application]) -> Dict[str, bool]:
        """Create desktop entries for all installed applications"""
        results = {}
        
        for app_name in installed_apps:
            if app_name in apps_database:
                app = apps_database[app_name]
                success = self.create_desktop_entry(app)
                results[app_name] = success
        
        # Update desktop database after creating entries
        self.update_desktop_database()
        
        return results
    
    def install_app_with_desktop_integration(self, app: Application, 
                                           install_func) -> tuple[bool, str]:
        """Install an app and create its desktop entry"""
        # Install the application
        success, message = install_func(app.name, dry_run=False)
        
        if success:
            # Create desktop entry
            desktop_success = self.create_desktop_entry(app)
            
            if desktop_success:
                return True, f"{message} Desktop launcher created."
            else:
                return True, f"{message} Warning: Desktop launcher creation failed."
        
        return success, message