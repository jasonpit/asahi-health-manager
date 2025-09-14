#!/usr/bin/env python3
"""
System Settings Integration UI for Asahi Health Manager
Provides native system settings integration with comprehensive cloud sync
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.text import Text

from core.enhanced_cloud_sync import EnhancedCloudSync
from core.user_profile import UserProfileManager
from ascii_art import get_header_for_width, APP_ICON_SMALL

class SystemSettingsIntegrationUI:
    """System Settings Integration with comprehensive cloud sync"""
    
    def __init__(self):
        self.console = Console()
        self.cloud_sync = EnhancedCloudSync()
        self.profile_manager = UserProfileManager()
        
    def display_header(self):
        """Display integration header"""
        ascii_header = get_header_for_width()
        self.console.print(ascii_header, style="bold green")
        
        subtitle = Panel.fit(
            "[dim]System Settings Integration - Sync your complete desktop environment across devices[/dim]",
            border_style="dim green",
            padding=(0, 1)
        )
        self.console.print(subtitle)
    
    def display_main_menu(self):
        """Display main system settings integration menu"""
        self.console.print("\n[bold]Asahi Health Manager - System Settings Integration[/bold]")
        self.console.print("1. [>] Setup Cloud Sync")
        self.console.print("2. [+] Backup Current System")
        self.console.print("3. [*] Restore from Cloud")
        self.console.print("4. [~] View Sync Status")
        self.console.print("5. [!] Manage Cloud Providers")
        self.console.print("6. [?] Hardware Compatibility Check")
        self.console.print("7. [<] Launch App Manager")
        self.console.print("8. [X] Exit")
        
        choice = Prompt.ask("\nChoose option", choices=["1", "2", "3", "4", "5", "6", "7", "8"], default="8")
        return choice
    
    def setup_cloud_sync(self):
        """Setup cloud synchronization"""
        self.console.print("\n[bold cyan]Cloud Sync Setup[/bold cyan]")
        self.console.print("Choose your preferred cloud storage provider for syncing your complete system configuration.")
        self.console.print()
        
        providers = {
            "1": ("github_gist", "GitHub Gist", "Private gists with your GitHub account"),
            "2": ("dropbox", "Dropbox", "Dropbox cloud storage (requires API key)"),  
            "3": ("google_drive", "Google Drive", "Google Drive storage (requires OAuth)"),
            "4": ("onedrive", "OneDrive", "Microsoft OneDrive (requires OAuth)"),
            "5": ("s3_compatible", "S3 Compatible", "Any S3-compatible storage (MinIO, etc.)"),
            "6": ("webdav", "WebDAV", "WebDAV server (Nextcloud, ownCloud, etc.)"),
            "7": ("local_network", "Local/Network", "USB drive or network folder")
        }
        
        self.console.print("[bold]Available Cloud Providers:[/bold]")
        for key, (provider_id, name, description) in providers.items():
            self.console.print(f"{key}. [cyan]{name}[/cyan] - {description}")
        
        choice = Prompt.ask("\nSelect provider", choices=list(providers.keys()), default="1")
        provider_id, provider_name, _ = providers[choice]
        
        credentials = self._get_provider_credentials(provider_id, provider_name)
        if not credentials:
            self.console.print("[yellow]Setup cancelled[/yellow]")
            return
        
        # Test and setup the provider
        self.console.print(f"\n[yellow]Setting up {provider_name}...[/yellow]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Testing connection...", total=None)
            
            success, message = self.cloud_sync.setup_cloud_provider(provider_id, credentials)
            
            progress.update(task, description="Setup completed")
        
        if success:
            self.console.print(f"[green][+] {message}[/green]")
            
            # Offer to create initial backup
            if Confirm.ask("\nWould you like to create your first backup now?"):
                self.backup_current_system()
        else:
            self.console.print(f"[red][-] Setup failed: {message}[/red]")
    
    def _get_provider_credentials(self, provider_id: str, provider_name: str) -> Optional[Dict[str, str]]:
        """Get credentials for the selected provider"""
        self.console.print(f"\n[bold]Setup {provider_name}[/bold]")
        
        if provider_id == "github_gist":
            self.console.print("You'll need a GitHub Personal Access Token with 'gist' permission.")
            self.console.print("Create one at: https://github.com/settings/tokens")
            self.console.print()
            
            import getpass
            token = getpass.getpass("GitHub Token (hidden): ")
            if not token.strip():
                return None
            
            return {"token": token}
            
        elif provider_id == "dropbox":
            self.console.print("You'll need a Dropbox API access token.")
            self.console.print("Create an app at: https://www.dropbox.com/developers/apps")
            
            token = Prompt.ask("Dropbox Access Token")
            if not token.strip():
                return None
            
            return {"token": token}
            
        elif provider_id == "local_network":
            self.console.print("Enter the path to your storage location (USB drive, network share, etc.)")
            
            default_path = str(Path.home() / "Documents" / "AsahiHealthManager")
            path = Prompt.ask("Storage path", default=default_path)
            
            return {"path": path}
            
        elif provider_id == "webdav":
            self.console.print("Enter your WebDAV server details:")
            
            url = Prompt.ask("WebDAV URL (e.g., https://cloud.example.com/remote.php/dav/files/username/)")
            username = Prompt.ask("Username")
            import getpass
            password = getpass.getpass("Password (hidden): ")
            
            return {
                "url": url,
                "username": username, 
                "password": password
            }
        
        # Add other provider credential gathering...
        else:
            self.console.print(f"[yellow]Credential setup not implemented for {provider_name}[/yellow]")
            return None
    
    def backup_current_system(self):
        """Create comprehensive backup of current system"""
        self.console.print("\n[bold cyan]Create System Backup[/bold cyan]")
        self.console.print("This will backup your complete system configuration including:")
        self.console.print("• Desktop theme settings (GTK, KDE, icons, fonts)")
        self.console.print("• Installed applications list")
        self.console.print("• Asahi Health Manager preferences")  
        self.console.print("• Desktop launcher configurations")
        self.console.print("• AI assistant settings")
        self.console.print("• System optimization preferences")
        self.console.print()
        
        if not Confirm.ask("Continue with backup?"):
            return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            # Collect current profile
            task1 = progress.add_task("Collecting user profile...", total=None)
            if not self.profile_manager.current_profile:
                # Create temporary profile for backup
                self.profile_manager.create_new_profile("BackupUser", None)
            
            current_profile = self.profile_manager.get_profile_dict()
            progress.update(task1, description="Profile collected")
            
            # Create comprehensive backup
            task2 = progress.add_task("Creating comprehensive backup...", total=None)
            backup_data = self.cloud_sync.create_comprehensive_backup(current_profile)
            progress.update(task2, description="Backup data prepared")
            
            # Upload to cloud
            task3 = progress.add_task("Uploading to cloud...", total=None)
            success, message = self.cloud_sync.sync_to_cloud(backup_data)
            progress.update(task3, description="Upload completed")
        
        if success:
            self.console.print(f"\n[green][+] Backup created successfully![/green]")
            self.console.print(f"[green]{message}[/green]")
            self._display_backup_summary(backup_data)
        else:
            self.console.print(f"\n[red][-] Backup failed: {message}[/red]")
    
    def _display_backup_summary(self, backup_data: Dict[str, Any]):
        """Display summary of what was backed up"""
        self.console.print("\n[bold]Backup Summary:[/bold]")
        
        summary_table = Table(show_header=False)
        summary_table.add_column("Category", style="cyan")
        summary_table.add_column("Details", style="white")
        
        # System theme settings
        theme_settings = backup_data.get('system_theme_settings', {})
        desktop_env = theme_settings.get('desktop_environment', 'Unknown')
        theme_count = len(theme_settings.get('theme_data', {}))
        summary_table.add_row("Desktop Environment", f"{desktop_env} ({theme_count} settings)")
        
        # Installed apps
        apps = backup_data.get('installed_apps', [])
        summary_table.add_row("Installed Applications", f"{len(apps)} applications")
        
        # User preferences  
        prefs = backup_data.get('user_preferences', {})
        pref_categories = len([k for k in prefs.keys() if isinstance(prefs.get(k), (dict, list))])
        summary_table.add_row("User Preferences", f"{pref_categories} categories")
        
        # Desktop launchers
        launchers = backup_data.get('asahi_health_settings', {}).get('desktop_launcher_configs', [])
        summary_table.add_row("Desktop Launchers", f"{len(launchers)} launchers")
        
        # Hardware profile
        hardware = backup_data.get('hardware_profile', {})
        silicon_model = hardware.get('apple_silicon_model', 'Unknown')
        summary_table.add_row("Hardware Profile", f"Apple {silicon_model}")
        
        self.console.print(summary_table)
    
    def restore_from_cloud(self):
        """Restore system configuration from cloud"""
        self.console.print("\n[bold cyan]Restore from Cloud[/bold cyan]")
        
        # Check if cloud sync is configured
        if not self.cloud_sync.sync_config_file.exists():
            self.console.print("[red]No cloud provider configured. Please setup cloud sync first.[/red]")
            return
        
        self.console.print("[bold yellow]WARNING:[/bold yellow] This will modify your current system settings.")
        self.console.print("Your current configuration will be backed up before restoration.")
        self.console.print()
        
        if not Confirm.ask("Continue with restoration?"):
            return
        
        # Get backup ID if needed (for providers like GitHub Gist)
        backup_id = None
        with open(self.cloud_sync.sync_config_file, 'r') as f:
            import json
            config = json.load(f)
            provider = config.get('provider')
            
        if provider == 'github_gist':
            backup_id = Prompt.ask("Enter Gist ID to restore from")
            if not backup_id.strip():
                self.console.print("[yellow]Restoration cancelled[/yellow]")
                return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            # Create safety backup first
            task1 = progress.add_task("Creating safety backup...", total=None)
            try:
                current_profile = self.profile_manager.get_profile_dict() if self.profile_manager.current_profile else {}
                safety_backup = self.cloud_sync.create_comprehensive_backup(current_profile)
                # Save locally
                import datetime
                safety_file = self.cloud_sync.backup_dir / f"safety-backup-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
                with open(safety_file, 'w') as f:
                    json.dump(safety_backup, f, indent=2)
                progress.update(task1, description="Safety backup created")
            except Exception as e:
                progress.update(task1, description=f"Safety backup failed: {e}")
            
            # Restore from cloud
            task2 = progress.add_task("Downloading from cloud...", total=None)
            success, message = self.cloud_sync.restore_from_cloud(backup_id)
            progress.update(task2, description="Restoration completed")
        
        if success:
            self.console.print(f"\n[green][+] System restored successfully![/green]")
            self.console.print(f"[green]{message}[/green]")
            self.console.print(f"\n[blue][INFO][/blue] Safety backup saved to: {safety_file}")
            self.console.print("\n[yellow]You may need to log out and back in for all changes to take effect.[/yellow]")
        else:
            self.console.print(f"\n[red][-] Restoration failed: {message}[/red]")
    
    def view_sync_status(self):
        """Display current sync status and configuration"""
        self.console.print("\n[bold cyan]Cloud Sync Status[/bold cyan]")
        
        if not self.cloud_sync.sync_config_file.exists():
            self.console.print("[yellow]No cloud sync configured[/yellow]")
            self.console.print("Use option 1 to setup cloud synchronization.")
            return
        
        # Load and display configuration
        with open(self.cloud_sync.sync_config_file, 'r') as f:
            import json
            config = json.load(f)
        
        status_table = Table(title="Cloud Sync Configuration", show_header=False)
        status_table.add_column("Setting", style="cyan")
        status_table.add_column("Value", style="white")
        
        status_table.add_row("Provider", config.get('provider', 'Unknown'))
        status_table.add_row("Status", "[green]Enabled[/green]" if config.get('enabled', False) else "[red]Disabled[/red]")
        status_table.add_row("Setup Date", config.get('setup_date', 'Unknown')[:10])
        
        # Detect current system info
        current_de = self.cloud_sync.detect_desktop_environment()
        status_table.add_row("Current Desktop", current_de.upper())
        
        # Hardware info
        try:
            hardware_info = self.profile_manager._detect_hardware() if self.profile_manager else {}
            apple_silicon = hardware_info.get('apple_silicon_model', 'Unknown')
            status_table.add_row("Apple Silicon", apple_silicon)
        except:
            status_table.add_row("Apple Silicon", "Detection failed")
        
        self.console.print(status_table)
        
        # Show recent backups if available
        backups = list(self.cloud_sync.backup_dir.glob("*.json"))
        if backups:
            self.console.print(f"\n[bold]Local Backups:[/bold] {len(backups)} files")
            recent_backups = sorted(backups, key=os.path.getctime, reverse=True)[:3]
            for backup in recent_backups:
                import time
                mtime = os.path.getctime(backup)
                date_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))
                self.console.print(f"  • {backup.name} ({date_str})")
    
    def manage_cloud_providers(self):
        """Manage cloud provider settings"""
        self.console.print("\n[bold cyan]Manage Cloud Providers[/bold cyan]")
        
        self.console.print("1. [+] Add New Provider")
        self.console.print("2. [~] Test Current Connection")
        self.console.print("3. [!] Remove Current Provider")
        self.console.print("4. [?] View Provider Details")
        self.console.print("5. [<] Back to Main Menu")
        
        choice = Prompt.ask("\nChoose option", choices=["1", "2", "3", "4", "5"], default="5")
        
        if choice == "1":
            self.setup_cloud_sync()
        elif choice == "2":
            self._test_provider_connection()
        elif choice == "3":
            self._remove_provider()
        elif choice == "4":
            self._view_provider_details()
    
    def _test_provider_connection(self):
        """Test connection to current provider"""
        if not self.cloud_sync.sync_config_file.exists():
            self.console.print("[red]No cloud provider configured[/red]")
            return
        
        with open(self.cloud_sync.sync_config_file, 'r') as f:
            import json
            config = json.load(f)
        
        provider = config.get('provider')
        credentials = config.get('credentials', {})
        
        self.console.print(f"[yellow]Testing connection to {provider}...[/yellow]")
        success, message = self.cloud_sync._test_provider_connection(provider, credentials)
        
        if success:
            self.console.print(f"[green][+] Connection successful: {message}[/green]")
        else:
            self.console.print(f"[red][-] Connection failed: {message}[/red]")
    
    def _remove_provider(self):
        """Remove current cloud provider"""
        if not self.cloud_sync.sync_config_file.exists():
            self.console.print("[yellow]No cloud provider configured[/yellow]")
            return
        
        if Confirm.ask("Are you sure you want to remove the current cloud provider?"):
            self.cloud_sync.sync_config_file.unlink()
            self.console.print("[green]Cloud provider configuration removed[/green]")
    
    def _view_provider_details(self):
        """View detailed provider information"""
        self.console.print("\n[bold]Supported Cloud Providers:[/bold]")
        
        providers_info = {
            "GitHub Gist": {
                "description": "Private gists for secure backup storage",
                "requirements": "GitHub Personal Access Token with 'gist' scope",
                "pros": ["Free", "Version history", "Private by default"],
                "cons": ["Requires GitHub account", "API rate limits"]
            },
            "Dropbox": {
                "description": "Popular cloud storage service",
                "requirements": "Dropbox API access token",
                "pros": ["Reliable", "Good sync", "Mobile access"],
                "cons": ["Requires API setup", "Limited free storage"]
            },
            "Local/Network": {
                "description": "USB drive or network folder storage",
                "requirements": "Writable folder path",
                "pros": ["No internet required", "Full control", "Fast"],
                "cons": ["Manual sync", "No remote access"]
            }
        }
        
        for provider, info in providers_info.items():
            panel_content = f"""[bold cyan]{provider}[/bold cyan]
{info['description']}

[green]Requirements:[/green] {info['requirements']}

[green]Pros:[/green] {', '.join(info['pros'])}
[red]Cons:[/red] {', '.join(info['cons'])}"""
            
            self.console.print(Panel(panel_content, expand=False))
    
    def hardware_compatibility_check(self):
        """Check hardware compatibility for cross-Mac sync"""
        self.console.print("\n[bold cyan]Hardware Compatibility Check[/bold cyan]")
        self.console.print("Analyzing your system for cross-Mac compatibility...\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Detecting hardware...", total=None)
            
            try:
                # Get current hardware info
                if self.profile_manager.current_profile:
                    hardware = self.profile_manager.current_profile.hardware_profile
                else:
                    # Detect hardware
                    hardware_dict = self.profile_manager._detect_hardware()
                    from core.user_profile import HardwareProfile
                    hardware = HardwareProfile(**hardware_dict)
                
                progress.update(task, description="Hardware detected")
                
                # Generate compatibility report
                compatibility_info = self.cloud_sync._generate_compatibility_info()
                
            except Exception as e:
                progress.update(task, description=f"Detection failed: {e}")
                return
        
        # Display compatibility report
        self.console.print("[bold]Current System:[/bold]")
        
        hw_table = Table(show_header=False)
        hw_table.add_column("Component", style="cyan")
        hw_table.add_column("Details", style="white")
        
        hw_table.add_row("Apple Silicon", hardware.apple_silicon_model)
        hw_table.add_row("RAM", f"{hardware.ram_gb}GB")
        hw_table.add_row("Desktop Environment", hardware.desktop_environment)
        hw_table.add_row("Asahi Version", hardware.asahi_version)
        hw_table.add_row("Architecture", hardware.cpu_arch)
        
        self.console.print(hw_table)
        
        # Compatibility matrix
        self.console.print("\n[bold]Cross-Mac Compatibility:[/bold]")
        
        supported_chips = compatibility_info.get('supported_apple_silicon', [])
        current_chip = hardware.apple_silicon_model
        
        compat_table = Table(title="Apple Silicon Compatibility")
        compat_table.add_column("Chip", style="cyan")
        compat_table.add_column("Compatibility", style="white")
        compat_table.add_column("Notes", style="dim")
        
        for chip in supported_chips:
            if chip == current_chip:
                compat_table.add_row(chip, "[green]✓ Current[/green]", "Your current system")
            elif chip.startswith(current_chip[0:2]):  # Same generation (M1, M2, M3)
                compat_table.add_row(chip, "[green]✓ Full[/green]", "Same generation - full compatibility")
            else:
                compat_table.add_row(chip, "[yellow]✓ Adapted[/yellow]", "Will adapt settings automatically")
        
        self.console.print(compat_table)
        
        # Recommendations
        self.console.print("\n[bold green]Recommendations:[/bold green]")
        self.console.print("• Settings will be automatically adapted for different Mac models")
        self.console.print("• Theme preferences work across all desktop environments")
        self.console.print("• Application lists are filtered by package availability")
        self.console.print("• Performance settings are optimized per Apple Silicon model")
    
    def launch_app_manager(self):
        """Launch the main app manager"""
        self.console.print("\n[cyan]Launching Asahi Health Manager...[/cyan]")
        
        try:
            import subprocess
            subprocess.run([sys.executable, str(project_root / "ui" / "app_manager_ui.py")])
        except Exception as e:
            self.console.print(f"[red]Error launching app manager: {e}[/red]")
    
    def run(self):
        """Main integration UI loop"""
        try:
            while True:
                self.console.clear()
                self.display_header()
                
                choice = self.display_main_menu()
                
                if choice == "1":
                    self.setup_cloud_sync()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "2":
                    self.backup_current_system()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "3":
                    self.restore_from_cloud()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "4":
                    self.view_sync_status()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "5":
                    self.manage_cloud_providers()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "6":
                    self.hardware_compatibility_check()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "7":
                    self.launch_app_manager()
                elif choice == "8":
                    self.console.print("\n[cyan]Thank you for using Asahi Health Manager![/cyan]")
                    break
                    
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Interrupted by user[/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")

if __name__ == "__main__":
    ui = SystemSettingsIntegrationUI()
    ui.run()