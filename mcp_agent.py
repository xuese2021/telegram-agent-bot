"""
MCP 模式 Agent：支持 Gemini 或 Claude，工具调用直接返回，无需剪贴板。
优先使用 GEMINI_API_KEY（你已有），无需 Claude。
"""
import os
import logging
from typing import Any

from anthropic import Anthropic
from tools import (
    run_command,
    read_file,
    write_file,
    list_dir,
    glob_search,
    grep_search,
    set_approved_base,
)

logger = logging.getLogger(__name__)

# 允许操作的基础目录（沙箱）
APPROVED_BASE = os.environ.get("APPROVED_DIRECTORY", os.path.expanduser("~"))
set_approved_base(APPROVED_BASE)

# Claude 工具定义 - 参考 AC-AIBot agent_cursor、agent_filesystem
CLAUDE_TOOLS = [
    {
        "name": "run_command",
        "description": "【agent_cursor】运行终端命令并返回输出。用于执行脚本、测试、git、安装依赖等。",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string", "description": "要执行的命令"}},
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": "【agent_filesystem】读取文件内容。",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "limit": {"type": "integer", "description": "最大读取字符数，默认8000", "default": 8000},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "【agent_filesystem】将内容写入文件，若存在则覆盖。",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "要写入的内容"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_dir",
        "description": "【agent_filesystem】列出目录下的文件和子目录。类似 ls 命令。",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "目录路径，默认当前目录", "default": "."}},
            "required": [],
        },
    },
    {
        "name": "glob_search",
        "description": "【agent_filesystem】按通配符搜索文件。例如 *.py 或 **/*.md",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "通配符模式"},
                "base_dir": {"type": "string", "description": "搜索根目录", "default": "."},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "grep_search",
        "description": "【agent_filesystem】在文件或目录中搜索包含指定文本的行。",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "要搜索的文本或正则"},
                "path": {"type": "string", "description": "文件或目录路径"},
                "max_results": {"type": "integer", "description": "最多返回行数", "default": 20},
            },
            "required": ["pattern", "path"],
        },
    },
]


def _execute_tool(name: str, args: dict[str, Any]) -> str:
    """执行工具并返回结果。"""
    try:
        if name == "run_command":
            return run_command(args["command"])
        if name == "read_file":
            return read_file(args["path"], args.get("limit", 8000))
        if name == "write_file":
            return write_file(args["path"], args["content"])
        if name == "list_dir":
            return list_dir(args.get("path", "."))
        if name == "glob_search":
            return glob_search(args["pattern"], args.get("base_dir", "."))
        if name == "grep_search":
            return grep_search(
                args["pattern"],
                args["path"],
                args.get("max_results", 20),
            )
        return f"未知工具: {name}"
    except PermissionError as e:
        return str(e)
    except Exception as e:
        return f"执行失败: {str(e)}"


def process_with_claude(
    message: str,
    api_key: str,
    model: str = "claude-sonnet-4-20250514",
    max_turns: int = 10,
) -> str:
    """
    使用 Claude API + 工具调用处理消息，直接返回最终文本，无需剪贴板。
    """
    client = Anthropic(api_key=api_key)
    messages: list[dict[str, Any]] = [{"role": "user", "content": message}]

    system_prompt = (
        "你是运行在用户本地的 AI 编程助手。你可以通过工具执行命令、读写文件来完成任务。"
        "请用中文回复。路径请使用绝对路径或相对于工作目录的路径。"
        f"允许操作的基础目录: {APPROVED_BASE}"
    )

    for _ in range(max_turns):
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            tools=CLAUDE_TOOLS,
            messages=messages,
        )

        # 无 tool_use 则返回最终文本
        if response.stop_reason == "end_turn":
            for block in reversed(response.content):
                if block.type == "text":
                    return block.text
            return "（无文本回复）"

        # 处理 tool_use
        tool_results: list[dict[str, Any]] = []
        for block in response.content:
            if block.type == "tool_use":
                result = _execute_tool(block.name, block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )
                logger.info(f"工具调用: {block.name} -> {len(result)} 字符")

        # 将 assistant 回复和 tool_result 加入对话
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return "任务暂停：工具调用轮次过多。"


# ============ Gemini 实现（优先，你已有 GEMINI_API_KEY）============
GEMINI_TOOL_DECLARATIONS = [
    {"name": "run_command", "description": "运行终端命令", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
    {"name": "read_file", "description": "读取文件内容", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["path"]}},
    {"name": "write_file", "description": "写入文件", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "list_dir", "description": "列出目录", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}},
    {"name": "glob_search", "description": "通配符搜索文件", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "base_dir": {"type": "string"}}, "required": ["pattern"]}},
    {"name": "grep_search", "description": "在文件中搜索文本", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}, "max_results": {"type": "integer"}}, "required": ["pattern", "path"]}},
]


def process_with_gemini(message: str, api_key: str, model: str = "gemini-2.0-flash", max_turns: int = 10) -> str:
    """使用 Gemini API，无需 Claude。"""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    tools = [types.Tool(function_declarations=GEMINI_TOOL_DECLARATIONS)]
    config = types.GenerateContentConfig(
        system_instruction=f"你是本地 AI 编程助手。用工具执行命令、读写文件。用中文回复。沙箱目录: {APPROVED_BASE}",
        tools=tools,
        temperature=0.7,
    )
    history = [types.Content(role="user", parts=[types.Part.from_text(text=message)])]

    for _ in range(max_turns):
        response = client.models.generate_content(model=model, contents=history, config=config)
        parts = response.candidates[0].content.parts if response.candidates else []
        has_tool_call = False

        for part in parts:
            if hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                name = fc.name
                args = dict(fc.args) if fc.args else {}
                result = _execute_tool(name, args)
                logger.info(f"工具: {name} -> {len(result)} 字符")
                history.append(types.Content(role="model", parts=[part]))
                history.append(types.Content(role="user", parts=[types.Part.from_function_response(name=name, response={"result": result})]))
                has_tool_call = True
                break

        if not has_tool_call:
            text = response.text or ""
            return text.strip() or "（无回复）"

    return "任务暂停：工具调用轮次过多。"


def process(message: str) -> str:
    """自动选择：GEMINI_API_KEY 优先，否则 ANTHROPIC_API_KEY"""
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()

    if gemini_key:
        return process_with_gemini(message, gemini_key)
    if anthropic_key:
        return process_with_claude(message, anthropic_key)
    raise ValueError("请在 .env 中配置 GEMINI_API_KEY 或 ANTHROPIC_API_KEY")
