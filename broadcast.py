import logging
import asyncio
import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters

WAITING_FOR_BROADCAST_MSG = 2
DB_FILE = "users_data.json"
BROADCAST_LOG_FILE = "broadcast_history.json"

# Users Data Load
def load_users():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

# Broadcast History Load
def load_broadcast_logs():
    if os.path.exists(BROADCAST_LOG_FILE):
        with open(BROADCAST_LOG_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []

# Broadcast History Save
def save_broadcast_log(log_entry):
    logs = load_broadcast_logs()
    logs.append(log_entry)
    
    temp_file = f"{BROADCAST_LOG_FILE}.tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=4, ensure_ascii=False)
    os.replace(temp_file, BROADCAST_LOG_FILE)


# Broadcast Start Command
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = context.bot_data.get("ADMIN_ID")
    user_id = update.effective_user.id

    if int(user_id) != int(admin_id):
        await update.message.reply_text("❌ Aap admin nahi hain!")
        return ConversationHandler.END

    users_db = load_users()
    total_users = len(users_db)

    await update.message.reply_text(
        f"📢 <b>Broadcast Mode Active</b>\nTotal Targeted Users: <code>{total_users}</code>\n\n"
        "Jo message saare members ko bhejna hai, wo text/photo/video yahan bhejein.\nCancel karne ke liye /cancel likhein.",
        parse_mode="HTML"
    )
    return WAITING_FOR_BROADCAST_MSG


# Process and Save Broadcast
async def process_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    users_db = load_users()
    user_ids = list(users_db.keys())
    total_users = len(user_ids)

    if total_users == 0:
        await update.message.reply_text("❌ Broadcast ke liye koi users nahi mile!")
        return ConversationHandler.END

    success = 0
    failed = 0

    status_msg = await update.message.reply_text(f"⏳ Broadcast shuru ho raha hai... (0/{total_users})")

    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for index, user_id_str in enumerate(user_ids, 1):
        try:
            await msg.copy(chat_id=int(user_id_str))
            success += 1
        except Exception as e:
            logging.error(f"Broadcast failed to {user_id_str}: {e}")
            failed += 1

        await asyncio.sleep(0.05)

        if index % 20 == 0 or index == total_users:
            try:
                await status_msg.edit_text(f"⏳ Broadcast chal raha hai... ({index}/{total_users})")
            except Exception:
                pass

    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Broadcast Data Save Function Call
    broadcast_data = {
        "broadcast_id": len(load_broadcast_logs()) + 1,
        "date_start": start_time,
        "date_end": end_time,
        "total_users": total_users,
        "success_count": success,
        "failed_count": failed,
        "message_text": msg.text or msg.caption or "[Media Content]"
    }
    save_broadcast_log(broadcast_data)

    await status_msg.edit_text(
        f"✅ <b>Broadcast Completed & Saved!</b>\n\n"
        f"🎯 Success: <code>{success}</code>\n"
        f"❌ Failed: <code>{failed}</code>\n"
        f"👥 Total Targeted: <code>{total_users}</code>\n"
        f"💾 <i>Data successfully saved in broadcast history!</i>",
        parse_mode="HTML"
    )
    return ConversationHandler.END


async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Broadcast operation cancel kar diya gaya hai.")
    return ConversationHandler.END


def get_broadcast_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={
            WAITING_FOR_BROADCAST_MSG: [
                MessageHandler(filters.ALL & ~filters.COMMAND, process_broadcast)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_broadcast)
        ],
        allow_reentry=True,
        per_message=False,
    )
  
