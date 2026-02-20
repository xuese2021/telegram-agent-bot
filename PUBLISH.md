# 发布指南

## 发布到 GitHub

### 1. 创建仓库

在 GitHub 新建仓库，例如 `telegram-agent-bot`。

### 2. 初始化并推送

```bash
cd telegram-agent-bot
git init
git add .
git commit -m "Initial commit: 永动机 - Telegram 远程控制 Cursor Agent"
git branch -M main
git remote add origin https://github.com/你的用户名/telegram-agent-bot.git
git push -u origin main
```

### 3. 隐私检查

确保以下文件未被提交：
- `.env`（已在 .gitignore）
- 任何包含 Token、用户 ID、服务器地址的文件

## 文章发布到 WordPress 草稿箱

### 方式一：使用脚本（需配置环境变量）

```bash
export WP_SSH_HOST=你的服务器
export WP_SSH_USER=root
export WP_SSH_PASSWORD=你的密码
python openclaw-cleanup/create_telegram_agent_bot_draft.py
```

### 方式二：手动发布

1. 打开 `article_draft.md`
2. 复制内容到 WordPress 后台 → 文章 → 新建
3. 保存为草稿
4. 发布前将 GitHub 链接替换为实际地址
