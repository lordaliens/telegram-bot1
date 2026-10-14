import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "")
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(",") if admin_id.strip().isdigit()]

SUPPORTED_LANGUAGES = {
    'fa': '🇮🇷 فارسی',
    'en': '🇬🇧 English',
    'ar': '🇸🇦 العربية',
    'ku': '☀️ کوردی (سورانی)',
    'ru': '🇷🇺 Русский',
    'ps': '🇦🇫 پښتو / دری',
    'ka': '🇬🇪 ქართული'
}

SUPPORTED_CURRENCIES = {
    'USD': '$ USD',
    'IQD': 'IQD (دینار)',
    'GEL': 'GEL (لاری)',
    'TJS': 'TJS (سامانی)',
    'AFN': 'AFN (افغانی)',
    'IRR': 'IRR (تومان/ریال)'
}
