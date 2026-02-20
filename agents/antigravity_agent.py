import os
from google import genai
from google.genai import types
from .base_agent import BaseAgent
from tools import run_command, read_file, write_file

class AntiGravityAgent(BaseAgent):
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"
        self.history = []
        self.tools = [run_command, read_file, write_file]
        
        system_instruction = (
            "你是 AntiGravity，一个运行在用户本地机器上的强大 AI 编程智能体。 "
            "你可以通过使用工具来执行终端命令、读取文件和修改文件内容，以此来帮助用户完成复杂的任务。 "
            "在与用户交谈时，请使用中文。"
        )
        self.config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=self.tools,
            temperature=0.7
        )

    def process_message(self, message: str) -> str:
        self.history.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))
        
        try:
            # 简单的循环来自动处理最多 5 个连续的工具调用
            for _ in range(5):
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=self.history,
                    config=self.config
                )
                
                if response.function_calls:
                    # 将模型尝试调用工具的请求存入历史记录
                    self.history.append(response.candidates[0].content)
                    
                    tool_responses = []
                    for function_call in response.function_calls:
                        name = function_call.name
                        args = function_call.args
                        try:
                            if name == "run_command":
                                result = run_command(**args)
                            elif name == "read_file":
                                result = read_file(**args)
                            elif name == "write_file":
                                result = write_file(**args)
                            else:
                                result = f"未知函数: {name}"
                        except Exception as e:
                            result = f"执行 {name} 失败: {str(e)}"
                            
                        tool_responses.append(types.Part.from_function_response(
                            name=name,
                            response={"result": result}
                        ))
                    
                    # 将工具执行结果返回给模型
                    self.history.append(types.Content(role="user", parts=tool_responses))
                else:
                    self.history.append(response.candidates[0].content)
                    return response.text
                    
            return "任务暂停: 单轮对话中的工具调用次数过多。"
            
        except Exception as e:
            return f"Agent 报错: {str(e)}"
