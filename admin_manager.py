import yaml
import bcrypt
import sys
import os
from yaml.loader import SafeLoader

CONFIG_FILE = 'auth_config.yaml'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ Error: {CONFIG_FILE} not found!")
        return None
    with open(CONFIG_FILE) as file:
        return yaml.load(file, Loader=SafeLoader)

def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)
    print("✅ Config Saved!")

def add_user(username, email, name, raw_password):
    config = load_config()
    if not config: return

    if username in config['credentials']['usernames']:
        print(f"⚠️ User '{username}' exists.")
        return

    hashed_pw = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

    config['credentials']['usernames'][username] = {
        "email": email,
        "name": name,
        "password": hashed_pw
    }
    
    if 'preauthorized' not in config or config['preauthorized'] is None:
         config['preauthorized'] = {'emails': []}
         
    if email not in config['preauthorized']['emails']:
        config['preauthorized']['emails'].append(email)

    save_config(config)
    print(f"👤 User '{username}' added.")

def delete_user(username):
    config = load_config()
    if not config: return
    if username not in config['credentials']['usernames']:
        print(f"⚠️ User not found.")
        return
    del config['credentials']['usernames'][username]
    save_config(config)
    print(f"🗑️ User deleted.")

def list_users():
    config = load_config()
    if not config: return
    print("\n📋 Admins:")
    for user, data in config['credentials']['usernames'].items():
        print(f" - {user} ({data['name']})")
    print("")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 admin_manager.py [add|del|list]")
        exit()

    action = sys.argv[1]
    if action == "add" and len(sys.argv) == 6:
        add_user(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    elif action == "del" and len(sys.argv) == 3:
        delete_user(sys.argv[2])
    elif action == "list":
        list_users()
    else:
        print("❌ Invalid args")
