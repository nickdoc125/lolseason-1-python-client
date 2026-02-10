# history_manager.py
import json
import os
from paths_config import paths_config

# ===================== HISTORY MANAGEMENT =====================
def load_history():
    """Φόρτωση του history από το αρχείο"""
    default_history = {
        "usernames": [],
        "ips": []
    }
    
    try:
        if os.path.exists(paths_config.HISTORY_JSON):
            with open(paths_config.HISTORY_JSON, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading history: {e}")
    
    return default_history

def save_history(history_data):
    """Αποθήκευση του history στο αρχείο"""
    try:
        with open(paths_config.HISTORY_JSON, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving history: {e}")
        return False

def add_username_to_history(username):
    """Προσθήκη username στο history"""
    if not username:
        return
    
    history = load_history()
    username = username.strip()
    
    # Αφαίρεση αν υπάρχει ήδη και προσθήκη στην αρχή
    if username in history["usernames"]:
        history["usernames"].remove(username)
    history["usernames"].insert(0, username)
    
    # Διατήρηση μόνο των 10 πιο πρόσφατων
    history["usernames"] = history["usernames"][:10]
    
    save_history(history)

def add_ip_to_history(ip):
    """Προσθήκη IP στο history"""
    if not ip:
        return
    
    history = load_history()
    ip = ip.strip()
    
    # Αφαίρεση αν υπάρχει ήδη και προσθήκη στην αρχή
    if ip in history["ips"]:
        history["ips"].remove(ip)
    history["ips"].insert(0, ip)
    
    # Διατήρηση μόνο των 10 πιο πρόσφατων
    history["ips"] = history["ips"][:10]
    
    save_history(history)