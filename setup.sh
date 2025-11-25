#!/bin/bash
# X-UI Monitor Installer

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit
fi

echo "Installing X-UI Monitor..."

# 1. System
apt update -q
apt install -y python3-pip python3-venv git -q

# 2. Venv
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 3. Deps
source venv/bin/activate
pip install -r requirements.txt

# 4. Configs
if [ ! -f "auth_config.yaml" ] && [ -f "auth_config.example.yaml" ]; then
    cp auth_config.example.yaml auth_config.yaml
fi

if [ ! -f "secret.key" ]; then
    python3 -c "from cryptography.fernet import Fernet; open('secret.key', 'wb').write(Fernet.generate_key())"
fi

# 5. Service
SERVICE_FILE="/etc/systemd/system/xui-monitor.service"
cat <<EOF > $SERVICE_FILE
[Unit]
Description=X-UI Monitor
After=network.target

[Service]
User=root
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/streamlit run main.py --server.port 8501 --server.address 0.0.0.0 --theme.base "dark"
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable xui-monitor
systemctl restart xui-monitor

echo "✅ Done! Panel: http://$(curl -s ifconfig.me):8501"

# Admin Creation
if grep -q "usernames:" auth_config.yaml && ! grep -q "email:" auth_config.yaml; then
    echo "Creating Admin..."
    read -p "User: " u
    read -p "Pass: " p
    read -p "Email: " e
    python3 admin_manager.py add "$u" "$e" "Admin" "$p"
    systemctl restart xui-monitor
fi
