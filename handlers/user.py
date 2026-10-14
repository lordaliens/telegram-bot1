from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import logging
import os

from database import db_manager
from config import SUPPORTED_LANGUAGES, SUPPORTED_CURRENCIES
from i18n import get_text
from pdf_generator import generate_invoice_pdf

logger = logging.getLogger(__name__)

# Conversation states for user calculator
CALC_QTY = 1

def build_main_keyboard(lang='fa'):
    keyboard = [
        [InlineKeyboardButton(get_text('menu_catalog', lang), callback_data="user_catalog")],
        [InlineKeyboardButton(get_text('menu_calc', lang), callback_data="user_calc")],
        [InlineKeyboardButton(get_text('menu_currency', lang), callback_data="user_change_currency")],
        [InlineKeyboardButton(get_text('menu_lang', lang), callback_data="user_change_lang")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    db_user = await db_manager.get_user(user_id)
    if not db_user:
        # Prompt language selection on first start
        keyboard = []
        for code, label in SUPPORTED_LANGUAGES.items():
            keyboard.append([InlineKeyboardButton(label, callback_data=f"set_lang_{code}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            get_text('select_lang', 'en'),
            reply_markup=reply_markup
        )
        return

    lang = db_user.get('language', 'fa')
    welcome_msg = get_text('welcome', lang, name=user.first_name)
    await update.message.reply_text(welcome_msg, reply_markup=build_main_keyboard(lang))

async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    lang_code = query.data.replace("set_lang_", "")

    db_user = await db_manager.get_user(user_id)
    if not db_user:
        await db_manager.add_user(user_id, language=lang_code)
    else:
        await db_manager.update_user_language(user_id, lang_code)

    welcome_msg = get_text('welcome', lang_code, name=query.from_user.first_name)
    await query.message.edit_text(welcome_msg, reply_markup=build_main_keyboard(lang_code))

async def change_currency_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db_user = await db_manager.get_user(user_id)
    lang = db_user.get('language', 'fa') if db_user else 'fa'

    keyboard = []
    for code, label in SUPPORTED_CURRENCIES.items():
        keyboard.append([InlineKeyboardButton(label, callback_data=f"set_curr_{code}")])
    keyboard.append([InlineKeyboardButton("🔙", callback_data="user_main_menu")])

    await query.message.edit_text(get_text('select_currency_prompt', lang), reply_markup=InlineKeyboardMarkup(keyboard))

async def set_currency_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    curr_code = query.data.replace("set_curr_", "")

    await db_manager.update_user_currency(user_id, curr_code)
    db_user = await db_manager.get_user(user_id)
    lang = db_user.get('language', 'fa') if db_user else 'fa'

    await query.message.edit_text(
        get_text('currency_selected', lang, currency=curr_code),
        reply_markup=build_main_keyboard(lang)
    )

async def catalog_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db_user = await db_manager.get_user(user_id)
    lang = db_user.get('language', 'fa') if db_user else 'fa'

    keyboard = [
        [InlineKeyboardButton(get_text('sheets', lang), callback_data="cat_user_sheets")],
        [InlineKeyboardButton(get_text('rebars', lang), callback_data="cat_user_rebars")],
        [InlineKeyboardButton(get_text('ibeams', lang), callback_data="cat_user_ibeams")],
        [InlineKeyboardButton("🔙", callback_data="user_main_menu")]
    ]
    await query.message.edit_text(get_text('select_category', lang), reply_markup=InlineKeyboardMarkup(keyboard))

async def view_category_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    category = query.data.replace("cat_user_", "")

    db_user = await db_manager.get_user(user_id)
    lang = db_user.get('language', 'fa') if db_user else 'fa'
    user_curr = db_user.get('currency', 'USD') if db_user else 'USD'

    products = await db_manager.get_products(category=category)
    rate = await db_manager.get_exchange_rate(user_curr)

    if not products:
        await query.message.edit_text(
            get_text('no_products', lang),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="user_catalog")]])
        )
        return

    text = f"📦 **{get_text('menu_catalog', lang)} ({category})**\n\n"
    keyboard = []
    for p in products:
        final_usd = p['raw_price_usd'] * (1 + p['tariff_percent'] / 100.0)
        final_in_curr = final_usd * rate

        text += (
            f"🔹 **{p['name']}**\n"
            f"   {get_text('product_detail', lang, name=p['name'], spec=p['specification'], unit=p['unit'], price=f'{final_in_curr:,.2f}', currency=user_curr)}\n\n"
        )
        keyboard.append([InlineKeyboardButton(f"🧮 {p['name']}", callback_data=f"calc_prod_{p['id']}")])

    keyboard.append([InlineKeyboardButton("🔙", callback_data="user_catalog")])
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def start_calc_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    prod_id = int(query.data.replace("calc_prod_", ""))

    db_user = await db_manager.get_user(user_id)
    lang = db_user.get('language', 'fa') if db_user else 'fa'

    product = await db_manager.get_product(prod_id)
    if not product:
        await query.message.edit_text("Product not found.")
        return ConversationHandler.END

    context.user_data['calc_prod_id'] = prod_id
    context.user_data['calc_prod'] = product

    await query.message.edit_text(
        get_text('enter_quantity', lang, unit=product['unit'])
    )
    return CALC_QTY

async def calc_qty_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = await db_manager.get_user(user_id)
    lang = db_user.get('language', 'fa') if db_user else 'fa'
    user_curr = db_user.get('currency', 'USD') if db_user else 'USD'

    try:
        quantity = float(update.message.text.strip())
        if quantity <= 0:
            raise ValueError()

        product = context.user_data['calc_prod']
        rate = await db_manager.get_exchange_rate(user_curr)

        raw_price_usd = product['raw_price_usd']
        tariff_percent = product['tariff_percent']

        final_unit_usd = raw_price_usd * (1 + tariff_percent / 100.0)
        final_unit_in_curr = final_unit_usd * rate

        raw_total_usd = raw_price_usd * quantity
        final_total_usd = final_unit_usd * quantity
        final_total_in_curr = final_unit_in_curr * quantity

        # Create Order record in DB
        order_id = await db_manager.create_order(
            user_id=user_id,
            product_id=product['id'],
            product_name=product['name'],
            quantity=quantity,
            unit=product['unit'],
            raw_total_usd=raw_total_usd,
            final_total_usd=final_total_usd,
            currency=user_curr,
            final_total_in_currency=final_total_in_curr
        )

        context.user_data['last_order_id'] = order_id
        context.user_data['last_order_data'] = {
            'order_id': order_id,
            'user_id': user_id,
            'product_name': product['name'],
            'spec': product['specification'],
            'quantity': quantity,
            'unit': product['unit'],
            'unit_price': final_unit_in_curr,
            'total_price': final_total_in_curr,
            'currency': user_curr
        }

        result_msg = get_text(
            'calc_result',
            lang,
            name=product['name'],
            quantity=quantity,
            unit=product['unit'],
            unit_price=f"{final_unit_in_curr:,.2f}",
            total=f"{final_total_in_curr:,.2f}",
            currency=user_curr
        )

        keyboard = [
            [InlineKeyboardButton(get_text('btn_generate_pdf', lang), callback_data=f"gen_pdf_{order_id}")],
            [InlineKeyboardButton("🔙", callback_data="user_main_menu")]
        ]

        await update.message.reply_text(result_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(get_text('invalid_input', lang))
        return CALC_QTY

async def generate_pdf_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    order_id = int(query.data.replace("gen_pdf_", ""))

    db_user = await db_manager.get_user(user_id)
    lang = db_user.get('language', 'fa') if db_user else 'fa'

    order_data = context.user_data.get('last_order_data')
    if not order_data or order_data['order_id'] != order_id:
        # Fallback fetch from DB if state lost
        await query.message.reply_text("Error fetching order data.")
        return

    pdf_path = f"invoice_{order_id}.pdf"
    generate_invoice_pdf(
        order_id=order_data['order_id'],
        user_id=order_data['user_id'],
        product_name=order_data['product_name'],
        spec=order_data['spec'],
        quantity=order_data['quantity'],
        unit=order_data['unit'],
        unit_price=order_data['unit_price'],
        total_price=order_data['total_price'],
        currency=order_data['currency'],
        filename=pdf_path
    )

    await query.message.reply_document(
        document=open(pdf_path, 'rb'),
        caption=get_text('pdf_generated', lang)
    )

    # Clean up PDF file
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db_user = await db_manager.get_user(user_id)
    lang = db_user.get('language', 'fa') if db_user else 'fa'

    welcome_msg = get_text('welcome', lang, name=query.from_user.first_name)
    await query.message.edit_text(welcome_msg, reply_markup=build_main_keyboard(lang))
