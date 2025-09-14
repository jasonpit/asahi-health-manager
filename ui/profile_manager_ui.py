#!/usr/bin/env python3
"""
User Profile Manager UI for Asahi Health Manager
Provides interface for managing user profiles and cloud sync
"""

import getpass
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional

from core.user_profile import UserProfileManager, UserProfile
from ascii_art import get_header_for_width, APP_ICON_SMALL

class ProfileManagerUI:
    """User interface for profile management"""
    
    def __init__(self):
        self.console = Console()
        self.profile_manager = UserProfileManager()
    
    def display_header(self):
        """Display the profile manager header with ASCII art"""
        # Display ASCII art header
        ascii_header = get_header_for_width()
        self.console.print(ascii_header, style="bold blue")
        
        # Add profile-specific subtitle
        subtitle = Panel.fit(
            "[dim]User Profile & Cloud Sync Manager - Sync your settings across devices[/dim]",
            border_style="dim blue",
            padding=(0, 1)
        )
        self.console.print(subtitle)
    
    def display_current_profile(self):
        """Display current profile information"""
        if not self.profile_manager.current_profile:
            self.console.print("[yellow]No profile configured[/yellow]")
            return
        
        profile = self.profile_manager.current_profile
        hw = profile.hardware_profile
        prefs = profile.preferences
        
        # Create profile table
        table = Table(title="Current Profile", show_header=False)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Username", profile.username)
        table.add_row("Email", profile.email or "Not set")
        table.add_row("Profile ID", profile.profile_id[:12] + "...")
        table.add_row("Created", profile.created_date[:10])
        table.add_row("Last Updated", profile.last_updated[:10])
        
        self.console.print(table)
        
        # Hardware info
        hw_table = Table(title="Hardware Profile", show_header=False)
        hw_table.add_column("Component", style="green")
        hw_table.add_column("Details", style="white")
        
        hw_table.add_row("Apple Silicon", hw.apple_silicon_model)
        hw_table.add_row("CPU", hw.cpu_model[:50] + "..." if len(hw.cpu_model) > 50 else hw.cpu_model)
        hw_table.add_row("RAM", f"{hw.ram_gb}GB")
        hw_table.add_row("Screen", hw.screen_resolution)
        hw_table.add_row("Desktop", hw.desktop_environment)
        hw_table.add_row("System ID", hw.system_id)
        
        self.console.print(hw_table)
        
        # Sync status
        sync_status = self.profile_manager.get_sync_status()
        sync_color = "green" if sync_status['enabled'] else "yellow"
        
        sync_table = Table(title="Cloud Sync Status", show_header=False)
        sync_table.add_column("Setting", style="magenta")
        sync_table.add_column("Value", style=sync_color)
        
        sync_table.add_row("Status", sync_status['status'])
        sync_table.add_row("Provider", sync_status.get('provider', 'None'))
        sync_table.add_row("Last Sync", sync_status.get('last_sync', 'Never')[:16] if sync_status.get('last_sync') else 'Never')
        
        self.console.print(sync_table)
    
    def create_new_profile(self):
        """Create a new user profile"""
        self.console.print("\n[bold]Create New User Profile[/bold]")
        self.console.print("This will save your app preferences and settings for sync across devices.\n")
        
        username = Prompt.ask("Username")
        email = Prompt.ask("Email (optional, press Enter to skip)", default="")
        email = email if email.strip() else None
        
        # Confirm hardware detection
        self.console.print("\n[yellow]Detecting hardware configuration...[/yellow]")
        with self.console.status("[bold green]Scanning system..."):
            profile = self.profile_manager.create_new_profile(username, email)
        
        self.console.print("[green][+] Profile created successfully![/green]")
        
        # Show detected hardware
        hw = profile.hardware_profile
        self.console.print(f"\n[bold]Detected Hardware:[/bold]")
        self.console.print(f"  • Apple Silicon: {hw.apple_silicon_model}")
        self.console.print(f"  • RAM: {hw.ram_gb}GB")
        self.console.print(f"  • Desktop: {hw.desktop_environment}")
        self.console.print(f"  • System ID: {hw.system_id}")
        
        # Save profile
        if self.profile_manager.save_profile():
            self.console.print("\n[green][+] Profile saved locally[/green]")
        else:
            self.console.print("\n[red][-] Failed to save profile[/red]")
        
        # Ask about cloud sync setup
        if Confirm.ask("\nWould you like to setup cloud sync now?"):
            self.setup_cloud_sync()
    
    def setup_cloud_sync(self):
        """Setup cloud synchronization"""
        self.console.print("\n[bold]Cloud Sync Setup[/bold]")
        self.console.print("Choose your cloud storage provider:")
        self.console.print("1. GitHub Gist (private, requires token)")
        self.console.print("2. Local Storage (USB drive, network folder)")
        self.console.print("3. Cancel")
        
        choice = Prompt.ask("Choice", choices=["1", "2", "3"], default="3")
        
        if choice == "1":
            self.setup_github_sync()
        elif choice == "2":
            self.setup_local_sync()
        else:
            self.console.print("[yellow]Cloud sync setup cancelled[/yellow]")
    
    def setup_github_sync(self):
        """Setup GitHub Gist synchronization"""
        self.console.print("\n[bold cyan]GitHub Gist Setup[/bold cyan]")
        self.console.print("You'll need a GitHub Personal Access Token with 'gist' permission.")
        self.console.print("Create one at: https://github.com/settings/tokens")
        self.console.print()
        
        token = getpass.getpass("GitHub Token (hidden): ")
        
        if not token.strip():
            self.console.print("[red]Token required for GitHub sync[/red]")
            return
        
        # Test the token
        with self.console.status("[bold green]Testing GitHub connection..."):
            success, message = self.profile_manager.setup_cloud_sync('github', token=token)
        
        if success:
            self.console.print(f"[green][+] {message}[/green]")
            
            # Offer to sync now
            if Confirm.ask("Upload your profile now?"):
                self.sync_to_cloud()
        else:
            self.console.print(f"[red][-] {message}[/red]")
    
    def setup_local_sync(self):
        """Setup local storage synchronization"""
        self.console.print("\n[bold cyan]Local Storage Setup[/bold cyan]")
        self.console.print("Choose a folder for storing your profile (USB drive, network share, etc.)")
        
        default_path = str(Path.home() / "Documents" / "AsahiHealthManager")
        storage_path = Prompt.ask("Storage path", default=default_path)
        
        success, message = self.profile_manager.setup_cloud_sync('local', path=storage_path)
        
        if success:
            self.console.print(f"[green][+] {message}[/green]")
            
            # Offer to sync now
            if Confirm.ask("Save your profile now?"):
                self.sync_to_cloud()
        else:
            self.console.print(f"[red][-] {message}[/red]")
    
    def sync_to_cloud(self):
        """Sync current profile to cloud"""
        if not self.profile_manager.current_profile:
            self.console.print("[red]No profile to sync[/red]")
            return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Syncing to cloud...", total=None)
            
            success, message = self.profile_manager.sync_to_cloud()
            
            progress.update(task, description="Sync completed")
        
        if success:
            self.console.print(f"[green][+] {message}[/green]")
        else:
            self.console.print(f"[red][-] {message}[/red]")
    
    def sync_from_cloud(self):
        """Sync profile from cloud"""
        self.console.print("\n[bold]Sync from Cloud[/bold]")
        
        sync_status = self.profile_manager.get_sync_status()
        if not sync_status['enabled']:
            self.console.print("[red]Cloud sync not configured[/red]")
            return
        
        provider = sync_status['provider']
        
        if provider == 'github':
            gist_id = Prompt.ask("Enter Gist ID to sync from")
            if not gist_id.strip():
                self.console.print("[yellow]Sync cancelled[/yellow]")
                return
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                
                task = progress.add_task("Syncing from GitHub Gist...", total=None)
                success, message = self.profile_manager.sync_from_cloud(gist_id)
                progress.update(task, description="Sync completed")
        
        elif provider == 'local':
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                
                task = progress.add_task("Syncing from local storage...", total=None)
                success, message = self.profile_manager.sync_from_cloud()
                progress.update(task, description="Sync completed")
        
        if success:
            self.console.print(f"[green][+] {message}[/green]")
            self.console.print("\n[bold]Profile synced! Your preferences have been adapted for this hardware.[/bold]")
        else:
            self.console.print(f"[red][-] {message}[/red]")
    
    def update_preferences(self):
        """Update user preferences"""
        if not self.profile_manager.current_profile:
            self.console.print("[red]No profile configured[/red]")
            return
        
        self.console.print("\n[bold]Update Preferences[/bold]")
        
        prefs = self.profile_manager.current_profile.preferences
        
        # Performance profile
        self.console.print(f"\nCurrent performance profile: [cyan]{prefs.performance_profile}[/cyan]")
        new_performance = Prompt.ask(
            "Performance profile", 
            choices=["power_save", "balanced", "performance"], 
            default=prefs.performance_profile
        )
        
        # Auto-update preferences
        current_security = prefs.auto_update_settings.get('security_updates', True)
        new_security = Confirm.ask(f"Auto-install security updates", default=current_security)
        
        current_apps = prefs.auto_update_settings.get('app_updates', False)
        new_apps = Confirm.ask(f"Auto-update applications", default=current_apps)
        
        # Privacy settings
        current_usage = prefs.privacy_settings.get('collect_usage_stats', False)
        new_usage = Confirm.ask(f"Allow usage statistics collection", default=current_usage)
        
        # Update preferences
        self.profile_manager.update_preferences(
            performance_profile=new_performance
        )
        
        prefs.auto_update_settings.update({
            'security_updates': new_security,
            'app_updates': new_apps
        })
        
        prefs.privacy_settings.update({
            'collect_usage_stats': new_usage
        })
        
        if self.profile_manager.save_profile():
            self.console.print("[green][+] Preferences updated[/green]")
        else:
            self.console.print("[red][-] Failed to save preferences[/red]")
    
    def view_installed_apps(self):
        """View and manage tracked installed apps"""
        if not self.profile_manager.current_profile:
            self.console.print("[red]No profile configured[/red]")
            return
        
        installed_apps = self.profile_manager.current_profile.installed_apps
        
        if not installed_apps:
            self.console.print("[yellow]No apps tracked in profile[/yellow]")
        else:
            self.console.print(f"\n[bold]Tracked Applications ({len(installed_apps)}):[/bold]")
            for i, app in enumerate(installed_apps, 1):
                self.console.print(f"  {i:2d}. {app}")
        
        if Confirm.ask("\nSync installed apps from system?"):
            # This would integrate with the app manager to get current installed apps
            self.console.print("[yellow]This would scan and sync your currently installed apps[/yellow]")
            self.console.print("[yellow]Integration with app manager needed[/yellow]")
    
    def display_main_menu(self):
        """Display the main menu options"""
        self.console.print("\n[bold]Profile Manager Menu:[/bold]")
        self.console.print("1. View Current Profile")
        self.console.print("2. Create New Profile")  
        self.console.print("3. Setup Cloud Sync")
        self.console.print("4. Sync to Cloud")
        self.console.print("5. Sync from Cloud")
        self.console.print("6. Update Preferences")
        self.console.print("7. View Tracked Apps")
        self.console.print("8. Export Profile (JSON)")
        self.console.print("9. Return to Main Menu")
    
    def export_profile(self):
        """Export profile to JSON file"""
        if not self.profile_manager.current_profile:
            self.console.print("[red]No profile to export[/red]")
            return
        
        export_path = Prompt.ask(
            "Export path", 
            default=str(Path.home() / "asahi-profile-export.json")
        )
        
        try:
            import json
            from dataclasses import asdict
            
            profile_data = asdict(self.profile_manager.current_profile)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2)
            
            self.console.print(f"[green][+] Profile exported to {export_path}[/green]")
            
        except Exception as e:
            self.console.print(f"[red][-] Export failed: {str(e)}[/red]")
    
    def run(self):
        """Main UI loop"""
        try:
            while True:
                self.console.clear()
                self.display_header()
                
                # Show quick status
                if self.profile_manager.current_profile:
                    sync_status = self.profile_manager.get_sync_status()
                    status_color = "green" if sync_status['enabled'] else "yellow"
                    self.console.print(f"\n[bold]Current User:[/bold] {self.profile_manager.current_profile.username}")
                    self.console.print(f"[bold]Sync Status:[/bold] [{status_color}]{sync_status['status']}[/{status_color}]")
                else:
                    self.console.print(f"\n[yellow]No profile configured[/yellow]")
                
                self.display_main_menu()
                
                choice = Prompt.ask("\nChoose option", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9"], default="9")
                
                if choice == "1":
                    self.display_current_profile()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "2":
                    self.create_new_profile()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "3":
                    self.setup_cloud_sync()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "4":
                    self.sync_to_cloud()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "5":
                    self.sync_from_cloud()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "6":
                    self.update_preferences()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "7":
                    self.view_installed_apps()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "8":
                    self.export_profile()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "9":
                    self.console.print("\n[cyan]Returning to main menu...[/cyan]")
                    break
                    
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Interrupted by user[/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")


if __name__ == "__main__":
    ui = ProfileManagerUI()
    ui.run()