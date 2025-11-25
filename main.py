import streamlit as st
import requests
import pandas as pd
import time
import json
import os
import yaml
import jdatetime
import re
import urllib3
from urllib.parse import quote
from datetime import datetime
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from streamlit_option_menu import option_menu 
from utils import load_servers, save_server, delete_server

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Page Config ---
st.set_page_config(page_title="X-UI Monitor", layout="wide", page_icon="🛡️")

# --- 1. INJECT VAZIRMATN FONT & CUSTOM CSS ---
st.markdown("""
    <style>
        @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
        
        html, body, [class*="css"] {
            font-family: 'Vazirmatn', sans-serif !important;
        }
        
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 3rem !important;
        }
        
        p {
            margin-bottom: 0px !important;
            line-height: 1.4 !important;
        }
        
        .user-card {
            background-color: #262730;
            border-radius: 8px;
            padding: 10px 14px;
            margin-bottom: 6px;
            border-left: 5px solid #555;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .user-info {
            flex-grow: 1;
        }
        
        .user-name {
            font-weight: bold;
            font-size: 1.15em;
            color: #fff;
        }
        
        .server-name {
            font-size: 0.85em;
            color: #aaa;
            margin-right: 5px;
        }
        
        .status-text {
            font-size: 0.95em;
            font-weight: bold;
        }
        
        .tech-details {
            font-size: 0.9em;
            color: #ccc;
            margin-top: 4px;
            display: block;
        }

        .action-btn-container {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .action-btn-container a {
            text-decoration: none !important;
            border: none !important;
        }
        
        .icon-btn {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            transition: all 0.2s ease-in-out;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        
        .icon-btn svg {
            width: 22px;
            height: 22px;
            fill: white;
        }
        
        .sms-btn {
            background-color: #444;
            border: 1px solid #666;
        }
        
        .wa-btn {
            background-color: #25D366;
            border: 1px solid #128c7e;
        }

        hr {
            margin: 0.5rem 0 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- Constants ---
GB = 1024 * 1024 * 1024
MB = 1024 * 1024
DAY_SECONDS = 24 * 60 * 60
SETTINGS_FILE = "settings.json"

# --- SVG ICONS ---
SVG_WA = """<svg viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>"""
SVG_SMS = """<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>"""

# --- Helper Functions ---
def get_default_settings():
    return {
        "filters": {"days": 3, "gb": 2.0, "hide": 7, "debug": False},
        "templates": {
            "ended": "مشترک گرامی {user}، حجم سرویس شما به پایان رسیده است.\nلطفا جهت تمدید اقدام فرمایید.",
            "expired": "مشترک گرامی {user}، زمان سرویس شما به پایان رسیده است.\nلطفا جهت تمدید اقدام فرمایید.",
            "low": "مشترک گرامی {user}، تنها {rem} از حجم سرویس شما باقی مانده است.\nتمدید میفرمایید؟",
            "soon": "مشترک گرامی {user}، تنها {time} از زمان سرویس شما باقی مانده است.\nتمدید میفرمایید؟"
        }
    }

def load_settings():
    defaults = get_default_settings()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if "filters" not in saved: saved["filters"] = defaults["filters"]
                if "templates" not in saved: saved["templates"] = defaults["templates"]
                return saved
        except:
            return defaults
    return defaults

def save_all_settings(settings_dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings_dict, f, ensure_ascii=False, indent=4)

def to_jalali(timestamp_ms):
    try:
        if timestamp_ms <= 0: return "-"
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        jalali_date = jdatetime.date.fromgregorian(date=dt.date())
        return jalali_date.strftime("%Y/%m/%d")
    except:
        return "-"

def format_time_remaining(days_decimal):
    if days_decimal == '∞' or not isinstance(days_decimal, (int, float)): 
        return '∞'
    if days_decimal < 0:
        return f"Expired ({int(abs(days_decimal))}d)"
    total_seconds = int(days_decimal * DAY_SECONDS)
    days = total_seconds // DAY_SECONDS
    hours = (total_seconds % DAY_SECONDS) // 3600
    if days > 0: return f"{days}d {hours}h"
    return f"{hours}h"

def extract_core_phone(username):
    digits_only = re.sub(r'\D', '', username)
    match_98 = re.search(r'98(9\d{9})', digits_only)
    if match_98: return match_98.group(1)
    match_09 = re.search(r'0(9\d{9})', digits_only)
    if match_09: return match_09.group(1)
    return None

def get_sms_link(core_number, text):
    if not core_number: return "#"
    phone = "+98" + core_number
    return f"sms:{phone}?body={quote(text)}"

def get_wa_link(core_number, text):
    if not core_number: return "#"
    phone = "98" + core_number
    return f"whatsapp://send?phone={phone}&text={quote(text)}"

# --- Authentication ---
with open('auth_config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

authenticator.login()

if st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
elif st.session_state["authentication_status"]:
    
    if 'app_settings' not in st.session_state:
        st.session_state['app_settings'] = load_settings()
    settings = st.session_state['app_settings']

    # ---------------- HEADER ----------------
    c_title, c_user = st.columns([3, 1])
    with c_title:
        st.title("🛡️ X-UI Monitor")
    with c_user:
        st.write(f"👤 **{st.session_state['name']}**")
        authenticator.logout("Log out", "main")

    # ---------------- S I D E B A R ----------------
    with st.sidebar:
        st.header("⚙️ Settings")
        
        val_days = settings['filters'].get('days', 3)
        val_gb = settings['filters'].get('gb', 2.0)
        val_hide = settings['filters'].get('hide', 7)
        val_debug = settings['filters'].get('debug', False)

        warning_days = st.number_input("Warning Days (<)", value=val_days, min_value=1)
        warning_gb = st.number_input("Warning GB (<)", value=val_gb, min_value=0.5, step=0.5)
        hide_days = st.number_input("Hide Expired (> Days)", value=val_hide, min_value=1)
        debug_mode = st.checkbox("🐞 Debug Mode", value=val_debug)
        
        st.divider()
        with st.expander("💬 Message Templates", expanded=True):
            st.caption("Vars: `{user}`, `{rem}`, `{time}`, `{date}`")
            current_tpl = settings['templates']
            new_ended = st.text_area("⛔ Ended:", value=current_tpl["ended"], height=70)
            new_expired = st.text_area("☠️ Expired:", value=current_tpl["expired"], height=70)
            new_low = st.text_area("🪫 Low Data:", value=current_tpl["low"], height=70)
            new_soon = st.text_area("⏱️ Expiring Soon:", value=current_tpl["soon"], height=70)
        
        st.write("")
        if st.button("💾 Save All Settings", type="primary", use_container_width=True):
            settings['filters']['days'] = warning_days
            settings['filters']['gb'] = warning_gb
            settings['filters']['hide'] = hide_days
            settings['filters']['debug'] = debug_mode
            settings['templates']['ended'] = new_ended
            settings['templates']['expired'] = new_expired
            settings['templates']['low'] = new_low
            settings['templates']['soon'] = new_soon
            save_all_settings(settings)
            st.success("Saved!")
            time.sleep(0.5)
            st.rerun()

    # ---------------- T O P   M E N U ----------------
    selected = option_menu(
        menu_title=None,  
        options=["Monitor", "Servers"], 
        icons=["activity", "hdd-network"], 
        menu_icon="cast", 
        default_index=0, 
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#262730"},
            "icon": {"color": "orange", "font-size": "18px"}, 
            "nav-link": {"font-size": "16px", "text-align": "center", "margin":"0px", "--hover-color": "#333"},
            "nav-link-selected": {"background-color": "#ff4b4b"},
        }
    )

    # =======================================================
    # PAGE 1: MONITOR
    # =======================================================
    if selected == "Monitor":
        
        def login_and_get_stats(server):
            session = requests.Session()
            base_url = server['url'].rstrip('/')
            login_url = f"{base_url}/login"
            payload = {"username": server['username'], "password": server['password']}
            
            try:
                session.post(login_url, data=payload, timeout=8, verify=False)
            except: return None

            api_endpoints = [
                f"{base_url}/panel/api/inbounds/list",  # Sanaei / 3x-ui
                f"{base_url}/xui/API/inbounds/",        # Alireza
                f"{base_url}/xui/API/inbounds",         
                f"{base_url}/xui/API/inbounds/list",    
                f"{base_url}/api/inbounds/list"         
            ]
            
            for url in api_endpoints:
                try:
                    res = session.get(url, timeout=8, verify=False)
                    if res.status_code == 200:
                        try:
                            data = res.json()
                            if data.get('success'): return data.get('obj')
                        except: pass
                except: pass
            return None

        def process_clients(server_name, inbounds, debug=False):
            alerts = []
            current_time = int(time.time() * 1000) 
            for inbound in inbounds:
                stats_map = {}
                if 'clientStats' in inbound:
                    for stat in inbound['clientStats']:
                        stats_map[stat['email']] = {'up': stat.get('up',0), 'down': stat.get('down',0)}
                try:
                    settings = inbound['settings']
                    if isinstance(settings, str): settings = json.loads(settings)
                    clients = settings.get('clients', [])
                except: clients = []
                
                for client in clients:
                    email = client.get('email', 'Unknown')
                    enable = client.get('enable', True)
                    is_enabled = True
                    if enable is False or str(enable).lower() == "false" or enable == 0: is_enabled = False
                    
                    if not is_enabled and not debug: continue
                    
                    real_stats = stats_map.get(email)
                    if real_stats:
                        up, down = real_stats['up'], real_stats['down']
                    else:
                        up, down = client.get('up', 0), client.get('down', 0)
                    
                    total_allowed = client.get('totalGB', 0)
                    expiry_time = client.get('expiryTime', 0)
                    formatted_rem, days_left_formatted = "∞", "∞"
                    status, jalali_expiry = "OK", "-"
                    total_usage = up + down
                    
                    if total_allowed > 0:
                        remaining = total_allowed - total_usage
                        remaining_gb_val = remaining / GB
                        if remaining <= 0: status = "⛔ ENDED"
                        elif remaining_gb_val < warning_gb:
                            if total_usage > 0: status = f"🪫 LOW DATA"
                        if remaining_gb_val < 1: formatted_rem = f"{int(remaining/MB)}MB"
                        else: formatted_rem = f"{remaining_gb_val:.1f}GB"
                    
                    is_zombie = False
                    if expiry_time > 0:
                        jalali_expiry = to_jalali(expiry_time)
                        diff_ms = expiry_time - current_time
                        days_decimal = diff_ms / (1000 * DAY_SECONDS)
                        days_left_formatted = format_time_remaining(days_decimal)
                        if diff_ms <= 0:
                            if (abs(diff_ms)/(1000*DAY_SECONDS)) > hide_days: is_zombie = True
                            if "ENDED" not in status: status = "☠️ EXPIRED" 
                        elif diff_ms < (warning_days * DAY_SECONDS * 1000):
                            if "ENDED" not in status: status = f"⏱️ SOON"

                    show_row = False
                    if debug: show_row = True
                    else:
                        if is_zombie: show_row = False
                        elif "⛔" in status or "☠️" in status or "🪫" in status or "⏱️" in status: show_row = True
                    
                    if show_row:
                        alerts.append({
                            "Server": server_name, "User": email, "Status": status,
                            "Rem": formatted_rem, "Time": days_left_formatted,
                            "ExpDate": jalali_expiry
                        })
            return alerts

        if st.button("🔄 Check Servers Now", type="primary", use_container_width=True):
            st.session_state['checking'] = True
            if 'scan_results' in st.session_state: del st.session_state['scan_results']

        if st.session_state.get('checking', False):
            servers = load_servers()
            if not servers:
                st.warning("No servers added yet.")
                st.session_state['checking'] = False
            else:
                all_data = []
                progress_bar = st.progress(0, text="Scanning...")
                total = len(servers)
                for i, s in enumerate(servers):
                    progress_bar.progress((i + 1) / total, text=f"Scanning {s['name']}...")
                    inbounds = login_and_get_stats(s)
                    if inbounds:
                        alerts = process_clients(s['name'], inbounds, debug=debug_mode)
                        all_data.extend(alerts)
                    else:
                        all_data.append({"Server": s['name'], "User": "-", "Status": "❌ Failed", "Rem": "-", "Time": "-", "ExpDate": "-"})
                progress_bar.empty()
                st.session_state['scan_results'] = all_data
                st.session_state['checking'] = False
                st.rerun()

        if 'scan_results' in st.session_state:
            results = st.session_state['scan_results']
            if results:
                df = pd.DataFrame(results)
                
                avail = df['Server'].unique().tolist()
                sel = st.multiselect("Filter:", options=avail, default=avail, label_visibility="collapsed")
                
                if sel:
                    df_filtered = df[df['Server'].isin(sel)].copy()
                    st.caption(f"Found {len(df_filtered)} issues.")
                    
                    tpl = settings['templates']

                    for index, row in df_filtered.iterrows():
                        color = "#777"
                        msg_template = ""
                        
                        if "⛔" in row['Status']: 
                            color = "#ff4b4b"
                            msg_template = tpl["ended"]
                        elif "☠️" in row['Status']:
                            color = "#a020f0"
                            msg_template = tpl["expired"]
                        elif "🪫" in row['Status']:
                            color = "#ffa500"
                            msg_template = tpl["low"]
                        elif "⏱️" in row['Status']:
                            color = "#ffff00"
                            msg_template = tpl["soon"]

                        core_number = extract_core_phone(row['User'])
                        btns_html = ""
                        
                        if core_number:
                            final_msg = msg_template.replace("{user}", row['User']) \
                                                    .replace("{rem}", str(row['Rem'])) \
                                                    .replace("{time}", str(row['Time'])) \
                                                    .replace("{date}", str(row['ExpDate']))
                            
                            sms_link = get_sms_link(core_number, final_msg)
                            wa_link = get_wa_link(core_number, final_msg)
                            
                            btns_html = f'<div class="action-btn-container"><a href="{sms_link}" target="_blank" title="SMS"><span class="icon-btn sms-btn">{SVG_SMS}</span></a><a href="{wa_link}" target="_blank" title="WhatsApp"><span class="icon-btn wa-btn">{SVG_WA}</span></a></div>'
                        else:
                            btns_html = "<span style='opacity:0.3'>🚫</span>"

                        st.markdown(f"""
                        <div class="user-card" style="border-left-color: {color};">
                            <div class="user-info">
                                <div>
                                    <span class="user-name">{row['User']}</span>
                                    <span class="server-name">({row['Server']})</span>
                                </div>
                                <div style="margin-top:2px;">
                                    <span class="status-text" style="color: {color};">{row['Status']}</span>
                                    <span style="color:#666; margin: 0 5px;">|</span>
                                    <span class="tech-details">
                                        Data: <b>{row['Rem']}</b> • Time: <b>{row['Time']}</b> • Exp: {row['ExpDate']}
                                    </span>
                                </div>
                            </div>
                            {btns_html}
                        </div>
                        """, unsafe_allow_html=True)

                else: st.warning("Select a server.")
            else:
                st.balloons()
                st.success("✅ Clean!")

    # =======================================================
    # PAGE 2: SERVERS
    # =======================================================
    if selected == "Servers":
        st.title("⚙️ Servers")
        
        current_servers = load_servers()
        if current_servers:
            df_servers = pd.DataFrame(current_servers)
            st.dataframe(df_servers[['name', 'url', 'username']], width="stretch")
            
            st.divider()
            c1, c2 = st.columns([2, 1])
            with c1:
                server_to_delete = st.selectbox("Select Server", options=[s['name'] for s in current_servers])
            with c2:
                st.write("") 
                st.write("") 
                if st.button("🗑️ Delete", type="primary"):
                    delete_server(server_to_delete)
                    st.success("Removed!")
                    time.sleep(1)
                    st.rerun()
        else:
            st.info("No servers.")

        st.divider()
        st.subheader("Add Server")
        with st.form("add_server_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                new_name = st.text_input("Name")
                new_url = st.text_input("URL")
            with col_b:
                new_user = st.text_input("User", value="admin")
                new_pass = st.text_input("Pass", type="password")
            
            if st.form_submit_button("Save"):
                save_server(new_name, new_url, new_user, new_pass)
                st.success("Saved!")
                time.sleep(1)
                st.rerun()
