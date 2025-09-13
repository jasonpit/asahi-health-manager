#!/usr/bin/env python3
"""
Theme Manager for Asahi Linux
Detects desktop environment and provides comprehensive theming options
"""

import subprocess
import os
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class DesktopEnvironment(Enum):
    """Supported desktop environments"""
    KDE_PLASMA = "kde"
    GNOME = "gnome"
    XFCE = "xfce"
    MATE = "mate"
    CINNAMON = "cinnamon"
    I3WM = "i3"
    SWAY = "sway"
    HYPRLAND = "hyprland"
    BUDGIE = "budgie"
    UNKNOWN = "unknown"


class ThemeType(Enum):
    """Types of themes"""
    GTK_THEME = "gtk"
    ICON_PACK = "icons"
    CURSOR_THEME = "cursors"
    WALLPAPER = "wallpapers"
    FONT_FAMILY = "fonts"
    PLASMA_THEME = "plasma"
    SHELL_THEME = "shell"
    COLOR_SCHEME = "colors"


@dataclass
class Theme:
    """Theme metadata"""
    name: str
    display_name: str
    theme_type: ThemeType
    description: str
    package_name: str
    compatible_de: List[DesktopEnvironment]
    package_manager: str = "dnf"
    homepage: str = ""
    preview_url: str = ""
    installation_notes: str = ""
    post_install_commands: List[str] = None
    popularity_score: int = 0
    dark_variant: bool = True
    light_variant: bool = True

    def __post_init__(self):
        if self.post_install_commands is None:
            self.post_install_commands = []


class ThemeManager:
    """Manages desktop themes and customization"""
    
    def __init__(self):
        self.current_de = self._detect_desktop_environment()
        self.themes_database = self._initialize_themes_database()
        
    def _detect_desktop_environment(self) -> DesktopEnvironment:
        """Detect the current desktop environment"""
        # Check environment variables
        desktop_session = os.environ.get('DESKTOP_SESSION', '').lower()
        xdg_current_desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        kde_session_version = os.environ.get('KDE_SESSION_VERSION', '')
        
        # Check for specific DEs
        if 'kde' in desktop_session or 'plasma' in xdg_current_desktop or kde_session_version:
            return DesktopEnvironment.KDE_PLASMA
        elif 'gnome' in xdg_current_desktop or 'ubuntu' in xdg_current_desktop:
            return DesktopEnvironment.GNOME
        elif 'xfce' in xdg_current_desktop:
            return DesktopEnvironment.XFCE
        elif 'mate' in xdg_current_desktop:
            return DesktopEnvironment.MATE
        elif 'cinnamon' in xdg_current_desktop:
            return DesktopEnvironment.CINNAMON
        elif 'budgie' in xdg_current_desktop:
            return DesktopEnvironment.BUDGIE
        elif 'sway' in desktop_session:
            return DesktopEnvironment.SWAY
        elif 'hyprland' in desktop_session:
            return DesktopEnvironment.HYPRLAND
        elif 'i3' in desktop_session:
            return DesktopEnvironment.I3WM
            
        # Check running processes as fallback
        try:
            processes = subprocess.check_output(['ps', 'aux'], text=True)
            if 'kded5' in processes or 'plasmashell' in processes:
                return DesktopEnvironment.KDE_PLASMA
            elif 'gnome-shell' in processes:
                return DesktopEnvironment.GNOME
            elif 'xfwm4' in processes:
                return DesktopEnvironment.XFCE
            elif 'mate-panel' in processes:
                return DesktopEnvironment.MATE
            elif 'cinnamon' in processes:
                return DesktopEnvironment.CINNAMON
        except Exception:
            pass
            
        return DesktopEnvironment.UNKNOWN
    
    def _initialize_themes_database(self) -> Dict[str, Theme]:
        """Initialize the comprehensive themes database"""
        themes = []
        
        # GTK Themes
        themes.extend([
            Theme(
                name="arc-theme",
                display_name="Arc Theme",
                theme_type=ThemeType.GTK_THEME,
                description="Modern flat theme with transparent elements",
                package_name="arc-theme",
                compatible_de=[DesktopEnvironment.GNOME, DesktopEnvironment.XFCE, DesktopEnvironment.MATE, DesktopEnvironment.CINNAMON],
                homepage="https://github.com/horst3180/arc-theme",
                popularity_score=9,
                dark_variant=True,
                light_variant=True
            ),
            Theme(
                name="adapta-theme",
                display_name="Adapta Theme",
                theme_type=ThemeType.GTK_THEME,
                description="Material Design inspired adaptive theme",
                package_name="adapta-gtk-theme",
                compatible_de=[DesktopEnvironment.GNOME, DesktopEnvironment.XFCE, DesktopEnvironment.MATE],
                homepage="https://github.com/adapta-project/adapta-gtk-theme",
                popularity_score=8,
                dark_variant=True,
                light_variant=True
            ),
            Theme(
                name="nordic-theme",
                display_name="Nordic Theme",
                theme_type=ThemeType.GTK_THEME,
                description="Dark Scandinavian theme inspired by Nord color palette",
                package_name="nordic-gtk-theme",
                package_manager="flatpak",
                compatible_de=[DesktopEnvironment.GNOME, DesktopEnvironment.XFCE, DesktopEnvironment.KDE_PLASMA],
                homepage="https://github.com/EliverLara/Nordic",
                popularity_score=9,
                dark_variant=True,
                light_variant=False
            ),
            Theme(
                name="orchis-theme",
                display_name="Orchis Theme",
                theme_type=ThemeType.GTK_THEME,
                description="Material Design theme with multiple color variants",
                package_name="orchis-gtk-theme",
                compatible_de=[DesktopEnvironment.GNOME, DesktopEnvironment.XFCE, DesktopEnvironment.CINNAMON],
                homepage="https://github.com/vinceliuice/Orchis-theme",
                popularity_score=8,
                dark_variant=True,
                light_variant=True
            ),
            Theme(
                name="materia-theme",
                display_name="Materia Theme",
                theme_type=ThemeType.GTK_THEME,
                description="Material Design theme for GTK3/4",
                package_name="materia-gtk-theme",
                compatible_de=[DesktopEnvironment.GNOME, DesktopEnvironment.XFCE, DesktopEnvironment.MATE],
                homepage="https://github.com/nana-4/materia-theme",
                popularity_score=7,
                dark_variant=True,
                light_variant=True
            )
        ])
        
        # KDE Plasma Themes
        themes.extend([
            Theme(
                name="breeze-dark",
                display_name="Breeze Dark",
                theme_type=ThemeType.PLASMA_THEME,
                description="Default dark theme for KDE Plasma",
                package_name="breeze",
                compatible_de=[DesktopEnvironment.KDE_PLASMA],
                popularity_score=9,
                dark_variant=True,
                light_variant=False
            ),
            Theme(
                name="latte-dock-themes",
                display_name="Latte Dock Themes",
                theme_type=ThemeType.PLASMA_THEME,
                description="Collection of beautiful dock themes for KDE",
                package_name="latte-dock",
                compatible_de=[DesktopEnvironment.KDE_PLASMA],
                homepage="https://github.com/KDE/latte-dock",
                popularity_score=8,
                post_install_commands=[
                    "# Configure Latte Dock",
                    "kquitapp5 plasmashell",
                    "sleep 2",
                    "plasmashell &"
                ]
            ),
            Theme(
                name="sweet-kde",
                display_name="Sweet KDE",
                theme_type=ThemeType.PLASMA_THEME,
                description="Candy theme for KDE Plasma desktop",
                package_name="sweet-kde-theme",
                compatible_de=[DesktopEnvironment.KDE_PLASMA],
                homepage="https://github.com/EliverLara/Sweet",
                popularity_score=8,
                dark_variant=True,
                light_variant=True
            )
        ])
        
        # Icon Packs
        themes.extend([
            Theme(
                name="papirus-icons",
                display_name="Papirus Icon Theme",
                theme_type=ThemeType.ICON_PACK,
                description="Free and open source SVG icon theme for Linux",
                package_name="papirus-icon-theme",
                compatible_de=[de for de in DesktopEnvironment if de != DesktopEnvironment.UNKNOWN],
                homepage="https://github.com/PapirusDev/papirus-icon-theme",
                popularity_score=10,
                dark_variant=True,
                light_variant=True
            ),
            Theme(
                name="tela-icons",
                display_name="Tela Icon Theme",
                theme_type=ThemeType.ICON_PACK,
                description="Flat colorful Design icon theme",
                package_name="tela-icon-theme",
                compatible_de=[de for de in DesktopEnvironment if de != DesktopEnvironment.UNKNOWN],
                homepage="https://github.com/vinceliuice/Tela-icon-theme",
                popularity_score=9,
                dark_variant=True,
                light_variant=True
            ),
            Theme(
                name="fluent-icons",
                display_name="Fluent Icon Theme",
                theme_type=ThemeType.ICON_PACK,
                description="Fluent Design System inspired icon theme",
                package_name="fluent-icon-theme",
                compatible_de=[de for de in DesktopEnvironment if de != DesktopEnvironment.UNKNOWN],
                homepage="https://github.com/vinceliuice/Fluent-icon-theme",
                popularity_score=8,
                dark_variant=True,
                light_variant=True
            ),
            Theme(
                name="candy-icons",
                display_name="Candy Icons",
                theme_type=ThemeType.ICON_PACK,
                description="Sweet gradient icons for modern desktops",
                package_name="candy-icon-theme",
                compatible_de=[de for de in DesktopEnvironment if de != DesktopEnvironment.UNKNOWN],
                homepage="https://github.com/EliverLara/candy-icons",
                popularity_score=7,
                dark_variant=True,
                light_variant=True
            ),
            Theme(
                name="la-capitaine-icons",
                display_name="La Capitaine Icon Theme",
                theme_type=ThemeType.ICON_PACK,
                description="Icon pack inspired by macOS and Google Material Design",
                package_name="la-capitaine-icon-theme",
                compatible_de=[de for de in DesktopEnvironment if de != DesktopEnvironment.UNKNOWN],
                homepage="https://github.com/keeferrourke/la-capitaine-icon-theme",
                popularity_score=8,
                dark_variant=True,
                light_variant=True
            )
        ])
        
        # Cursor Themes
        themes.extend([
            Theme(
                name="bibata-cursor",
                display_name="Bibata Cursor Theme",
                theme_type=ThemeType.CURSOR_THEME,
                description="Material Based Cursor Theme",
                package_name="bibata-cursor-theme",
                compatible_de=[de for de in DesktopEnvironment if de != DesktopEnvironment.UNKNOWN],
                homepage="https://github.com/ful1e5/Bibata_Cursor",
                popularity_score=9,
                dark_variant=True,
                light_variant=True
            ),
            Theme(
                name="capitaine-cursors",
                display_name="Capitaine Cursors",
                theme_type=ThemeType.CURSOR_THEME,
                description="An x-cursor theme inspired by macOS and based on KDE Breeze",
                package_name="capitaine-cursors",
                compatible_de=[de for de in DesktopEnvironment if de != DesktopEnvironment.UNKNOWN],
                homepage="https://github.com/keeferrourke/capitaine-cursors",
                popularity_score=8,
                dark_variant=True,
                light_variant=True
            ),
            Theme(
                name="oreo-cursor",
                display_name="Oreo Cursor Theme",
                theme_type=ThemeType.CURSOR_THEME,
                description="Animated cursor theme with smooth transitions",
                package_name="oreo-cursor-theme",
                compatible_de=[de for de in DesktopEnvironment if de != DesktopEnvironment.UNKNOWN],
                homepage="https://github.com/varlesh/oreo-cursor",
                popularity_score=7,
                dark_variant=True,
                light_variant=True
            )
        ])
        
        # Wallpaper Collections
        themes.extend([
            Theme(
                name="dynamic-wallpapers",
                display_name="Dynamic Wallpaper Collection",
                theme_type=ThemeType.WALLPAPER,
                description="Time-based dynamic wallpapers that change throughout the day",
                package_name="dynamic-wallpaper-editor",
                compatible_de=[DesktopEnvironment.GNOME, DesktopEnvironment.KDE_PLASMA],
                homepage="https://github.com/adi1090x/dynamic-wallpaper",
                popularity_score=9,
                post_install_commands=[
                    "mkdir -p ~/.local/share/wallpapers/dynamic",
                    "# Download curated wallpaper collection"
                ]
            ),
            Theme(
                name="nordic-wallpapers",
                display_name="Nordic Wallpaper Pack",
                theme_type=ThemeType.WALLPAPER,
                description="Minimalist wallpapers matching Nordic color scheme",
                package_name="nordic-wallpapers",
                compatible_de=[de for de in DesktopEnvironment if de != DesktopEnvironment.UNKNOWN],
                homepage="https://github.com/linuxdotexe/nordic-wallpapers",
                popularity_score=8
            ),
            Theme(
                name="firewatch-wallpapers",
                display_name="Firewatch Wallpaper Collection",
                theme_type=ThemeType.WALLPAPER,
                description="Beautiful landscape wallpapers inspired by the Firewatch game",
                package_name="firewatch-wallpapers",
                compatible_de=[de for de in DesktopEnvironment if de != DesktopEnvironment.UNKNOWN],
                popularity_score=8
            ),
            Theme(
                name="abstract-wallpapers",
                display_name="Abstract Art Wallpapers",
                theme_type=ThemeType.WALLPAPER,
                description="Modern abstract and geometric wallpaper collection",
                package_name="abstract-wallpapers",
                compatible_de=[de for de in DesktopEnvironment if de != DesktopEnvironment.UNKNOWN],
                popularity_score=7
            )
        ])
        
        # Font Families
        themes.extend([
            Theme(
                name="fira-code",
                display_name="Fira Code Font",
                theme_type=ThemeType.FONT_FAMILY,
                description="Monospaced font with programming ligatures",
                package_name="fira-code-fonts",
                compatible_de=[de for de in DesktopEnvironment if de != DesktopEnvironment.UNKNOWN],
                homepage="https://github.com/tonsky/FiraCode",
                popularity_score=10,
                installation_notes="Perfect for coding and terminal use"
            ),
            Theme(
                name="jetbrains-mono",
                display_name="JetBrains Mono",
                theme_type=ThemeType.FONT_FAMILY,
                description="Monospace font designed for developers",
                package_name="jetbrains-mono-fonts",
                compatible_de=[de for de in DesktopEnvironment if de != DesktopEnvironment.UNKNOWN],
                homepage="https://www.jetbrains.com/lp/mono/",
                popularity_score=9,
                installation_notes="Excellent readability for code"
            ),
            Theme(
                name="cascadia-code",
                display_name="Cascadia Code",
                theme_type=ThemeType.FONT_FAMILY,
                description="Microsoft's modern coding font with ligatures",
                package_name="cascadia-code-fonts",
                compatible_de=[de for de in DesktopEnvironment if de != DesktopEnvironment.UNKNOWN],
                homepage="https://github.com/microsoft/cascadia-code",
                popularity_score=8,
                installation_notes="Microsoft's coding font with ligatures"
            ),
            Theme(
                name="inter-font",
                display_name="Inter Font Family",
                theme_type=ThemeType.FONT_FAMILY,
                description="Modern UI font designed for computer screens",
                package_name="google-inter-fonts",
                compatible_de=[de for de in DesktopEnvironment if de != DesktopEnvironment.UNKNOWN],
                homepage="https://rsms.me/inter/",
                popularity_score=9,
                installation_notes="Excellent for UI text and readability"
            ),
            Theme(
                name="noto-fonts",
                display_name="Noto Font Collection",
                theme_type=ThemeType.FONT_FAMILY,
                description="Google's font family supporting all languages",
                package_name="google-noto-fonts-common",
                compatible_de=[de for de in DesktopEnvironment if de != DesktopEnvironment.UNKNOWN],
                homepage="https://fonts.google.com/noto",
                popularity_score=9,
                installation_notes="Comprehensive language support"
            )
        ])
        
        # Shell Themes (GNOME)
        themes.extend([
            Theme(
                name="user-themes-extension",
                display_name="User Themes Extension",
                theme_type=ThemeType.SHELL_THEME,
                description="GNOME extension to enable custom shell themes",
                package_name="gnome-shell-extension-user-theme",
                compatible_de=[DesktopEnvironment.GNOME],
                popularity_score=10,
                post_install_commands=[
                    "gnome-extensions enable user-theme@gnome-shell-extensions.gcampax.github.com"
                ]
            ),
            Theme(
                name="dash-to-dock",
                display_name="Dash to Dock",
                theme_type=ThemeType.SHELL_THEME,
                description="Customizable dock for GNOME Shell",
                package_name="gnome-shell-extension-dash-to-dock",
                compatible_de=[DesktopEnvironment.GNOME],
                homepage="https://micheleg.github.io/dash-to-dock/",
                popularity_score=10,
                post_install_commands=[
                    "gnome-extensions enable dash-to-dock@micxgx.gmail.com"
                ]
            ),
            Theme(
                name="arc-menu",
                display_name="Arc Menu",
                theme_type=ThemeType.SHELL_THEME,
                description="Application menu for GNOME Shell with search",
                package_name="gnome-shell-extension-arc-menu",
                compatible_de=[DesktopEnvironment.GNOME],
                homepage="https://gitlab.com/arcmenu/Arc-Menu",
                popularity_score=8,
                post_install_commands=[
                    "gnome-extensions enable arc-menu@linxgem33.com"
                ]
            )
        ])
        
        return {theme.name: theme for theme in themes}
    
    def get_compatible_themes(self, theme_type: Optional[ThemeType] = None) -> List[Theme]:
        """Get themes compatible with current desktop environment"""
        compatible = []
        
        for theme in self.themes_database.values():
            if (self.current_de in theme.compatible_de or 
                DesktopEnvironment.UNKNOWN in theme.compatible_de):
                if theme_type is None or theme.theme_type == theme_type:
                    compatible.append(theme)
        
        return sorted(compatible, key=lambda x: x.popularity_score, reverse=True)
    
    def get_theme_by_type(self, theme_type: ThemeType) -> List[Theme]:
        """Get all themes of a specific type"""
        return [
            theme for theme in self.themes_database.values()
            if theme.theme_type == theme_type
        ]
    
    def get_desktop_environment_name(self) -> str:
        """Get human-readable desktop environment name"""
        de_names = {
            DesktopEnvironment.KDE_PLASMA: "KDE Plasma",
            DesktopEnvironment.GNOME: "GNOME",
            DesktopEnvironment.XFCE: "XFCE",
            DesktopEnvironment.MATE: "MATE",
            DesktopEnvironment.CINNAMON: "Cinnamon",
            DesktopEnvironment.I3WM: "i3 Window Manager",
            DesktopEnvironment.SWAY: "Sway",
            DesktopEnvironment.HYPRLAND: "Hyprland",
            DesktopEnvironment.BUDGIE: "Budgie",
            DesktopEnvironment.UNKNOWN: "Unknown/Generic"
        }
        return de_names.get(self.current_de, "Unknown")
    
    def install_theme(self, theme_name: str, dry_run: bool = False) -> Tuple[bool, str]:
        """Install a theme"""
        if theme_name not in self.themes_database:
            return False, f"Theme '{theme_name}' not found"
        
        theme = self.themes_database[theme_name]
        
        # Build installation command
        if theme.package_manager == "dnf":
            install_cmd = f"sudo dnf install -y {theme.package_name}"
        elif theme.package_manager == "flatpak":
            install_cmd = f"flatpak install -y flathub {theme.package_name}"
        else:
            return False, f"Unsupported package manager: {theme.package_manager}"
        
        if dry_run:
            return True, f"Would run: {install_cmd}"
        
        try:
            # Install theme
            result = subprocess.run(
                install_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                # Run post-install commands
                for cmd in theme.post_install_commands:
                    if not cmd.startswith('#'):  # Skip comments
                        subprocess.run(cmd, shell=True, capture_output=True)
                
                return True, f"Successfully installed {theme.display_name}"
            else:
                return False, f"Installation failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, f"Installation timed out for {theme.display_name}"
        except Exception as e:
            return False, f"Installation error: {str(e)}"
    
    def get_theme_categories_summary(self) -> Dict[ThemeType, Dict]:
        """Get summary of themes by category"""
        summary = {}
        
        for theme_type in ThemeType:
            type_themes = self.get_theme_by_type(theme_type)
            compatible_themes = [t for t in type_themes if self.current_de in t.compatible_de]
            
            summary[theme_type] = {
                "total": len(type_themes),
                "compatible": len(compatible_themes),
                "themes": compatible_themes
            }
        
        return summary
    
    def create_theme_preset(self, preset_name: str) -> List[str]:
        """Create curated theme presets for different styles"""
        presets = {
            "modern_dark": [
                "nordic-theme", "papirus-icons", "bibata-cursor", 
                "fira-code", "dynamic-wallpapers"
            ],
            "material_design": [
                "adapta-theme", "tela-icons", "capitaine-cursors",
                "jetbrains-mono", "abstract-wallpapers"
            ],
            "minimal_light": [
                "arc-theme", "la-capitaine-icons", "capitaine-cursors",
                "inter-font", "nordic-wallpapers"
            ],
            "developer_setup": [
                "nordic-theme", "papirus-icons", "bibata-cursor",
                "fira-code", "jetbrains-mono", "cascadia-code"
            ],
            "kde_candy": [
                "sweet-kde", "candy-icons", "oreo-cursor",
                "inter-font", "firewatch-wallpapers"
            ]
        }
        
        return presets.get(preset_name, [])