#!/bin/bash

# Asahi System Healer Installation Script
# This script installs the Asahi System Healer on Asahi Linux systems

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/asahi-healer"
BIN_DIR="/usr/local/bin"
CONFIG_DIR="$HOME/.config/asahi_healer"
SERVICE_FILE="/etc/systemd/system/asahi-healer.service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Asahi Linux
check_asahi() {
    info "Checking if running on Asahi Linux..."
    
    if uname -r | grep -q "asahi\|16k"; then
        success "Asahi Linux detected"
        return 0
    else
        warning "This doesn't appear to be Asahi Linux"
        echo "The system healer is specifically designed for Asahi Linux on Apple Silicon Macs."
        echo "While it may work on other systems, some features may not function correctly."
        
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Installation cancelled"
            exit 1
        fi
    fi
}

# Check system requirements
check_requirements() {
    info "Checking system requirements..."
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -ge 9 ]]; then
            success "Python $PYTHON_VERSION found"
        else
            error "Python 3.9 or higher required (found $PYTHON_VERSION)"
            exit 1
        fi
    else
        error "Python 3 not found"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        error "pip3 not found. Please install pip3."
        exit 1
    fi
    
    # Check required system tools
    local required_tools=("sudo" "systemctl" "crontab")
    for tool in "${required_tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            success "$tool found"
        else
            error "$tool not found but required"
            exit 1
        fi
    done
}

# Install Python dependencies
install_dependencies() {
    info "Installing Python dependencies..."
    
    if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
        pip3 install --user -r "$SCRIPT_DIR/requirements.txt"
        success "Dependencies installed"
    else
        error "requirements.txt not found"
        exit 1
    fi
}

# Install the application
install_application() {
    info "Installing Asahi System Healer..."
    
    # Create installation directory
    sudo mkdir -p "$INSTALL_DIR"
    
    # Copy application files
    sudo cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"
    
    # Set proper permissions
    sudo chmod +x "$INSTALL_DIR/asahi_healer.py"
    sudo chmod +x "$INSTALL_DIR/install.sh"
    
    # Create symlink in PATH
    sudo ln -sf "$INSTALL_DIR/asahi_healer.py" "$BIN_DIR/asahi-healer"
    
    success "Application installed to $INSTALL_DIR"
}

# Create configuration directory
setup_config() {
    info "Setting up configuration..."
    
    mkdir -p "$CONFIG_DIR"
    
    if [[ ! -f "$CONFIG_DIR/config.yaml" ]]; then
        # Run configuration wizard
        info "Running configuration wizard..."
        python3 "$INSTALL_DIR/asahi_healer.py" --setup || {
            warning "Configuration wizard failed or was cancelled"
            info "You can run 'asahi-healer --setup' later to configure the application"
        }
    else
        info "Configuration already exists at $CONFIG_DIR"
    fi
}

# Create systemd service
create_service() {
    info "Creating systemd service..."
    
    cat > /tmp/asahi-healer.service << EOF
[Unit]
Description=Asahi System Healer Daemon
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=10
User=$USER
ExecStart=$INSTALL_DIR/asahi_healer.py --daemon
WorkingDirectory=$INSTALL_DIR
Environment=PATH=/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF

    sudo mv /tmp/asahi-healer.service "$SERVICE_FILE"
    sudo systemctl daemon-reload
    
    success "Systemd service created"
}

# Setup log rotation
setup_logrotate() {
    info "Setting up log rotation..."
    
    cat > /tmp/asahi-healer << EOF
$HOME/.local/log/asahi_healer/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
}
EOF

    sudo mv /tmp/asahi-healer /etc/logrotate.d/asahi-healer
    success "Log rotation configured"
}

# Display post-installation instructions
show_instructions() {
    success "Installation completed successfully!"
    echo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
    info "🚀 Getting Started:"
    echo
    echo "  1. Run a system scan:"
    echo "     asahi-healer --scan"
    echo
    echo "  2. Setup scheduled scans:"
    echo "     asahi-healer --schedule daily"
    echo
    echo "  3. Start the daemon service:"
    echo "     sudo systemctl enable --now asahi-healer"
    echo
    echo "  4. View help:"
    echo "     asahi-healer --help"
    echo
    info "📁 Important Locations:"
    echo
    echo "  Application:    $INSTALL_DIR"
    echo "  Configuration:  $CONFIG_DIR"
    echo "  Logs:          $HOME/.local/log/asahi_healer"
    echo "  Backups:       $HOME/.asahi_healer_backups"
    echo
    info "🔧 Configuration:"
    echo
    echo "  Run the setup wizard anytime:"
    echo "     asahi-healer --setup"
    echo
    echo "  Edit configuration file:"
    echo "     nano $CONFIG_DIR/config.yaml"
    echo
    info "🤖 AI Features:"
    echo
    echo "  To enable AI-powered analysis, set your API keys:"
    echo "     export CLAUDE_API_KEY=\"your-claude-key\""
    echo "     export OPENAI_API_KEY=\"your-openai-key\""
    echo
    echo "  Or add them to your shell configuration (~/.bashrc, ~/.zshrc)"
    echo
    warning "⚠️  Important Security Notes:"
    echo
    echo "  • Always review fixes before applying them"
    echo "  • Backups are created automatically before changes"
    echo "  • Use --dry-run to preview changes safely"
    echo "  • Check logs regularly: tail -f $HOME/.local/log/asahi_healer/asahi_healer.log"
    echo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
    success "Happy system healing! 🩺✨"
}

# Uninstall function
uninstall() {
    info "Uninstalling Asahi System Healer..."
    
    # Stop and disable service
    if [[ -f "$SERVICE_FILE" ]]; then
        sudo systemctl stop asahi-healer 2>/dev/null || true
        sudo systemctl disable asahi-healer 2>/dev/null || true
        sudo rm -f "$SERVICE_FILE"
        sudo systemctl daemon-reload
    fi
    
    # Remove cron jobs
    crontab -l 2>/dev/null | grep -v "asahi_healer" | crontab - 2>/dev/null || true
    
    # Remove application files
    if [[ -d "$INSTALL_DIR" ]]; then
        sudo rm -rf "$INSTALL_DIR"
    fi
    
    # Remove symlink
    if [[ -L "$BIN_DIR/asahi-healer" ]]; then
        sudo rm -f "$BIN_DIR/asahi-healer"
    fi
    
    # Remove log rotation
    if [[ -f "/etc/logrotate.d/asahi-healer" ]]; then
        sudo rm -f /etc/logrotate.d/asahi-healer
    fi
    
    # Ask about configuration and logs
    echo
    warning "The following directories contain user data:"
    echo "  Configuration: $CONFIG_DIR"
    echo "  Logs: $HOME/.local/log/asahi_healer"
    echo "  Backups: $HOME/.asahi_healer_backups"
    echo
    read -p "Remove these directories? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$CONFIG_DIR" 2>/dev/null || true
        rm -rf "$HOME/.local/log/asahi_healer" 2>/dev/null || true
        rm -rf "$HOME/.asahi_healer_backups" 2>/dev/null || true
        info "User data removed"
    else
        info "User data preserved"
    fi
    
    success "Uninstallation completed"
}

# Main installation function
main() {
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                 ASAHI SYSTEM HEALER INSTALLER                 ║"
    echo "║            Advanced System Health Management                  ║"
    echo "║                   for Asahi Linux                           ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo
    
    # Parse arguments
    case "${1:-install}" in
        install|"")
            check_asahi
            check_requirements
            install_dependencies
            install_application
            setup_config
            create_service
            setup_logrotate
            show_instructions
            ;;
        uninstall|remove)
            uninstall
            ;;
        update)
            info "Updating Asahi System Healer..."
            install_dependencies
            install_application
            sudo systemctl daemon-reload
            success "Update completed"
            ;;
        --help|-h)
            echo "Asahi System Healer Installer"
            echo
            echo "Usage: $0 [command]"
            echo
            echo "Commands:"
            echo "  install    Install Asahi System Healer (default)"
            echo "  uninstall  Remove Asahi System Healer"
            echo "  update     Update to latest version"
            echo "  --help     Show this help message"
            ;;
        *)
            error "Unknown command: $1"
            echo "Use '$0 --help' for usage information"
            exit 1
            ;;
    esac
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    error "Do not run this installer as root"
    echo "The installer will use sudo when needed for system-level changes"
    exit 1
fi

# Run main function
main "$@"