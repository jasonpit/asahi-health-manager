#!/bin/bash
# Asahi Theme Manager Launcher Script

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set working directory to the app location
cd "$SCRIPT_DIR"

# Launch theme manager directly
if [ -t 1 ]; then
    # We're already in a terminal, run directly
    python3 -c "
from ui.theme_manager_ui import ThemeManagerUI
ui = ThemeManagerUI()
ui.run()
"
else
    # We need to open a terminal
    if command -v konsole >/dev/null 2>&1; then
        konsole --hold -e bash -c "cd '$SCRIPT_DIR' && python3 -c 'from ui.theme_manager_ui import ThemeManagerUI; ui = ThemeManagerUI(); ui.run()'"
    elif command -v gnome-terminal >/dev/null 2>&1; then
        gnome-terminal --wait --title="Asahi Theme Manager" -- bash -c "cd '$SCRIPT_DIR' && python3 -c 'from ui.theme_manager_ui import ThemeManagerUI; ui = ThemeManagerUI(); ui.run()'; read -p 'Press Enter to close...'"
    elif command -v xfce4-terminal >/dev/null 2>&1; then
        xfce4-terminal --hold --title="Asahi Theme Manager" --command="bash -c 'cd $SCRIPT_DIR && python3 -c \"from ui.theme_manager_ui import ThemeManagerUI; ui = ThemeManagerUI(); ui.run()\"'"
    else
        # Fallback
        x-terminal-emulator -T "Asahi Theme Manager" -e bash -c "cd '$SCRIPT_DIR' && python3 -c 'from ui.theme_manager_ui import ThemeManagerUI; ui = ThemeManagerUI(); ui.run()'; read -p 'Press Enter to close...'"
    fi
fi