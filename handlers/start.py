from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from database import db_manager
from config import CHANNEL_USERNAME

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    args = context.args

    # Check if user is in channel
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['left', 'kicked']:
            keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Please join our channel before using this bot!",
                reply_markup=reply_markup
            )
            return
    except Exception as e:
        logger.error(f"Error checking chat member for {user_id}: {e}")
        # Be careful here: if the bot is not admin in the channel, it will fail to get member status.
        pass
        
    # Process referral
    referrer_id = None
    if args:
        try:
            referrer_id = int(args[0])
            if referrer_id == user_id:
                referrer_id = None # Can't refer yourself
        except ValueError:
            pass

    # Add user
    added = await db_manager.add_user(user_id, referrer_id)
    if added and referrer_id:
        try:
             await context.bot.send_message(chat_id=referrer_id, text=f"Someone joined using your referral link!")
        except Exception as e:
             logger.error(f"Could not notify referrer {referrer_id}: {e}")

    bot_username = context.bot.username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    ref_count = await db_manager.get_referral_count(user_id)

    welcome_msg = (
        f"Welcome {user.first_name}!\n\n"
        f"Your referral link: {referral_link}\n"
        f"You have referred {ref_count} users."
    )
    
    await update.message.reply_text(welcome_msg)
