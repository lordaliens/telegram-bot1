from telegram import Update
from telegram.ext import ContextTypes
import logging
import asyncio

from database import db_manager
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not update.message.reply_to_message and not context.args:
        await update.message.reply_text("Please reply to a message or provide text to broadcast.")
        return

    users = await db_manager.get_all_users()
    success_count = 0
    fail_count = 0

    message_to_send = None
    if update.message.reply_to_message:
         pass 
    elif context.args:
         message_to_send = update.message.text.partition(' ')[2]

    await update.message.reply_text(f"Broadcasting to {len(users)} users...")

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
        
        # Rate limit to avoid Telegram API errors
        await asyncio.sleep(0.05)

    await update.message.reply_text(f"Broadcast complete!\nSuccess: {success_count}\nFailed: {fail_count}")
