import logging
import asyncio
import os
from datetime import datetime
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters
from pymongo import MongoClient

WAITING_FOR_BROADCAST_MSG = 2
MONGO_URI = os.environ.get("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["telegram_bot_db"]
users_col = db["users"]
broadcast_logs_col = db["broadcast_logs"]


# Broadcast Start Command
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = context.bot_data.get("ADMIN_ID")
    user_id = update.effective_user.id

    if int(user_id) != int(admin_id):
        await update.message.reply_text("❌ Aap admin nahi hain!")
        return ConversationHandler.END

    total_users = users_col.count_documents({})

    await update.message.reply_text(
        f"📢 <b>Broadcast Mode Active</b>\nTotal Targeted Users: <code>{total_users}</code>\n\n"
        "Jo message saare members ko bhejna hai, wo text/photo/video yahan bhejein.\nCancel karne ke liye /cancel likhein.",
        parse_mode="HTML"
    )
    return WAITING_FOR_BROADCAST_MSG


# Process and Save Broadcast
async def process_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    users = list(users_col.find({}, {"_id": 1}))
    total_users = len(users)

    if total_users == 0:
        await update.message.reply_text("❌ Broadcast ke liye koi users nahi mile!")
        return ConversationHandler.END

    success = 0
    failed = 0

    status_msg = await update.message.reply_text(f"⏳ Broadcast shuru ho raha hai... (0/{total_users})")

    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for index, user in enumerate(users, 1):
        user_id_str = user["_id"]
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

    # Broadcast Data Save in MongoDB
    total_broadcasts = broadcast_logs_col.count_documents({})
    broadcast_data = {
        "broadcast_id": total_broadcasts + 1,
        "date_start": start_time,
        "date_end": end_time,
        "total_users": total_users,
        "success_count": success,
        "failed_count": failed,
        "message_text": msg.text or msg.caption or "[Media Content]"
    }
    broadcast_logs_col.insert_one(broadcast_data)

    await status_msg.edit_text(
        f"✅ <b>Broadcast Completed & Saved!</b>\n\n"
        f"🎯 Success: <code>{success}</code>\n"
        f"❌ Failed: <code>{failed}</code>\n"
        f"👥 Total Targeted: <code>{total_users}</code>\n"
        f"💾 <i>Data successfully saved in MongoDB broadcast history!</i>",
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
