#!/bin/bash
#═══════════════════════════════════════════════════════════════════════════════
# X-UI Monitor - Professional Installer & Manager
# Version: 2.0
# Description: Complete installation and management script for X-UI Monitor
#═══════════════════════════════════════════════════════════════════════════════

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="xui-monitor"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
INSTALL_DIR=$(pwd)
VENV_DIR="${INSTALL_DIR}/venv"
CONFIG_FILE="${INSTALL_DIR}/auth_config.yaml"
SECRET_KEY="${INSTALL_DIR}/secret.key"
PORT=8501

#═══════════════════════════════════════════════════════════════════════════════
# Utility Functions
#═══════════════════════════════════════════════════════════════════════════════

print_banner() {
    clear
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║              X-UI Monitor Management System                   ║"
    echo "║                      Version 2.0                              ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Please run as root (use sudo)"
        exit 1
    fi
}

loading_animation() {
    local pid=$1
    local message=$2
    local spin='-\|/'
    local i=0
    
    while kill -0 $pid 2>/dev/null; do
        i=$(( (i+1) %4 ))
        printf "\r${BLUE}${spin:$i:1}${NC} $message"
        sleep .1
    done
    printf "\r"
}

#═══════════════════════════════════════════════════════════════════════════════
# Installation Functions
#═══════════════════════════════════════════════════════════════════════════════

install_dependencies() {
    print_info "Installing system dependencies..."
    
    apt update -qq &
    loading_animation $! "Updating package lists..."
    wait $!
    print_success "Package lists updated"
    
    apt install -y python3-pip python3-venv git curl -qq &
    loading_animation $! "Installing dependencies..."
    wait $!
    print_success "Dependencies installed"
}

setup_virtual_environment() {
    print_info "Setting up Python virtual environment..."
    
    if [ -d "$VENV_DIR" ]; then
        print_warning "Virtual environment already exists, skipping..."
    else
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    fi
    
    source "$VENV_DIR/bin/activate"
    
    print_info "Installing Python packages..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    print_success "Python packages installed"
}

setup_configuration() {
    print_info "Setting up configuration files..."
    
    # Create auth config
    if [ ! -f "$CONFIG_FILE" ]; then
        if [ -f "auth_config.example.yaml" ]; then
            cp auth_config.example.yaml "$CONFIG_FILE"
        else
            cat > "$CONFIG_FILE" <<EOF
credentials:
  usernames: {}
cookie:
  expiry_days: 30
  key: 'random_signature_key_$(date +%s)'
  name: 'xui_cookie'
preauthorized:
  emails: []
EOF
        fi
        print_success "Configuration file created"
    else
        print_warning "Configuration file already exists"
    fi
    
    # Generate encryption key
    if [ ! -f "$SECRET_KEY" ]; then
        python3 -c "from cryptography.fernet import Fernet; open('$SECRET_KEY', 'wb').write(Fernet.generate_key())"
        print_success "Encryption key generated"
    else
        print_warning "Encryption key already exists"
    fi
}

create_admin_user() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${WHITE}              Administrator Account Setup${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Check if any admin users exist
    local has_users=false
    if ! grep -q "usernames: {}" "$CONFIG_FILE" && grep -q "usernames:" "$CONFIG_FILE"; then
        # Show existing users
        echo -e "${BLUE}Existing admin users:${NC}"
        python3 -c "
import yaml
try:
    with open('$CONFIG_FILE') as f:
        config = yaml.safe_load(f)
        users = config.get('credentials', {}).get('usernames', {})
        if users:
            for idx, (username, data) in enumerate(users.items(), 1):
                print(f'  {idx}. {username} ({data.get(\"email\", \"N/A\")})')
        else:
            print('  No users found')
except:
    print('  No users found')
"
        echo ""
        has_users=true
    else
        print_warning "No admin users found!"
        echo ""
    fi
    
    # Ask if user wants to create new admin
    local create_new=""
    if [ "$has_users" = true ]; then
        read -p "$(echo -e ${CYAN}Do you want to create a new admin user? [y/N]:${NC} )" create_new
    else
        create_new="y"
        print_info "You need to create at least one admin user to access the panel."
        echo ""
    fi
    
    if [[ "$create_new" =~ ^[Yy]$ ]]; then
        local username password email confirm_password name
        
        # Get username
        while true; do
            read -p "$(echo -e ${GREEN}Username:${NC} )" username
            if [ -z "$username" ]; then
                print_error "Username cannot be empty"
            elif [[ ! "$username" =~ ^[a-zA-Z0-9_]+$ ]]; then
                print_error "Username can only contain letters, numbers and underscore"
            else
                # Check if username already exists
                if python3 -c "
import yaml
with open('$CONFIG_FILE') as f:
    config = yaml.safe_load(f)
    users = config.get('credentials', {}).get('usernames', {})
    exit(0 if '$username' in users else 1)
" 2>/dev/null; then
                    print_error "Username '$username' already exists!"
                else
                    break
                fi
            fi
        done
        
        # Get full name
        while true; do
            read -p "$(echo -e ${GREEN}Full Name:${NC} )" name
            if [ -z "$name" ]; then
                print_error "Name cannot be empty"
            else
                break
            fi
        done
        
        # Get email
        while true; do
            read -p "$(echo -e ${GREEN}Email:${NC} )" email
            if [ -z "$email" ]; then
                print_error "Email cannot be empty"
            elif [[ ! "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
                print_error "Invalid email format"
            else
                break
            fi
        done
        
        # Get password
        while true; do
            read -s -p "$(echo -e ${GREEN}Password:${NC} )" password
            echo ""
            if [ -z "$password" ]; then
                print_error "Password cannot be empty"
            elif [ ${#password} -lt 6 ]; then
                print_error "Password must be at least 6 characters"
            else
                read -s -p "$(echo -e ${GREEN}Confirm Password:${NC} )" confirm_password
                echo ""
                if [ "$password" != "$confirm_password" ]; then
                    print_error "Passwords do not match"
                else
                    break
                fi
            fi
        done
        
        # Create admin user
        echo ""
        print_info "Creating admin user..."
        python3 admin_manager.py add "$username" "$email" "$name" "$password"
        
        echo ""
        echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}Username:${NC} $username"
        echo -e "${GREEN}Name:${NC}     $name"
        echo -e "${GREEN}Email:${NC}    $email"
        echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    else
        print_info "Skipping admin user creation."
    fi
}

create_systemd_service() {
    print_info "Creating systemd service..."
    
    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=X-UI Monitor Dashboard
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
ExecStart=${VENV_DIR}/bin/streamlit run main.py --server.port ${PORT} --server.address 0.0.0.0 --theme.base "dark"
Restart=always
RestartSec=3
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=${SERVICE_NAME}

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME" > /dev/null 2>&1
    print_success "Systemd service created and enabled"
}

start_service() {
    print_info "Starting X-UI Monitor service..."
    systemctl restart "$SERVICE_NAME"
    
    # Wait for service to start
    sleep 2
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Service started successfully"
        return 0
    else
        print_error "Service failed to start"
        print_info "Check logs with: journalctl -u $SERVICE_NAME -n 50"
        return 1
    fi
}

display_installation_complete() {
    local ipv4=$(curl -4s --max-time 5 ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")
    
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║            ✓ Installation Completed Successfully!            ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Access your panel at:${NC}"
    echo -e "${WHITE}  → http://${ipv4}:${PORT}${NC}"
    echo ""
    echo -e "${CYAN}Useful commands:${NC}"
    echo -e "${WHITE}  Status:  ${NC}systemctl status ${SERVICE_NAME}"
    echo -e "${WHITE}  Stop:    ${NC}systemctl stop ${SERVICE_NAME}"
    echo -e "${WHITE}  Start:   ${NC}systemctl start ${SERVICE_NAME}"
    echo -e "${WHITE}  Restart: ${NC}systemctl restart ${SERVICE_NAME}"
    echo -e "${WHITE}  Logs:    ${NC}journalctl -u ${SERVICE_NAME} -f"
    echo ""
}

#═══════════════════════════════════════════════════════════════════════════════
# Uninstallation Functions
#═══════════════════════════════════════════════════════════════════════════════

uninstall_service() {
    print_banner
    echo -e "${RED}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                  UNINSTALL X-UI MONITOR                       ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    print_warning "This will remove X-UI Monitor completely from your system"
    echo ""
    read -p "$(echo -e ${YELLOW}Are you sure? [y/N]:${NC} )" confirm
    
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        print_info "Uninstallation cancelled"
        return
    fi
    
    echo ""
    read -p "$(echo -e ${YELLOW}Delete all data and configurations? [y/N]:${NC} )" delete_data
    
    echo ""
    print_info "Starting uninstallation..."
    
    # Stop and disable service
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        systemctl stop "$SERVICE_NAME"
        print_success "Service stopped"
    fi
    
    if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        systemctl disable "$SERVICE_NAME" > /dev/null 2>&1
        print_success "Service disabled"
    fi
    
    # Remove service file
    if [ -f "$SERVICE_FILE" ]; then
        rm -f "$SERVICE_FILE"
        systemctl daemon-reload
        print_success "Service file removed"
    fi
    
    # Remove data if requested
    if [[ "$delete_data" =~ ^[Yy]$ ]]; then
        if [ -d "$VENV_DIR" ]; then
            rm -rf "$VENV_DIR"
            print_success "Virtual environment removed"
        fi
        
        if [ -f "$CONFIG_FILE" ]; then
            rm -f "$CONFIG_FILE"
            print_success "Configuration file removed"
        fi
        
        if [ -f "$SECRET_KEY" ]; then
            rm -f "$SECRET_KEY"
            print_success "Encryption key removed"
        fi
        
        # Remove Python cache
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        print_success "Cache files removed"
    else
        print_info "Configuration and data files preserved"
    fi
    
    echo ""
    print_success "X-UI Monitor has been uninstalled successfully"
    echo ""
}

#═══════════════════════════════════════════════════════════════════════════════
# Service Management Functions
#═══════════════════════════════════════════════════════════════════════════════

service_status() {
    print_banner
    echo -e "${CYAN}Service Status:${NC}"
    echo ""
    systemctl status "$SERVICE_NAME" --no-pager || true
    echo ""
}

service_logs() {
    print_banner
    echo -e "${CYAN}Service Logs (Last 50 lines):${NC}"
    echo -e "${CYAN}Press Ctrl+C to exit${NC}"
    echo ""
    journalctl -u "$SERVICE_NAME" -n 50 -f
}

restart_service() {
    print_info "Restarting X-UI Monitor service..."
    systemctl restart "$SERVICE_NAME"
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Service restarted successfully"
    else
        print_error "Service failed to restart"
    fi
}

#═══════════════════════════════════════════════════════════════════════════════
# Main Menu
#═══════════════════════════════════════════════════════════════════════════════

show_main_menu() {
    while true; do
        print_banner
        echo -e "${WHITE}Please select an option:${NC}"
        echo ""
        echo -e "  ${GREEN}1)${NC} Install X-UI Monitor"
        echo -e "  ${BLUE}2)${NC} Service Status"
        echo -e "  ${BLUE}3)${NC} Restart Service"
        echo -e "  ${BLUE}4)${NC} View Logs"
        echo -e "  ${PURPLE}5)${NC} Manage Admin Users"
        echo -e "  ${RED}6)${NC} Uninstall X-UI Monitor"
        echo -e "  ${WHITE}0)${NC} Exit"
        echo ""
        read -p "$(echo -e ${CYAN}Enter your choice [0-6]:${NC} )" choice
        
        case $choice in
            1)
                install_xui_monitor
                read -p "Press Enter to continue..."
                ;;
            2)
                service_status
                read -p "Press Enter to continue..."
                ;;
            3)
                restart_service
                read -p "Press Enter to continue..."
                ;;
            4)
                service_logs
                ;;
            5)
                manage_admins
                read -p "Press Enter to continue..."
                ;;
            6)
                uninstall_service
                read -p "Press Enter to continue..."
                ;;
            0)
                echo ""
                print_info "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid option"
                sleep 1
                ;;
        esac
    done
}

manage_admins() {
    print_banner
    source "$VENV_DIR/bin/activate" 2>/dev/null || {
        print_error "Virtual environment not found. Please install first."
        return
    }
    
    python3 admin_manager.py
}

install_xui_monitor() {
    print_banner
    echo -e "${GREEN}Starting X-UI Monitor installation...${NC}"
    echo ""
    
    install_dependencies
    setup_virtual_environment
    setup_configuration
    create_admin_user
    create_systemd_service
    start_service
    
    if [ $? -eq 0 ]; then
        display_installation_complete
    fi
}

#═══════════════════════════════════════════════════════════════════════════════
# Main Entry Point
#═══════════════════════════════════════════════════════════════════════════════

main() {
    check_root
    
    # Check if running with arguments
    if [ $# -eq 0 ]; then
        show_main_menu
    else
        case "$1" in
            install)
                install_xui_monitor
                ;;
            uninstall)
                uninstall_service
                ;;
            status)
                service_status
                ;;
            restart)
                restart_service
                ;;
            logs)
                service_logs
                ;;
            *)
                echo "Usage: $0 {install|uninstall|status|restart|logs}"
                echo "  Or run without arguments for interactive menu"
                exit 1
                ;;
        esac
    fi
}

main "$@"
