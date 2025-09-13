#!/usr/bin/env python3
"""
Standalone Profile Manager launcher for Asahi Health Manager
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ui.profile_manager_ui import ProfileManagerUI

def main():
    """Main entry point"""
    try:
        ui = ProfileManagerUI()
        ui.run()
    except KeyboardInterrupt:
        print("\n\nProfile manager closed.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()