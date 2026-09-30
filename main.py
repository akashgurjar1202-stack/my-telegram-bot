import logging
import json
import os
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

# Import separate broadcast module
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
            "is_verified": False
        }
        save_data(users_db)


async def is_user_joined(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=f"@{FIRST_CHANNEL_USERNAME}", user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return True


# Helper function: Feature Menu Buttons (Jo verification ke baad dikhenge)
def get_main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔗 Generate/Get Invite Link", callback_data="get_invite")
        ],
        [
            InlineKeyboardButton("💰 Check Balance", callback_data="check_balance"),
            InlineKeyboardButton("💸 Withdrawal ₹10", callback_data="start_withdraw")
        ]
    ])


# /start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    str_id = str(user.id)
    
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

    users_db = load_data()
    is_verified = users_db.get(str_id, {}).get("is_verified", False)

    # Agar user pehle se verified hai toh direct main menu dikhao
    if is_verified:
        await update.message.reply_text(
            "🎉 <b>WELCOME BACK!</b>\n\nAapka account verified hai. Niche diye gaye options use karein:",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        return

    welcome_text = (
        "🎉 <b>WELCOME TO REFER & EARN BOT</b> 🎉\n\n"
        "📢 <b>Offer Details:</b>\n"
        "🎁 <b>Per Refer:</b> ₹2\n"
        "💳 <b>Minimum Withdrawal:</b> ₹10\n\n"
        "⚠️ <b>Aage badhne ke liye sabse pehle niche diye gaye Channels ko join karein!</b>"
    )

    # Sirf Join buttons aur Claim button dikhao
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Join ✨", url="https://t.me/+SdK1d0-scTFhMzA1"),
            InlineKeyboardButton("Join ✨", url="https://t.me/+y8wdkiMoBwpiNmZl")
        ],
        [
            InlineKeyboardButton("Join ✨", url="https://t.me/Gift_Codes_on"),
            InlineKeyboardButton("Join ✨", url="https://t.me/+N0Dc5UOJwY41YTE1")
        ],
        [
            InlineKeyboardButton("Join ✨", url="https://t.me/Gift_Codes_on"),
            InlineKeyboardButton("Join ✨", url="https://t.me/+N0Dc5UOJwY41YTE1")
        ],
        [
            InlineKeyboardButton("Join ✨", url="https://t.me/+SdK1d0-scTFhMzA1"),
            InlineKeyboardButton("Join ✨", url="https://t.me/+y8wdkiMoBwpiNmZl")
        ],
        [
            InlineKeyboardButton("Join ✨", url="https://t.me/Gift_Codes_on"),
            InlineKeyboardButton("Join ✨", url="https://t.me/+N0Dc5UOJwY41YTE1")
        ],
        [
            InlineKeyboardButton("Join ✨", url="https://t.me/Gift_Codes_on"),
            InlineKeyboardButton("Join ✨", url="https://t.me/+N0Dc5UOJwY41YTE1")
        ],
        [
            InlineKeyboardButton("🔒 Claim", callback_data="check_joined")
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


# Callback Query Handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    str_id = str(user_id)
    bot_info = await context.bot.get_me()
    users_db = load_data()

    if str_id not in users_db:
        register_user(user_id, query.from_user.username)
        users_db = load_data()

    if query.data == "check_joined":
        if not await is_user_joined(context, user_id):
            await query.answer("⚠️ Pehle saare Channels join karein tabhi claim unlock hoga!", show_alert=True)
            return

        users_db[str_id]["is_verified"] = True
        save_data(users_db)
        await query.answer("🔓 Verification Successful!", show_alert=True)
        
        # Verification ke baad Invite Link, Balance aur Withdrawal buttons ka menu bhejein
        await query.message.reply_text(
            "✅ <b>Verification Successful!</b>\n\nAb aap Refer, Check Balance, aur Withdraw kar sakte hain:",
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
                InlineKeyboardButton("💸 Withdrawal ₹10", callback_data="start_withdraw"),
            ]
        ])
        await query.message.reply_text(msg, parse_mode="HTML", reply_markup=sub_keyboard)

    elif query.data == "check_balance":
        bal = users_db.get(str_id, {}).get("balance", 0.0)
        await query.message.reply_text(f"💰 <b>Aapka Current Balance:</b> ₹{bal:.2f}", parse_mode="HTML")


# Withdrawal Process
async def start_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    str_id = str(user_id)
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
    users_db = load_data()
    await update.message.reply_text(f"📊 <b>Bot Statistics:</b>\n\nTotal Joined Users: <code>{len(users_db)}</code>", parse_mode="HTML")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancel kar diya gaya hai.")
    return ConversationHandler.END


# Main Application
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
    app.add_handler(withdraw_handler)
    
    # Broadcast handler register from broadcast.py
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
        
