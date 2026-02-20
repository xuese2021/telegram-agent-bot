# 本地服务器部署指南

## 可以安装到本地服务器吗？

**可以。** 仅 API 模式，只需 Python + 网络，适合任意环境：

| 环境 | 支持 |
|------|------|
| Windows 桌面 / 服务器 | ✅ |
| Linux 服务器 | ✅ |
| 树莓派 / NAS | ✅ |

---

## 快速启动（当前环境）

```powershell
cd telegram-agent-bot
python main.py
```

---

## Windows 服务方式（开机自启）

### 方法 1：任务计划程序

1. 打开「任务计划程序」
2. 创建基本任务 → 触发器选「计算机启动时」
3. 操作：启动程序 → `python`，参数：`main.py`，起始于：项目目录

### 方法 2：NSSM（推荐）

```powershell
# 下载 NSSM: https://nssm.cc/download
nssm install TelegramAgentBot "C:\Python311\python.exe" "C:\path\to\telegram-agent-bot\main.py"
nssm set TelegramAgentBot AppDirectory "C:\path\to\telegram-agent-bot"
nssm start TelegramAgentBot
```

---

## Linux 服务器部署

```bash
# 1. 安装
cd /opt
git clone <your-repo> telegram-agent-bot
cd telegram-agent-bot
pip install -r requirements.txt

# 2. 配置
cp .env.example .env
nano .env  # 填入 TELEGRAM_BOT_TOKEN、ANTHROPIC_API_KEY 等

# 3. systemd 服务（开机自启）
sudo tee /etc/systemd/system/telegram-agent-bot.service << 'EOF'
[Unit]
Description=Telegram Agent Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/opt/telegram-agent-bot
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10
EnvironmentFile=/opt/telegram-agent-bot/.env

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable telegram-agent-bot
sudo systemctl start telegram-agent-bot
```

---

## 网络要求

- 能访问 `api.telegram.org`（Telegram Bot API）
- API 模式需能访问 Anthropic API

如在公司内网，需确认防火墙/代理允许上述地址。
