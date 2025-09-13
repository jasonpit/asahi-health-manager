#!/usr/bin/env python3
"""
Intelligent Application Manager for Asahi Linux
Provides curated app recommendations and easy installation for Asahi Linux users
"""

import json
import subprocess
import logging
import asyncio
import concurrent.futures
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class PackageManager(Enum):
    """Supported package managers"""
    DNF = "dnf"
    YUM = "yum"
    FLATPAK = "flatpak"
    SNAP = "snap"
    APPIMAGE = "appimage"
    SOURCE = "source"


class AppCategory(Enum):
    """Application categories"""
    DEVELOPMENT = "Development"
    PRODUCTIVITY = "Productivity"
    MULTIMEDIA = "Multimedia"
    GAMING = "Gaming"
    COMMUNICATION = "Communication"
    SYSTEM = "System Tools"
    GRAPHICS = "Graphics & Design"
    THEMES = "Themes & Customization"
    NETWORK = "Network"
    EDUCATION = "Education"
    UTILITIES = "Utilities"


@dataclass
class Application:
    """Application metadata"""
    name: str
    display_name: str
    category: AppCategory
    description: str
    package_name: str
    package_manager: PackageManager
    homepage: str = ""
    asahi_compatible: bool = True
    performance_notes: str = ""
    alternatives: List[str] = None
    dependencies: List[str] = None
    post_install_commands: List[str] = None
    verification_command: str = ""
    size_mb: int = 0
    popularity_score: int = 0  # 1-10 scale

    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []
        if self.dependencies is None:
            self.dependencies = []
        if self.post_install_commands is None:
            self.post_install_commands = []


class AsahiAppManager:
    """Manages application recommendations and installation for Asahi Linux"""
    
    def __init__(self):
        self.apps_database = self._initialize_apps_database()
        self.installed_apps = set()
        self._detect_installed_apps()
        
        # Initialize desktop integration
        try:
            from core.desktop_integration import DesktopIntegration
            self.desktop_integration = DesktopIntegration()
        except ImportError:
            logger.warning("Desktop integration not available")
            self.desktop_integration = None
        
    def _initialize_apps_database(self) -> Dict[str, Application]:
        """Initialize the curated database of applications"""
        apps = [
            # Development Tools
            Application(
                name="vscode",
                display_name="Visual Studio Code",
                category=AppCategory.DEVELOPMENT,
                description="Powerful code editor with extensive plugin support",
                package_name="code",
                package_manager=PackageManager.DNF,
                homepage="https://code.visualstudio.com/",
                verification_command="code --version",
                size_mb=350,
                popularity_score=10
            ),
            Application(
                name="neovim",
                display_name="Neovim",
                category=AppCategory.DEVELOPMENT,
                description="Hyperextensible Vim-based text editor",
                package_name="neovim",
                package_manager=PackageManager.DNF,
                verification_command="nvim --version",
                size_mb=50,
                popularity_score=9
            ),
            Application(
                name="git",
                display_name="Git",
                category=AppCategory.DEVELOPMENT,
                description="Distributed version control system",
                package_name="git",
                package_manager=PackageManager.DNF,
                verification_command="git --version",
                size_mb=45,
                popularity_score=10
            ),
            Application(
                name="docker",
                display_name="Docker",
                category=AppCategory.DEVELOPMENT,
                description="Container platform for application deployment",
                package_name="docker-ce",
                package_manager=PackageManager.DNF,
                post_install_commands=[
                    "sudo systemctl enable docker",
                    "sudo systemctl start docker",
                    "sudo usermod -aG docker $USER"
                ],
                verification_command="docker --version",
                size_mb=500,
                popularity_score=9
            ),
            Application(
                name="rust",
                display_name="Rust (via rustup)",
                category=AppCategory.DEVELOPMENT,
                description="Rust programming language toolchain (16K page compatible)",
                package_name="rustup",
                package_manager=PackageManager.SOURCE,
                homepage="https://rustup.rs/",
                post_install_commands=[
                    "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
                    "source $HOME/.cargo/env"
                ],
                performance_notes="Use rustup instead of system packages to avoid 16K page issues",
                verification_command="rustc --version",
                size_mb=600,
                popularity_score=8
            ),
            Application(
                name="nodejs",
                display_name="Node.js",
                category=AppCategory.DEVELOPMENT,
                description="JavaScript runtime built on Chrome's V8 engine",
                package_name="nodejs",
                package_manager=PackageManager.DNF,
                verification_command="node --version",
                size_mb=100,
                popularity_score=9
            ),
            Application(
                name="python3-pip",
                display_name="Python Pip",
                category=AppCategory.DEVELOPMENT,
                description="Python package installer",
                package_name="python3-pip",
                package_manager=PackageManager.DNF,
                verification_command="pip3 --version",
                size_mb=20,
                popularity_score=9
            ),
            
            # Productivity
            Application(
                name="firefox",
                display_name="Firefox",
                category=AppCategory.PRODUCTIVITY,
                description="Privacy-focused web browser",
                package_name="firefox",
                package_manager=PackageManager.DNF,
                verification_command="firefox --version",
                size_mb=250,
                popularity_score=10
            ),
            Application(
                name="chromium",
                display_name="Chromium",
                category=AppCategory.PRODUCTIVITY,
                description="Open-source web browser",
                package_name="chromium",
                package_manager=PackageManager.DNF,
                verification_command="chromium-browser --version",
                size_mb=300,
                popularity_score=8
            ),
            Application(
                name="thunderbird",
                display_name="Thunderbird",
                category=AppCategory.PRODUCTIVITY,
                description="Email, calendar, and chat client",
                package_name="thunderbird",
                package_manager=PackageManager.DNF,
                verification_command="thunderbird --version",
                size_mb=200,
                popularity_score=7
            ),
            Application(
                name="libreoffice",
                display_name="LibreOffice",
                category=AppCategory.PRODUCTIVITY,
                description="Complete office suite (Writer, Calc, Impress)",
                package_name="libreoffice",
                package_manager=PackageManager.DNF,
                verification_command="libreoffice --version",
                size_mb=800,
                popularity_score=8
            ),
            Application(
                name="obsidian",
                display_name="Obsidian",
                category=AppCategory.PRODUCTIVITY,
                description="Knowledge base and note-taking app",
                package_name="obsidian",
                package_manager=PackageManager.FLATPAK,
                verification_command="flatpak list | grep obsidian",
                size_mb=150,
                popularity_score=8
            ),
            
            # Multimedia
            Application(
                name="vlc",
                display_name="VLC Media Player",
                category=AppCategory.MULTIMEDIA,
                description="Versatile media player supporting most formats",
                package_name="vlc",
                package_manager=PackageManager.DNF,
                homepage="https://www.videolan.org/vlc/",
                performance_notes="Excellent hardware acceleration support on Apple Silicon",
                verification_command="vlc --version",
                size_mb=150,
                popularity_score=9
            ),
            Application(
                name="mpv",
                display_name="MPV",
                category=AppCategory.MULTIMEDIA,
                description="Lightweight and powerful media player",
                package_name="mpv",
                package_manager=PackageManager.DNF,
                verification_command="mpv --version",
                size_mb=50,
                popularity_score=8
            ),
            Application(
                name="spotify",
                display_name="Spotify",
                category=AppCategory.MULTIMEDIA,
                description="Music streaming service",
                package_name="com.spotify.Client",
                package_manager=PackageManager.FLATPAK,
                verification_command="flatpak list | grep spotify",
                size_mb=300,
                popularity_score=9
            ),
            Application(
                name="audacity",
                display_name="Audacity",
                category=AppCategory.MULTIMEDIA,
                description="Audio editor and recorder",
                package_name="audacity",
                package_manager=PackageManager.DNF,
                verification_command="audacity --version",
                size_mb=100,
                popularity_score=7
            ),
            
            # Graphics & Design
            Application(
                name="gimp",
                display_name="GIMP",
                category=AppCategory.GRAPHICS,
                description="Advanced image editor (Photoshop alternative)",
                package_name="gimp",
                package_manager=PackageManager.DNF,
                verification_command="gimp --version",
                size_mb=250,
                popularity_score=8
            ),
            Application(
                name="inkscape",
                display_name="Inkscape",
                category=AppCategory.GRAPHICS,
                description="Vector graphics editor (Illustrator alternative)",
                package_name="inkscape",
                package_manager=PackageManager.DNF,
                verification_command="inkscape --version",
                size_mb=200,
                popularity_score=7
            ),
            Application(
                name="krita",
                display_name="Krita",
                category=AppCategory.GRAPHICS,
                description="Professional digital painting and illustration software",
                package_name="krita",
                package_manager=PackageManager.DNF,
                homepage="https://krita.org/",
                performance_notes="Excellent for digital art on Apple Silicon. Supports pressure-sensitive tablets.",
                verification_command="krita --version",
                size_mb=300,
                popularity_score=9
            ),
            Application(
                name="blender",
                display_name="Blender",
                category=AppCategory.GRAPHICS,
                description="3D creation suite",
                package_name="blender",
                package_manager=PackageManager.DNF,
                performance_notes="GPU acceleration available with Asahi graphics drivers",
                verification_command="blender --version",
                size_mb=500,
                popularity_score=8
            ),
            
            # Communication
            Application(
                name="discord",
                display_name="Discord",
                category=AppCategory.COMMUNICATION,
                description="Voice, video, and text communication",
                package_name="com.discordapp.Discord",
                package_manager=PackageManager.FLATPAK,
                verification_command="flatpak list | grep discord",
                size_mb=200,
                popularity_score=9
            ),
            Application(
                name="slack",
                display_name="Slack",
                category=AppCategory.COMMUNICATION,
                description="Team collaboration and messaging",
                package_name="com.slack.Slack",
                package_manager=PackageManager.FLATPAK,
                verification_command="flatpak list | grep slack",
                size_mb=250,
                popularity_score=7
            ),
            Application(
                name="signal",
                display_name="Signal",
                category=AppCategory.COMMUNICATION,
                description="Privacy-focused messaging app",
                package_name="org.signal.Signal",
                package_manager=PackageManager.FLATPAK,
                verification_command="flatpak list | grep signal",
                size_mb=150,
                popularity_score=7
            ),
            
            # System Tools - Critical Asahi Components
            Application(
                name="asahi-audio",
                display_name="Asahi Audio",
                category=AppCategory.SYSTEM,
                description="Essential audio configuration for Apple Silicon Macs - provides DSP processing",
                package_name="asahi-audio",
                package_manager=PackageManager.DNF,
                homepage="https://github.com/AsahiLinux/asahi-audio",
                performance_notes="CRITICAL: Required for proper audio on Apple Silicon. Provides DSP configuration for speakers and microphones. Aims for better audio than macOS.",
                dependencies=["speakersafetyd", "linux-asahi"],
                post_install_commands=[
                    "sudo systemctl enable --now speakersafetyd",
                    "systemctl --user restart wireplumber"
                ],
                verification_command="systemctl --user status wireplumber | grep -q asahi-audio || systemctl is-active speakersafetyd",
                size_mb=50,
                popularity_score=10,
                asahi_compatible=True
            ),
            Application(
                name="htop",
                display_name="htop",
                category=AppCategory.SYSTEM,
                description="Interactive process viewer",
                package_name="htop",
                package_manager=PackageManager.DNF,
                verification_command="htop --version",
                size_mb=5,
                popularity_score=9
            ),
            Application(
                name="neofetch",
                display_name="Neofetch",
                category=AppCategory.SYSTEM,
                description="System information display tool",
                package_name="neofetch",
                package_manager=PackageManager.DNF,
                verification_command="neofetch --version",
                size_mb=2,
                popularity_score=8
            ),
            Application(
                name="timeshift",
                display_name="Timeshift",
                category=AppCategory.SYSTEM,
                description="System backup and restore utility",
                package_name="timeshift",
                package_manager=PackageManager.DNF,
                verification_command="timeshift --version",
                size_mb=50,
                popularity_score=7
            ),
            Application(
                name="gparted",
                display_name="GParted",
                category=AppCategory.SYSTEM,
                description="Partition editor",
                package_name="gparted",
                package_manager=PackageManager.DNF,
                verification_command="gparted --version",
                size_mb=50,
                popularity_score=7
            ),
            
            # Gaming (with Asahi compatibility notes)
            Application(
                name="wine",
                display_name="Wine",
                category=AppCategory.GAMING,
                description="Windows compatibility layer for running Windows applications",
                package_name="wine",
                package_manager=PackageManager.DNF,
                homepage="https://www.winehq.org/",
                performance_notes="Requires Box64 for x86 Windows apps on Apple Silicon. ARM64 Windows apps work natively.",
                dependencies=["box64"],
                verification_command="wine --version",
                size_mb=200,
                popularity_score=8
            ),
            Application(
                name="lutris",
                display_name="Lutris",
                category=AppCategory.GAMING,
                description="Gaming platform for Linux with Wine integration",
                package_name="lutris",
                package_manager=PackageManager.DNF,
                performance_notes="x86 emulation required for many games. Includes Wine management.",
                dependencies=["wine", "box64"],
                verification_command="lutris --version",
                size_mb=100,
                popularity_score=7
            ),
            Application(
                name="box64",
                display_name="Box64",
                category=AppCategory.GAMING,
                description="x86-64 emulator for ARM64",
                package_name="box64",
                package_manager=PackageManager.SOURCE,
                homepage="https://github.com/ptitSeb/box64",
                performance_notes="Essential for running x86 games and Windows apps on Apple Silicon",
                size_mb=50,
                popularity_score=8
            ),
            Application(
                name="bottles",
                display_name="Bottles",
                category=AppCategory.GAMING,
                description="Modern Wine wrapper with easy Windows app management",
                package_name="com.usebottles.bottles",
                package_manager=PackageManager.FLATPAK,
                homepage="https://usebottles.com/",
                performance_notes="User-friendly Wine frontend. Works with Box64 for x86 Windows apps.",
                dependencies=["wine"],
                verification_command="flatpak list | grep bottles",
                size_mb=150,
                popularity_score=7
            ),
            Application(
                name="steam",
                display_name="Steam (Experimental)",
                category=AppCategory.GAMING,
                description="Steam gaming platform with ARM64/x86 emulation support",
                package_name="steam",
                package_manager=PackageManager.DNF,
                homepage="https://store.steampowered.com/",
                performance_notes="EXPERIMENTAL: Requires Box64 for x86 games. Native ARM64 games work best. Some games may not work. Use Lutris for better compatibility.",
                dependencies=["box64"],
                alternatives=["lutris", "bottles"],
                post_install_commands=[
                    "# Enable Proton for Windows games",
                    "# Note: Performance varies significantly"
                ],
                verification_command="steam --version",
                size_mb=500,
                popularity_score=6
            ),
            Application(
                name="steam-flatpak",
                display_name="Steam (Flatpak)",
                category=AppCategory.GAMING,
                description="Steam via Flatpak with better sandboxing",
                package_name="com.valvesoftware.Steam",
                package_manager=PackageManager.FLATPAK,
                homepage="https://flathub.org/apps/details/com.valvesoftware.Steam",
                performance_notes="EXPERIMENTAL: Flatpak version may have better compatibility. Still requires x86 emulation for most games.",
                dependencies=["box64"],
                alternatives=["steam", "lutris"],
                verification_command="flatpak list | grep steam",
                size_mb=600,
                popularity_score=5
            ),
            Application(
                name="supertuxkart",
                display_name="SuperTuxKart",
                category=AppCategory.GAMING,
                description="Fun 3D kart racing game (native ARM64)",
                package_name="supertuxkart",
                package_manager=PackageManager.DNF,
                homepage="https://supertuxkart.net/",
                performance_notes="Native ARM64 game - excellent performance on Apple Silicon with Asahi graphics drivers",
                verification_command="supertuxkart --version",
                size_mb=300,
                popularity_score=7
            ),
            Application(
                name="minetest",
                display_name="Minetest",
                category=AppCategory.GAMING,
                description="Open-source voxel game (native ARM64)",
                package_name="minetest",
                package_manager=PackageManager.DNF,
                homepage="https://www.minetest.net/",
                performance_notes="Native ARM64 game - great performance on Apple Silicon",
                verification_command="minetest --version",
                size_mb=100,
                popularity_score=6
            ),
            
            # Themes & Customization
            Application(
                name="theme-manager",
                display_name="Theme Manager",
                category=AppCategory.THEMES,
                description="Comprehensive desktop theming system with curated themes, icons, and fonts",
                package_name="theme-manager",
                package_manager=PackageManager.SOURCE,
                homepage="Built-in theme management system",
                performance_notes="Detects your desktop environment and offers compatible themes. Includes GTK themes, icon packs, cursors, wallpapers, and fonts.",
                verification_command="# Built-in component",
                size_mb=0,
                popularity_score=10,
                asahi_compatible=True
            ),
            
            # Utilities
            Application(
                name="keepassxc",
                display_name="KeePassXC",
                category=AppCategory.UTILITIES,
                description="Password manager",
                package_name="keepassxc",
                package_manager=PackageManager.DNF,
                verification_command="keepassxc --version",
                size_mb=50,
                popularity_score=8
            ),
            Application(
                name="flameshot",
                display_name="Flameshot",
                category=AppCategory.UTILITIES,
                description="Powerful screenshot tool",
                package_name="flameshot",
                package_manager=PackageManager.DNF,
                verification_command="flameshot --version",
                size_mb=20,
                popularity_score=8
            ),
            Application(
                name="rclone",
                display_name="Rclone",
                category=AppCategory.UTILITIES,
                description="Cloud storage sync tool",
                package_name="rclone",
                package_manager=PackageManager.DNF,
                verification_command="rclone --version",
                size_mb=50,
                popularity_score=7
            ),
        ]
        
        return {app.name: app for app in apps}
    
    def _detect_installed_apps(self):
        """Detect which applications are already installed"""
        for app_name, app in self.apps_database.items():
            if self._is_app_installed(app):
                self.installed_apps.add(app_name)
                logger.debug(f"Detected installed app: {app.display_name}")
    
    def get_all_installed_packages(self) -> Dict[str, List[str]]:
        """Get comprehensive list of all installed packages from all package managers"""
        installed = {
            'dnf': [],
            'flatpak': [],
            'snap': [],
            'pip': [],
            'npm': [],
            'cargo': []
        }
        
        # DNF/RPM packages
        try:
            result = subprocess.run(
                ["rpm", "-qa", "--queryformat", "%{NAME}\n"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                installed['dnf'] = sorted([pkg.strip() for pkg in result.stdout.split('\n') if pkg.strip()])
        except Exception as e:
            logger.warning(f"Failed to query DNF packages: {e}")
        
        # Flatpak packages
        try:
            result = subprocess.run(
                ["flatpak", "list", "--app", "--columns=application"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                installed['flatpak'] = sorted([pkg.strip() for pkg in result.stdout.split('\n') if pkg.strip()])
        except Exception:
            pass  # Flatpak might not be installed
        
        # Snap packages
        try:
            result = subprocess.run(
                ["snap", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.split('\n')[1:]  # Skip header
                installed['snap'] = sorted([line.split()[0] for line in lines if line.strip()])
        except Exception:
            pass  # Snap might not be installed
        
        # Python pip packages
        try:
            result = subprocess.run(
                ["pip", "list", "--format=freeze"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                installed['pip'] = sorted([pkg.split('==')[0] for pkg in result.stdout.split('\n') if '==' in pkg])
        except Exception:
            pass
        
        # Node.js npm packages (global)
        try:
            result = subprocess.run(
                ["npm", "list", "-g", "--depth=0", "--json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                import json
                npm_data = json.loads(result.stdout)
                if 'dependencies' in npm_data:
                    installed['npm'] = sorted(list(npm_data['dependencies'].keys()))
        except Exception:
            pass
        
        # Rust cargo packages
        try:
            result = subprocess.run(
                ["cargo", "install", "--list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                cargo_packages = []
                for line in result.stdout.split('\n'):
                    if line and not line.startswith(' '):
                        pkg_name = line.split()[0]
                        if pkg_name.endswith(':'):
                            pkg_name = pkg_name[:-1]
                        cargo_packages.append(pkg_name)
                installed['cargo'] = sorted(cargo_packages)
        except Exception:
            pass
        
        return installed
    
    def _is_app_installed(self, app: Application) -> bool:
        """Check if an application is installed"""
        # Special handling for built-in components
        if app.name == "theme-manager":
            return False  # Always show as available to launch
            
        if app.verification_command and not app.verification_command.startswith('#'):
            try:
                result = subprocess.run(
                    app.verification_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return result.returncode == 0
            except (subprocess.TimeoutExpired, Exception):
                pass
        
        # Fallback to package manager check
        if app.package_manager == PackageManager.DNF:
            return self._check_dnf_package(app.package_name)
        elif app.package_manager == PackageManager.FLATPAK:
            return self._check_flatpak_package(app.package_name)
        
        return False
    
    def _check_dnf_package(self, package: str) -> bool:
        """Check if a DNF package is installed"""
        try:
            result = subprocess.run(
                ["rpm", "-q", package],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _check_flatpak_package(self, package: str) -> bool:
        """Check if a Flatpak package is installed"""
        try:
            result = subprocess.run(
                ["flatpak", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return package in result.stdout
        except Exception:
            return False
    
    def get_apps_by_category(self, category: AppCategory) -> List[Application]:
        """Get all applications in a specific category"""
        return [
            app for app in self.apps_database.values()
            if app.category == category
        ]
    
    def get_recommended_apps(self, limit: int = 10) -> List[Application]:
        """Get top recommended applications based on popularity"""
        sorted_apps = sorted(
            self.apps_database.values(),
            key=lambda x: x.popularity_score,
            reverse=True
        )
        return [
            app for app in sorted_apps
            if app.name not in self.installed_apps
        ][:limit]
    
    def get_installation_command(self, app: Application) -> str:
        """Generate the installation command for an application"""
        if app.package_manager == PackageManager.DNF:
            return f"sudo dnf install -y {app.package_name}"
        elif app.package_manager == PackageManager.FLATPAK:
            return f"flatpak install -y flathub {app.package_name}"
        elif app.package_manager == PackageManager.SOURCE:
            if app.post_install_commands:
                return " && ".join(app.post_install_commands)
        return ""
    
    def install_app(self, app_name: str, dry_run: bool = False) -> Tuple[bool, str]:
        """Install an application"""
        if app_name not in self.apps_database:
            return False, f"Application '{app_name}' not found in database"
        
        app = self.apps_database[app_name]
        
        if app_name in self.installed_apps:
            return True, f"{app.display_name} is already installed"
        
        # Get installation command
        install_cmd = self.get_installation_command(app)
        if not install_cmd:
            return False, f"No installation method available for {app.display_name}"
        
        if dry_run:
            return True, f"Would run: {install_cmd}"
        
        # Install dependencies first
        for dep in app.dependencies:
            dep_success, dep_msg = self.install_app(dep, dry_run=False)
            if not dep_success:
                return False, f"Failed to install dependency {dep}: {dep_msg}"
        
        # Run installation
        try:
            logger.info(f"Installing {app.display_name}...")
            result = subprocess.run(
                install_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Run post-install commands if any
                for cmd in app.post_install_commands:
                    subprocess.run(cmd, shell=True, capture_output=True)
                
                # Verify installation
                if self._is_app_installed(app):
                    self.installed_apps.add(app_name)
                    
                    # Create desktop entry if desktop integration is available
                    desktop_msg = ""
                    if self.desktop_integration:
                        try:
                            desktop_success = self.desktop_integration.create_desktop_entry(app)
                            if desktop_success:
                                desktop_msg = " Desktop launcher created."
                            else:
                                desktop_msg = " Warning: Desktop launcher creation failed."
                        except Exception as e:
                            logger.warning(f"Desktop integration failed for {app.display_name}: {e}")
                            desktop_msg = " Warning: Desktop launcher creation failed."
                    
                    return True, f"Successfully installed {app.display_name}{desktop_msg}"
                else:
                    return False, f"Installation completed but verification failed for {app.display_name}"
            else:
                return False, f"Installation failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, f"Installation timed out for {app.display_name}"
        except Exception as e:
            return False, f"Installation error: {str(e)}"
    
    def install_app_fast(self, app_name: str, dry_run: bool = False) -> Tuple[bool, str]:
        """Fast installation with optimizations"""
        if app_name not in self.apps_database:
            return False, f"Application '{app_name}' not found in database"
        
        app = self.apps_database[app_name]
        
        if app_name in self.installed_apps:
            return True, f"{app.display_name} is already installed"
        
        # Get installation command
        install_cmd = self.get_installation_command(app)
        if not install_cmd:
            return False, f"No installation method available for {app.display_name}"
        
        if dry_run:
            return True, f"Would run: {install_cmd}"
        
        # Optimized installation with reduced timeout and parallel deps
        try:
            logger.info(f"Installing {app.display_name}...")
            
            # Install dependencies in parallel if multiple
            if len(app.dependencies) > 1:
                dep_results = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    future_to_dep = {
                        executor.submit(self.install_app_fast, dep): dep 
                        for dep in app.dependencies
                    }
                    
                    for future in concurrent.futures.as_completed(future_to_dep):
                        dep = future_to_dep[future]
                        try:
                            success, msg = future.result()
                            dep_results.append((success, dep, msg))
                        except Exception as e:
                            dep_results.append((False, dep, str(e)))
                
                # Check if any dependencies failed
                failed_deps = [dep for success, dep, msg in dep_results if not success]
                if failed_deps:
                    return False, f"Failed to install dependencies: {', '.join(failed_deps)}"
            
            # Sequential dependency installation for single deps
            elif app.dependencies:
                for dep in app.dependencies:
                    dep_success, dep_msg = self.install_app_fast(dep, dry_run=False)
                    if not dep_success:
                        return False, f"Failed to install dependency {dep}: {dep_msg}"
            
            # Optimize package manager commands
            optimized_cmd = self._optimize_install_command(install_cmd)
            
            # Run installation with reduced timeout
            result = subprocess.run(
                optimized_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120  # Reduced from 300 to 120 seconds
            )
            
            if result.returncode == 0:
                # Run post-install commands in background if they're non-critical
                if app.post_install_commands:
                    self._run_post_install_async(app.post_install_commands)
                
                # Quick verification
                if self._is_app_installed(app):
                    self.installed_apps.add(app_name)
                    return True, f"Successfully installed {app.display_name}"
                else:
                    return False, f"Installation completed but verification failed for {app.display_name}"
            else:
                error_msg = result.stderr.strip()[:200]  # Truncate long error messages
                return False, f"Installation failed: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, f"Installation timed out for {app.display_name}"
        except Exception as e:
            return False, f"Installation error: {str(e)}"
    
    def _optimize_install_command(self, cmd: str) -> str:
        """Optimize installation commands for speed"""
        # Add parallel download flags for DNF
        if 'dnf install' in cmd:
            if '--assumeyes' not in cmd:
                cmd = cmd.replace('dnf install', 'dnf install --assumeyes')
            if '--best' not in cmd:
                cmd = cmd.replace('dnf install', 'dnf install --best')
            # Enable parallel downloads
            cmd = cmd.replace('dnf install', 'dnf install --setopt=max_parallel_downloads=10')
        
        # Add quiet flags to reduce output processing
        if 'dnf' in cmd and '--quiet' not in cmd:
            cmd = cmd.replace('dnf', 'dnf --quiet')
        
        # Optimize flatpak installs
        if 'flatpak install' in cmd:
            if '--assumeyes' not in cmd:
                cmd = cmd.replace('flatpak install', 'flatpak install --assumeyes')
            if '--noninteractive' not in cmd:
                cmd = cmd.replace('flatpak install', 'flatpak install --noninteractive')
        
        return cmd
    
    def _run_post_install_async(self, commands: List[str]):
        """Run post-install commands asynchronously"""
        def run_commands():
            for cmd in commands:
                try:
                    subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
                except Exception as e:
                    logger.warning(f"Post-install command failed: {cmd}, error: {e}")
        
        # Run in background thread
        import threading
        thread = threading.Thread(target=run_commands)
        thread.daemon = True
        thread.start()
    
    def batch_install_optimized(self, app_names: List[str], max_workers: int = 3) -> Dict[str, Tuple[bool, str]]:
        """Install multiple applications in parallel with optimizations"""
        results = {}
        
        # Group applications by package manager for batch operations
        dnf_apps = []
        other_apps = []
        
        for app_name in app_names:
            if app_name in self.apps_database:
                app = self.apps_database[app_name]
                if app.package_manager == PackageManager.DNF:
                    dnf_apps.append(app_name)
                else:
                    other_apps.append(app_name)
        
        # Batch install DNF packages if possible
        if dnf_apps:
            batch_success = self._batch_install_dnf(dnf_apps)
            for app_name in dnf_apps:
                results[app_name] = batch_success.get(app_name, (False, "Batch install failed"))
        
        # Install other packages in parallel
        if other_apps:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_app = {
                    executor.submit(self.install_app_fast, app_name): app_name 
                    for app_name in other_apps
                }
                
                for future in concurrent.futures.as_completed(future_to_app):
                    app_name = future_to_app[future]
                    try:
                        results[app_name] = future.result()
                    except Exception as e:
                        results[app_name] = (False, str(e))
        
        return results
    
    def _batch_install_dnf(self, app_names: List[str]) -> Dict[str, Tuple[bool, str]]:
        """Batch install DNF packages for efficiency"""
        results = {}
        
        # Get package names
        package_names = []
        for app_name in app_names:
            if app_name in self.apps_database:
                app = self.apps_database[app_name]
                package_names.append(app.package_name)
        
        if not package_names:
            return results
        
        try:
            # Single DNF command for all packages
            cmd = f"dnf install --assumeyes --quiet --best --setopt=max_parallel_downloads=10 {' '.join(package_names)}"
            logger.info(f"Batch installing DNF packages: {', '.join(package_names)}")
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                # All packages installed successfully
                for app_name in app_names:
                    if app_name in self.apps_database:
                        app = self.apps_database[app_name]
                        if self._is_app_installed(app):
                            self.installed_apps.add(app_name)
                            results[app_name] = (True, f"Successfully installed {app.display_name}")
                        else:
                            results[app_name] = (False, f"Batch install completed but verification failed")
            else:
                # Fallback to individual installs
                logger.warning(f"Batch install failed, falling back to individual installs: {result.stderr}")
                for app_name in app_names:
                    results[app_name] = self.install_app_fast(app_name)
                    
        except Exception as e:
            logger.error(f"Batch install error: {e}")
            # Fallback to individual installs
            for app_name in app_names:
                results[app_name] = self.install_app_fast(app_name)
        
        return results
    
    def get_app_info(self, app_name: str) -> Optional[Application]:
        """Get detailed information about an application"""
        return self.apps_database.get(app_name)
    
    def search_apps(self, query: str) -> List[Application]:
        """Search for applications by name or description"""
        query_lower = query.lower()
        results = []
        
        for app in self.apps_database.values():
            if (query_lower in app.name.lower() or
                query_lower in app.display_name.lower() or
                query_lower in app.description.lower()):
                results.append(app)
        
        return sorted(results, key=lambda x: x.popularity_score, reverse=True)
    
    def get_categories_summary(self) -> Dict[AppCategory, Dict]:
        """Get a summary of apps by category"""
        summary = {}
        
        for category in AppCategory:
            category_apps = self.get_apps_by_category(category)
            installed = [app for app in category_apps if app.name in self.installed_apps]
            
            summary[category] = {
                "total": len(category_apps),
                "installed": len(installed),
                "available": len(category_apps) - len(installed),
                "apps": category_apps
            }
        
        return summary
    
    def create_desktop_entries_for_installed_apps(self) -> Dict[str, bool]:
        """Create desktop entries for all installed applications"""
        if not self.desktop_integration:
            logger.warning("Desktop integration not available")
            return {}
        
        results = {}
        success_count = 0
        
        logger.info(f"Creating desktop entries for {len(self.installed_apps)} installed apps...")
        
        for app_name in self.installed_apps:
            if app_name in self.apps_database:
                app = self.apps_database[app_name]
                try:
                    success = self.desktop_integration.create_desktop_entry(app)
                    results[app_name] = success
                    if success:
                        success_count += 1
                except Exception as e:
                    logger.error(f"Failed to create desktop entry for {app.display_name}: {e}")
                    results[app_name] = False
        
        # Update desktop database
        if success_count > 0:
            self.desktop_integration.update_desktop_database()
            logger.info(f"Created {success_count} desktop entries")
        
        return results
    
    def export_recommendations(self, output_file: Path) -> bool:
        """Export app recommendations to a JSON file"""
        try:
            recommendations = {
                "categories": {},
                "top_recommended": [],
                "installed": list(self.installed_apps)
            }
            
            # Add category data
            for category, data in self.get_categories_summary().items():
                recommendations["categories"][category.value] = {
                    "total": data["total"],
                    "installed": data["installed"],
                    "apps": [
                        {
                            "name": app.name,
                            "display_name": app.display_name,
                            "description": app.description,
                            "installed": app.name in self.installed_apps
                        }
                        for app in data["apps"]
                    ]
                }
            
            # Add top recommendations
            for app in self.get_recommended_apps(20):
                recommendations["top_recommended"].append({
                    "name": app.name,
                    "display_name": app.display_name,
                    "category": app.category.value,
                    "description": app.description,
                    "popularity": app.popularity_score
                })
            
            with open(output_file, 'w') as f:
                json.dump(recommendations, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to export recommendations: {e}")
            return False
    
    def get_system_updates(self) -> Dict[str, any]:
        """Check for available system updates across all package managers"""
        updates = {
            'dnf': {'available': [], 'count': 0, 'security': 0},
            'flatpak': {'available': [], 'count': 0},
            'firmware': {'available': [], 'count': 0},
            'total_count': 0,
            'reboot_required': False
        }
        
        # Check DNF updates
        try:
            result = subprocess.run(
                ["dnf", "check-update", "--quiet"],
                capture_output=True,
                text=True,
                timeout=30
            )
            # DNF returns 100 if updates are available
            if result.returncode == 100:
                update_lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('Last metadata')]
                updates['dnf']['available'] = update_lines[:20]  # Limit to first 20 for display
                updates['dnf']['count'] = len(update_lines)
                
                # Check for security updates
                sec_result = subprocess.run(
                    ["dnf", "updateinfo", "list", "sec", "--quiet"],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                if sec_result.returncode == 0:
                    sec_lines = [line for line in sec_result.stdout.split('\n') if line.strip()]
                    updates['dnf']['security'] = len(sec_lines)
                    
        except Exception as e:
            logger.warning(f"Failed to check DNF updates: {e}")
        
        # Check Flatpak updates
        try:
            result = subprocess.run(
                ["flatpak", "remote-ls", "--updates"],
                capture_output=True,
                text=True,
                timeout=20
            )
            if result.returncode == 0 and result.stdout.strip():
                update_lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                updates['flatpak']['available'] = update_lines[:10]
                updates['flatpak']['count'] = len(update_lines)
        except Exception:
            pass  # Flatpak might not be installed
        
        # Check firmware updates (fwupd)
        try:
            result = subprocess.run(
                ["fwupdmgr", "get-updates", "--no-unreported"],
                capture_output=True,
                text=True,
                timeout=20
            )
            if result.returncode == 0 and 'No updates' not in result.stdout:
                firmware_lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and '•' in line]
                updates['firmware']['available'] = firmware_lines[:5]
                updates['firmware']['count'] = len(firmware_lines)
        except Exception:
            pass  # fwupd might not be available
        
        # Check if reboot is required
        try:
            reboot_files = [
                '/var/run/reboot-required',
                '/run/reboot-required'
            ]
            for file_path in reboot_files:
                if Path(file_path).exists():
                    updates['reboot_required'] = True
                    break
        except Exception:
            pass
        
        # Calculate total
        updates['total_count'] = updates['dnf']['count'] + updates['flatpak']['count'] + updates['firmware']['count']
        
        return updates
    
    def perform_system_update(self, update_type: str = 'all', dry_run: bool = False) -> Tuple[bool, str]:
        """Perform system updates"""
        if dry_run:
            updates = self.get_system_updates()
            total_updates = updates['total_count']
            return True, f"Would update {total_updates} packages (DNF: {updates['dnf']['count']}, Flatpak: {updates['flatpak']['count']}, Firmware: {updates['firmware']['count']})"
        
        results = []
        overall_success = True
        
        if update_type in ['all', 'dnf']:
            try:
                logger.info("Updating DNF packages...")
                result = subprocess.run(
                    ["sudo", "dnf", "upgrade", "--assumeyes", "--quiet", "--best", "--setopt=max_parallel_downloads=10"],
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 minutes for system updates
                )
                if result.returncode == 0:
                    results.append("DNF packages updated successfully")
                else:
                    results.append(f"DNF update failed: {result.stderr[:100]}")
                    overall_success = False
            except subprocess.TimeoutExpired:
                results.append("DNF update timed out")
                overall_success = False
            except Exception as e:
                results.append(f"DNF update error: {str(e)}")
                overall_success = False
        
        if update_type in ['all', 'flatpak']:
            try:
                logger.info("Updating Flatpak applications...")
                result = subprocess.run(
                    ["flatpak", "update", "--assumeyes", "--noninteractive"],
                    capture_output=True,
                    text=True,
                    timeout=900  # 15 minutes for Flatpak
                )
                if result.returncode == 0:
                    results.append("Flatpak applications updated successfully")
                else:
                    if "Nothing to do" in result.stdout:
                        results.append("Flatpak applications are up to date")
                    else:
                        results.append(f"Flatpak update failed: {result.stderr[:100]}")
                        overall_success = False
            except subprocess.TimeoutExpired:
                results.append("Flatpak update timed out")
                overall_success = False
            except Exception:
                results.append("Flatpak not available or failed")
        
        if update_type in ['all', 'firmware']:
            try:
                logger.info("Updating firmware...")
                result = subprocess.run(
                    ["sudo", "fwupdmgr", "update", "--assume-yes"],
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minutes for firmware
                )
                if result.returncode == 0:
                    results.append("Firmware updated successfully")
                else:
                    if "No updates" in result.stdout:
                        results.append("Firmware is up to date")
                    else:
                        results.append(f"Firmware update failed: {result.stderr[:100]}")
            except subprocess.TimeoutExpired:
                results.append("Firmware update timed out")
            except Exception:
                results.append("Firmware updates not available")
        
        # Clean up package cache to free space
        if update_type in ['all', 'dnf']:
            try:
                subprocess.run(["sudo", "dnf", "clean", "packages"], capture_output=True, timeout=30)
                results.append("Package cache cleaned")
            except Exception:
                pass
        
        return overall_success, "; ".join(results)
    
    def get_update_recommendations(self) -> Dict[str, any]:
        """Get intelligent update recommendations"""
        updates = self.get_system_updates()
        recommendations = {
            'priority': 'low',
            'recommended_action': 'none',
            'reasons': [],
            'schedule_suggestion': '',
            'estimated_time': '5-15 minutes'
        }
        
        total_updates = updates['total_count']
        security_updates = updates['dnf']['security']
        
        if security_updates > 0:
            recommendations['priority'] = 'critical'
            recommendations['recommended_action'] = 'immediate'
            recommendations['reasons'].append(f"{security_updates} security updates available")
            recommendations['schedule_suggestion'] = 'Install security updates immediately'
        elif total_updates > 50:
            recommendations['priority'] = 'high'
            recommendations['recommended_action'] = 'soon'
            recommendations['reasons'].append(f"Many updates available ({total_updates})")
            recommendations['schedule_suggestion'] = 'Schedule update session within 24 hours'
            recommendations['estimated_time'] = '15-30 minutes'
        elif total_updates > 10:
            recommendations['priority'] = 'medium'
            recommendations['recommended_action'] = 'scheduled'
            recommendations['reasons'].append(f"{total_updates} updates available")
            recommendations['schedule_suggestion'] = 'Include in weekly maintenance'
        elif total_updates > 0:
            recommendations['priority'] = 'low'
            recommendations['recommended_action'] = 'optional'
            recommendations['reasons'].append(f"{total_updates} minor updates available")
            recommendations['schedule_suggestion'] = 'Update at convenience'
        
        if updates['reboot_required']:
            recommendations['priority'] = 'high'
            recommendations['reasons'].append('System reboot required')
            recommendations['schedule_suggestion'] += ' (reboot needed)'
        
        if updates['firmware']['count'] > 0:
            recommendations['reasons'].append(f"{updates['firmware']['count']} firmware updates available")
        
        return recommendations