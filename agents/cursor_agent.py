from .base_agent import BaseAgent

class CursorAgent(BaseAgent):
    def __init__(self):
        # 预留：在此初始化 Cursor 连接或 API
        pass

    def process_message(self, message: str) -> str:
        """
        [预留位] 将消息发送给 Cursor 并返回其结果。
        """
        return f"[Cursor Agent 占位] 您发送了: {message}\n(Cursor 接口尚未实现，敬请期待)"
