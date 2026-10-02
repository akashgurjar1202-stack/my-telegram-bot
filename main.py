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
    ChatJoinRequestHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from broadcast import get_broadcast_handler

# ---------------- FLASK KEEP-ALIVE SERVER ----------------
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
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 7213470918))

START_PHOTO = "https://t.me/aaaafghjvx/13"
FIRST_CHANNEL_USERNAME = "RyanLoots"

WAITING_FOR_PAYMENT_DETAILS = 1
DB_FILE = "users_data.json"
db_lock = asyncio.Lock()


def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}


def save_data(data):
    temp_file = f"{DB_FILE}.tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    os.replace(temp_file, DB_FILE)


def register_user(user_id, username=None):
    users_db = load_data()
    str_id = str(user_id)
    if str_id not in users_db:
        users_db[str_id] = {
            "balance": 0.0,
            "username": username,
            "referred_by": None,
            "is_verified": False,
            "has_requested_join": False
        }
        save_data(users_db)


async def is_user_joined(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    str_id = str(user_id)
    
    # 1. Public Channel Check
    try:
        member = await context.bot.get_chat_member(chat_id=f"@{FIRST_CHANNEL_USERNAME}", user_id=user_id)
        is_public_ok = member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"Public channel check error: {e}")
        is_public_ok = True

    # 2. Private Channel Request Check
    async with db_lock:
        users_db = load_data()
        is_request_ok = users_db.get(str_id, {}).get("has_requested_join", False)

    return is_public_ok and is_request_ok


# Chat Join Request Handler
async def track_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request = update.chat_join_request
    user_id = request.from_user.id
    str_id = str(user_id)

    async with db_lock:
        users_db = load_data()
        if str_id not in users_db:
            register_user(user_id, request.from_user.username)
            users_db = load_data()
        
        users_db[str_id]["has_requested_join"] = True
        save_data(users_db)


def get_main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔗 Generate Invite Link", callback_data="get_invite")
        ],
        [
            InlineKeyboardButton("💰 Check Balance", callback_data="check_balance"),
            InlineKeyboardButton("💸 Withdraw ₹10", callback_data="start_withdraw")
        ]
    ])


# ---------------- 12 CHANNEL BUTTONS KEYBOARD ----------------
def get_channels_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Channel 1 ✨", url="https://t.me/+SdK1d0-scTFhMzA1"),
            InlineKeyboardButton("Channel 2 ✨", url="https://t.me/+y8wdkiMoBwpiNmZl")
        ],
        [
            InlineKeyboardButton("Channel 3 ✨", url="https://t.me/Gift_Codes_on"),
            InlineKeyboardButton("Channel 4 ✨", url="https://t.me/+N0Dc5UOJwY41YTE1")
        ],
        [
            InlineKeyboardButton("Channel 5 ✨", url="https://t.me/your_channel_5"),
            InlineKeyboardButton("Channel 6 ✨", url="https://t.me/your_channel_6")
        ],
        [
            InlineKeyboardButton("Channel 7 ✨", url="https://t.me/your_channel_7"),
            InlineKeyboardButton("Channel 8 ✨", url="https://t.me/your_channel_8")
        ],
        [
            InlineKeyboardButton("Channel 9 ✨", url="https://t.me/your_channel_9"),
            InlineKeyboardButton("Channel 10 ✨", url="https://t.me/your_channel_10")
        ],
        [
            InlineKeyboardButton("Channel 11 ✨", url="https://t.me/your_channel_11"),
            InlineKeyboardButton("Channel 12 ✨", url="https://t.me/your_channel_12")
        ],
        [
            InlineKeyboardButton("🔒 Claim Reward", callback_data="check_joined")
        ]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    str_id = str(user.id)
    
    async with db_lock:
        users_db = load_data()
        is_new = str_id not in users_db
        register_user(user.id, user.username)

        if is_new and context.args:
            referrer_id = str(context.args[0])
            users_db = load_data()
            if referrer_id != str_id and referrer_id in users_db:
                users_db[str_id]["referred_by"] = referrer_id
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
        "⚠️ <b>Aage badhne ke liye sabse pehle niche diye gaye Channels ko join/request karein!</b>"
    )

    keyboard = get_channels_keyboard()

    try:
        await update.message.reply_photo(
            photo=START_PHOTO,
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


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    str_id = str(user_id)
    bot_info = await context.bot.get_me()

    async with db_lock:
        users_db = load_data()
        if str_id not in users_db:
            register_user(user_id, query.from_user.username)
            users_db = load_data()

    if query.data == "check_joined":
        # Check karna ki user ne join/request kiya hai ya nahi
        if not await is_user_joined(context, user_id):
            not_joined_msg = (
                "❌ <b>Aapne abhi tak sabhi channels join nahi kiye hain!</b>\n\n"
                "⚠️ Reward claim karne ke liye pehle uper diye gaye sabhi channels par Join / Request to Join karein, phir se Claim Reward par click karein."
            )
            # User ko chat mein message bhejna
            await query.message.reply_text(
                text=not_joined_msg,
                parse_mode="HTML",
                reply_markup=get_channels_keyboard()
            )
            return

        async with db_lock:
            users_db = load_data()
            users_db[str_id]["is_verified"] = True
            save_data(users_db)

        await query.answer("🔓 Verification Successful!", show_alert=True)
        
        await query.message.reply_text(
            "✅ <b>Verification Successful!</b>\n\nAb aap niche diye gaye features use kar sakte hain:",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )

    elif query.data == "get_invite":
        invite_link = f"https://t.me/{bot_info.username}?start={user_id}"
        msg = f"🔗 <b>Aapka Personal Invite Link:</b>\n<code>{invite_link}</code>\n\nIs link ko apne dosto ko bhejein aur har refer par ₹2 kamayein!"
        share_text = f"🎁 Is bot se har refer par ₹2 kamayein! Abhi join karein:\n{invite_link}"

        sub_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 Share Link To Friends", switch_inline_query=share_text)],
            [
                InlineKeyboardButton("💰 Check Balance", callback_data="check_balance"),
                InlineKeyboardButton("💸 Withdraw ₹10", callback_data="start_withdraw"),
            ]
        ])
        await query.message.reply_text(msg, parse_mode="HTML", reply_markup=sub_keyboard)

    elif query.data == "check_balance":
        async with db_lock:
            users_db = load_data()
            bal = users_db.get(str_id, {}).get("balance", 0.0)
        await query.message.reply_text(f"💰 <b>Aapka Current Balance:</b> ₹{bal:.2f}", parse_mode="HTML")


async def start_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    str_id = str(user_id)

    async with db_lock:
        users_db = load_data()
        bal = users_db.get(str_id, {}).get("balance", 0.0)

    if bal < 10.0:
        await query.message.reply_text("❌ Minimum withdrawal amount <b>₹10</b> hai. Aapke paas kaafi balance nahi hai.", parse_mode="HTML")
        return ConversationHandler.END

    await query.message.reply_text("📝 Kripya apni payment detail bhejein (Paytm Number / UPI ID):")
    return WAITING_FOR_PAYMENT_DETAILS


async def process_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    str_id = str(user.id)
    details = update.message.text

    async with db_lock:
        users_db = load_data()
        bal = users_db.get(str_id, {}).get("balance", 0.0)

        if bal < 10.0:
            await update.message.reply_text("❌ Aapka balance kam hai.")
            return ConversationHandler.END

        users_db[str_id]["balance"] = bal - 10.0
        save_data(users_db)

    await update.message.reply_text("✅ Aapki withdrawal request submit ho gayi hai!")

    admin_text = (
        "🚨 <b>NEW WITHDRAWAL REQUEST</b> 🚨\n\n"
        f"👤 <b>User:</b> {user.full_name} (@{user.username})\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"💰 <b>Amount:</b> ₹10.00\n"
        f"💳 <b>Payment Details:</b> <code>{details}</code>"
    )

    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Failed sending alert: {e}")

    return ConversationHandler.END


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if int(update.effective_user.id) != int(ADMIN_ID):
        return
    async with db_lock:
        users_db = load_data()
    await update.message.reply_text(f"📊 <b>Bot Statistics:</b>\n\nTotal Joined Users: <code>{len(users_db)}</code>", parse_mode="HTML")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancel kar diya gaya hai.")
    return ConversationHandler.END


def main():
    keep_alive()

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN Environment Variable missing!")

    app = Application.builder().token(BOT_TOKEN).build()
    app.bot_data["ADMIN_ID"] = ADMIN_ID

    withdraw_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_withdraw, pattern="^start_withdraw$")],
        states={
            WAITING_FOR_PAYMENT_DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdrawal)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    
    app.add_handler(ChatJoinRequestHandler(track_join_request))

    app.add_handler(withdraw_handler)
    app.add_handler(get_broadcast_handler())
    app.add_handler(CallbackQueryHandler(button_handler))

    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        level=logging.INFO,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.info("Bot started successfully...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
