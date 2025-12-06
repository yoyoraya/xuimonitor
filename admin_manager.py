#!/usr/bin/env python3
"""
X-UI Monitor - Admin User Management System
Professional interactive menu for managing admin users
"""

import yaml
import bcrypt
import sys
import os
import re
import getpass
from yaml.loader import SafeLoader

# ANSI Color Codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
PURPLE = '\033[0;35m'
CYAN = '\033[0;36m'
WHITE = '\033[1;37m'
BOLD = '\033[1m'
NC = '\033[0m'  # No Color

CONFIG_FILE = 'auth_config.yaml'

#═══════════════════════════════════════════════════════════════════════════════
# Utility Functions
#═══════════════════════════════════════════════════════════════════════════════

def print_banner():
    """Print application banner"""
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"{CYAN}╔═══════════════════════════════════════════════════════════════╗{NC}")
    print(f"{CYAN}║                                                               ║{NC}")
    print(f"{CYAN}║           X-UI Monitor - Admin User Manager                   ║{NC}")
    print(f"{CYAN}║                     Version 2.0                               ║{NC}")
    print(f"{CYAN}║                                                               ║{NC}")
    print(f"{CYAN}╚═══════════════════════════════════════════════════════════════╝{NC}")
    print()

def print_success(message):
    """Print success message"""
    print(f"{GREEN}✓{NC} {message}")

def print_error(message):
    """Print error message"""
    print(f"{RED}✗{NC} {message}")

def print_warning(message):
    """Print warning message"""
    print(f"{YELLOW}⚠{NC} {message}")

def print_info(message):
    """Print info message"""
    print(f"{BLUE}ℹ{NC} {message}")

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validate username format (alphanumeric and underscore only)"""
    pattern = r'^[a-zA-Z0-9_]+$'
    return re.match(pattern, username) is not None

#═══════════════════════════════════════════════════════════════════════════════
# Configuration Management
#═══════════════════════════════════════════════════════════════════════════════

def load_config():
    """Load configuration from YAML file"""
    if not os.path.exists(CONFIG_FILE):
        print_error(f"Configuration file '{CONFIG_FILE}' not found!")
        return None
    
    with open(CONFIG_FILE) as file:
        try:
            config = yaml.load(file, Loader=SafeLoader)
            if config is None:
                config = {}
            if 'credentials' not in config or config['credentials'] is None:
                config['credentials'] = {}
            if 'usernames' not in config['credentials'] or config['credentials']['usernames'] is None:
                config['credentials']['usernames'] = {}
            return config
        except Exception as e:
            print_error(f"Error loading configuration: {e}")
            return {'credentials': {'usernames': {}}}

def save_config(config):
    """Save configuration to YAML file"""
    try:
        with open(CONFIG_FILE, 'w') as file:
            yaml.dump(config, file, default_flow_style=False)
        print_success("Configuration updated successfully!")
        return True
    except Exception as e:
        print_error(f"Failed to save configuration: {e}")
        return False

#═══════════════════════════════════════════════════════════════════════════════
# User Management Functions
#═══════════════════════════════════════════════════════════════════════════════

def add_user(username, email, name, raw_password):
    """Add a new admin user"""
    config = load_config()
    if not config:
        return False

    if username in config['credentials']['usernames']:
        print_warning(f"User '{username}' already exists.")
        return False

    # Hash password
    hashed_pw = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

    # Add user
    config['credentials']['usernames'][username] = {
        "email": email,
        "name": name,
        "password": hashed_pw
    }
    
    # Add to preauthorized emails
    if 'preauthorized' not in config or config['preauthorized'] is None:
        config['preauthorized'] = {'emails': []}
    
    if 'emails' not in config['preauthorized'] or config['preauthorized']['emails'] is None:
        config['preauthorized']['emails'] = []

    if email not in config['preauthorized']['emails']:
        config['preauthorized']['emails'].append(email)

    if save_config(config):
        print_success(f"User '{username}' added successfully!")
        return True
    return False

def delete_user(username):
    """Delete an admin user"""
    config = load_config()
    if not config:
        return False

    if username not in config['credentials']['usernames']:
        print_warning(f"User '{username}' not found.")
        return False

    # Get email before deletion for cleanup
    user_data = config['credentials']['usernames'][username]
    email = user_data.get('email')

    # Delete user
    del config['credentials']['usernames'][username]
    
    # Remove from preauthorized if no other user has this email
    if email and 'preauthorized' in config and 'emails' in config['preauthorized']:
        # Check if any other user has this email
        other_users_with_email = any(
            u.get('email') == email 
            for u in config['credentials']['usernames'].values()
        )
        if not other_users_with_email and email in config['preauthorized']['emails']:
            config['preauthorized']['emails'].remove(email)

    if save_config(config):
        print_success(f"User '{username}' deleted successfully!")
        return True
    return False

def list_users():
    """List all admin users"""
    config = load_config()
    if not config:
        return []
    
    usernames = config.get('credentials', {}).get('usernames', {})
    
    if not usernames:
        print_warning("No users found.")
        return []

    print()
    print(f"{CYAN}╔═══════════════════════════════════════════════════════════════╗{NC}")
    print(f"{CYAN}║                    Active Admin Users                        ║{NC}")
    print(f"{CYAN}╚═══════════════════════════════════════════════════════════════╝{NC}")
    print()
    
    for idx, (username, data) in enumerate(usernames.items(), 1):
        name = data.get('name', 'N/A')
        email = data.get('email', 'N/A')
        print(f"  {GREEN}{idx}.{NC} {BOLD}{username}{NC}")
        print(f"     Name:  {name}")
        print(f"     Email: {email}")
        print()
    
    return list(usernames.keys())

#═══════════════════════════════════════════════════════════════════════════════
# Interactive Menu Functions
#═══════════════════════════════════════════════════════════════════════════════

def interactive_add_user():
    """Interactive user addition with validation"""
    print_banner()
    print(f"{GREEN}╔═══════════════════════════════════════════════════════════════╗{NC}")
    print(f"{GREEN}║                      Add New Admin User                      ║{NC}")
    print(f"{GREEN}╚═══════════════════════════════════════════════════════════════╝{NC}")
    print()
    
    # Get username
    while True:
        username = input(f"{CYAN}Username:{NC} ").strip()
        if not username:
            print_error("Username cannot be empty!")
        elif not validate_username(username):
            print_error("Username can only contain letters, numbers, and underscore!")
        else:
            break
    
    # Get full name
    while True:
        name = input(f"{CYAN}Full Name:{NC} ").strip()
        if not name:
            print_error("Name cannot be empty!")
        else:
            break
    
    # Get email
    while True:
        email = input(f"{CYAN}Email:{NC} ").strip()
        if not email:
            print_error("Email cannot be empty!")
        elif not validate_email(email):
            print_error("Invalid email format!")
        else:
            break
    
    # Get password
    while True:
        password = getpass.getpass(f"{CYAN}Password:{NC} ")
        if not password:
            print_error("Password cannot be empty!")
        elif len(password) < 6:
            print_error("Password must be at least 6 characters!")
        else:
            confirm = getpass.getpass(f"{CYAN}Confirm Password:{NC} ")
            if password != confirm:
                print_error("Passwords do not match!")
            else:
                break
    
    print()
    print_info("Creating user...")
    
    if add_user(username, email, name, password):
        print()
        print(f"{CYAN}═══════════════════════════════════════════════════════════════{NC}")
        print(f"{GREEN}Username:{NC} {username}")
        print(f"{GREEN}Name:{NC}     {name}")
        print(f"{GREEN}Email:{NC}    {email}")
        print(f"{CYAN}═══════════════════════════════════════════════════════════════{NC}")

def interactive_delete_user():
    """Interactive user deletion with confirmation"""
    print_banner()
    print(f"{RED}╔═══════════════════════════════════════════════════════════════╗{NC}")
    print(f"{RED}║                      Delete Admin User                       ║{NC}")
    print(f"{RED}╚═══════════════════════════════════════════════════════════════╝{NC}")
    print()
    
    # List users first
    users = list_users()
    
    if not users:
        return
    
    print()
    
    # Get username to delete
    while True:
        username = input(f"{CYAN}Enter username to delete:{NC} ").strip()
        if not username:
            print_error("Username cannot be empty!")
        elif username not in users:
            print_error(f"User '{username}' not found! Please select from the list above.")
        else:
            break
    
    # Confirmation
    print()
    print_warning(f"You are about to delete user: {BOLD}{username}{NC}")
    confirm = input(f"{YELLOW}Are you sure? [y/N]:{NC} ").strip().lower()
    
    if confirm in ['y', 'yes']:
        print()
        delete_user(username)
    else:
        print_info("Deletion cancelled.")

def show_main_menu():
    """Display and handle main menu"""
    while True:
        print_banner()
        print(f"{WHITE}Please select an option:{NC}")
        print()
        print(f"  {GREEN}1){NC} Add New Admin User")
        print(f"  {BLUE}2){NC} List All Admin Users")
        print(f"  {RED}3){NC} Delete Admin User")
        print(f"  {WHITE}0){NC} Exit")
        print()
        
        choice = input(f"{CYAN}Enter your choice [0-3]:{NC} ").strip()
        
        if choice == '1':
            interactive_add_user()
            input(f"\n{CYAN}Press Enter to continue...{NC}")
        elif choice == '2':
            print_banner()
            list_users()
            input(f"{CYAN}Press Enter to continue...{NC}")
        elif choice == '3':
            interactive_delete_user()
            input(f"\n{CYAN}Press Enter to continue...{NC}")
        elif choice == '0':
            print()
            print_info("Goodbye!")
            print()
            sys.exit(0)
        else:
            print_error("Invalid option!")
            input(f"{CYAN}Press Enter to continue...{NC}")

#═══════════════════════════════════════════════════════════════════════════════
# Main Entry Point
#═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Check if running with command-line arguments (for backward compatibility)
    if len(sys.argv) > 1:
        action = sys.argv[1]
        
        if action == "add" and len(sys.argv) == 6:
            add_user(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        elif action == "del" and len(sys.argv) == 3:
            delete_user(sys.argv[2])
        elif action == "list":
            list_users()
        else:
            print_error("Invalid arguments!")
            print()
            print("Usage:")
            print("  python3 admin_manager.py add <username> <email> <name> <password>")
            print("  python3 admin_manager.py del <username>")
            print("  python3 admin_manager.py list")
            print()
            print("Or run without arguments for interactive menu:")
            print("  python3 admin_manager.py")
    else:
        # Run interactive menu
        try:
            show_main_menu()
        except KeyboardInterrupt:
            print()
            print()
            print_info("Interrupted by user. Goodbye!")
            print()
            sys.exit(0)
