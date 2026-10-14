import logging
import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from telegram.request import HTTPXRequest

from config import BOT_TOKEN, ADMIN_IDS
from database import db_manager
from handlers import user, admin, broadcast

# Set proxy if explicitly provided in environment variables
http_proxy = os.getenv("HTTP_PROXY")
https_proxy = os.getenv("HTTPS_PROXY")
if http_proxy:
    os.environ["HTTP_PROXY"] = http_proxy
if https_proxy:
    os.environ["HTTPS_PROXY"] = https_proxy

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

    # Conversation handler for Admin Adding Product
    admin_add_prod_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin.start_add_product, pattern="^admin_add_product$")],
        states={
            admin.ADD_PROD_CAT: [CallbackQueryHandler(admin.add_prod_cat_selected, pattern="^cat_")],
            admin.ADD_PROD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_prod_name_entered)],
            admin.ADD_PROD_SPEC: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_prod_spec_entered)],
            admin.ADD_PROD_RAW_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_prod_raw_price_entered)],
            admin.ADD_PROD_TARIFF: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_prod_tariff_entered)],
        },
        fallbacks=[CommandHandler("cancel", admin.cancel_admin_conv)]
    )

    # Conversation handler for Admin Setting Exchange Rate
    admin_set_rate_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin.start_set_rate, pattern="^set_rate_")],
        states={
            admin.SET_CURRENCY_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.set_rate_entered)]
        },
        fallbacks=[CommandHandler("cancel", admin.cancel_admin_conv)]
    )

    # Conversation handler for User Quantity Input in Calculator
    user_calc_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(user.start_calc_product, pattern="^calc_prod_")],
        states={
            user.CALC_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, user.calc_qty_entered)]
        },
        fallbacks=[CommandHandler("cancel", admin.cancel_admin_conv)]
    )

    # Register handlers
    application.add_handler(CommandHandler("start", user.start))
    application.add_handler(CommandHandler("admin", admin.admin_panel))
    application.add_handler(CommandHandler("broadcast", broadcast.broadcast))

    application.add_handler(admin_add_prod_handler)
    application.add_handler(admin_set_rate_handler)
    application.add_handler(user_calc_handler)

    # Callback handlers
    application.add_handler(CallbackQueryHandler(user.set_language_callback, pattern="^set_lang_"))
    application.add_handler(CallbackQueryHandler(user.set_currency_callback, pattern="^set_curr_"))
    application.add_handler(CallbackQueryHandler(user.change_currency_menu, pattern="^user_change_currency$"))
    application.add_handler(CallbackQueryHandler(user.catalog_menu, pattern="^user_catalog$"))
    application.add_handler(CallbackQueryHandler(user.view_category_products, pattern="^cat_user_"))
    application.add_handler(CallbackQueryHandler(user.generate_pdf_callback, pattern="^gen_pdf_"))
    application.add_handler(CallbackQueryHandler(user.main_menu_callback, pattern="^user_main_menu$"))
    application.add_handler(CallbackQueryHandler(user.set_language_callback, pattern="^user_change_lang$"))

    # Admin Callback handlers
    application.add_handler(CallbackQueryHandler(admin.admin_panel, pattern="^admin_back$"))
    application.add_handler(CallbackQueryHandler(admin.list_products_admin, pattern="^admin_list_products$"))
    application.add_handler(CallbackQueryHandler(admin.delete_product_handler, pattern="^del_prod_"))
    application.add_handler(CallbackQueryHandler(admin.view_rates_admin, pattern="^admin_rates$"))
    application.add_handler(CallbackQueryHandler(admin.view_orders_admin, pattern="^admin_orders$"))
    application.add_handler(CallbackQueryHandler(admin.admin_broadcast_prompt, pattern="^admin_broadcast$"))

    logger.info("Steel Export Bot initialized successfully.")

if __name__ == "__main__":
    main()
