#!/bin/bash
# Install Asahi Health Manager into system settings for KDE and GNOME

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DESKTOP_INTEGRATION_DIR="$SCRIPT_DIR"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect desktop environment
detect_desktop_environment() {
    if [ -n "$KDE_FULL_SESSION" ] || [ "$XDG_CURRENT_DESKTOP" = "KDE" ] || [ -n "$KDE_SESSION_VERSION" ]; then
        echo "kde"
    elif [ "$XDG_CURRENT_DESKTOP" = "GNOME" ] || [ -n "$GNOME_DESKTOP_SESSION_ID" ]; then
        echo "gnome"
    elif [ "$XDG_CURRENT_DESKTOP" = "XFCE" ]; then
        echo "xfce"
    elif [ "$XDG_CURRENT_DESKTOP" = "MATE" ]; then
        echo "mate"
    else
        echo "unknown"
    fi
}

# Install to system location
install_to_system() {
    print_status "Installing Asahi Health Manager to system location..."
    
    # Create system directory
    sudo mkdir -p /opt/asahi-health-manager
    
    # Copy all project files
    sudo cp -r "$PROJECT_ROOT"/* /opt/asahi-health-manager/
    
    # Set permissions
    sudo chmod +x /opt/asahi-health-manager/*.py
    sudo chmod +x /opt/asahi-health-manager/*.sh
    sudo chmod -R 755 /opt/asahi-health-manager/
    
    # Create system symlink
    sudo ln -sf /opt/asahi-health-manager/ui/app_manager_ui.py /usr/local/bin/asahi-health-manager
    
    print_success "Installed to /opt/asahi-health-manager"
}

# Install icon to system
install_icon() {
    print_status "Installing application icon..."
    
    local icon_source="$PROJECT_ROOT/icons/asahi-app-manager.svg"
    
    if [ -f "$icon_source" ]; then
        sudo mkdir -p /usr/share/pixmaps/
        sudo cp "$icon_source" /usr/share/pixmaps/
        
        # Install to hicolor theme as well
        for size in 16x16 24x24 32x32 48x48 64x64 128x128; do
            sudo mkdir -p "/usr/share/icons/hicolor/$size/apps/"
            sudo cp "$icon_source" "/usr/share/icons/hicolor/$size/apps/asahi-app-manager.svg"
        done
        
        # Update icon cache
        sudo gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true
        
        print_success "Icon installed to system directories"
    else
        print_warning "Icon file not found: $icon_source"
    fi
}

# Install KDE integration
install_kde_integration() {
    print_status "Installing KDE System Settings integration..."
    
    local kde_desktop="$DESKTOP_INTEGRATION_DIR/kde/asahi-health-manager.desktop"
    local kde_target_dir="/usr/share/kservices5"
    local kde_target="$kde_target_dir/kcm_asahi_health.desktop"
    
    # Create KDE services directory
    sudo mkdir -p "$kde_target_dir"
    
    # Install desktop file
    sudo cp "$kde_desktop" "$kde_target"
    
    # Also install to applications directory for fallback
    sudo mkdir -p /usr/share/applications/
    sudo cp "$kde_desktop" /usr/share/applications/asahi-health-manager-kde.desktop
    
    print_success "KDE integration installed"
    print_status "Access via: System Settings → System Administration → Asahi Health Manager"
}

# Install GNOME integration  
install_gnome_integration() {
    print_status "Installing GNOME Control Center integration..."
    
    local gnome_desktop="$DESKTOP_INTEGRATION_DIR/gnome/asahi-health-manager.desktop"
    local gnome_target_dir="/usr/share/applications/"
    local gnome_target="$gnome_target_dir/asahi-health-manager-gnome.desktop"
    
    # Create applications directory
    sudo mkdir -p "$gnome_target_dir"
    
    # Install desktop file
    sudo cp "$gnome_desktop" "$gnome_target"
    
    # Update desktop database
    sudo update-desktop-database "$gnome_target_dir" 2>/dev/null || true
    
    print_success "GNOME integration installed"
    print_status "Access via: Settings → System → Asahi Health Manager"
}

# Install XFCE integration
install_xfce_integration() {
    print_status "Installing XFCE Settings integration..."
    
    local xfce_desktop="$DESKTOP_INTEGRATION_DIR/gnome/asahi-health-manager.desktop"
    local xfce_target="/usr/share/applications/asahi-health-manager-xfce.desktop"
    
    # Modify desktop file for XFCE
    sudo cp "$xfce_desktop" "$xfce_target"
    sudo sed -i 's/Categories=Settings;System;HardwareSettings;/Categories=Settings;System;/' "$xfce_target"
    
    print_success "XFCE integration installed"
    print_status "Access via: Settings Manager → System → Asahi Health Manager"
}

# Main installation function
main() {
    print_status "Asahi Health Manager - System Settings Integration Installer"
    print_status "============================================================"
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        print_error "Please do not run this script as root. Use sudo when prompted."
        exit 1
    fi
    
    # Check if project files exist
    if [ ! -f "$PROJECT_ROOT/ui/app_manager_ui.py" ]; then
        print_error "Project files not found. Please run from the correct directory."
        exit 1
    fi
    
    # Detect desktop environment
    local desktop_env=$(detect_desktop_environment)
    print_status "Detected desktop environment: $desktop_env"
    
    # Install system files
    install_to_system
    install_icon
    
    # Install desktop environment specific integration
    case $desktop_env in
        "kde")
            install_kde_integration
            ;;
        "gnome")
            install_gnome_integration
            ;;
        "xfce")
            install_xfce_integration
            ;;
        "mate")
            install_gnome_integration  # MATE uses similar structure to GNOME
            print_status "Access via: Control Center → System → Asahi Health Manager"
            ;;
        *)
            print_warning "Unknown desktop environment. Installing generic integration..."
            install_gnome_integration  # Generic fallback
            ;;
    esac
    
    # Final setup
    print_status "Running final setup..."
    
    # Create launcher script
    sudo tee /usr/local/bin/asahi-health-settings >/dev/null <<EOF
#!/bin/bash
# Asahi Health Manager System Settings Launcher
cd /opt/asahi-health-manager
exec python3 ui/app_manager_ui.py "\$@"
EOF
    sudo chmod +x /usr/local/bin/asahi-health-settings
    
    print_success "Installation complete!"
    print_status ""
    print_status "Asahi Health Manager has been integrated into your system settings."
    print_status "You can now access it through:"
    
    case $desktop_env in
        "kde")
            print_status "• System Settings → System Administration → Asahi Health Manager"
            ;;
        "gnome")
            print_status "• Settings → System → Asahi Health Manager" 
            ;;
        "xfce")
            print_status "• Settings Manager → System → Asahi Health Manager"
            ;;
        "mate")
            print_status "• Control Center → System → Asahi Health Manager"
            ;;
        *)
            print_status "• Your system's Settings/Control Panel → System section"
            ;;
    esac
    
    print_status "• Command line: asahi-health-settings"
    print_status "• Applications menu: Search for 'Asahi Health Manager'"
    print_status ""
    print_status "You may need to log out and back in for changes to take full effect."
}

# Run main function
main "$@"