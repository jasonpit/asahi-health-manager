import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import logging
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.layout import Layout
from rich.live import Live
from rich.tree import Tree
from rich.syntax import Syntax
import shutil

class TerminalUI:
    def __init__(self):
        self.console = Console()
        self.width = shutil.get_terminal_size().columns
        self.progress = None
        
    async def initialize(self):
        """Initialize the terminal UI"""
        self.console.clear()
        self._show_banner()
        
    def _show_banner(self):
        """Show the application banner"""
        banner = """
╔═══════════════════════════════════════════════════════════════╗
║                   ASAHI SYSTEM HEALER                         ║
║               Advanced System Health Management               ║
║                     for Asahi Linux                          ║
╚═══════════════════════════════════════════════════════════════╝
        """
        
        self.console.print(banner, style="bold blue")
        self.console.print(f"Apple Silicon Mac System Health Management", style="green")
        self.console.print(f"AI-Powered Analysis & Recommendations", style="cyan")
        self.console.print("")
    
    def show_progress(self, description: str, total: Optional[int] = None):
        """Show progress indicator"""
        if self.progress:
            self.progress.stop()
        
        if total:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=self.console
            )
            self.progress.start()
            return self.progress.add_task(description, total=total)
        else:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            )
            self.progress.start()
            return self.progress.add_task(description)
    
    def update_progress(self, task_id, advance: int = 1, description: Optional[str] = None):
        """Update progress"""
        if self.progress:
            self.progress.update(task_id, advance=advance, description=description)
    
    def stop_progress(self):
        """Stop progress indicator"""
        if self.progress:
            self.progress.stop()
            self.progress = None
    
    async def display_scan_results(self, scan_results: Dict[str, Any], recommendations: List[Dict[str, Any]]):
        """Display comprehensive scan results"""
        self.stop_progress()
        
        # System Overview
        await self._display_system_overview(scan_results)
        
        # Health Summary
        await self._display_health_summary(scan_results)
        
        # Issues Found
        await self._display_issues_found(scan_results, recommendations)
        
        # Recommendations Summary
        await self._display_recommendations_summary(recommendations)
    
    async def _display_system_overview(self, scan_results: Dict[str, Any]):
        """Display system overview"""
        os_health = scan_results.get('os_health', {})
        system_info = os_health.get('system_info', {})
        
        overview_table = Table(title="System Overview", show_header=False, box=None)
        overview_table.add_column("Property", style="cyan", width=20)
        overview_table.add_column("Value", style="white")
        
        overview_table.add_row("Hostname", system_info.get('hostname', 'Unknown'))
        overview_table.add_row("Distribution", system_info.get('distribution', 'Unknown'))
        overview_table.add_row("Kernel", system_info.get('kernel', 'Unknown'))
        overview_table.add_row("Architecture", system_info.get('architecture', 'Unknown'))
        overview_table.add_row("Apple Chip", system_info.get('apple_chip', 'Unknown'))
        overview_table.add_row("Uptime", system_info.get('uptime', 'Unknown'))
        
        self.console.print(Panel(overview_table, border_style="blue"))
        self.console.print("")
    
    async def _display_health_summary(self, scan_results: Dict[str, Any]):
        """Display health summary with status indicators"""
        os_health = scan_results.get('os_health', {})
        
        # Create health indicators
        health_items = []
        
        # Memory Health
        memory = os_health.get('memory_usage', {})
        memory_percent = memory.get('memory_percent', 0)
        memory_status = "Critical" if memory_percent > 90 else "Warning" if memory_percent > 75 else "Good"
        health_items.append(f"Memory: {memory_status} ({memory_percent:.1f}%)")
        
        # Disk Health
        disk_usage = os_health.get('disk_usage', {}).get('partitions', {})
        max_disk = max((info.get('percent', 0) for info in disk_usage.values()), default=0)
        disk_status = "Critical" if max_disk > 90 else "Warning" if max_disk > 80 else "Good"
        health_items.append(f"Disk: {disk_status} ({max_disk:.1f}%)")
        
        # Network Health
        network = os_health.get('network_health', {}).get('connectivity', {})
        net_status = "Poor" if not network.get('internet', True) else "Limited" if not network.get('dns', True) else "Good"
        health_items.append(f"Network: {net_status}")
        
        # Services Health
        services = os_health.get('systemd_services', {})
        failed_count = services.get('failed', 0)
        svc_status = "Issues" if failed_count > 5 else "Warning" if failed_count > 0 else "Good"
        health_items.append(f"Services: {svc_status} ({failed_count} failed)")
        
        # Thermal Health
        thermal = os_health.get('thermal_status', {}).get('thermal_zones', {})
        hot_zones = sum(1 for zone in thermal.values() if zone.get('critical', False))
        thermal_status = "Hot" if hot_zones > 0 else "Good"
        health_items.append(f"Thermal: {thermal_status}")
        
        health_table = Table(title="System Health Summary", show_header=False)
        health_table.add_column("Component", width=40)
        
        for item in health_items:
            health_table.add_row(item)
        
        self.console.print(Panel(health_table, border_style="green"))
        self.console.print("")
    
    async def _display_issues_found(self, scan_results: Dict[str, Any], recommendations: List[Dict[str, Any]]):
        """Display issues found during scan"""
        
        issues_tree = Tree("Issues Detected")
        
        # Categorize issues
        categories = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'info': []
        }
        
        for rec in recommendations:
            severity = rec.get('severity', 'medium')
            categories[severity].append(rec)
        
        # Display by severity
        severity_colors = {
            'critical': 'red',
            'high': 'orange1',
            'medium': 'yellow',
            'low': 'blue',
            'info': 'grey'
        }
        
        for severity, color in severity_colors.items():
            if categories[severity]:
                severity_branch = issues_tree.add(f"{severity.upper()} ({len(categories[severity])})", style=color)
                
                for issue in categories[severity][:5]:  # Show first 5 issues per severity
                    title = issue.get('title', 'Unknown Issue')
                    description = issue.get('description', '')[:80]
                    severity_branch.add(f"{title}")
                    if description:
                        severity_branch.add(f"  → {description}...", style="dim")
                
                if len(categories[severity]) > 5:
                    severity_branch.add(f"... and {len(categories[severity]) - 5} more", style="dim")
        
        self.console.print(Panel(issues_tree, border_style="red", title="Issues Analysis"))
        self.console.print("")
    
    async def _display_recommendations_summary(self, recommendations: List[Dict[str, Any]]):
        """Display recommendations summary"""
        
        if not recommendations:
            self.console.print(Panel("No issues found - System is healthy!", border_style="green"))
            return
        
        # Count by severity
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        for rec in recommendations:
            severity = rec.get('severity', 'medium')
            severity_counts[severity] += 1
        
        # Create summary table
        summary_table = Table(title="Recommendations Summary")
        summary_table.add_column("Severity", style="bold")
        summary_table.add_column("Count", justify="right")
        summary_table.add_column("Actions Available", style="cyan")
        
        severity_info = {
            'critical': ('Critical', 'Immediate action required'),
            'high': ('High', 'Address within 24 hours'),
            'medium': ('Medium', 'Address when convenient'),
            'low': ('Low', 'Optional improvements'),
            'info': ('Info', 'Informational only')
        }
        
        for severity, count in severity_counts.items():
            if count > 0:
                label, action = severity_info[severity]
                summary_table.add_row(label, str(count), action)
        
        self.console.print(Panel(summary_table, border_style="cyan"))
        self.console.print("")
    
    async def get_user_choice(self, options: List[str]) -> int:
        """Get user choice from a list of options"""
        
        self.console.print("What would you like to do?", style="bold yellow")
        self.console.print("")
        
        for i, option in enumerate(options):
            self.console.print(f"  {i + 1}. {option}")
        
        self.console.print("")
        
        while True:
            try:
                choice = IntPrompt.ask(
                    "Enter your choice",
                    default=1,
                    console=self.console
                )
                
                if 1 <= choice <= len(options):
                    return choice - 1
                else:
                    self.console.print(f"Please enter a number between 1 and {len(options)}", style="red")
            except KeyboardInterrupt:
                self.console.print("\nGoodbye!")
                sys.exit(0)
            except Exception:
                self.console.print("Invalid input. Please enter a number.", style="red")
    
    async def select_fixes(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Allow user to select which fixes to apply"""
        
        self.console.print("Select Fixes to Apply", style="bold cyan")
        self.console.print("Use space to toggle, enter to confirm selection", style="dim")
        self.console.print("")
        
        # Display recommendations with selection
        selected = [False] * len(recommendations)
        
        while True:
            self.console.clear()
            self._show_banner()
            
            self.console.print("Select Fixes to Apply", style="bold cyan")
            self.console.print("Use numbers to toggle selection, 'a' for all, 'n' for none, 'd' when done", style="dim")
            self.console.print("")
            
            # Display recommendations
            table = Table()
            table.add_column("#", width=4)
            table.add_column("Selected", width=8)
            table.add_column("Severity", width=10)
            table.add_column("Issue", width=50)
            table.add_column("Risk", width=10)
            
            for i, rec in enumerate(recommendations):
                checkbox = "[X]" if selected[i] else "[ ]"
                severity = rec.get('severity', 'medium')
                title = rec.get('title', 'Unknown Issue')[:47] + "..." if len(rec.get('title', '')) > 50 else rec.get('title', 'Unknown Issue')
                risk = rec.get('risk_level', 'medium')
                
                severity_style = {
                    'critical': 'red',
                    'high': 'orange1', 
                    'medium': 'yellow',
                    'low': 'blue',
                    'info': 'grey'
                }.get(severity, 'white')
                
                table.add_row(
                    str(i + 1),
                    checkbox,
                    Text(severity.upper(), style=severity_style),
                    title,
                    risk
                )
            
            self.console.print(table)
            self.console.print("")
            
            selected_count = sum(selected)
            self.console.print(f"Selected: {selected_count}/{len(recommendations)}", style="green")
            self.console.print("")
            
            choice = Prompt.ask(
                "Enter number to toggle, 'a' for all, 'n' for none, 'd' when done",
                console=self.console
            ).lower().strip()
            
            if choice == 'd' or choice == 'done':
                break
            elif choice == 'a' or choice == 'all':
                selected = [True] * len(recommendations)
            elif choice == 'n' or choice == 'none':
                selected = [False] * len(recommendations)
            else:
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(recommendations):
                        selected[index] = not selected[index]
                    else:
                        self.console.print("Invalid number", style="red")
                        await asyncio.sleep(1)
                except ValueError:
                    self.console.print("Invalid input", style="red")
                    await asyncio.sleep(1)
        
        # Return selected recommendations
        return [rec for i, rec in enumerate(recommendations) if selected[i]]
    
    async def display_fix_results(self, results: Dict[str, Any]):
        """Display results of fix application"""
        
        self.console.print("Fix Results", style="bold green")
        self.console.print("")
        
        # Summary
        summary_table = Table(show_header=False, box=None)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", justify="right")
        
        summary_table.add_row("Total Fixes Attempted", str(results.get('total_fixes', 0)))
        summary_table.add_row("Successful", str(results.get('successful_fixes', 0)))
        summary_table.add_row("Failed", str(results.get('failed_fixes', 0)))
        summary_table.add_row("Skipped", str(results.get('skipped_fixes', 0)))
        
        self.console.print(Panel(summary_table, title="Summary", border_style="green"))
        self.console.print("")
        
        # Detailed results
        if results.get('execution_results'):
            self.console.print("Detailed Results:", style="bold")
            
            for result in results['execution_results']:
                status = result.get('status', 'unknown')
                title = result.get('title', 'Unknown Fix')
                
                status_icon = {
                    'success': '[SUCCESS]',
                    'failed': '[FAILED]',
                    'error': '[ERROR]',
                    'skipped': '[SKIPPED]',
                    'partial_success': '[PARTIAL]'
                }.get(status, '[UNKNOWN]')
                
                self.console.print(f"  {status_icon} {title}")
                
                if result.get('errors'):
                    for error in result['errors'][:2]:  # Show first 2 errors
                        self.console.print(f"    💭 {error}", style="red dim")
                
                if result.get('verification_results'):
                    successful_verifications = sum(1 for v in result['verification_results'] if v.get('successful'))
                    total_verifications = len(result['verification_results'])
                    if total_verifications > 0:
                        self.console.print(f"    Verification: {successful_verifications}/{total_verifications} passed", style="cyan dim")
        
        self.console.print("")
        
        # Backup info
        if results.get('backup_location'):
            self.console.print(f"Backup created at: {results['backup_location']}", style="blue")
            self.console.print("")
    
    async def configure_schedule(self) -> Optional[Dict[str, Any]]:
        """Configure scheduled scans"""
        
        self.console.print("Configure Scheduled Scans", style="bold cyan")
        self.console.print("")
        
        if not Confirm.ask("Would you like to setup automated system scans?", console=self.console):
            return None
        
        # Get schedule frequency
        frequency_options = [
            "Hourly (every hour)",
            "Daily (2 AM)",
            "Weekly (Sunday 2 AM)", 
            "Monthly (1st of month, 2 AM)",
            "Custom cron expression"
        ]
        
        self.console.print("Select scan frequency:")
        for i, option in enumerate(frequency_options):
            self.console.print(f"  {i + 1}. {option}")
        
        freq_choice = IntPrompt.ask("Choice", default=2, console=self.console)
        
        schedules = {
            1: '0 * * * *',    # Hourly
            2: '0 2 * * *',    # Daily at 2 AM
            3: '0 2 * * 0',    # Weekly on Sunday at 2 AM  
            4: '0 2 1 * *',    # Monthly on 1st at 2 AM
        }
        
        if freq_choice in schedules:
            cron_schedule = schedules[freq_choice]
        elif freq_choice == 5:
            cron_schedule = Prompt.ask("Enter cron expression", console=self.console)
        else:
            cron_schedule = '0 2 * * *'  # Default to daily
        
        # Get scan options
        auto_fix = Confirm.ask("Automatically fix low-risk issues?", default=True, console=self.console)
        generate_report = Confirm.ask("Generate detailed reports?", default=True, console=self.console)
        
        return {
            'tasks': [{
                'id': 'scheduled_scan',
                'name': 'Automated System Health Scan',
                'schedule': cron_schedule,
                'type': 'full_scan',
                'enabled': True,
                'parameters': {
                    'auto_fix_low_risk': auto_fix,
                    'generate_report': generate_report,
                    'send_notifications': True
                }
            }]
        }
    
    async def display_report(self, report: Dict[str, Any]):
        """Display detailed system report"""
        
        self.console.print("Detailed System Health Report", style="bold cyan")
        self.console.print("")
        
        # Executive Summary
        if 'executive_summary' in report:
            summary = report['executive_summary']
            
            # Overall health indicator
            health = summary.get('overall_health', 'unknown')
            health_colors = {
                'critical': 'red',
                'concerning': 'orange1',
                'fair': 'yellow',
                'good': 'green'
            }
            health_color = health_colors.get(health, 'white')
            
            self.console.print(f"Overall System Health: {health.upper()}", style=f"bold {health_color}")
            
            # Key stats
            critical_count = summary.get('critical_issues_count', 0)
            high_count = summary.get('high_priority_issues_count', 0)
            
            if critical_count > 0:
                self.console.print(f"🚨 {critical_count} critical issues require immediate attention", style="red")
            if high_count > 0:
                self.console.print(f"⚠️  {high_count} high-priority issues found", style="orange1")
            
            # Key findings
            key_findings = summary.get('key_findings', [])
            if key_findings:
                self.console.print("\n📝 Key Findings:", style="bold")
                for finding in key_findings[:5]:
                    self.console.print(f"  • {finding}")
        
        self.console.print("")
        
        # System Health Overview
        if 'system_health_overview' in report:
            overview = report['system_health_overview']
            
            overview_table = Table(title="System Health Overview")
            overview_table.add_column("Component", style="cyan")
            overview_table.add_column("Status", justify="center")
            overview_table.add_column("Details")
            
            for component, status in overview.items():
                if component == 'system_uptime':
                    continue
                
                status_icon = {
                    'critical': '🔴',
                    'concerning': '🟡', 
                    'poor': '🟠',
                    'good': '🟢'
                }.get(status, '❓')
                
                overview_table.add_row(
                    component.replace('_', ' ').title(),
                    f"{status_icon} {status.title()}",
                    ""
                )
            
            self.console.print(Panel(overview_table, border_style="blue"))
        
        # Recommendations count
        if 'recommendations' in report:
            rec_data = report['recommendations']
            total = rec_data.get('total_count', 0)
            by_severity = rec_data.get('by_severity', {})
            
            self.console.print(f"\n📋 {total} recommendations generated", style="bold")
            
            if by_severity:
                for severity, count in by_severity.items():
                    if count > 0:
                        self.console.print(f"  • {severity.title()}: {count}")
        
        self.console.print("")
        
        # Ask if user wants to see more details
        if Confirm.ask("Show detailed findings?", default=False, console=self.console):
            await self._display_detailed_findings(report)
    
    async def _display_detailed_findings(self, report: Dict[str, Any]):
        """Display detailed findings from report"""
        
        detailed_findings = report.get('detailed_findings', {})
        
        for category, findings in detailed_findings.items():
            if not findings:
                continue
                
            category_title = category.replace('_', ' ').title()
            self.console.print(f"\n🔍 {category_title}:", style="bold")
            
            for finding in findings[:3]:  # Show first 3 findings per category
                issue = finding.get('issue', 'Unknown Issue')
                details = finding.get('details', '')
                severity = finding.get('severity', 'medium')
                
                severity_icon = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🔵'
                }.get(severity, '❓')
                
                self.console.print(f"  {severity_icon} {issue}")
                if details:
                    self.console.print(f"    {details}", style="dim")
            
            if len(findings) > 3:
                self.console.print(f"    ... and {len(findings) - 3} more findings", style="dim")
    
    def show_message(self, message: str, style: str = "white"):
        """Show a message to the user"""
        self.console.print(f"💬 {message}", style=style)
    
    async def confirm(self, question: str) -> bool:
        """Ask user for confirmation"""
        return Confirm.ask(question, console=self.console)
    
    def clear_screen(self):
        """Clear the screen"""
        self.console.clear()
    
    async def show_loading(self, message: str = "Loading..."):
        """Show loading indicator"""
        with self.console.status(message, spinner="dots"):
            await asyncio.sleep(0.1)  # Brief pause for visual effect