#!/usr/bin/env python3
"""
UI component for the Intelligent Application Manager
Provides interactive interface for browsing and installing curated applications
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
from typing import List, Optional
import sys
sys.path.append('..')
from core.app_manager import AsahiAppManager, AppCategory, Application
from ui.theme_manager_ui import ThemeManagerUI


class AppManagerUI:
    """Interactive UI for the Application Manager"""
    
    def __init__(self):
        self.console = Console()
        self.app_manager = AsahiAppManager()
        
    def display_header(self):
        """Display the application manager header"""
        header = Panel.fit(
            "[bold cyan]Asahi Linux Intelligent App Manager[/bold cyan]\n"
            "[dim]Curated applications optimized for Apple Silicon[/dim]",
            border_style="cyan",
            padding=(1, 2)
        )
        self.console.print(header)
        self.console.print()
    
    def display_main_menu(self) -> str:
        """Display the main menu and get user choice"""
        self.console.print("[bold]Main Menu:[/bold]")
        self.console.print("1. [+] Browse by Category")
        self.console.print("2. [*] View Top Recommendations")
        self.console.print("3. [?] Search Applications")
        self.console.print("4. [#] View Installed Apps")
        self.console.print("5. [!] Quick Install Essentials")
        self.console.print("6. [~] Create Desktop Launchers")
        self.console.print("7. [>] Export Recommendations")
        self.console.print("8. [X] Exit")
        self.console.print()
        
        choice = Prompt.ask(
            "Enter your choice",
            choices=["1", "2", "3", "4", "5", "6", "7", "8"],
            default="1"
        )
        return choice
    
    def display_categories(self):
        """Display application categories with counts"""
        self.console.print("\n[bold cyan]Application Categories[/bold cyan]\n")
        
        summary = self.app_manager.get_categories_summary()
        
        table = Table(
            title="Available Categories",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("Category", style="cyan", width=20)
        table.add_column("Total Apps", justify="center", style="yellow")
        table.add_column("Installed", justify="center", style="green")
        table.add_column("Available", justify="center", style="blue")
        
        categories = list(AppCategory)
        for i, category in enumerate(categories, 1):
            data = summary[category]
            table.add_row(
                f"{i}. {category.value}",
                str(data["total"]),
                str(data["installed"]),
                str(data["available"])
            )
        
        self.console.print(table)
        self.console.print()
        
        # Get user selection
        choice = Prompt.ask(
            "Select a category (number) or 'b' to go back",
            default="b"
        )
        
        if choice.lower() == 'b':
            return
        
        try:
            category_index = int(choice) - 1
            if 0 <= category_index < len(categories):
                self.display_category_apps(categories[category_index])
        except (ValueError, IndexError):
            self.console.print("[red]Invalid selection[/red]")
    
    def display_category_apps(self, category: AppCategory):
        """Display all apps in a specific category"""
        apps = self.app_manager.get_apps_by_category(category)
        
        self.console.print(f"\n[bold cyan]{category.value} Applications[/bold cyan]\n")
        
        table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("#", style="dim", width=3)
        table.add_column("Application", style="cyan", width=20)
        table.add_column("Description", style="white", width=40)
        table.add_column("Status", justify="center", width=12)
        table.add_column("Size", justify="right", width=8)
        
        for i, app in enumerate(apps, 1):
            status = "[green]Installed[/green]" if app.name in self.app_manager.installed_apps else "[yellow]Available[/yellow]"
            size = f"{app.size_mb} MB" if app.size_mb > 0 else "N/A"
            
            table.add_row(
                str(i),
                app.display_name,
                app.description[:40] + "..." if len(app.description) > 40 else app.description,
                status,
                size
            )
        
        self.console.print(table)
        self.console.print()
        
        # Allow selection for installation
        choice = Prompt.ask(
            "Select app(s): single number (1), multiple (1,3,5), range (1-5), 'all', or 'b' to go back",
            default="b"
        )
        
        if choice.lower() == 'b':
            return
        
        selected_apps = self._parse_selection(choice, apps)
        if selected_apps:
            if len(selected_apps) == 1:
                self.display_app_details(selected_apps[0])
            else:
                self._handle_multiple_app_selection(selected_apps)
    
    def display_app_details(self, app: Application):
        """Display detailed information about an application"""
        is_installed = app.name in self.app_manager.installed_apps
        
        # Create detail panel
        details = f"""
[bold cyan]{app.display_name}[/bold cyan]
{'=' * 50}

[bold]Description:[/bold] {app.description}
[bold]Category:[/bold] {app.category.value}
[bold]Package:[/bold] {app.package_name}
[bold]Package Manager:[/bold] {app.package_manager.value}
[bold]Status:[/bold] {"[green]Installed[/green]" if is_installed else "[yellow]Not Installed[/yellow]"}
[bold]Size:[/bold] {app.size_mb} MB
[bold]Popularity:[/bold] {"*" * app.popularity_score}/10
"""
        
        if app.homepage:
            details += f"[bold]Homepage:[/bold] {app.homepage}\n"
        
        if app.performance_notes:
            details += f"\n[bold yellow]Performance Notes:[/bold yellow]\n{app.performance_notes}\n"
        
        if app.alternatives:
            details += f"\n[bold]Alternatives:[/bold] {', '.join(app.alternatives)}\n"
        
        panel = Panel(
            details.strip(),
            title=f"[bold]{app.display_name}[/bold]",
            border_style="cyan",
            expand=False
        )
        
        self.console.print(panel)
        self.console.print()
        
        # Action menu
        if app.name == "theme-manager":
            if Confirm.ask(f"Launch {app.display_name}?"):
                self.launch_theme_manager()
        elif not is_installed:
            if Confirm.ask(f"Install {app.display_name}?"):
                self.install_application(app)
        else:
            self.console.print(f"[green]{app.display_name} is already installed[/green]")
        
        self.console.print()
        Prompt.ask("Press Enter to continue")
    
    def display_recommendations(self):
        """Display top recommended applications"""
        self.console.print("\n[bold cyan]Top Recommended Applications[/bold cyan]\n")
        self.console.print("[dim]Based on popularity and Asahi Linux compatibility[/dim]\n")
        
        recommendations = self.app_manager.get_recommended_apps(15)
        
        if not recommendations:
            self.console.print("[green]All recommended apps are already installed![/green]")
            return
        
        table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("#", style="dim", width=3)
        table.add_column("Application", style="cyan", width=20)
        table.add_column("Category", style="yellow", width=15)
        table.add_column("Description", style="white", width=35)
        table.add_column("Rating", justify="center", width=12)
        
        for i, app in enumerate(recommendations, 1):
            rating = "*" * app.popularity_score
            table.add_row(
                str(i),
                app.display_name,
                app.category.value,
                app.description[:35] + "..." if len(app.description) > 35 else app.description,
                rating
            )
        
        self.console.print(table)
        self.console.print()
        
        choice = Prompt.ask(
            "Select app(s): single number (1), multiple (1,3,5), range (1-5), 'all', or 'b' to go back",
            default="b"
        )
        
        if choice.lower() == 'b':
            return
        elif choice.lower() == 'all':
            self.batch_install_apps(recommendations)
        else:
            selected_apps = self._parse_selection(choice, recommendations)
            if selected_apps:
                if len(selected_apps) == 1:
                    self.display_app_details(selected_apps[0])
                else:
                    self._handle_multiple_app_selection(selected_apps)
    
    def search_applications(self):
        """Search for applications"""
        query = Prompt.ask("\n[bold]Enter search term[/bold]")
        
        results = self.app_manager.search_apps(query)
        
        if not results:
            self.console.print(f"[yellow]No applications found matching '{query}'[/yellow]")
            return
        
        self.console.print(f"\n[bold cyan]Search Results for '{query}'[/bold cyan]\n")
        
        table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("#", style="dim", width=3)
        table.add_column("Application", style="cyan", width=20)
        table.add_column("Category", style="yellow", width=15)
        table.add_column("Description", style="white", width=40)
        
        for i, app in enumerate(results, 1):
            table.add_row(
                str(i),
                app.display_name,
                app.category.value,
                app.description[:40] + "..." if len(app.description) > 40 else app.description
            )
        
        self.console.print(table)
        self.console.print()
        
        choice = Prompt.ask(
            "Select app(s): single number (1), multiple (1,3,5), range (1-5), 'all', or 'b' to go back",
            default="b"
        )
        
        if choice.lower() == 'b':
            return
        elif choice.lower() == 'all':
            available_results = [app for app in results if app.name not in self.app_manager.installed_apps]
            if available_results:
                self.batch_install_apps(available_results)
            else:
                self.console.print("[yellow]All search results are already installed[/yellow]")
        else:
            selected_apps = self._parse_selection(choice, results)
            if selected_apps:
                if len(selected_apps) == 1:
                    self.display_app_details(selected_apps[0])
                else:
                    self._handle_multiple_app_selection(selected_apps)
    
    def display_installed_apps(self):
        """Display all installed applications"""
        installed = [
            self.app_manager.apps_database[name]
            for name in self.app_manager.installed_apps
        ]
        
        if not installed:
            self.console.print("[yellow]No tracked applications are installed[/yellow]")
            return
        
        self.console.print("\n[bold cyan]Installed Applications[/bold cyan]\n")
        
        # Group by category
        by_category = {}
        for app in installed:
            if app.category not in by_category:
                by_category[app.category] = []
            by_category[app.category].append(app)
        
        tree = Tree("[bold]Installed Applications[/bold]")
        
        for category, apps in sorted(by_category.items(), key=lambda x: x[0].value):
            category_branch = tree.add(f"[yellow]{category.value}[/yellow]")
            for app in sorted(apps, key=lambda x: x.display_name):
                category_branch.add(f"[cyan]{app.display_name}[/cyan]")
        
        self.console.print(tree)
        self.console.print(f"\n[dim]Total installed: {len(installed)} applications[/dim]")
    
    def quick_install_essentials(self):
        """Quick install essential applications"""
        self.console.print("\n[bold cyan]Essential Applications for Asahi Linux[/bold cyan]\n")
        
        essentials = [
            "asahi-audio", "git", "vscode", "firefox", "htop", "neovim",
            "nodejs", "python3-pip", "vlc", "neofetch"
        ]
        
        essential_apps = []
        for name in essentials:
            if name in self.app_manager.apps_database:
                app = self.app_manager.apps_database[name]
                if app.name not in self.app_manager.installed_apps:
                    essential_apps.append(app)
        
        if not essential_apps:
            self.console.print("[green]All essential applications are already installed![/green]")
            return
        
        self.console.print("The following essential applications will be installed:\n")
        
        for app in essential_apps:
            self.console.print(f"  - [cyan]{app.display_name}[/cyan] - {app.description}")
        
        self.console.print()
        
        if Confirm.ask("Proceed with installation?"):
            self.batch_install_apps(essential_apps)
    
    def install_application(self, app: Application):
        """Install a single application with progress display"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            
            task = progress.add_task(
                f"Installing {app.display_name}...",
                total=100
            )
            
            # Show installation command
            install_cmd = self.app_manager.get_installation_command(app)
            self.console.print(f"[dim]Command: {install_cmd}[/dim]\n")
            
            progress.update(task, advance=20)
            
            # Perform installation
            success, message = self.app_manager.install_app(app.name, dry_run=False)
            
            progress.update(task, advance=80)
            
            if success:
                self.console.print(f"[green][+] {message}[/green]")
            else:
                self.console.print(f"[red][-] {message}[/red]")
            
            progress.update(task, completed=100)
    
    def batch_install_apps(self, apps: List[Application]):
        """Install multiple applications"""
        self.console.print(f"\n[bold]Installing {len(apps)} applications...[/bold]\n")
        
        success_count = 0
        failed_apps = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            
            main_task = progress.add_task(
                "Overall progress...",
                total=len(apps)
            )
            
            for app in apps:
                app_task = progress.add_task(
                    f"Installing {app.display_name}...",
                    total=100
                )
                
                success, message = self.app_manager.install_app(app.name, dry_run=False)
                
                if success:
                    success_count += 1
                    self.console.print(f"[green][+] {app.display_name} installed[/green]")
                else:
                    failed_apps.append((app, message))
                    self.console.print(f"[red][-] {app.display_name} failed[/red]")
                
                progress.update(app_task, completed=100)
                progress.update(main_task, advance=1)
        
        # Summary
        self.console.print(f"\n[bold]Installation Summary:[/bold]")
        self.console.print(f"  [green]Successful: {success_count}[/green]")
        self.console.print(f"  [red]Failed: {len(failed_apps)}[/red]")
        
        if failed_apps:
            self.console.print("\n[bold red]Failed installations:[/bold red]")
            for app, error in failed_apps:
                self.console.print(f"  - {app.display_name}: {error}")
    
    def export_recommendations(self):
        """Export recommendations to a file"""
        from pathlib import Path
        
        output_file = Path.home() / "asahi_app_recommendations.json"
        
        if self.app_manager.export_recommendations(output_file):
            self.console.print(f"[green]Recommendations exported to: {output_file}[/green]")
        else:
            self.console.print("[red]Failed to export recommendations[/red]")
    
    def launch_theme_manager(self):
        """Launch the theme manager UI"""
        try:
            theme_ui = ThemeManagerUI()
            theme_ui.run()
        except Exception as e:
            self.console.print(f"[red]Error launching theme manager: {e}[/red]")
    
    def _parse_selection(self, choice: str, apps: List[Application]) -> List[Application]:
        """Parse user selection and return list of selected apps"""
        try:
            selected_apps = []
            
            if ',' in choice:
                # Multiple selections: 1,3,5
                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                for idx in indices:
                    if 0 <= idx < len(apps):
                        selected_apps.append(apps[idx])
                    else:
                        self.console.print(f"[yellow]Invalid index: {idx + 1}[/yellow]")
                        
            elif '-' in choice:
                # Range selection: 1-5
                start, end = map(str.strip, choice.split('-'))
                start_idx = int(start) - 1
                end_idx = int(end) - 1
                
                if 0 <= start_idx <= end_idx < len(apps):
                    selected_apps = apps[start_idx:end_idx + 1]
                else:
                    self.console.print(f"[red]Invalid range: {choice}[/red]")
                    
            else:
                # Single selection: 1
                idx = int(choice) - 1
                if 0 <= idx < len(apps):
                    selected_apps = [apps[idx]]
                else:
                    self.console.print(f"[red]Invalid selection: {choice}[/red]")
                    
        except ValueError:
            self.console.print(f"[red]Invalid input format: {choice}[/red]")
            
        return selected_apps
    
    def _handle_multiple_app_selection(self, selected_apps: List[Application]):
        """Handle installation of multiple selected apps"""
        # Filter out already installed apps
        available_apps = [app for app in selected_apps if app.name not in self.app_manager.installed_apps]
        installed_apps = [app for app in selected_apps if app.name in self.app_manager.installed_apps]
        
        if installed_apps:
            self.console.print(f"\n[yellow]Already installed ({len(installed_apps)} apps):[/yellow]")
            for app in installed_apps:
                self.console.print(f"  - [cyan]{app.display_name}[/cyan]")
        
        if not available_apps:
            self.console.print("[green]All selected apps are already installed![/green]")
            return
        
        self.console.print(f"\n[bold]Selected {len(available_apps)} apps to install:[/bold]")
        
        total_size = sum(app.size_mb for app in available_apps if app.size_mb > 0)
        
        table = Table(box=box.SIMPLE)
        table.add_column("#", style="dim", width=3)
        table.add_column("Application", style="cyan", width=25)
        table.add_column("Category", style="yellow", width=15)
        table.add_column("Size", justify="right", width=8)
        
        for i, app in enumerate(available_apps, 1):
            size = f"{app.size_mb} MB" if app.size_mb > 0 else "N/A"
            table.add_row(
                str(i),
                app.display_name,
                app.category.value,
                size
            )
        
        self.console.print(table)
        
        if total_size > 0:
            self.console.print(f"\n[dim]Total download size: ~{total_size} MB[/dim]")
        
        if Confirm.ask(f"\nInstall {len(available_apps)} applications?"):
            self.batch_install_apps_with_summary(available_apps)
    
    def batch_install_apps_with_summary(self, apps: List[Application]):
        """Install multiple applications with enhanced progress tracking"""
        self.console.print(f"\n[bold]Installing {len(apps)} applications...[/bold]\n")
        
        success_count = 0
        failed_apps = []
        skipped_apps = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            console=self.console
        ) as progress:
            
            main_task = progress.add_task(
                "Overall progress...",
                total=len(apps)
            )
            
            for i, app in enumerate(apps, 1):
                # Check if already installed (in case status changed)
                if app.name in self.app_manager.installed_apps:
                    skipped_apps.append(app)
                    progress.console.print(f"[yellow][~] {app.display_name} already installed[/yellow]")
                    progress.update(main_task, advance=1)
                    continue
                
                app_task = progress.add_task(
                    f"[{i}/{len(apps)}] Installing {app.display_name}...",
                    total=100
                )
                
                # Show what we're about to install
                install_cmd = self.app_manager.get_installation_command(app)
                progress.console.print(f"[dim]    Command: {install_cmd}[/dim]")
                
                success, message = self.app_manager.install_app(app.name, dry_run=False)
                
                if success:
                    success_count += 1
                    progress.console.print(f"[green][+] {app.display_name} installed successfully[/green]")
                else:
                    failed_apps.append((app, message))
                    progress.console.print(f"[red][-] {app.display_name} failed: {message}[/red]")
                
                progress.update(app_task, completed=100)
                progress.update(main_task, advance=1)
        
        # Enhanced summary
        self.console.print(f"\n[bold]Installation Summary:[/bold]")
        self.console.print(f"  [green]Successfully installed: {success_count}[/green]")
        if skipped_apps:
            self.console.print(f"  [yellow]Already installed: {len(skipped_apps)}[/yellow]")
        if failed_apps:
            self.console.print(f"  [red]Failed: {len(failed_apps)}[/red]")
        
        if success_count > 0:
            self.console.print(f"\n[bold green]✓ {success_count} applications installed successfully![/bold green]")
            
        if skipped_apps:
            self.console.print(f"\n[bold yellow]Skipped applications:[/bold yellow]")
            for app in skipped_apps:
                self.console.print(f"  - {app.display_name}")
        
        if failed_apps:
            self.console.print(f"\n[bold red]Failed installations:[/bold red]")
            for app, error in failed_apps:
                self.console.print(f"  - {app.display_name}: {error}")
        
        self.console.print()
    
    def create_desktop_launchers(self):
        """Create desktop launchers for all installed apps"""
        self.console.print("\n[bold cyan]Create Desktop Launchers[/bold cyan]\n")
        self.console.print("[dim]This will create searchable desktop entries for all installed applications[/dim]\n")
        
        # Show currently installed apps
        installed = [
            self.app_manager.apps_database[name]
            for name in self.app_manager.installed_apps
            if name in self.app_manager.apps_database
        ]
        
        if not installed:
            self.console.print("[yellow]No installed applications found to create launchers for[/yellow]")
            return
        
        self.console.print(f"[bold]Found {len(installed)} installed applications:[/bold]")
        
        # Group by category for display
        by_category = {}
        for app in installed:
            if app.category not in by_category:
                by_category[app.category] = []
            by_category[app.category].append(app)
        
        for category, apps in sorted(by_category.items(), key=lambda x: x[0].value):
            self.console.print(f"\n[yellow]{category.value}:[/yellow]")
            for app in sorted(apps, key=lambda x: x.display_name):
                self.console.print(f"  - [cyan]{app.display_name}[/cyan]")
        
        self.console.print()
        
        if not Confirm.ask("Create desktop launchers for these applications?"):
            return
        
        # Create desktop entries
        self.console.print("\n[bold]Creating desktop launchers...[/bold]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Creating desktop entries...", total=len(installed))
            
            results = self.app_manager.create_desktop_entries_for_installed_apps()
            
            success_count = sum(1 for success in results.values() if success)
            failed_count = len(results) - success_count
            
            progress.update(task, completed=len(installed))
        
        # Summary
        self.console.print(f"\n[bold]Desktop Launcher Creation Summary:[/bold]")
        self.console.print(f"  [green]Successfully created: {success_count}[/green]")
        if failed_count > 0:
            self.console.print(f"  [red]Failed: {failed_count}[/red]")
        
        if success_count > 0:
            self.console.print(f"\n[bold green]✓ {success_count} desktop launchers created![/bold green]")
            self.console.print("\n[bold]You can now:[/bold]")
            self.console.print("  - Search for these apps in your application launcher")
            self.console.print("  - Pin them to your taskbar/dock")
            self.console.print("  - Find them in your applications menu")
            
            # Desktop environment specific instructions
            self.console.print(f"\n[bold]How to find your new launchers:[/bold]")
            self.console.print("  • Press Super/Meta key and start typing the app name")
            self.console.print("  • Check your applications menu (usually organized by category)")
            self.console.print("  • Right-click apps in the menu to pin to favorites/taskbar")
        
        if failed_count > 0:
            failed_apps = [name for name, success in results.items() if not success]
            self.console.print(f"\n[bold red]Failed to create launchers for:[/bold red]")
            for app_name in failed_apps:
                if app_name in self.app_manager.apps_database:
                    app = self.app_manager.apps_database[app_name]
                    self.console.print(f"  - {app.display_name}")
    
    def run(self):
        """Main UI loop"""
        try:
            while True:
                self.console.clear()
                self.display_header()
                
                choice = self.display_main_menu()
                
                if choice == "1":
                    self.display_categories()
                elif choice == "2":
                    self.display_recommendations()
                elif choice == "3":
                    self.search_applications()
                elif choice == "4":
                    self.display_installed_apps()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "5":
                    self.quick_install_essentials()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "6":
                    self.create_desktop_launchers()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "7":
                    self.export_recommendations()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "8":
                    self.console.print("\n[cyan]Thank you for using Asahi App Manager![/cyan]")
                    break
                    
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Interrupted by user[/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")


if __name__ == "__main__":
    ui = AppManagerUI()
    ui.run()