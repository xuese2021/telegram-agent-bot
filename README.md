# 永动机 - Telegram ↔ Cursor Agent 中间层

## 三种场景流程

详见 [流程说明.md](流程说明.md)

## 架构（全部已验证）

```
📱 你的手机
   │ "做一个登录页面"
   ▼
Telegram Bot
   │ 写入 .tg_task_xxx.txt
   ▼
MCP: wait_for_task()  ← 阻塞等待，已验证可行
   │ 返回任务内容
   ▼
Cursor Agent 干活  ← 用 Cursor 自带模型，不花额外钱
   │
   ├─ 需要审批 → MCP: request_approval()
   │              等你手机点按钮
   │
   ├─ 完成 → MCP: report_done()
   │           推送到你手机
   │
   ▼
MCP: wait_for_task()  ← 回到等待
   ♻️ 永动机
```

## 启动

### 1. 启动 Bot（必须常驻）

```bash
cd telegram-agent-bot
python main.py
```

### 2. 配置 Cursor MCP

已在 `~/.cursor/mcp.json` 添加 `middleware` 服务器。重启 Cursor 后生效。

### 3. 启动 Agent 永动机

**方式 A：守护脚本（推荐，可开机自启）**

```bash
python daemon.py
```

每 10 秒：有新任务？Agent 忙？→ 唤起 → 标记忙。统一覆盖三种情景。

**方式 B：手动触发**

在 Cursor 开 Agent，发送：

```
按 AGENTS.md 的流程运行：循环调用 wait_for_task，收到任务后执行，需要时 request_approval，完成后 report_done，再回到 wait_for_task。
```

## 出门前必做（否则远程时 Agent 会卡在「点同意」）

1. **开启 Cursor Auto-Run**：`Ctrl+Shift+J` → Features → Agent → 开启 Auto-run
2. **workspace 约束**：新建文件放在 workspace 根目录内，避免 Cursor 弹「点同意」

## 配置 .env

```
TELEGRAM_BOT_TOKEN=your_bot_token
ALLOWED_USER_IDS=12345678
```

## MCP 工具

| 工具 | 说明 |
|------|------|
| `wait_for_task` | 阻塞等待新任务 |
| `request_approval` | 请求放权，等用户点按钮 |
| `report_done` | 汇报完成 |
| `report_progress` | 汇报进度 |
