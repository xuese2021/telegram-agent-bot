import sys
import os
import requests
from dotenv import load_dotenv

def send_message(message):
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    allowed_users = os.getenv("ALLOWED_USER_IDS", "")
    
    if not token or not allowed_users:
        print("Error: Missing Telegram configuration in .env")
        sys.exit(1)
        
    # Get the first allowed user as the primary admin
    main_user_id = allowed_users.split(",")[0].strip()
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": main_user_id,
        "text": f"🤖 **【Agent 汇报】**\n\n{message}",
        "parse_mode": "Markdown"
    }
    
    try:
        req = requests.post(url, json=payload)
        req.raise_for_status()
        print("Message sent successfully.")
    except Exception as e:
        print(f"Failed to send message: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tg_send.py '<message>'")
        sys.exit(1)
    
    msg = sys.argv[1]
    send_message(msg)
