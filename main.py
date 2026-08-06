import logging
import os
import asyncio
import google.generativeai as genai

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

from config import BOT_TOKEN, CHANNEL_USERNAME, GEMINI_API_KEY, ADMIN_IDS
from database import db_manager

# Proxy setup (from existing code)
# os.environ["HTTP_PROXY"] = "http://127.0.0.1:7897"
# os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7897"

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Generation config for Gemini
generation_config = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 50,
    "max_output_tokens": 1024,
}

SYSTEM_PROMPT = """شما یک ربات تلگرامی صمیمی، دوستانه و باهوش هستید.
شما به زبان فارسی صحبت می‌کنید. هدف شما این است که با کاربر ارتباطی نزدیک و گرم برقرار کنید.
به مرور در لابلای صحبت‌هایتان، کاربر را ترغیب کنید که برای مطالب بیشتر و جذاب‌تر به کانال تلگرام ما بپیوندد.
سعی کنید پاسخ‌هایتان کوتاه، جذاب و مانند یک انسان واقعی باشد.
همیشه آماده کمک به کاربر هستید."""

async def get_gemini_response(user_id: int, text: str) -> str:
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            system_instruction=SYSTEM_PROMPT
        )

        # Get history from DB
        history = await db_manager.get_history(user_id)

        # Convert history format for Gemini
        gemini_history = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg["content"]]})

        chat = model.start_chat(history=gemini_history)
        response = await asyncio.to_thread(chat.send_message, text)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        return "ببخشید، الان یه مشکلی پیش اومده. میشه یکم بعد دوباره امتحان کنی؟ 🙏"

async def check_channel_membership(bot, user_id: int) -> bool:
    if not CHANNEL_USERNAME:
        return True
    try:
        member = await bot.get_chat_member(f"@{CHANNEL_USERNAME.lstrip('@')}", user_id)
        return member.status not in ['left', 'kicked']
    except Exception as e:
        logger.error(f"Error checking chat member for {user_id}: {e}")
        # If the bot is not admin or channel doesn't exist, allow it to pass gracefully
        return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    await db_manager.add_user(user_id)

    welcome_text = (
        f"سلام {user.first_name} عزیز! 👋\n\n"
        "من اینجا هستم تا با هم گپ بزنیم و بهت کمک کنم. هر سوالی داری یا دوست داری در مورد چیزی صحبت کنیم، برام بنویس!"
    )
    await update.message.reply_text(welcome_text)

    # We do NOT add the welcome text to history, because Gemini requires the first message in history to be from the 'user' role.

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    text = update.message.text

    # Ensure user exists
    await db_manager.add_user(user_id)

    # Increment and get message count
    await db_manager.increment_message_count(user_id)
    msg_count = await db_manager.get_message_count(user_id)

    # Force Join Funnel logic
    if msg_count > 10:
        is_member = await check_channel_membership(context.bot, user_id)
        if not is_member:
            await db_manager.set_pending_message(user_id, text)

            keyboard = [
                [InlineKeyboardButton("عضویت در کانال 📢", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
                [InlineKeyboardButton("بررسی عضویت ✅", callback_data="check_join")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "دوست عزیز، برای ادامه گپ و گفتمون و استفاده از امکانات بیشتر، لطفا اول توی کانال ما عضو شو. 😉👇",
                reply_markup=reply_markup
            )
            return

    # Process message with Gemini
    # Send "typing" action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    response_text = await get_gemini_response(user_id, text)
    # Save both user and model messages to DB AFTER the API call
    await db_manager.add_history(user_id, "user", text)
    await db_manager.add_history(user_id, "model", response_text)

    await update.message.reply_text(response_text)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id

    await query.answer()

    if query.data == "check_join":
        is_member = await check_channel_membership(context.bot, user_id)

        if is_member:
            await query.edit_message_text("ممنون که عضو شدی! 😍 حالا می‌تونیم به گفتگومون ادامه بدیم.")

            pending_msg = await db_manager.get_pending_message(user_id)
            if pending_msg:
                await db_manager.clear_pending_message(user_id)

                await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

                response_text = await get_gemini_response(user_id, pending_msg)
                # Save both messages to DB after the API call
                await db_manager.add_history(user_id, "user", pending_msg)
                await db_manager.add_history(user_id, "model", response_text)

                await context.bot.send_message(chat_id=user_id, text=response_text)
        else:
            keyboard = [
                [InlineKeyboardButton("عضویت در کانال 📢", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
                [InlineKeyboardButton("بررسی عضویت ✅", callback_data="check_join")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "هنوز که عضو نشدی! 🤔 لطفا اول از طریق دکمه زیر عضو شو و بعد دکمه بررسی رو بزن.",
                reply_markup=reply_markup
            )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("شما دسترسی لازم برای این دستور را ندارید.")
        return

    if not update.message.reply_to_message and not context.args:
        await update.message.reply_text("لطفا به یک پیام ریپلای کنید یا متن پیام را وارد کنید.")
        return

    users = await db_manager.get_all_users()
    success_count = 0
    fail_count = 0

    message_to_send = None
    if update.message.reply_to_message:
         pass
    elif context.args:
         message_to_send = update.message.text.partition(' ')[2]

    await update.message.reply_text(f"در حال ارسال به {len(users)} کاربر...")

    for uid in users:
        try:
            if update.message.reply_to_message:
                await update.message.reply_to_message.copy(uid)
            else:
                await context.bot.send_message(chat_id=uid, text=message_to_send)
            success_count += 1
        except Exception as e:
            logger.warning(f"Failed to send broadcast to {uid}: {e}")
            fail_count += 1

        await asyncio.sleep(0.05)

    await update.message.reply_text(f"ارسال پیام به پایان رسید!\nموفق: {success_count}\nناموفق: {fail_count}")

async def post_init(application: Application):
    logger.info("Initializing database...")
    await db_manager.init_db()
    logger.info("Database initialized.")

def main():
    if not BOT_TOKEN:
        logger.error("No BOT_TOKEN provided in .env file.")
        return

    if not GEMINI_API_KEY:
        logger.error("No GEMINI_API_KEY provided in .env file.")
        return

    request_config = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0
    )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .request(request_config)
        .get_updates_request(request_config)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("Starting bot...")
    application.run_polling()

if __name__ == "__main__":
    main()
