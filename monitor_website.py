import requests
import os
import hashlib
import sys

# Configuration
URL = "https://kassilviailvesonhetkelvallaline.ee/"
STATE_FILE = "last_state.txt"
PHONE_NUMBER = os.environ.get("CALLMEBOT_PHONE")
API_KEY = os.environ.get("CALLMEBOT_API_KEY")

def get_website_content():
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching website: {e}")
        return None

def extract_status(html):
    # Simple extraction: look for "Ei" or "Jah" in the content
    # or just hash the whole content if we want to detect ANY change
    # For this specific site, let's normalize the content a bit to avoid false positives on dynamic tokens if any
    return hashlib.md5(html.encode('utf-8')).hexdigest()

def send_whatsapp_notification(message):
    if not PHONE_NUMBER or not API_KEY:
        print("WhatsApp configuration missing. Skipping notification.")
        return

    # CallMeBot API URL
    url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE_NUMBER}&text={requests.utils.quote(message)}&apikey={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("Notification sent successfully!")
        else:
            print(f"Failed to send notification: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"Error sending notification: {e}")

def main():
    print(f"Checking {URL}...")
    current_content = get_website_content()
    
    if not current_content:
        sys.exit(1)

    current_hash = extract_status(current_content)
    
    # Read last state
    last_hash = ""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            last_hash = f.read().strip()

    print(f"Current Hash: {current_hash}")
    print(f"Last Hash:    {last_hash}")

    if current_hash != last_hash:
        print("Change detected!")
        count_ei = current_content.lower().count("ei")
        count_jah = current_content.lower().count("jah")
        
        status_text = "Muutus tuvastatud!"
        if "ei" in current_content.lower() and "jah" not in current_content.lower():
             status_text = "Silvia on tõenäoliselt endiselt hõivatud (Leidsin sõna 'Ei')."
        elif "jah" in current_content.lower():
             status_text = "TÄHELEPANU! Silvia võib olla vallaline! (Leidsin sõna 'Jah')."
        
        msg = f"Silvia Ilvese staatus muutus!\n\n{status_text}\n\nVaata: {URL}"
        
        send_whatsapp_notification(msg)
        
        # Update state file
        with open(STATE_FILE, "w") as f:
            f.write(current_hash)
    else:
        print("No change detected.")

if __name__ == "__main__":
    main()
