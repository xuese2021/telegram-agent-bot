# 永动机：用 Telegram 远程控制 Cursor Agent 写代码

## 项目概述

**永动机**（telegram-agent-bot）是一个轻量中间层，让你用手机通过 Telegram Bot 远程控制 Cursor AI Agent 执行编程任务。出门在外发一条消息，家里的 Cursor 就能自动写代码、改文件，需要放权时在手机点按钮即可。

**GitHub**：https://github.com/（待填写）

## 核心特性

- **📱 手机发任务**：直接给 Bot 发消息，任务加入队列
- **🤖 Cursor Agent 执行**：通过 MCP 获取任务，用 Cursor 自带模型，不花额外钱
- **🔐 远程放权**：需要审批时 Bot 推送「允许/拒绝」按钮，手机点选
- **♻️ 统一流程**：三种情景（有项目在跑、人在外面、出门前说一声）全覆盖
- **🛡️ 守护脚本**：daemon 每 10 秒轮询，Agent 忙则任务排队，不卡

## 架构

```
手机 → Telegram Bot → 写入任务队列
                ↓
MCP: wait_for_task() ← 阻塞等待
                ↓
Cursor Agent 执行
                ↓
需要放权 → request_approval() → 手机点按钮
完成 → report_done() → 推送到手机
                ↓
继续 wait_for_task 或 daemon 唤起下一个
```

## 三种情景

| 情景 | 行为 |
|------|------|
| **有项目在跑，人走开** | Agent 忙 → 新任务排队 → 干完自动取下一个 |
| **没项目跑，人在外面** | daemon 检测到任务 → 唤起 Agent（Cursor 未开则启动） |
| **出门前说「我要出门了」** | Agent 进入 wait_for_task → 直接消费任务 |

## 快速开始

### 1. 配置

```bash
git clone https://github.com/xxx/telegram-agent-bot.git
cd telegram-agent-bot
cp .env.example .env
# 填入 TELEGRAM_BOT_TOKEN、ALLOWED_USER_IDS
pip install -r requirements.txt
```

### 2. 启动 Bot

```bash
python main.py
```

### 3. 配置 Cursor MCP

在 `~/.cursor/mcp.json` 添加 middleware 服务器，指向 `mcp_middleware_server.py`。

### 4. 启动守护（可选，可开机自启）

```bash
python daemon.py
```

## MCP 工具

| 工具 | 说明 |
|------|------|
| wait_for_task | 阻塞等待新任务 |
| request_approval | 请求放权，等用户手机点按钮 |
| report_done | 汇报完成，推送到手机 |
| report_progress | 汇报进度 |

## 技术栈

- Python 3.10+
- python-telegram-bot
- fastmcp（MCP 服务器）
- pyautogui / pyperclip / pygetwindow（daemon 模拟键盘）

## 隐私与安全

- Bot Token 和用户 ID 仅存于本地 `.env`，不提交到仓库
- 任务内容通过本地文件队列传递，不经过第三方
- 放权操作需在 Bot 中点击，仅限 ALLOWED_USER_IDS 内用户

## 资源

- **GitHub**：待发布后填写
- **许可证**：MIT
