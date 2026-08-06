import logging
import os
from telegram.ext import Application, CommandHandler
from telegram.request import HTTPXRequest
from config import BOT_TOKEN
from database import db_manager
from handlers import start, broadcast

# ست کردن پروکسی Clash Verge برای کل پروژه پایتون (سازگار با همه نسخه‌ها)
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7897"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7897"

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def post_init(application: Application):
    logger.info("Initializing database...")
    await db_manager.init_db()
    logger.info("Database initialized.")

def main():
    if not BOT_TOKEN:
        logger.error("No BOT_TOKEN provided in .env file.")
        return

    # تنظیم افزایش مهلت اتصال (Timeout)
    request_config = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0
    )

    # ساخت ربات
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .request(request_config)
        .get_updates_request(request_config)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start.start))
    application.add_handler(CommandHandler("broadcast", broadcast.broadcast))

    logger.info("Starting bot...")
    application.run_polling()

if __name__ == "__main__":
    main()