# 永动机 Agent 指令

## 模式判断

- **用户说「我要出门了」** = 进入 `wait_for_task` 循环，等你用 Bot 发任务
- **Bot 有消息** = 用户出门了，必须远程控制。项目流程、方向、权限全部通过 MCP 获取。
- **消息来自 Cursor 对话框**（且非「我要出门了」）= 用户在现场，直接对话。停掉 MCP 获取，用当前对话内容。
- **消息为「请读取 xxx/current_task.md 并执行任务」** = 守护脚本触发，读取该文件执行，完成后必须调用 `report_done`。

## 守护脚本触发模式（daemon.py）

1. 读取消息中指定的 `current_task.md` 路径获取任务内容
2. 执行任务
3. 需要放权时用 `request_approval`
4. **完成后必须调用 `report_done`**，否则守护脚本会一直等待

## 远程模式（用户通过 Bot 发消息）

1. **wait_for_task**：调用 MCP `wait_for_task`，阻塞等待
2. **收到任务**：停掉本次等待，开始处理
3. **退出信号**：若任务为「停止监听」「退出」「我回来了」→ 直接退出循环，不再监听
4. **执行**：项目流程、方向、权限全部通过 MCP 工具获取
5. **需要放权**：`request_approval`，等用户手机点按钮
6. **完成**：`report_done` 汇报
7. **回到步骤 1**：继续 `wait_for_task`

### 远程模式约束（避免 Cursor 弹窗要你点「同意」）

- **新建文件/目录**：一律放在**当前 workspace 根目录**内，不要写到 workspace 外
- 这样 Cursor 不会弹「Blocked / Accept」让你点，你出门后 Agent 才能自动执行

## 本地模式（用户直接在 Cursor 对话）

- 不调用 `wait_for_task`
- 直接使用用户当前消息
- 需要放权时仍用 `request_approval`

## MCP 工具

| 工具 | 说明 |
|------|------|
| `wait_for_task` | 远程模式：等待 Bot 队列中的任务 |
| `request_approval` | 请求放权，等用户点按钮 |
| `report_done` | 汇报完成 |
| `report_progress` | 汇报进度 |
