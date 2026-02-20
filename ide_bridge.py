import time
import pyperclip
import pyautogui
import pygetwindow as gw
import logging

logger = logging.getLogger(__name__)

# 配置不同环境的热键映射
TARGET_CONFIGS = {
    "antigravity": {
        "window_titles": ["antigravity", "visual studio code", "vs code"], 
        "focus_hotkeys": ["ctrl", "l"],
        "description": "IDE 内置 AntiGravity AI"
    },
    "cursor": {
        "window_titles": ["cursor"],
        "focus_hotkeys": ["ctrl", "l"],
        "description": "Cursor AI 编辑器"
    },
    "vscode": {
        "window_titles": ["visual studio code", "vs code", "管理员"],
        "focus_hotkeys": ["ctrl", "`"],
        "description": "原版 VS Code 终端"
    }
}

def activate_window_and_send(target: str, message: str) -> bool:
    """
    尝试激活指定窗口，并模拟键入发送消息
    """
    if target not in TARGET_CONFIGS:
        logger.error(f"未知的目标环境: {target}")
        return False
        
    config = TARGET_CONFIGS[target]
    
    # 1. 查找目标窗口 (忽略大小写进行匹配)
    target_windows = []
    all_windows = gw.getAllWindows()
    
    for win in all_windows:
        if not win.title:
            continue
        title_lower = win.title.lower()
        for keyword in config["window_titles"]:
            if keyword in title_lower:
                # 只要优先匹配到了特有关键词，就认为是目标窗口
                target_windows.append(win)
                break
                
    if not target_windows:
        logger.error(f"找不到符合条件 {config['window_titles']} 的活动窗口。")
        return False
        
    # 取第一个匹配到的窗口
    win = target_windows[0]
    
    try:
        if not win.isActive:
            win.activate()
            time.sleep(1)
            
        if win.isMinimized:
            win.restore()
            time.sleep(1)
            
        logger.info(f"成功激活窗口: {win.title}")
        
        # 3. 发送对应软件的强制聚焦热键 (比如 Ctrl+L)
        pyautogui.hotkey(*config["focus_hotkeys"])
        time.sleep(0.5) 
        
        # 4. 把长文本放入剪贴板然后粘贴
        pyperclip.copy(message)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)
        
        # 5. 发送回车键执行
        pyautogui.press('enter')
        logger.info(f"成功输入并按下了回车。")
        time.sleep(0.5)
        
        return True
        
    except Exception as e:
        logger.error(f"UI 自动化控制 {target} 时发生错误: {str(e)}")
        return False
