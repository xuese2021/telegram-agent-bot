"""
中间层：跟进 AI 工作、汇报进度、远程放权

流程：
  AI/脚本 工作 → 汇报给中间层 → 中间层推送到 Telegram
  AI 需要放权 → 中间层发「允许/拒绝」按钮 → 你远程点击 → 中间层通知 AI 继续/停止
"""
import os
import time
import uuid
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_IDS = [x.strip() for x in os.getenv("ALLOWED_USER_IDS", "").split(",") if x.strip()]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _send(text: str, parse_mode: str = "Markdown") -> bool:
    """发送消息到 Telegram"""
    if not TOKEN or not ALLOWED_IDS:
        logger.warning("未配置 TELEGRAM_BOT_TOKEN 或 ALLOWED_USER_IDS")
        return False
    try:
        import requests
        for chat_id in ALLOWED_IDS:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": text[:4000], "parse_mode": parse_mode},
                timeout=10,
            )
        return True
    except Exception as e:
        logger.error(f"发送失败: {e}")
        return False


TASK_DIR = BASE_DIR
TASK_PREFIX = ".tg_task_"


def wait_for_task(poll_interval_sec: float = 5, timeout_sec: int = 0) -> str:
    """
    阻塞等待新任务。Bot 收到用户消息时会写入 .tg_task_xxx.txt
    timeout_sec=0 表示无限等待
    返回任务内容，无任务时返回空字符串（仅在超时情况下）
    """
    import glob
    deadline = (time.time() + timeout_sec) if timeout_sec > 0 else None
    pattern = os.path.join(TASK_DIR, f"{TASK_PREFIX}*.txt")
    while True:
        files = sorted(glob.glob(pattern))
        if files:
            try:
                with open(files[0], "r", encoding="utf-8") as f:
                    content = f.read()
                os.remove(files[0])
                return content.strip()
            except Exception as e:
                logger.warning(f"读取任务文件失败: {e}")
        if deadline and time.time() >= deadline:
            return ""
        time.sleep(poll_interval_sec)


def report_done(message: str, task_id: str = "") -> bool:
    """任务完成，推送到用户手机"""
    prefix = "✅ **【任务完成】**" + (f" `{task_id}`" if task_id else "")
    text = f"{prefix}\n\n{message}"
    ok = _send(text)
    # 守护脚本模式：写入完成信号，移除 Agent 忙标记
    waiting = os.path.join(BASE_DIR, ".daemon_waiting")
    done = os.path.join(BASE_DIR, ".daemon_task_done")
    busy = os.path.join(BASE_DIR, ".agent_busy")
    if os.path.exists(waiting):
        try:
            with open(done, "w") as f:
                f.write("")
        except Exception:
            pass
    try:
        if os.path.exists(busy):
            os.remove(busy)
    except Exception:
        pass
    return ok


def report(step: str, message: str, task_id: str = "") -> bool:
    """
    汇报进度给远程用户
    step: 步骤标识，如 "1/5"、"分析完成"
    message: 详细内容
    """
    prefix = f"📋 **【进度汇报】**" + (f" `{task_id}`" if task_id else "")
    text = f"{prefix}\n\n**{step}**\n\n{message}"
    return _send(text)


def request_approval(question: str, task_id: str = "", timeout_sec: int = 3600) -> bool:
    """
    请求远程放权，阻塞直到用户点击或超时
    返回 True=允许执行下一步，False=拒绝或超时
    """
    if not TOKEN or not ALLOWED_IDS:
        logger.warning("未配置 Telegram")
        return False

    import requests
    req_id = str(uuid.uuid4())[:8]
    signal_file = os.path.join(BASE_DIR, f".tg_response_{req_id}.txt")

    prefix = "⚠️ **【请求放权】**" + (f" `{task_id}`" if task_id else "")
    text = f"{prefix}\n\n{question}"
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ 允许执行下一步", "callback_data": f"approve_{req_id}"},
            {"text": "❌ 拒绝", "callback_data": f"reject_{req_id}"},
        ]]
    }
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": ALLOWED_IDS[0], "text": text, "parse_mode": "Markdown", "reply_markup": keyboard},
            timeout=10,
        )
        r.raise_for_status()
    except Exception as e:
        logger.error(f"发送放权请求失败: {e}")
        return False

    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if os.path.exists(signal_file):
            try:
                with open(signal_file, "r", encoding="utf-8") as f:
                    verdict = f.read().strip()
                os.remove(signal_file)
                return verdict == "APPROVED"
            except Exception:
                pass
        time.sleep(1)
    logger.warning("放权请求超时")
    return False


def write_task(content: str) -> str:
    """写入新任务文件，供 wait_for_task 读取。返回 task_id"""
    task_id = str(uuid.uuid4())[:8]
    path = os.path.join(TASK_DIR, f"{TASK_PREFIX}{task_id}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return task_id