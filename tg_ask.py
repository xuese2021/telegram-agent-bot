import sys
import os
import time
import uuid
import requests
from dotenv import load_dotenv

def ask_permission(question):
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    allowed_users = os.getenv("ALLOWED_USER_IDS", "")
    
    if not token or not allowed_users:
        print("Error: Missing Telegram configuration in .env")
        sys.exit(1)
        
    main_user_id = allowed_users.split(",")[0].strip()
    req_id = str(uuid.uuid4())[:8]
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ 允许执行", "callback_data": f"approve_{req_id}"},
            {"text": "❌ 拒绝放行", "callback_data": f"reject_{req_id}"}
        ]]
    }
    
    payload = {
        "chat_id": main_user_id,
        "text": f"⚠️ **【请求权限】**\n\n{question}",
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }
    
    try:
        req = requests.post(url, json=payload)
        req.raise_for_status()
        print(f"[{req_id}] 权限请求已发送给管理员，等待回复中...")
    except Exception as e:
        print(f"发送请求失败: {e}")
        sys.exit(1)
        
    signal_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), f".tg_response_{req_id}.txt")
    
    # 阻塞轮询等待文件出现
    while True:
        if os.path.exists(signal_file):
            with open(signal_file, "r", encoding="utf-8") as f:
                verdict = f.read().strip()
            
            # 清理临时文件
            try:
                os.remove(signal_file)
            except:
                pass
                
            if verdict == "APPROVED":
                print("\n[SUCCESS] 用户已批准操作。继续执行。")
                sys.exit(0)
            else:
                print("\n[REJECTED] 用户拒绝了操作。安全回退。")
                sys.exit(1)
                
        time.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tg_ask.py '<question>'")
        sys.exit(1)
        
    question = sys.argv[1]
    ask_permission(question)
