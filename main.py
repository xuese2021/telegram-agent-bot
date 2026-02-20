"""
Telegram Agent Bot - 永动机

用户发消息 → 写入任务队列 → Cursor Agent 通过 MCP 获取并执行
无需打开 Cursor 窗口，无需 UI 操控。
"""
import os
import glob
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_IDS = os.getenv("ALLOWED_USER_IDS", "")
allowed_users = [int(uid.strip()) for uid in ALLOWED_USER_IDS.split(",") if uid.strip().isdigit()]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def _pending_count() -> int:
    """当前待处理任务数"""
    return len(glob.glob(os.path.join(BASE_DIR, ".tg_task_*.txt")))


async def _cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看队列状态"""
    if update.effective_user.id not in allowed_users:
        return
    n = _pending_count()
    await update.message.reply_text(f"📋 待处理任务: {n} 个", parse_mode="Markdown")


async def _cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """清空任务队列"""
    if update.effective_user.id not in allowed_users:
        return
    pattern = os.path.join(BASE_DIR, ".tg_task_*.txt")
    files = glob.glob(pattern)
    for f in files:
        try:
            os.remove(f)
        except Exception as e:
            logger.warning(f"删除失败 {f}: {e}")
    await update.message.reply_text(f"🗑️ 已清空 {len(files)} 个待处理任务", parse_mode="Markdown")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in allowed_users:
        return

    n = _pending_count()
    msg = (
        "🤖 **永动机**\n\n"
        "直接发任务即可，我会加入队列。\n"
        "Cursor Agent 通过 MCP 获取并执行。\n\n"
        f"📋 待处理: {n} 个"
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("📋 查看队列", callback_data="status"),
    ]])
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=keyboard)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理按钮：approve/reject（放权）、status（查看队列）"""
    query = update.callback_query
    if query.from_user.id not in allowed_users:
        await query.answer("无权操作", show_alert=True)
        return

    await query.answer()
    data = query.data

    if data == "status":
        n = _pending_count()
        await query.edit_message_text(
            f"📋 **队列状态**\n\n待处理任务: {n} 个\n\n直接发消息即可添加新任务。",
            parse_mode="Markdown",
        )
        return

    if data.startswith("approve_"):
        req_id = data.split("_")[1]
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f".tg_response_{req_id}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("APPROVED")
        await query.edit_message_text(f"{query.message.text}\n\n✅ **已点选: 允许执行**", parse_mode="Markdown")
    elif data.startswith("reject_"):
        req_id = data.split("_")[1]
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f".tg_response_{req_id}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("REJECTED")
        await query.edit_message_text(f"{query.message.text}\n\n❌ **已点选: 拒绝放行**", parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in allowed_users:
        return

    user_message = update.message.text
    if not user_message:
        return

    try:
        from middleware import write_task

        task_id = write_task(user_message)
        n = _pending_count()
        await update.message.reply_text(
            f"📥 **已加入队列**\n\n"
            f"任务 ID: `{task_id}`\n"
            f"待处理: {n} 个\n\n"
            "Agent 会通过 MCP 获取并执行。",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"写入任务失败: {e}")
        await update.message.reply_text(f"❌ 写入失败: {str(e)}")


def main():
    if not TELEGRAM_TOKEN or not allowed_users:
        logger.error("缺少 TELEGRAM_BOT_TOKEN 或 ALLOWED_USER_IDS 配置。")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", _cmd_status))
    app.add_handler(CommandHandler("clear", _cmd_clear))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("永动机 Bot 已启动")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
