#!/bin/bash
# Install desktop integration for Asahi App Manager

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Installing Asahi App Manager Desktop Integration...${NC}"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create directories if they don't exist
mkdir -p ~/.local/share/applications
mkdir -p ~/.local/share/icons/hicolor/scalable/apps

# Copy icon
echo -e "${YELLOW}Installing application icon...${NC}"
cp "$SCRIPT_DIR/icons/asahi-app-manager.svg" ~/.local/share/icons/hicolor/scalable/apps/

# Update desktop entry with absolute paths
echo -e "${YELLOW}Creating desktop entry...${NC}"
sed "s|/home/jason/src/GitHub/asahi-health-manager|$SCRIPT_DIR|g" "$SCRIPT_DIR/asahi-app-manager.desktop" > ~/.local/share/applications/asahi-app-manager.desktop

# Make desktop entry executable
chmod +x ~/.local/share/applications/asahi-app-manager.desktop

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    echo -e "${YELLOW}Updating desktop database...${NC}"
    update-desktop-database ~/.local/share/applications/
fi

# Update icon cache
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    echo -e "${YELLOW}Updating icon cache...${NC}"
    gtk-update-icon-cache ~/.local/share/icons/hicolor/ 2>/dev/null || true
fi

# Detect desktop environment and provide specific instructions
DE="Unknown"
if [ "$XDG_CURRENT_DESKTOP" ]; then
    DE="$XDG_CURRENT_DESKTOP"
elif [ "$DESKTOP_SESSION" ]; then
    DE="$DESKTOP_SESSION"
fi

echo -e "${GREEN}✓ Desktop integration installed successfully!${NC}"
echo
echo -e "${BLUE}How to access Asahi App Manager:${NC}"
echo

case "$DE" in
    *KDE*|*Plasma*)
        echo -e "• ${YELLOW}KDE Plasma:${NC}"
        echo "  - Press Alt+F2 and type 'Asahi App Manager'"
        echo "  - Right-click on desktop/taskbar → Add widgets → Search for 'Asahi'"
        echo "  - Open Application Menu → System → Asahi App Manager"
        ;;
    *GNOME*|*Ubuntu*)
        echo -e "• ${YELLOW}GNOME:${NC}"
        echo "  - Press Super key and type 'Asahi App Manager'"
        echo "  - Open Activities → Show Applications → Asahi App Manager"
        echo "  - Right-click the app icon → Add to Favorites"
        ;;
    *XFCE*)
        echo -e "• ${YELLOW}XFCE:${NC}"
        echo "  - Open Applications Menu → System → Asahi App Manager"
        echo "  - Right-click on panel → Panel → Add New Items → Application Launcher"
        ;;
    *MATE*)
        echo -e "• ${YELLOW}MATE:${NC}"
        echo "  - Open Applications Menu → System Tools → Asahi App Manager"
        echo "  - Right-click the app → Add this launcher to panel"
        ;;
    *)
        echo -e "• ${YELLOW}General:${NC}"
        echo "  - Look in your applications menu under 'System' category"
        echo "  - Search for 'Asahi App Manager'"
        ;;
esac

echo
echo -e "${BLUE}Available actions:${NC}"
echo "• Main App Manager - Browse and install applications"
echo "• Theme Manager - Customize your desktop appearance"  
echo "• System Health Scan - Check system health"
echo
echo -e "${GREEN}Right-click the app icon for quick access to these features!${NC}"

# Test if we can launch the app
echo
echo -e "${YELLOW}Testing installation...${NC}"
if [ -f ~/.local/share/applications/asahi-app-manager.desktop ]; then
    echo -e "${GREEN}✓ Desktop entry created successfully${NC}"
else
    echo -e "${RED}✗ Failed to create desktop entry${NC}"
fi

if [ -f ~/.local/share/icons/hicolor/scalable/apps/asahi-app-manager.svg ]; then
    echo -e "${GREEN}✓ Icon installed successfully${NC}"
else
    echo -e "${RED}✗ Failed to install icon${NC}"
fi

echo
echo -e "${BLUE}Installation complete! You can now find 'Asahi App Manager' in your applications menu.${NC}"