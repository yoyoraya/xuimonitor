#!/bin/bash
# X-UI Monitor Installer

# Check Root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit
fi

echo "Installing X-UI Monitor..."

# 1. System Update & Install Dependencies
apt update -q
apt install -y python3-pip python3-venv git -q

# 2. Virtual Environment Setup
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 3. Install Python Libraries
source venv/bin/activate
pip install -r requirements.txt

# 4. Configuration Setup
# اگر فایل کانفیگ نیست، از نمونه کپی کن
if [ ! -f "auth_config.yaml" ]; then
    if [ -f "auth_config.example.yaml" ]; then
        cp auth_config.example.yaml auth_config.yaml
    else
        # ساخت فایل کانفیگ خام اگر نمونه هم نبود (برای جلوگیری از ارور)
        echo "credentials:" > auth_config.yaml
        echo "  usernames: {}" >> auth_config.yaml
        echo "cookie:" >> auth_config.yaml
        echo "  expiry_days: 30" >> auth_config.yaml
        echo "  key: 'random_key'" >> auth_config.yaml
        echo "  name: 'xui_cookie'" >> auth_config.yaml
        echo "preauthorized:" >> auth_config.yaml
        echo "  emails: []" >> auth_config.yaml
    fi
fi

# Generate Encryption Key
if [ ! -f "secret.key" ]; then
    python3 -c "from cryptography.fernet import Fernet; open('secret.key', 'wb').write(Fernet.generate_key())"
fi

# 5. Create Systemd Service
SERVICE_FILE="/etc/systemd/system/xui-monitor.service"
cat <<EOF > $SERVICE_FILE
[Unit]
Description=X-UI Monitor Dashboard
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

# Reload & Start Service
systemctl daemon-reload
systemctl enable xui-monitor
systemctl restart xui-monitor

# 6. Display Info (IPv4 FORCE)
# استفاده از فلگ -4 برای دریافت آی‌پی نسخه 4
IPV4=$(curl -4s ifconfig.me)
echo "✅ Done! Panel: http://$IPV4:8501"

# 7. Create Admin Interaction
# چک میکنیم اگر یوزرنیم خالیه، درخواست ساخت بده
if grep -q "usernames: {}" auth_config.yaml || ! grep -q "usernames:" auth_config.yaml; then
    echo "-----------------------------------"
    echo "⚠️ No admin found. Let's create one:"
    read -p "Username: " u
    read -p "Password: " p
    read -p "Email: " e
    
    # اجرا با پایتون برای ساخت یوزر
    python3 admin_manager.py add "$u" "$e" "Admin" "$p"
    
    # ریستارت سرویس برای اعمال تغییرات
    systemctl restart xui-monitor
fi
