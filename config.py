import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(",") if admin_id.strip().isdigit()]
