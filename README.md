# 🛡️ X-UI Monitor Dashboard

A comprehensive, mobile-friendly monitoring dashboard for managing multiple X-UI panels (Sanaei, Alireza, etc.) in one place.

## ✨ Features
- **Multi-Server Monitoring:** View all your servers and users in a unified dashboard.
- **Smart Alerts:** Automatically detects users with:
  - ⛔ Ended Traffic
  - ☠️ Expired Time
  - 🪫 Low Data
  - ⏱️ Expiring Soon
- **Mobile First Design:** Optimized UI for mobile devices with compact cards.
- **Quick Actions:** Send renewal notifications via **SMS** or **WhatsApp** with one click.
- **Auto-Discovery:** Smartly detects phone numbers from usernames.
- **Secure:** Passwords are hashed (Bcrypt) and server details are encrypted (Fernet).

## 🚀 Installation (One-Command)

Run the following command on your Ubuntu/Debian server:

```bash
apt update && apt install -y git && git clone https://github.com/yoyoraya/xuimonitor.git /root/xui_monitor && cd /root/xui_monitor && chmod +x setup.sh && ./setup.sh
```
## ⚙️ Usage
After installation, the panel will be available at: **http://YOUR_SERVER_IP:8501**

Login with the admin credentials you created during setup.

Go to the Servers tab to add your X-UI panels.

## 🛠️ Management
To update, uninstall, or manage the panel, simply run the setup script again:

```./setup.sh
```
##🔒 Security Note
This project does not store your server credentials in plain text. All sensitive data is encrypted locally on your server.

##Developed with 🤖 & ❤️
> **Note:** This is a **Personal Project**. All code was generated with the assistance of **Google Gemini 3** AI.
