from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def process_message(self, message: str) -> str:
        """
        处理传入的消息并返回回复结果。
        """
        pass
