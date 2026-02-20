"""
工具模块 - 参考 AC-AIBot 工具市场设计
agent_cursor: 执行系统命令
agent_filesystem: 文件读写、目录列表、搜索
"""
import subprocess
import os
import glob as glob_module

# 默认沙箱目录，由 mcp_agent 设置
_approved_base = os.path.expanduser("~")


def set_approved_base(path: str) -> None:
    """设置允许操作的基础目录。"""
    global _approved_base
    _approved_base = os.path.abspath(path)


def _resolve_path(path: str) -> str:
    """解析为绝对路径并确保在沙箱内。"""
    abs_path = os.path.abspath(os.path.expanduser(path))
    base = os.path.abspath(_approved_base)
    if not abs_path.startswith(base):
        raise PermissionError(f"路径 {path} 不在允许的目录 {_approved_base} 内")
    return abs_path


# ============ agent_cursor：命令执行 ============
def run_command(command: str) -> str:
    """运行终端命令并返回其输出结果。用于执行脚本、测试、git、安装依赖等。"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            timeout=60,
            cwd=_approved_base,
        )
        output = result.stdout
        if result.stderr:
            output += f"\nStderr: {result.stderr}"
        return output[:6000] if output else "(无输出)"
    except subprocess.TimeoutExpired:
        return "命令执行超时（60秒）"
    except Exception as e:
        return f"执行命令时出现异常: {str(e)}"


# ============ agent_filesystem：文件操作 ============
def read_file(path: str, limit: int = 8000) -> str:
    """读取文件内容。支持文本文件。"""
    try:
        safe_path = _resolve_path(path)
        with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except PermissionError as e:
        return str(e)
    except Exception as e:
        return f"读取文件 {path} 时出错: {str(e)}"


def write_file(path: str, content: str) -> str:
    """将内容写入文件，若文件存在则覆盖。"""
    try:
        safe_path = _resolve_path(path)
        os.makedirs(os.path.dirname(safe_path) or ".", exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"成功写入文件 {path}"
    except PermissionError as e:
        return str(e)
    except Exception as e:
        return f"写入文件 {path} 时出错: {str(e)}"


def list_dir(path: str = ".") -> str:
    """列出目录下的文件和子目录。类似 ls 命令。"""
    try:
        safe_path = _resolve_path(path)
        items = sorted(os.listdir(safe_path))
        lines = []
        for name in items[:100]:  # 最多 100 项
            full = os.path.join(safe_path, name)
            prefix = "[DIR] " if os.path.isdir(full) else ""
            lines.append(f"{prefix}{name}")
        return "\n".join(lines) if lines else "(空目录)"
    except PermissionError as e:
        return str(e)
    except Exception as e:
        return f"列出目录 {path} 时出错: {str(e)}"


def glob_search(pattern: str, base_dir: str = ".") -> str:
    """按通配符模式搜索文件。例如 *.py 或 **/*.md（** 表示递归）"""
    try:
        safe_base = _resolve_path(base_dir)
        full_pattern = os.path.join(safe_base, pattern)
        matches = glob_module.glob(full_pattern, recursive=True)
        # 转为相对路径便于阅读
        rel = [os.path.relpath(m, safe_base) for m in matches[:50]]
        return "\n".join(rel) if rel else f"未找到匹配: {pattern}"
    except PermissionError as e:
        return str(e)
    except Exception as e:
        return f"搜索 {pattern} 时出错: {str(e)}"


def grep_search(pattern: str, path: str, max_results: int = 20) -> str:
    """在文件或目录中搜索包含指定文本的行。path 可以是文件或目录。"""
    try:
        import re
        safe_path = _resolve_path(path)
        results = []
        regex = re.compile(pattern, re.IGNORECASE)

        def search_in_file(fp: str) -> None:
            try:
                with open(fp, "r", encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f, 1):
                        if regex.search(line):
                            results.append(f"{fp}:{i}: {line.rstrip()}")
                            if len(results) >= max_results:
                                return
            except Exception:
                pass

        if os.path.isfile(safe_path):
            search_in_file(safe_path)
        elif os.path.isdir(safe_path):
            for root, _, files in os.walk(safe_path):
                for f in files:
                    if len(results) >= max_results:
                        break
                    search_in_file(os.path.join(root, f))
        else:
            return f"路径不存在: {path}"

        return "\n".join(results) if results else f"未找到匹配: {pattern}"
    except PermissionError as e:
        return str(e)
    except Exception as e:
        return f"搜索时出错: {str(e)}"
