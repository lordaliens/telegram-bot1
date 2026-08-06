import urllib.parse
import httpx
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def get_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    if not user_text:
        return

    if user_text == "ربات هواشناسی":
        await update.message.reply_text("بله")
        return

    # Check if the user is replying to a previous message from the bot that says "بله"
    is_reply_to_bot = (
        update.message.reply_to_message and
        update.message.reply_to_message.from_user and
        update.message.reply_to_message.from_user.id == context.bot.id and
        update.message.reply_to_message.text == "بله"
    )

    if not is_reply_to_bot:
        return

    encoded_city = urllib.parse.quote(user_text)
    url = f"https://wttr.in/{encoded_city}?format=3"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers={"User-Agent": "curl/7.68.0"})
            response.raise_for_status()
            weather_data = response.text.strip()

            if weather_data:
                await update.message.reply_text(weather_data)
            else:
                await update.message.reply_text("Could not fetch weather data for that city.")
    except Exception as e:
        logger.error(f"Error fetching weather for {user_text}: {e}")
        await update.message.reply_text("An error occurred while fetching the weather. Please check the city name and try again.")
