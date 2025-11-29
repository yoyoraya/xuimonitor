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
        try:
            config = yaml.load(file, Loader=SafeLoader)
            # اگر فایل کلا خالی بود یا مشکل داشت، ساختار اولیه را بساز
            if config is None:
                config = {}
            if 'credentials' not in config or config['credentials'] is None:
                config['credentials'] = {}
            if 'usernames' not in config['credentials'] or config['credentials']['usernames'] is None:
                config['credentials']['usernames'] = {}
            return config
        except Exception as e:
            print(f"Error loading yaml: {e}")
            return {'credentials': {'usernames': {}}}

def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)
    print("✅ Configuration updated successfully!")

def add_user(username, email, name, raw_password):
    config = load_config()
    if not config: return

    # اینجا دیگه ارور نمیده چون بالا مطمئن شدیم دیکشنری هست
    if username in config['credentials']['usernames']:
        print(f"⚠️ User '{username}' already exists.")
        return

    hashed_pw = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

    config['credentials']['usernames'][username] = {
        "email": email,
        "name": name,
        "password": hashed_pw
    }
    
    # اطمینان از وجود بخش preauthorized
    if 'preauthorized' not in config or config['preauthorized'] is None:
         config['preauthorized'] = {'emails': []}
    
    if 'emails' not in config['preauthorized'] or config['preauthorized']['emails'] is None:
        config['preauthorized']['emails'] = []

    if email not in config['preauthorized']['emails']:
        config['preauthorized']['emails'].append(email)

    save_config(config)
    print(f"👤 User '{username}' added successfully.")

def delete_user(username):
    config = load_config()
    if not config: return

    if username not in config['credentials']['usernames']:
        print(f"⚠️ User '{username}' not found.")
        return

    del config['credentials']['usernames'][username]
    save_config(config)
    print(f"🗑️ User '{username}' deleted.")

def list_users():
    config = load_config()
    if not config: return
    
    usernames = config.get('credentials', {}).get('usernames', {})
    
    if not usernames:
        print("No users found.")
        return

    print("\n📋 Registered Admins:")
    for user, data in usernames.items():
        print(f" - {user} ({data.get('name', 'No Name')})")
    print("")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 admin_manager.py add <username> <email> <name> <password>")
        print("  python3 admin_manager.py del <username>")
        print("  python3 admin_manager.py list")
        exit()

    action = sys.argv[1]

    if action == "add" and len(sys.argv) == 6:
        add_user(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    elif action == "del" and len(sys.argv) == 3:
        delete_user(sys.argv[2])
    elif action == "list":
        list_users()
    else:
        print("❌ Invalid arguments.")
