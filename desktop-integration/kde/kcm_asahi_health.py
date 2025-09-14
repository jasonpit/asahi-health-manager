#!/usr/bin/env python3
"""
KDE Control Module for Asahi Health Manager
Provides native integration with KDE System Settings
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                                QLabel, QTextEdit, QTabWidget, QProgressBar,
                                QGroupBox, QGridLayout, QFrame, QScrollArea)
    from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
    from PyQt5.QtGui import QFont, QPalette, QPixmap
    
    # KDE specific imports
    from PyKF5.KCoreAddons import KAboutData, ki18n
    from PyKF5.KConfigWidgets import KCModule
    from PyKF5.KWidgetsAddons import KMessageWidget
    
    KDE_AVAILABLE = True
except ImportError:
    KDE_AVAILABLE = False
    print("KDE libraries not available. Falling back to basic integration.")

# Import our application components
try:
    from core.app_manager import AsahiAppManager
    from core.system_scanner import SystemScanner
    from ui.app_manager_ui import AppManagerUI
except ImportError as e:
    print(f"Warning: Could not import Asahi Health Manager components: {e}")

class SystemHealthThread(QThread):
    """Background thread for running system health checks"""
    health_updated = pyqtSignal(dict)
    progress_updated = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.scanner = None
        
    def run(self):
        """Run system health check in background"""
        try:
            self.progress_updated.emit(10)
            # Initialize scanner
            # This would integrate with our actual system scanner
            self.progress_updated.emit(30)
            
            # Mock health data for now - would be real data from SystemScanner
            health_data = {
                'cpu_temp': 45.2,
                'memory_usage': 62.5,
                'disk_usage': 78.1,
                'system_health': 'Good',
                'updates_available': 5,
                'last_scan': 'Just now'
            }
            
            self.progress_updated.emit(70)
            self.health_updated.emit(health_data)
            self.progress_updated.emit(100)
            
        except Exception as e:
            print(f"Error in health check: {e}")

class AsahiHealthKCM(KCModule if KDE_AVAILABLE else QWidget):
    """KDE Control Module for Asahi Health Manager"""
    
    def __init__(self, parent=None, args=None):
        if KDE_AVAILABLE:
            # Initialize KDE Control Module
            about = KAboutData(
                "kcm_asahi_health",
                ki18n("Asahi Health Manager"),
                "1.0.0",
                ki18n("System health management for Asahi Linux"),
                KAboutData.License_MIT,
                ki18n("© 2024 Mr User")
            )
            super().__init__(about, parent)
        else:
            super().__init__(parent)
            
        self.app_manager = None
        self.health_thread = SystemHealthThread()
        self.health_thread.health_updated.connect(self.update_health_display)
        self.health_thread.progress_updated.connect(self.update_progress)
        
        self.setup_ui()
        self.start_health_check()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Header
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        
        title_label = QLabel("Asahi Health Manager")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addWidget(header_frame)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # System Health Tab
        health_tab = self.create_health_tab()
        tab_widget.addTab(health_tab, "System Health")
        
        # Applications Tab  
        apps_tab = self.create_apps_tab()
        tab_widget.addTab(apps_tab, "Applications")
        
        # Updates Tab
        updates_tab = self.create_updates_tab()
        tab_widget.addTab(updates_tab, "Updates")
        
        # Settings Tab
        settings_tab = self.create_settings_tab()
        tab_widget.addTab(settings_tab, "Settings")
        
        layout.addWidget(tab_widget)
        
    def create_health_tab(self):
        """Create system health monitoring tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Progress bar for health check
        self.health_progress = QProgressBar()
        self.health_progress.setVisible(False)
        layout.addWidget(self.health_progress)
        
        # Health status group
        health_group = QGroupBox("System Health Status")
        health_layout = QGridLayout(health_group)
        
        # Health indicators
        self.health_labels = {}
        health_items = [
            ("System Status", "system_health", "Good"),
            ("CPU Temperature", "cpu_temp", "45.2°C"),
            ("Memory Usage", "memory_usage", "62.5%"),
            ("Disk Usage", "disk_usage", "78.1%"),
            ("Updates Available", "updates_available", "5"),
            ("Last Scan", "last_scan", "Just now")
        ]
        
        for i, (label, key, default) in enumerate(health_items):
            health_layout.addWidget(QLabel(f"{label}:"), i, 0)
            value_label = QLabel(default)
            self.health_labels[key] = value_label
            health_layout.addWidget(value_label, i, 1)
            
        layout.addWidget(health_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        scan_btn = QPushButton("Run Health Check")
        scan_btn.clicked.connect(self.start_health_check)
        button_layout.addWidget(scan_btn)
        
        fix_btn = QPushButton("Auto-Fix Issues")
        fix_btn.clicked.connect(self.auto_fix_issues)
        button_layout.addWidget(fix_btn)
        
        advanced_btn = QPushButton("Advanced Settings")
        advanced_btn.clicked.connect(self.launch_advanced_ui)
        button_layout.addWidget(advanced_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        layout.addStretch()
        return widget
        
    def create_apps_tab(self):
        """Create applications management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Info label
        info_label = QLabel("Manage applications optimized for Asahi Linux")
        layout.addWidget(info_label)
        
        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        install_essentials_btn = QPushButton("Install Essential Apps")
        install_essentials_btn.clicked.connect(self.install_essentials)
        actions_layout.addWidget(install_essentials_btn)
        
        browse_apps_btn = QPushButton("Browse Available Apps")
        browse_apps_btn.clicked.connect(self.browse_apps)
        actions_layout.addWidget(browse_apps_btn)
        
        manage_themes_btn = QPushButton("Manage Themes")
        manage_themes_btn.clicked.connect(self.manage_themes)
        actions_layout.addWidget(manage_themes_btn)
        
        layout.addWidget(actions_group)
        layout.addStretch()
        return widget
        
    def create_updates_tab(self):
        """Create system updates tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Updates info
        updates_group = QGroupBox("System Updates")
        updates_layout = QVBoxLayout(updates_group)
        
        self.updates_label = QLabel("Checking for updates...")
        updates_layout.addWidget(self.updates_label)
        
        # Update buttons
        update_btn_layout = QHBoxLayout()
        
        check_updates_btn = QPushButton("Check for Updates")
        check_updates_btn.clicked.connect(self.check_updates)
        update_btn_layout.addWidget(check_updates_btn)
        
        install_updates_btn = QPushButton("Install Updates")
        install_updates_btn.clicked.connect(self.install_updates)
        update_btn_layout.addWidget(install_updates_btn)
        
        updates_layout.addLayout(update_btn_layout)
        layout.addWidget(updates_group)
        
        layout.addStretch()
        return widget
        
    def create_settings_tab(self):
        """Create settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Settings info
        settings_label = QLabel("Configure Asahi Health Manager settings")
        layout.addWidget(settings_label)
        
        # Settings actions
        settings_group = QGroupBox("Configuration")
        settings_layout = QVBoxLayout(settings_group)
        
        profile_btn = QPushButton("Manage User Profiles")
        profile_btn.clicked.connect(self.manage_profiles)
        settings_layout.addWidget(profile_btn)
        
        ai_config_btn = QPushButton("Configure AI Settings")
        ai_config_btn.clicked.connect(self.configure_ai)
        settings_layout.addWidget(ai_config_btn)
        
        layout.addWidget(settings_group)
        layout.addStretch()
        return widget
        
    def update_health_display(self, health_data):
        """Update health status display"""
        for key, value in health_data.items():
            if key in self.health_labels:
                if key == 'cpu_temp':
                    self.health_labels[key].setText(f"{value}°C")
                elif key in ['memory_usage', 'disk_usage']:
                    self.health_labels[key].setText(f"{value}%")
                else:
                    self.health_labels[key].setText(str(value))
                    
        self.health_progress.setVisible(False)
        
    def update_progress(self, value):
        """Update progress bar"""
        self.health_progress.setVisible(True)
        self.health_progress.setValue(value)
        
    def start_health_check(self):
        """Start system health check"""
        self.health_progress.setVisible(True)
        self.health_progress.setValue(0)
        if not self.health_thread.isRunning():
            self.health_thread.start()
            
    def auto_fix_issues(self):
        """Launch auto-fix for detected issues"""
        self.launch_terminal_command("python3 ui/terminal_ui.py --auto-fix")
        
    def launch_advanced_ui(self):
        """Launch the advanced application manager UI"""
        self.launch_terminal_command("python3 ui/app_manager_ui.py")
        
    def install_essentials(self):
        """Install essential applications"""
        self.launch_terminal_command("python3 ui/app_manager_ui.py --quick-essentials")
        
    def browse_apps(self):
        """Browse available applications"""  
        self.launch_terminal_command("python3 ui/app_manager_ui.py --browse")
        
    def manage_themes(self):
        """Launch theme manager"""
        self.launch_terminal_command("python3 ui/theme_manager_ui.py")
        
    def check_updates(self):
        """Check for system updates"""
        self.updates_label.setText("Checking for updates...")
        # This would integrate with the actual update checker
        QTimer.singleShot(2000, lambda: self.updates_label.setText("5 updates available"))
        
    def install_updates(self):
        """Install system updates"""
        self.launch_terminal_command("python3 ui/app_manager_ui.py --updates")
        
    def manage_profiles(self):
        """Launch profile manager"""
        self.launch_terminal_command("python3 ui/profile_manager_ui.py")
        
    def configure_ai(self):
        """Configure AI settings"""
        self.launch_terminal_command("python3 ui/app_manager_ui.py --ai-setup")
        
    def launch_terminal_command(self, command):
        """Launch a command in terminal"""
        try:
            # Change to project directory and run command
            project_dir = str(Path(__file__).parent.parent.parent)
            
            # Try to detect the terminal emulator
            terminals = ['konsole', 'gnome-terminal', 'xfce4-terminal', 'xterm']
            
            for terminal in terminals:
                if subprocess.run(['which', terminal], capture_output=True).returncode == 0:
                    if terminal == 'konsole':
                        subprocess.Popen([
                            'konsole', '--workdir', project_dir, 
                            '-e', 'bash', '-c', f'{command}; read -p "Press Enter to close..."'
                        ])
                    elif terminal == 'gnome-terminal':
                        subprocess.Popen([
                            'gnome-terminal', '--working-directory', project_dir,
                            '--', 'bash', '-c', f'{command}; read -p "Press Enter to close..."'
                        ])
                    else:
                        subprocess.Popen([
                            terminal, '-e', 'bash', '-c', 
                            f'cd {project_dir} && {command}; read -p "Press Enter to close..."'
                        ])
                    break
            else:
                # Fallback: run in background
                subprocess.Popen(['bash', '-c', f'cd {project_dir} && {command}'])
                
        except Exception as e:
            print(f"Error launching command: {e}")

# Factory function for KDE
def create_kcm(parent, args):
    """Factory function to create the KCM"""
    return AsahiHealthKCM(parent, args)

# Standalone execution for testing
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create and show the widget
    widget = AsahiHealthKCM()
    widget.show()
    
    sys.exit(app.exec_())