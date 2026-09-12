import logging
import json
import os
import asyncio
from threading import Thread
from flask import Flask
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

# ---------------- DUMMY FLASK SERVER FOR RENDER ----------------
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8737434171:AAEuADW_NUm2DEfGb68VVAc1Sik3grl_7YE")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 7213470918))

START_PHOTO = "https://t.me/aaaafghjvx/13"
FIRST_CHANNEL_USERNAME = "RyanLoots"

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
            
            # Credit ₹2 to referrer
            ref_bal = users_db[referrer_id].get("balance", 0.0)
            users_db[referrer_id]["balance"] = ref_bal + 2.0
            save_data(users_db)

            try:
                await context.bot.send_message(
                    chat_id=int(referrer_id),
                    text=f"🎉 <b>Naya Refer!</b>\nUser ({user.full_name}) aapke link se juda. Aapko <b>₹2.00</b> mil gaye hain!",
                    parse_mode="HTML"
                )
            except Exception:
                pass

    welcome_text = (
        "🎉 <b>WELCOME TO REFER & EARN BOT</b> 🎉\n\n"
        "📢 <b>Offer Details:</b>\n"
        "🎁 <b>Per Refer:</b> ₹2\n"
        "💳 <b>Minimum Withdrawal:</b> ₹10\n\n"
        "⚠️ <b>Aage badhne ke liye sabse pehle niche diye gaye Channels ko join karein!</b>"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Channel 1", url="https://t.me/+SdK1d0-scTFhMzA1"),
            InlineKeyboardButton("📢 Channel 2", url="https://t.me/+y8wdkiMoBwpiNmZl")
        ],
        [
            InlineKeyboardButton("📢 Channel 3", url="https://t.me/Gift_Codes_on"),
            InlineKeyboardButton("📢 Channel 4", url="https://t.me/+N0Dc5UOJwY41YTE1")
        ],
        [
            InlineKeyboardButton("✅ Joined All Channels", callback_data="check_joined")
        ],
        [
            InlineKeyboardButton("🔗 Generate/Get Invite Link", callback_data="get_invite")
        ],
        [
            InlineKeyboardButton("💰 Check Balance", callback_data="check_balance"),
            InlineKeyboardButton("💸 Withdrawal ₹10", callback_data="start_withdraw")
        ]
    ])

    try:
        if START_PHOTO.startswith("http://") or START_PHOTO.startswith("https://"):
            await update.message.reply_photo(
                photo=START_PHOTO,
                caption=welcome_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        else:
            with open(START_PHOTO, "rb") as photo_file:
                await update.message.reply_photo(
                    photo=photo_file,
                    caption=welcome_text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
    except Exception:
        await update.message.reply_text(
            text=welcome_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )


# General Callback Buttons Handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    str_id = str(user_id)
    bot_info = await context.bot.get_me()

    if query.data == "check_joined":
        if not await is_user_joined(context, user_id):
            await query.message.reply_text(f"⚠️ Pehle <b>Channel 1</b> (@{FIRST_CHANNEL_USERNAME}) join karein!", parse_mode="HTML")
            return
        await query.message.reply_text("✅ Verification successful! Aap bot use kar sakte hain.")

    elif query.data == "get_invite":
        if not await is_user_joined(context, user_id):
            await query.message.reply_text(f"⚠️ Pehle <b>Channel 1</b> (@{FIRST_CHANNEL_USERNAME}) join karein!", parse_mode="HTML")
            return

        invite_link = f"https://t.me/{bot_info.username}?start={user_id}"
        msg = f"🔗 <b>Aapka Personal Invite Link:</b>\n<code>{invite_link}</code>\n\nIs link ko apne dosto ko bhejein aur har refer par ₹2 kamayein!"
        share_text = f"🎁 Is bot se har refer par ₹2 kamayein! Abhi join karein:\n{invite_link}"

        sub_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📱 Share Link To Friends", switch_inline_query=share_text)
            ],
            [
                InlineKeyboardButton("💰 Check Balance", callback_data="check_balance"),
                InlineKeyboardButton("💸 Withdrawal ₹10", callback_data="start_withdraw"),
            ]
        ])
        await query.message.reply_text(msg, parse_mode="HTML", reply_markup=sub_keyboard)

    elif query.data == "check_balance":
        if not await is_user_joined(context, user_id):
            await query.message.reply_text(f"⚠️ Pehle <b>Channel 1</b> (@{FIRST_CHANNEL_USERNAME}) join karein!", parse_mode="HTML")
            return

        bal = users_db.get(str_id, {}).get("balance", 0.0)
        await query.message.reply_text(f"💰 <b>Aapka Current Balance:</b> ₹{bal:.2f}", parse_mode="HTML")


# Entry point for Withdrawal Conversation
async def start_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    str_id = str(user_id)

    if not await is_user_joined(context, user_id):
        await query.message.reply_text(f"⚠️ Pehle <b>Channel 1</b> (@{FIRST_CHANNEL_USERNAME}) join karein!", parse_mode="HTML")
        return ConversationHandler.END

    bal = users_db.get(str_id, {}).get("balance", 0.0)
    if bal < 10.0:
        await query.message.reply_text("❌ Minimum withdrawal amount <b>₹10</b> hai. Aapke paas kaafi balance nahi hai.", parse_mode="HTML")
        return ConversationHandler.END

    await query.message.reply_text(
        "📝 Kripya apni payment detail bhejein (jaise Paytm Number, UPI ID, ya Bank Details):"
    )
    return WAITING_FOR_PAYMENT_DETAILS


# Processing Withdrawal Request
async def process_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    str_id = str(user.id)
    details = update.message.text
    bal = users_db.get(str_id, {}).get("balance", 0.0)

    if bal < 10.0:
        await update.message.reply_text("❌ Aapka balance kam hai.")
        return ConversationHandler.END

    users_db[str_id]["balance"] = bal - 10.0
    save_data(users_db)

    await update.message.reply_text("✅ Aapki withdrawal request submit ho gayi hai! Jaldi hi process kar di jayegi.")

    admin_text = (
        "🚨 <b>NEW WITHDRAWAL REQUEST</b> 🚨\n\n"
        f"👤 <b>User:</b> {user.full_name} (@{user.username})\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"💰 <b>Amount:</b> ₹10.00\n"
        f"💳 <b>Payment Details:</b> <code>{details}</code>"
    )

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode="HTML",
        )
    except Exception as e:
        logging.error(f"Failed to send alert to admin: {e}")

    return ConversationHandler.END


# BROADCAST FEATURE (ADMIN ONLY)
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Aap admin nahi hain!")
        return ConversationHandler.END

    total_users = len(users_db)
    await update.message.reply_text(
        f"📢 <b>Broadcast Mode Active</b>\nTotal Users: <code>{total_users}</code>\n\n"
        "Jo message saare members ko bhejna hai, wo yahan bhejein.\nCancel karne ke liye /cancel likhein.",
        parse_mode="HTML"
    )
    return WAITING_FOR_BROADCAST_MSG


async def process_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    total_users = len(users_db)
    success = 0
    failed = 0

    status_msg = await update.message.reply_text(f"⏳ Broadcast shuru ho raha hai... (0/{total_users})")

    for user_id_str in list(users_db.keys()):
        try:
            await msg.copy(chat_id=int(user_id_str))
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"✅ <b>Broadcast Completed!</b>\n\n"
        f"🎯 Success: <code>{success}</code>\n"
        f"❌ Failed: <code>{failed}</code>\n"
        f"👥 Total Users: <code>{total_users}</code>",
        parse_mode="HTML"
    )
    return ConversationHandler.END


# /stats Command
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    total_users = len(users_db)
    await update.message.reply_text(f"📊 <b>Bot Statistics:</b>\n\nTotal Joined Users: <code>{total_users}</code>", parse_mode="HTML")


# Cancel Handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancel kar diya gaya hai.")
    return ConversationHandler.END


# Main Runner
def main():
    keep_alive()

    app = Application.builder().token(BOT_TOKEN).build()

    withdraw_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_withdraw, pattern="^start_withdraw$")],
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
        
