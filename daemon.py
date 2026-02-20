"""
daemon.py - 四步循环，统一覆盖三种情景

每 10 秒：
  1. 有新任务吗？  → 没有 → sleep 继续
  2. Agent 在忙吗？ → 在忙 → 任务排队，继续
  3. 唤起 Agent     → 开新会话，喂任务
  4. 标记 Agent 忙
"""
import os
import sys
import glob
import time
import subprocess
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASK_PREFIX = ".tg_task_"
CURRENT_TASK = os.path.join(BASE_DIR, "current_task.md")
DAEMON_WAITING = os.path.join(BASE_DIR, ".daemon_waiting")
DAEMON_DONE = os.path.join(BASE_DIR, ".daemon_task_done")
AGENT_BUSY = os.path.join(BASE_DIR, ".agent_busy")
POLL_INTERVAL = int(os.getenv("DAEMON_POLL_INTERVAL", "10"))
TASK_TIMEOUT = 1800
CURSOR_EXE = os.getenv("CURSOR_EXE") or os.path.expandvars(r"%LOCALAPPDATA%\Programs\cursor\Cursor.exe")


def _trigger_msg():
    return f"请读取 {CURRENT_TASK} 并执行任务，完成后调用 report_done"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def _has_task() -> bool:
    """有新任务吗？（不消费）"""
    return bool(glob.glob(os.path.join(BASE_DIR, f"{TASK_PREFIX}*.txt")))


def _agent_busy() -> bool:
    """Agent 在忙吗？"""
    return os.path.exists(AGENT_BUSY)


def _get_next_task() -> tuple[str, str] | None:
    """消费一个任务，返回 (task_id, content) 或 None"""
    files = sorted(glob.glob(os.path.join(BASE_DIR, f"{TASK_PREFIX}*.txt")))
    if not files:
        return None
    path = files[0]
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        task_id = os.path.basename(path).replace(TASK_PREFIX, "").replace(".txt", "")
        os.remove(path)
        return task_id, content
    except Exception as e:
        logger.warning(f"读取任务失败: {e}")
        return None


def _ensure_cursor() -> bool:
    """Cursor 没开则启动"""
    try:
        import pygetwindow as gw
        for w in gw.getAllWindows():
            if "Cursor" in (w.title or ""):
                return True
    except Exception:
        pass
    if os.path.exists(CURSOR_EXE):
        try:
            subprocess.Popen([CURSOR_EXE], cwd=os.path.expanduser("~"))
            time.sleep(15)
            return True
        except Exception as e:
            logger.warning(f"启动 Cursor 失败: {e}")
    return False


def _trigger_cursor() -> bool:
    """模拟 Ctrl+I 唤起 Agent"""
    try:
        import pyautogui
        import pyperclip
    except ImportError:
        logger.error("请安装: pip install pyautogui pyperclip")
        return False
    try:
        import pygetwindow as gw
        for w in gw.getAllWindows():
            if "Cursor" in (w.title or ""):
                w.activate()
                time.sleep(0.5)
                break
    except Exception:
        pass
    pyautogui.hotkey("ctrl", "i")
    time.sleep(0.8)
    pyperclip.copy(_trigger_msg())
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.2)
    pyautogui.press("enter")
    return True


def _wait_for_done() -> bool:
    deadline = time.time() + TASK_TIMEOUT
    while time.time() < deadline:
        if os.path.exists(DAEMON_DONE):
            try:
                os.remove(DAEMON_DONE)
                return True
            except Exception:
                pass
        time.sleep(2)
    return False


def main():
    os.chdir(BASE_DIR)
    logger.info("daemon 已启动，每 %d 秒循环", POLL_INTERVAL)

    while True:
        # 1. 有新任务吗？
        if not _has_task():
            time.sleep(POLL_INTERVAL)
            continue

        # 2. Agent 在忙吗？→ 任务排队，继续
        if _agent_busy():
            time.sleep(POLL_INTERVAL)
            continue

        # 3. 唤起 Agent
        task = _get_next_task()
        if not task:
            time.sleep(POLL_INTERVAL)
            continue

        task_id, content = task
        logger.info("唤起 Agent，任务 %s", task_id[:8])

        if not _ensure_cursor():
            from middleware import write_task
            write_task(content)
            logger.warning("Cursor 未就绪，任务已回队列")
            time.sleep(POLL_INTERVAL)
            continue

        with open(CURRENT_TASK, "w", encoding="utf-8") as f:
            f.write(content)
        with open(DAEMON_WAITING, "w") as f:
            f.write(task_id)
        # 4. 标记 Agent 忙
        with open(AGENT_BUSY, "w") as f:
            f.write(task_id)

        if not _trigger_cursor():
            from middleware import write_task
            write_task(content)
            for p in (AGENT_BUSY, DAEMON_WAITING, CURRENT_TASK):
                try:
                    os.remove(p)
                except Exception:
                    pass
            time.sleep(POLL_INTERVAL)
            continue

        _wait_for_done()

        for p in (DAEMON_WAITING, CURRENT_TASK):
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
        # .agent_busy 由 report_done 移除
        try:
            if os.path.exists(AGENT_BUSY):
                os.remove(AGENT_BUSY)
        except Exception:
            pass
        logger.info("任务 %s 完成，继续轮询", task_id[:8])


if __name__ == "__main__":
    sys.path.insert(0, BASE_DIR)
    main()
