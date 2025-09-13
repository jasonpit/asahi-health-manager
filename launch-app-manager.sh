#!/bin/bash
# Asahi App Manager Launcher Script

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set working directory to the app location
cd "$SCRIPT_DIR"

# Check if we're in a terminal or need to open one
if [ -t 1 ]; then
    # We're already in a terminal, run directly
    python3 asahi_healer.py --apps
else
    # We need to open a terminal
    # Try different terminal emulators based on desktop environment
    if command -v konsole >/dev/null 2>&1; then
        # KDE Plasma
        konsole --hold -e bash -c "cd '$SCRIPT_DIR' && python3 asahi_healer.py --apps"
    elif command -v gnome-terminal >/dev/null 2>&1; then
        # GNOME
        gnome-terminal --wait --title="Asahi App Manager" -- bash -c "cd '$SCRIPT_DIR' && python3 asahi_healer.py --apps; read -p 'Press Enter to close...'"
    elif command -v xfce4-terminal >/dev/null 2>&1; then
        # XFCE
        xfce4-terminal --hold --title="Asahi App Manager" --command="bash -c 'cd $SCRIPT_DIR && python3 asahi_healer.py --apps'"
    elif command -v mate-terminal >/dev/null 2>&1; then
        # MATE
        mate-terminal --title="Asahi App Manager" --command="bash -c 'cd $SCRIPT_DIR && python3 asahi_healer.py --apps; read -p \"Press Enter to close...\"'"
    elif command -v alacritty >/dev/null 2>&1; then
        # Alacritty
        alacritty --title "Asahi App Manager" --hold --command bash -c "cd '$SCRIPT_DIR' && python3 asahi_healer.py --apps"
    elif command -v kitty >/dev/null 2>&1; then
        # Kitty
        kitty --title "Asahi App Manager" --hold bash -c "cd '$SCRIPT_DIR' && python3 asahi_healer.py --apps"
    elif command -v tilix >/dev/null 2>&1; then
        # Tilix
        tilix --title="Asahi App Manager" --command="bash -c 'cd $SCRIPT_DIR && python3 asahi_healer.py --apps; read -p \"Press Enter to close...\"'"
    elif command -v x-terminal-emulator >/dev/null 2>&1; then
        # Generic terminal
        x-terminal-emulator -T "Asahi App Manager" -e bash -c "cd '$SCRIPT_DIR' && python3 asahi_healer.py --apps; read -p 'Press Enter to close...'"
    else
        # Fallback: try to find any terminal
        for term in xterm urxvt rxvt terminator; do
            if command -v "$term" >/dev/null 2>&1; then
                "$term" -T "Asahi App Manager" -e bash -c "cd '$SCRIPT_DIR' && python3 asahi_healer.py --apps; read -p 'Press Enter to close...'"
                break
            fi
        done
    fi
fi