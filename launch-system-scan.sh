#!/bin/bash
# Asahi System Scan Launcher Script

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set working directory to the app location
cd "$SCRIPT_DIR"

# Launch system scan
if [ -t 1 ]; then
    # We're already in a terminal, run directly
    python3 asahi_healer.py --scan
else
    # We need to open a terminal
    if command -v konsole >/dev/null 2>&1; then
        konsole --hold -e bash -c "cd '$SCRIPT_DIR' && python3 asahi_healer.py --scan"
    elif command -v gnome-terminal >/dev/null 2>&1; then
        gnome-terminal --wait --title="Asahi System Scan" -- bash -c "cd '$SCRIPT_DIR' && python3 asahi_healer.py --scan; read -p 'Press Enter to close...'"
    elif command -v xfce4-terminal >/dev/null 2>&1; then
        xfce4-terminal --hold --title="Asahi System Scan" --command="bash -c 'cd $SCRIPT_DIR && python3 asahi_healer.py --scan'"
    else
        # Fallback
        x-terminal-emulator -T "Asahi System Scan" -e bash -c "cd '$SCRIPT_DIR' && python3 asahi_healer.py --scan; read -p 'Press Enter to close...'"
    fi
fi