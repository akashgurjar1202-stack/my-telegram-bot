import logging
import json
import os
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = "7513589199:AAGTDOe2mt9LnPD9wkFHq3q4YDfGujEB5_w"
ADMIN_ID = 1164326786

START_PHOTO = "https://t.me/aaaafghjvx/12"
FIRST_CHANNEL_USERNAME = "Britania68"

# States
WAITING_FOR_PAYMENT_DETAILS = 1
WAITING_FOR_BROADCAST_MSG = 2

# Database File Path
DB_FILE = "users_data.json"


def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}


def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


users_db = load_data()


def register_user(user_id, username=None):
    str_id = str(user_id)
    if str_id not in users_db:
        users_db[str_id] = {
            "balance": 0.0,
            "username": username,
            "referred_by": None
        }
        save_data(users_db)


async def is_user_joined(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=f"@{FIRST_CHANNEL_USERNAME}", user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return True


# /start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    str_id = str(user.id)
    
    # Track Referral
    is_new = str_id not in users_db
    register_user(user.id, user.username)

    if is_new and context.args:
        referrer_id = context.args[0]
        if referrer_id != str_id and referrer_id in users_db:
            users_db[str_id]["referred_by"] = referrer_id
            
            # Credit â‚¹1 to referrer
            ref_bal = users_db[referrer_id].get("balance", 0.0)
            users_db[referrer_id]["balance"] = ref_bal + 1.0
            save_data(users_db)

            try:
                await context.bot.send_message(
                    chat_id=int(referrer_id),
                    text=f"ðŸŽ‰ **Naya Refer!**\nUser ({user.full_name}) aapke link se juda. Aapko **â‚¹1.00** mil gaye hain!",
                    parse_mode="Markdown"
                )
            except Exception:
                pass

    welcome_text = (
        "ðŸŽ‰ **WELCOME TO REFER & EARN BOT** ðŸŽ‰\n\n"
        "ðŸ“¢ **Offer Details:**\n"
        "ðŸŽ **Per Refer:** â‚¹1\n"
        "ðŸ’³ **Minimum Withdrawal:** â‚¹1\n\n"
        "âš ï¸ **Aage badhne ke liye sabse pehle niche diye gaye Channels ko join karein!**"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ðŸ“¢ Channel 1", url=f"https://t.me/{FIRST_CHANNEL_USERNAME}"),
            InlineKeyboardButton("ðŸ“¢ Channel 2", url="https://t.me/your_channel_2")
        ],
        [
            InlineKeyboardButton("ðŸ“¢ Channel 3", url="https://t.me/your_channel_3"),
            InlineKeyboardButton("ðŸ“¢ Channel 4", url="https://t.me/your_channel_4")
        ],
        [
            InlineKeyboardButton("âœ… Joined All Channels", callback_data="check_joined")
        ],
        [
            InlineKeyboardButton("ðŸ”— Generate/Get Invite Link", callback_data="get_invite")
        ],
        [
            InlineKeyboardButton("ðŸ’° Check Balance", callback_data="check_balance"),
            InlineKeyboardButton("ðŸ’¸ Withdrawal â‚¹1", callback_data="start_withdraw")
        ]
    ])

    try:
        if START_PHOTO.startswith("http://") or START_PHOTO.startswith("https://"):
            await update.message.reply_photo(
                photo=START_PHOTO,
                caption=welcome_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        else:
            with open(START_PHOTO, "rb") as photo_file:
                await update.message.reply_photo(
                    photo=photo_file,
                    caption=welcome_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
    except Exception:
        await update.message.reply_text(
            text=welcome_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )


# Button Callbacks Handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    str_id = str(user_id)
    bot_info = await context.bot.get_me()

    if query.data == "check_joined":
        if not await is_user_joined(context, user_id):
            await query.message.reply_text(f"âš ï¸ Pehle **Channel 1** (@{FIRST_CHANNEL_USERNAME}) join karein!")
            return
        await query.message.reply_text("âœ… Verification successful! Aap bot use kar sakte hain.")

    elif query.data == "get_invite":
        if not await is_user_joined(context, user_id):
            await query.message.reply_text(f"âš ï¸ Pehle **Channel 1** (@{FIRST_CHANNEL_USERNAME}) join karein!")
            return

        invite_link = f"https://t.me/{bot_info.username}?start={user_id}"
        msg = f"ðŸ”— **Aapka Personal Invite Link:**\n`{invite_link}`\n\nIs link ko apne dosto ko bhejein aur har refer par â‚¹1 kamayein!"
        share_text = f"ðŸŽ Is bot se har refer par â‚¹1 kamayein! Abhi join karein:\n{invite_link}"

        sub_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("ðŸ“² Share Link To Friends", switch_inline_query=share_text)
            ],
            [
                InlineKeyboardButton("ðŸ’° Check Balance", callback_data="check_balance"),
                InlineKeyboardButton("ðŸ’¸ Withdrawal â‚¹1", callback_data="start_withdraw"),
            ]
        ])
        await query.message.reply_text(msg, parse_mode="Markdown", reply_markup=sub_keyboard)

    elif query.data == "check_balance":
        if not await is_user_joined(context, user_id):
            await query.message.reply_text(f"âš ï¸ Pehle **Channel 1** (@{FIRST_CHANNEL_USERNAME}) join karein!")
            return

        bal = users_db.get(str_id, {}).get("balance", 0.0)
        await query.message.reply_text(f"ðŸ’° **Aapka Current Balance:** â‚¹{bal:.2f}", parse_mode="Markdown")

    elif query.data == "start_withdraw":
        if not await is_user_joined(context, user_id):
            await query.message.reply_text(f"âš ï¸ Pehle **Channel 1** (@{FIRST_CHANNEL_USERNAME}) join karein!")
            return

        bal = users_db.get(str_id, {}).get("balance", 0.0)
        if bal < 1.0:
            await query.message.reply_text("âŒ Minimum withdrawal amount **â‚¹1** hai. Aapke paas kaafi balance nahi hai.", parse_mode="Markdown")
            return ConversationHandler.END

        await query.message.reply_text(
            "ðŸ“ Kripya apni payment detail bhejein (jaise Paytm Number, UPI ID, ya Bank Details):"
        )
        return WAITING_FOR_PAYMENT_DETAILS


# Processing Withdrawal Request
async def process_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    str_id = str(user.id)
    details = update.message.text
    bal = users_db.get(str_id, {}).get("balance", 0.0)

    if bal < 1.0:
        await update.message.reply_text("âŒ Aapka balance kam hai.")
        return ConversationHandler.END

    users_db[str_id]["balance"] = bal - 1.0
    save_data(users_db)

    await update.message.reply_text("âœ… Aapki withdrawal request submit ho gayi hai! Jaldi hi process kar di jayegi.")

    admin_text = (
        "ðŸš¨ **NEW WITHDRAWAL REQUEST** ðŸš¨\n\n"
        f"ðŸ‘¤ **User:** {user.full_name} (@{user.username})\n"
        f"ðŸ†” **User ID:** `{user.id}`\n"
        f"ðŸ’° **Amount:** â‚¹1.00\n"
        f"ðŸ’³ **Payment Details:** `{details}`"
    )

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode="Markdown",
        )
    except Exception as e:
        logging.error(f"Failed to send alert to admin: {e}")

    return ConversationHandler.END


# ðŸ“¢ BROADCAST FEATURE (ADMIN ONLY)
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("âŒ Aap admin nahi hain!")
        return ConversationHandler.END

    total_users = len(users_db)
    await update.message.reply_text(
        f"ðŸ“¢ **Broadcast Mode Active**\nTotal Users: `{total_users}`\n\n"
        "Jo message saare members ko bhejna hai, wo yahan bhejein.\nCancel karne ke liye /cancel likhein."
    )
    return WAITING_FOR_BROADCAST_MSG


async def process_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    total_users = len(users_db)
    success = 0
    failed = 0

    status_msg = await update.message.reply_text(f"â³ Broadcast shuru ho raha hai... (0/{total_users})")

    for user_id_str in list(users_db.keys()):
        try:
            await msg.copy(chat_id=int(user_id_str))
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"âœ… **Broadcast Completed!**\n\n"
        f"ðŸŽ¯ Success: `{success}`\n"
        f"âŒ Failed: `{failed}`\n"
        f"ðŸ‘¥ Total Users: `{total_users}`"
    )
    return ConversationHandler.END


# /stats Command
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    total_users = len(users_db)
    await update.message.reply_text(f"ðŸ“Š **Bot Statistics:**\n\nTotal Joined Users: `{total_users}`", parse_mode="Markdown")


# Cancel Handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancel kar diya gaya hai.")
    return ConversationHandler.END


# Main Runner
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    withdraw_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^start_withdraw$")],
        states={
            WAITING_FOR_PAYMENT_DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdrawal)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_chat=True,
    )

    broadcast_handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={
            WAITING_FOR_BROADCAST_MSG: [
                MessageHandler(filters.ALL & ~filters.COMMAND, process_broadcast)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_chat=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(withdraw_handler)
    app.add_handler(broadcast_handler)
    app.add_handler(CallbackQueryHandler(button_handler))

    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        level=logging.INFO,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.info("Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
    
