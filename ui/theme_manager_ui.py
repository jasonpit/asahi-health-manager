#!/usr/bin/env python3
"""
UI component for the Theme Manager
Provides interactive interface for browsing and installing desktop themes
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm
from rich.tree import Tree
from rich.layout import Layout
from rich.align import Align
from rich import box
import time
import subprocess
from typing import List, Optional, Dict
import sys
sys.path.append('..')
from core.theme_manager import ThemeManager, ThemeType, DesktopEnvironment, Theme


class ThemeManagerUI:
    """Interactive UI for the Theme Manager"""
    
    def __init__(self):
        self.console = Console()
        self.theme_manager = ThemeManager()
        
    def display_header(self):
        """Display the theme manager header"""
        de_name = self.theme_manager.get_desktop_environment_name()
        header = Panel.fit(
            f"[bold cyan]Asahi Linux Theme Manager[/bold cyan]\n"
            f"[dim]Desktop Environment: {de_name}[/dim]\n"
            f"[dim]Comprehensive theming for your Asahi Linux desktop[/dim]",
            border_style="cyan",
            padding=(1, 2)
        )
        self.console.print(header)
        self.console.print()
    
    def display_main_menu(self) -> str:
        """Display the main menu and get user choice"""
        self.console.print("[bold]Theme Manager Menu:[/bold]")
        self.console.print("1. [+] Browse by Theme Type")
        self.console.print("2. [*] View Compatible Themes")
        self.console.print("3. [!] Install Theme Presets")
        self.console.print("4. [?] Search Themes")
        self.console.print("5. [#] View Theme Categories")
        self.console.print("6. [>] Font Management")
        self.console.print("7. [~] Wallpaper Collections")
        self.console.print("8. [X] Back to Main Menu")
        self.console.print()
        
        choice = Prompt.ask(
            "Enter your choice",
            choices=["1", "2", "3", "4", "5", "6", "7", "8"],
            default="1"
        )
        return choice
    
    def display_theme_types(self):
        """Display theme types with counts"""
        self.console.print("\n[bold cyan]Theme Categories[/bold cyan]\n")
        
        summary = self.theme_manager.get_theme_categories_summary()
        
        table = Table(
            title="Available Theme Types",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("Type", style="cyan", width=20)
        table.add_column("Total Themes", justify="center", style="yellow")
        table.add_column("Compatible", justify="center", style="green")
        table.add_column("Description", style="white", width=40)
        
        type_descriptions = {
            ThemeType.GTK_THEME: "Window and application appearance",
            ThemeType.ICON_PACK: "Application and file icons",
            ThemeType.CURSOR_THEME: "Mouse cursor appearance",
            ThemeType.WALLPAPER: "Desktop background collections",
            ThemeType.FONT_FAMILY: "System and interface fonts",
            ThemeType.PLASMA_THEME: "KDE Plasma desktop themes",
            ThemeType.SHELL_THEME: "GNOME Shell extensions and themes",
            ThemeType.COLOR_SCHEME: "System-wide color schemes"
        }
        
        theme_types = list(ThemeType)
        for i, theme_type in enumerate(theme_types, 1):
            data = summary.get(theme_type, {"total": 0, "compatible": 0})
            description = type_descriptions.get(theme_type, "Various theme components")
            
            table.add_row(
                f"{i}. {theme_type.value.title()}",
                str(data["total"]),
                str(data["compatible"]),
                description
            )
        
        self.console.print(table)
        self.console.print()
        
        # Get user selection
        choice = Prompt.ask(
            "Select a theme type (number) or 'b' to go back",
            default="b"
        )
        
        if choice.lower() == 'b':
            return
        
        try:
            type_index = int(choice) - 1
            if 0 <= type_index < len(theme_types):
                self.display_themes_by_type(theme_types[type_index])
        except (ValueError, IndexError):
            self.console.print("[red]Invalid selection[/red]")
    
    def display_themes_by_type(self, theme_type: ThemeType):
        """Display all themes of a specific type"""
        themes = self.theme_manager.get_theme_by_type(theme_type)
        compatible_themes = [
            t for t in themes 
            if self.theme_manager.current_de in t.compatible_de
        ]
        
        self.console.print(f"\n[bold cyan]{theme_type.value.title()} Themes[/bold cyan]\n")
        
        if not compatible_themes:
            self.console.print(f"[yellow]No {theme_type.value} themes available for your desktop environment[/yellow]")
            return
        
        table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("#", style="dim", width=3)
        table.add_column("Theme", style="cyan", width=25)
        table.add_column("Description", style="white", width=40)
        table.add_column("Rating", justify="center", width=10)
        table.add_column("Variants", justify="center", width=12)
        
        for i, theme in enumerate(compatible_themes, 1):
            rating = "*" * theme.popularity_score
            variants = []
            if theme.dark_variant:
                variants.append("Dark")
            if theme.light_variant:
                variants.append("Light")
            variant_str = "/".join(variants) if variants else "N/A"
            
            table.add_row(
                str(i),
                theme.display_name,
                theme.description[:40] + "..." if len(theme.description) > 40 else theme.description,
                rating,
                variant_str
            )
        
        self.console.print(table)
        self.console.print()
        
        # Allow selection for installation
        choice = Prompt.ask(
            "Select a theme (number) to install/view details, or 'b' to go back",
            default="b"
        )
        
        if choice.lower() == 'b':
            return
        
        try:
            theme_index = int(choice) - 1
            if 0 <= theme_index < len(compatible_themes):
                self.display_theme_details(compatible_themes[theme_index])
        except (ValueError, IndexError):
            self.console.print("[red]Invalid selection[/red]")
    
    def display_theme_details(self, theme: Theme):
        """Display detailed information about a theme"""
        # Create detail panel
        details = f"""
[bold cyan]{theme.display_name}[/bold cyan]
{'=' * 50}

[bold]Type:[/bold] {theme.theme_type.value.title()}
[bold]Description:[/bold] {theme.description}
[bold]Package:[/bold] {theme.package_name}
[bold]Package Manager:[/bold] {theme.package_manager}
[bold]Popularity:[/bold] {"*" * theme.popularity_score}/10

[bold]Compatibility:[/bold]
"""
        
        # Add compatible desktop environments
        de_names = {
            DesktopEnvironment.KDE_PLASMA: "KDE Plasma",
            DesktopEnvironment.GNOME: "GNOME",
            DesktopEnvironment.XFCE: "XFCE",
            DesktopEnvironment.MATE: "MATE",
            DesktopEnvironment.CINNAMON: "Cinnamon",
            DesktopEnvironment.I3WM: "i3WM",
            DesktopEnvironment.SWAY: "Sway",
            DesktopEnvironment.HYPRLAND: "Hyprland",
            DesktopEnvironment.BUDGIE: "Budgie"
        }
        
        compatible_names = [de_names.get(de, de.value) for de in theme.compatible_de 
                          if de != DesktopEnvironment.UNKNOWN]
        details += f"  {', '.join(compatible_names)}\n"
        
        # Add variants
        variants = []
        if theme.dark_variant:
            variants.append("Dark")
        if theme.light_variant:
            variants.append("Light")
        if variants:
            details += f"\n[bold]Variants:[/bold] {', '.join(variants)}"
        
        if theme.homepage:
            details += f"\n[bold]Homepage:[/bold] {theme.homepage}"
        
        if theme.installation_notes:
            details += f"\n\n[bold yellow]Installation Notes:[/bold yellow]\n{theme.installation_notes}"
        
        if theme.post_install_commands:
            details += f"\n\n[bold]Post-install commands:[/bold]"
            for cmd in theme.post_install_commands:
                if not cmd.startswith('#'):
                    details += f"\n  {cmd}"
        
        panel = Panel(
            details.strip(),
            title=f"[bold]{theme.display_name}[/bold]",
            border_style="cyan",
            expand=False
        )
        
        self.console.print(panel)
        self.console.print()
        
        # Installation option
        if Confirm.ask(f"Install {theme.display_name}?"):
            self.install_theme(theme)
        
        self.console.print()
        Prompt.ask("Press Enter to continue")
    
    def display_compatible_themes(self):
        """Display all themes compatible with current DE"""
        compatible = self.theme_manager.get_compatible_themes()
        
        if not compatible:
            self.console.print("[yellow]No compatible themes found for your desktop environment[/yellow]")
            return
        
        self.console.print(f"\n[bold cyan]Themes Compatible with {self.theme_manager.get_desktop_environment_name()}[/bold cyan]\n")
        
        # Group by type
        by_type = {}
        for theme in compatible:
            if theme.theme_type not in by_type:
                by_type[theme.theme_type] = []
            by_type[theme.theme_type].append(theme)
        
        tree = Tree("[bold]Compatible Themes[/bold]")
        
        for theme_type, themes in sorted(by_type.items(), key=lambda x: x[0].value):
            type_branch = tree.add(f"[yellow]{theme_type.value.title()}[/yellow] ({len(themes)} themes)")
            for theme in sorted(themes, key=lambda x: x.popularity_score, reverse=True):
                rating = "*" * theme.popularity_score
                type_branch.add(f"[cyan]{theme.display_name}[/cyan] [{rating}]")
        
        self.console.print(tree)
        self.console.print(f"\n[dim]Total compatible themes: {len(compatible)}[/dim]")
    
    def display_theme_presets(self):
        """Display and install theme presets"""
        self.console.print("\n[bold cyan]Curated Theme Presets[/bold cyan]\n")
        self.console.print("[dim]Complete theme collections for different styles[/dim]\n")
        
        presets = {
            "modern_dark": {
                "name": "Modern Dark",
                "description": "Sleek dark theme with Nordic colors and modern icons",
                "components": "Nordic theme + Papirus icons + Bibata cursors + Fira Code font"
            },
            "material_design": {
                "name": "Material Design",
                "description": "Google Material Design inspired theme collection",
                "components": "Adapta theme + Tela icons + Capitaine cursors + JetBrains Mono"
            },
            "minimal_light": {
                "name": "Minimal Light",
                "description": "Clean and minimal light theme setup",
                "components": "Arc theme + La Capitaine icons + Inter font + Nordic wallpapers"
            },
            "developer_setup": {
                "name": "Developer Setup",
                "description": "Optimized for coding with multiple programming fonts",
                "components": "Nordic theme + Papirus icons + coding fonts collection"
            },
            "kde_candy": {
                "name": "KDE Candy",
                "description": "Colorful and sweet theme for KDE Plasma",
                "components": "Sweet KDE + Candy icons + Oreo cursors + Firewatch wallpapers"
            }
        }
        
        table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("#", style="dim", width=3)
        table.add_column("Preset", style="cyan", width=20)
        table.add_column("Description", style="white", width=35)
        table.add_column("Components", style="yellow", width=40)
        
        preset_keys = list(presets.keys())
        for i, (key, preset) in enumerate(presets.items(), 1):
            table.add_row(
                str(i),
                preset["name"],
                preset["description"],
                preset["components"]
            )
        
        self.console.print(table)
        self.console.print()
        
        choice = Prompt.ask(
            "Select a preset (number) to install, or 'b' to go back",
            default="b"
        )
        
        if choice.lower() == 'b':
            return
        
        try:
            preset_index = int(choice) - 1
            if 0 <= preset_index < len(preset_keys):
                preset_key = preset_keys[preset_index]
                self.install_theme_preset(preset_key, presets[preset_key]["name"])
        except (ValueError, IndexError):
            self.console.print("[red]Invalid selection[/red]")
    
    def install_theme_preset(self, preset_key: str, preset_name: str):
        """Install a complete theme preset"""
        theme_names = self.theme_manager.create_theme_preset(preset_key)
        
        if not theme_names:
            self.console.print(f"[red]Preset '{preset_name}' not found[/red]")
            return
        
        available_themes = []
        missing_themes = []
        
        for name in theme_names:
            if name in self.theme_manager.themes_database:
                theme = self.theme_manager.themes_database[name]
                if self.theme_manager.current_de in theme.compatible_de:
                    available_themes.append(theme)
                else:
                    missing_themes.append(f"{name} (incompatible with current DE)")
            else:
                missing_themes.append(f"{name} (not found)")
        
        if not available_themes:
            self.console.print(f"[red]No themes from '{preset_name}' preset are compatible with your desktop environment[/red]")
            return
        
        self.console.print(f"\n[bold]Installing '{preset_name}' theme preset...[/bold]\n")
        
        if missing_themes:
            self.console.print("[yellow]Some themes will be skipped:[/yellow]")
            for missing in missing_themes:
                self.console.print(f"  - {missing}")
            self.console.print()
        
        self.console.print(f"[green]Will install {len(available_themes)} themes:[/green]")
        for theme in available_themes:
            self.console.print(f"  - [cyan]{theme.display_name}[/cyan] ({theme.theme_type.value})")
        
        self.console.print()
        
        if Confirm.ask("Proceed with preset installation?"):
            self.batch_install_themes(available_themes)
    
    def search_themes(self):
        """Search for themes"""
        query = Prompt.ask("\n[bold]Enter search term[/bold]")
        
        results = []
        query_lower = query.lower()
        
        for theme in self.theme_manager.themes_database.values():
            if (query_lower in theme.name.lower() or
                query_lower in theme.display_name.lower() or
                query_lower in theme.description.lower()):
                if self.theme_manager.current_de in theme.compatible_de:
                    results.append(theme)
        
        if not results:
            self.console.print(f"[yellow]No compatible themes found matching '{query}'[/yellow]")
            return
        
        self.console.print(f"\n[bold cyan]Search Results for '{query}'[/bold cyan]\n")
        
        table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("#", style="dim", width=3)
        table.add_column("Theme", style="cyan", width=25)
        table.add_column("Type", style="yellow", width=15)
        table.add_column("Description", style="white", width=40)
        
        for i, theme in enumerate(results, 1):
            table.add_row(
                str(i),
                theme.display_name,
                theme.theme_type.value.title(),
                theme.description[:40] + "..." if len(theme.description) > 40 else theme.description
            )
        
        self.console.print(table)
        self.console.print()
        
        choice = Prompt.ask(
            "Select a theme (number) to view details, or 'b' to go back",
            default="b"
        )
        
        if choice.lower() != 'b':
            try:
                theme_index = int(choice) - 1
                if 0 <= theme_index < len(results):
                    self.display_theme_details(results[theme_index])
            except (ValueError, IndexError):
                self.console.print("[red]Invalid selection[/red]")
    
    def display_font_management(self):
        """Special interface for font management"""
        font_themes = self.theme_manager.get_theme_by_type(ThemeType.FONT_FAMILY)
        compatible_fonts = [
            t for t in font_themes 
            if self.theme_manager.current_de in t.compatible_de
        ]
        
        self.console.print("\n[bold cyan]Font Management[/bold cyan]\n")
        self.console.print("[dim]Essential fonts for development and UI[/dim]\n")
        
        if not compatible_fonts:
            self.console.print("[yellow]No fonts available[/yellow]")
            return
        
        # Categorize fonts
        coding_fonts = [f for f in compatible_fonts if "mono" in f.name.lower() or "code" in f.name.lower()]
        ui_fonts = [f for f in compatible_fonts if f not in coding_fonts]
        
        if coding_fonts:
            self.console.print("[bold]Coding Fonts:[/bold]")
            for font in coding_fonts:
                status = "[green][installed][/green]" if self._is_font_installed(font) else "[yellow][available][/yellow]"
                self.console.print(f"  - [cyan]{font.display_name}[/cyan] {status}")
                if font.installation_notes:
                    self.console.print(f"    [dim]{font.installation_notes}[/dim]")
            self.console.print()
        
        if ui_fonts:
            self.console.print("[bold]UI Fonts:[/bold]")
            for font in ui_fonts:
                status = "[green][installed][/green]" if self._is_font_installed(font) else "[yellow][available][/yellow]"
                self.console.print(f"  - [cyan]{font.display_name}[/cyan] {status}")
                if font.installation_notes:
                    self.console.print(f"    [dim]{font.installation_notes}[/dim]")
            self.console.print()
        
        if Confirm.ask("Install all recommended fonts?"):
            self.batch_install_themes(compatible_fonts)
    
    def _is_font_installed(self, font_theme: Theme) -> bool:
        """Check if a font is installed"""
        try:
            result = subprocess.run(
                ["fc-list", ":", "family"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return font_theme.display_name.lower().replace(" ", "") in result.stdout.lower().replace(" ", "")
        except Exception:
            return False
    
    def install_theme(self, theme: Theme):
        """Install a single theme with progress display"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            
            task = progress.add_task(
                f"Installing {theme.display_name}...",
                total=100
            )
            
            progress.update(task, advance=20)
            
            # Perform installation
            success, message = self.theme_manager.install_theme(theme.name, dry_run=False)
            
            progress.update(task, advance=80)
            
            if success:
                self.console.print(f"[green][+] {message}[/green]")
            else:
                self.console.print(f"[red][-] {message}[/red]")
            
            progress.update(task, completed=100)
    
    def batch_install_themes(self, themes: List[Theme]):
        """Install multiple themes"""
        self.console.print(f"\n[bold]Installing {len(themes)} themes...[/bold]\n")
        
        success_count = 0
        failed_themes = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            
            main_task = progress.add_task(
                "Overall progress...",
                total=len(themes)
            )
            
            for theme in themes:
                theme_task = progress.add_task(
                    f"Installing {theme.display_name}...",
                    total=100
                )
                
                success, message = self.theme_manager.install_theme(theme.name, dry_run=False)
                
                if success:
                    success_count += 1
                    self.console.print(f"[green][+] {theme.display_name} installed[/green]")
                else:
                    failed_themes.append((theme, message))
                    self.console.print(f"[red][-] {theme.display_name} failed[/red]")
                
                progress.update(theme_task, completed=100)
                progress.update(main_task, advance=1)
        
        # Summary
        self.console.print(f"\n[bold]Installation Summary:[/bold]")
        self.console.print(f"  [green]Successful: {success_count}[/green]")
        self.console.print(f"  [red]Failed: {len(failed_themes)}[/red]")
        
        if failed_themes:
            self.console.print("\n[bold red]Failed installations:[/bold red]")
            for theme, error in failed_themes:
                self.console.print(f"  - {theme.display_name}: {error}")
    
    def run(self):
        """Main UI loop"""
        try:
            while True:
                self.console.clear()
                self.display_header()
                
                choice = self.display_main_menu()
                
                if choice == "1":
                    self.display_theme_types()
                elif choice == "2":
                    self.display_compatible_themes()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "3":
                    self.display_theme_presets()
                elif choice == "4":
                    self.search_themes()
                elif choice == "5":
                    self.display_theme_types()
                elif choice == "6":
                    self.display_font_management()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "7":
                    wallpaper_themes = self.theme_manager.get_theme_by_type(ThemeType.WALLPAPER)
                    if wallpaper_themes:
                        self.batch_install_themes(wallpaper_themes)
                    else:
                        self.console.print("[yellow]No wallpaper collections available[/yellow]")
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "8":
                    break
                    
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Interrupted by user[/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")


if __name__ == "__main__":
    ui = ThemeManagerUI()
    ui.run()