#!/usr/bin/env python3

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
import subprocess
import signal

from core.system_scanner import SystemScanner
from core.ai_integration import AIIntegration  
from core.recommendation_engine import RecommendationEngine
from core.auto_fixer import AutoFixer
from core.scheduler import TaskScheduler
from ui.terminal_ui import TerminalUI
from utils.config_manager import ConfigManager
from utils.logger import Logger

class AsahiSystemHealer:
    def __init__(self):
        self.config = ConfigManager()
        self.logger = Logger()
        self.scanner = SystemScanner()
        self.ai_integration = AIIntegration()
        self.recommendation_engine = RecommendationEngine()
        self.auto_fixer = AutoFixer()
        self.scheduler = TaskScheduler()
        self.ui = TerminalUI()
        self.running = False
        
    async def initialize(self):
        """Initialize all components"""
        try:
            await self.config.load()
            await self.logger.initialize()
            await self.scanner.initialize()
            await self.ai_integration.initialize()
            await self.recommendation_engine.initialize()
            await self.auto_fixer.initialize()
            await self.scheduler.initialize()
            await self.ui.initialize()
            
            self.logger.info("Asahi System Healer initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False
    
    async def run_full_scan(self, interactive=True):
        """Run a complete system scan"""
        self.logger.info("Starting full system scan...")
        
        scan_results = {}
        
        if interactive:
            self.ui.show_progress("Scanning system health...")
        
        # Run all scan modules
        scan_results['os_health'] = await self.scanner.scan_os_health()
        scan_results['applications'] = await self.scanner.scan_applications()
        scan_results['configurations'] = await self.scanner.scan_configurations()
        scan_results['repositories'] = await self.scanner.scan_repositories()
        scan_results['logs'] = await self.scanner.scan_logs()
        scan_results['hardware'] = await self.scanner.scan_hardware()
        
        # Generate AI-powered recommendations
        if interactive:
            self.ui.show_progress("Analyzing results with AI...")
        
        recommendations = await self.recommendation_engine.generate_recommendations(scan_results)
        
        # Display results
        if interactive:
            await self.ui.display_scan_results(scan_results, recommendations)
            choice = await self.ui.get_user_choice([
                "Fix all issues automatically",
                "Select individual fixes",
                "Generate detailed report",
                "Schedule regular scans",
                "Exit"
            ])
            
            if choice == 0:
                await self.auto_fix_all(recommendations)
            elif choice == 1:
                await self.interactive_fix(recommendations)
            elif choice == 2:
                await self.generate_report(scan_results, recommendations)
            elif choice == 3:
                await self.setup_scheduling()
        
        return scan_results, recommendations
    
    async def auto_fix_all(self, recommendations):
        """Automatically fix all issues"""
        self.ui.show_progress("Applying automatic fixes...")
        results = await self.auto_fixer.fix_all(recommendations)
        await self.ui.display_fix_results(results)
    
    async def interactive_fix(self, recommendations):
        """Allow user to select individual fixes"""
        selected_fixes = await self.ui.select_fixes(recommendations)
        if selected_fixes:
            self.ui.show_progress("Applying selected fixes...")
            results = await self.auto_fixer.fix_selected(selected_fixes)
            await self.ui.display_fix_results(results)
    
    async def generate_report(self, scan_results, recommendations):
        """Generate detailed system report"""
        report = await self.recommendation_engine.generate_detailed_report(
            scan_results, recommendations
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"system_health_report_{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.ui.show_message(f"Report saved to: {report_path}")
        
        # Optionally display report in terminal
        if await self.ui.confirm("Display report in terminal?"):
            await self.ui.display_report(report)
    
    async def setup_scheduling(self):
        """Setup scheduled scans"""
        schedule_config = await self.ui.configure_schedule()
        if schedule_config:
            await self.scheduler.setup_schedule(schedule_config)
            self.ui.show_message("Scheduled scans configured successfully")
    
    async def daemon_mode(self):
        """Run in daemon mode for scheduled operations"""
        self.running = True
        self.logger.info("Starting daemon mode...")
        
        while self.running:
            try:
                if await self.scheduler.should_run_scan():
                    self.logger.info("Running scheduled scan...")
                    await self.run_full_scan(interactive=False)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in daemon mode: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def stop_daemon(self):
        """Stop daemon mode"""
        self.running = False
        self.logger.info("Stopping daemon mode...")
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.scheduler.cleanup()
            await self.scanner.cleanup()
            await self.ai_integration.cleanup()
            await self.logger.cleanup()
        except Exception as e:
            print(f"Cleanup error: {e}")

async def signal_handler(healer):
    """Handle shutdown signals"""
    healer.stop_daemon()
    await healer.cleanup()
    sys.exit(0)

async def main():
    parser = argparse.ArgumentParser(
        description="Asahi Linux System Healer - Comprehensive system health management"
    )
    parser.add_argument('--scan', action='store_true', help='Run full system scan')
    parser.add_argument('--daemon', action='store_true', help='Run in daemon mode')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--report-only', action='store_true', help='Generate report only')
    parser.add_argument('--fix-all', action='store_true', help='Auto-fix all issues')
    parser.add_argument('--schedule', help='Setup schedule (format: daily|weekly|monthly)')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    healer = AsahiSystemHealer()
    
    # Setup signal handlers
    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, lambda s, f: asyncio.create_task(signal_handler(healer)))
    
    if not await healer.initialize():
        print("Failed to initialize system healer")
        sys.exit(1)
    
    try:
        if args.daemon:
            await healer.daemon_mode()
        elif args.scan or not any(vars(args).values()):
            await healer.run_full_scan()
        elif args.report_only:
            results, recommendations = await healer.run_full_scan(interactive=False)
            await healer.generate_report(results, recommendations)
        elif args.fix_all:
            results, recommendations = await healer.run_full_scan(interactive=False)
            await healer.auto_fix_all(recommendations)
        elif args.schedule:
            # Setup basic schedule from command line
            await healer.scheduler.setup_basic_schedule(args.schedule)
            
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    finally:
        await healer.cleanup()

if __name__ == "__main__":
    asyncio.run(main())