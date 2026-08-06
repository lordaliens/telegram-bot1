import urllib.parse
import httpx
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def get_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text.strip()
    if not city:
        return

    encoded_city = urllib.parse.quote(city)
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
        logger.error(f"Error fetching weather for {city}: {e}")
        await update.message.reply_text("An error occurred while fetching the weather. Please check the city name and try again.")
