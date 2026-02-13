import requests
import os
import hashlib
import sys

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
URL = "https://kassilviailvesonhetkelvallaline.ee/"
STATE_FILE = "last_state.txt"
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")

def get_website_content():
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching website: {e}")
        return None

def extract_status(html):
    return hashlib.md5(html.encode('utf-8')).hexdigest()

def send_email_notification(subject, body):
    if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECEIVER:
        print("Email configuration missing. Skipping notification.")
        return

    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to Gmail SMTP server using SSL
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

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
        status_text = "Muutus tuvastatud!"
        if "ei" in current_content.lower() and "jah" not in current_content.lower():
             status_text = "Silvia on tõenäoliselt endiselt hõivatud (Leidsin sõna 'Ei')."
        elif "jah" in current_content.lower():
             status_text = "TÄHELEPANU! Silvia võib olla vallaline! (Leidsin sõna 'Jah')."
        
        subject = "Silvia Ilvese staatus muutus!"
        body = f"{status_text}\n\nVaata lähemalt: {URL}"
        
        send_email_notification(subject, body)
        
        # Update state file
        with open(STATE_FILE, "w") as f:
            f.write(current_hash)
    else:
        print("No change detected.")

if __name__ == "__main__":
    main()
