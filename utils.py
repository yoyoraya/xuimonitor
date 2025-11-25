import json
import os
from cryptography.fernet import Fernet

CONFIG_FILE = "servers.enc"
KEY_FILE = "secret.key"

def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
    else:
        with open(KEY_FILE, "rb") as key_file:
            key = key_file.read()
    return key

def load_servers():
    key = load_key()
    cipher_suite = Fernet(key)
    if not os.path.exists(CONFIG_FILE):
        return []
    
    with open(CONFIG_FILE, "rb") as f:
        encrypted_data = f.read()
    
    try:
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())
    except:
        return []

def save_server(name, url, username, password):
    servers = load_servers()
    # Update if exists, else append
    servers = [s for s in servers if s['name'] != name]
    servers.append({
        "name": name,
        "url": url.rstrip('/'),
        "username": username,
        "password": password
    })
    
    key = load_key()
    cipher_suite = Fernet(key)
    encrypted_data = cipher_suite.encrypt(json.dumps(servers).encode())
    
    with open(CONFIG_FILE, "wb") as f:
        f.write(encrypted_data)

def delete_server(name):
    servers = load_servers()
    new_servers = [s for s in servers if s['name'] != name]
    
    key = load_key()
    cipher_suite = Fernet(key)
    encrypted_data = cipher_suite.encrypt(json.dumps(new_servers).encode())
    
    with open(CONFIG_FILE, "wb") as f:
        f.write(encrypted_data)
