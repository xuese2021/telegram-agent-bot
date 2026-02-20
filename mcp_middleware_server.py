"""
MCP 服务器：暴露中间层工具给 Cursor Agent
- wait_for_task: 阻塞等待 Bot 写入的任务
- request_approval: 请求远程放权
- report_done: 汇报完成
"""
import os
import sys

# 确保从项目目录加载
_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(_DIR)
sys.path.insert(0, _DIR)

from fastmcp import FastMCP

mcp = FastMCP("middleware", instructions="Telegram 中间层：任务队列、放权、汇报")


@mcp.tool()
def wait_for_task(poll_interval_sec: float = 5, timeout_sec: int = 0) -> str:
    """
    阻塞等待新任务。用户通过 Telegram 发消息后，Bot 会写入任务文件。
    timeout_sec=0 表示无限等待。返回任务内容。
    """
    from middleware import wait_for_task as _wait_task

    return _wait_task(poll_interval_sec=poll_interval_sec, timeout_sec=timeout_sec)


@mcp.tool()
def request_approval(question: str, task_id: str = "", timeout_sec: int = 3600) -> bool:
    """
    请求远程放权。阻塞直到用户在 Telegram 点击按钮。返回 True=允许，False=拒绝或超时。
    """
    from middleware import request_approval as _ask

    return _ask(question=question, task_id=task_id, timeout_sec=timeout_sec)


@mcp.tool()
def report_done(message: str, task_id: str = "") -> bool:
    """任务完成，推送到用户手机"""
    from middleware import report_done as _report

    return _report(message=message, task_id=task_id)


@mcp.tool()
def report_progress(step: str, message: str, task_id: str = "") -> bool:
    """汇报进度给远程用户"""
    from middleware import report as _report

    return _report(step=step, message=message, task_id=task_id)


if __name__ == "__main__":
    mcp.run()
