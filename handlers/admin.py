from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import logging

from database import db_manager
from config import ADMIN_IDS, SUPPORTED_CURRENCIES
from i18n import get_text
from currency_service import fetch_and_update_exchange_rates

logger = logging.getLogger(__name__)

# Conversation states
ADD_PROD_CAT, ADD_PROD_NAME, ADD_PROD_SPEC, ADD_PROD_RAW_PRICE, ADD_PROD_TARIFF, ADD_PROD_PHOTO = range(6)
SET_CURRENCY_NAME, SET_CURRENCY_RATE = range(6, 8)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        if update.callback_query:
            await update.callback_query.message.reply_text("❌ شما دسترسی ادمین ندارید.")
        else:
            await update.message.reply_text("❌ شما دسترسی ادمین ندارید.")
        return

    keyboard = [
        [InlineKeyboardButton("➕ افزودن محصول جدید با عکس", callback_data="admin_add_product")],
        [InlineKeyboardButton("📋 مدیریت و لیست محصولات (حذف/ویرایش)", callback_data="admin_list_products")],
        [InlineKeyboardButton("💵 تنظیم نرخ ارزها (دستی / بروزرسانی زنده)", callback_data="admin_rates")],
        [InlineKeyboardButton("📊 مشاهده لیست سفارشات", callback_data="admin_orders")],
        [InlineKeyboardButton("📢 ارسال پیام همگانی (Broadcast)", callback_data="admin_broadcast")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.message.edit_text("⚙️ **پنل مدیریت ادمین**\nلطفاً بخش مورد نظر را انتخاب کنید:", reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text("⚙️ **پنل مدیریت ادمین**\nلطفاً بخش مورد نظر را انتخاب کنید:", reply_markup=reply_markup, parse_mode='Markdown')

async def start_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("فولاد مبارکه اصفهان (محصولات تخت)", callback_data="cat_mobarakeh_flat")],
        [InlineKeyboardButton("ذوب‌آهن اصفهان (مقاطع طویل)", callback_data="cat_zobahan_long")]
    ]
    await query.message.edit_text("دسته‌بندی اصلی محصول را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_PROD_CAT

async def add_prod_cat_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.replace("cat_", "")
    context.user_data['new_prod_cat'] = category

    await query.message.edit_text(f"دسته‌بندی `{category}` انتخاب شد.\n\nلطفاً **نام محصول** را وارد کنید (مثال: تیرآهن 18 ذوب‌آهن):", parse_mode='Markdown')
    return ADD_PROD_NAME

async def add_prod_name_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data['new_prod_name'] = name
    await update.message.reply_text("لطفاً **مشخصات/سایز/استاندارد** محصول را وارد کنید (مثال: شاخه 12 متری - IPE):")
    return ADD_PROD_SPEC

async def add_prod_spec_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    spec = update.message.text.strip()
    context.user_data['new_prod_spec'] = spec
    await update.message.reply_text("لطفاً **قیمت خام دلار (به ازای هر تن)** را وارد کنید (مثال: 580.0):")
    return ADD_PROD_RAW_PRICE

async def add_prod_raw_price_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        raw_price = float(update.message.text.strip())
        context.user_data['new_prod_raw_price'] = raw_price
        await update.message.reply_text("لطفاً **درصد تعرفه/کارمزد/سود ادمین (%)** را وارد کنید (مثال: 5.0 برای 5%):")
        return ADD_PROD_TARIFF
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید:")
        return ADD_PROD_RAW_PRICE

async def add_prod_tariff_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        tariff = float(update.message.text.strip())
        context.user_data['new_prod_tariff'] = tariff
        await update.message.reply_text("🖼️ لطفاً **تصویر محصول** را به صورت عکس ارسال کنید (یا کلمه `بدون عکس` را بفرستید):")
        return ADD_PROD_PHOTO
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید:")
        return ADD_PROD_TARIFF

async def add_prod_photo_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file_id = None
    if update.message.photo:
        photo_file_id = update.message.photo[-1].file_id
    elif update.message.text and update.message.text.strip() == "بدون عکس":
        photo_file_id = None

    cat = context.user_data['new_prod_cat']
    name = context.user_data['new_prod_name']
    spec = context.user_data['new_prod_spec']
    raw_price = context.user_data['new_prod_raw_price']
    tariff = context.user_data['new_prod_tariff']

    prod_id = await db_manager.add_product(
        category=cat,
        name=name,
        specification=spec,
        raw_price_usd=raw_price,
        tariff_percent=tariff,
        unit='ton',
        photo_file_id=photo_file_id
    )

    final_usd = raw_price * (1 + tariff / 100.0)

    msg_text = (
        f"✅ **محصول با موفقیت ثبت شد!**\n\n"
        f"ID: `{prod_id}`\n"
        f"نام: {name}\n"
        f"دسته: {cat}\n"
        f"قیمت خام: {raw_price} USD\n"
        f"تعرفه ادمین: {tariff}%\n"
        f"قیمت نهایی برای مشتری: {final_usd:.2f} USD"
    )

    if photo_file_id:
        await update.message.reply_photo(photo=photo_file_id, caption=msg_text, parse_mode='Markdown')
    else:
        await update.message.reply_text(msg_text, parse_mode='Markdown')

    return ConversationHandler.END

async def list_products_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    products = await db_manager.get_products()

    if not products:
        await query.message.edit_text("هیچ محصولی ثبت نشده است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data="admin_back")]]))
        return

    text = "📋 **لیست محصولات (دیدگاه ادمین با قیمت خام و تعرفه):**\n\n"
    keyboard = []
    for p in products:
        final_usd = p['raw_price_usd'] * (1 + p['tariff_percent'] / 100.0)
        has_photo = "📷 دارد" if p.get('photo_file_id') else "❌ ندارد"
        text += (
            f"🔹 ID: `{p['id']}` | **{p['name']}** ({p['category']})\n"
            f"   مشخصات: {p['specification']} | عکس: {has_photo}\n"
            f"   قیمت خام: ${p['raw_price_usd']} | تعرفه: {p['tariff_percent']}% | قیمت نهایی: ${final_usd:.2f}\n\n"
        )
        keyboard.append([InlineKeyboardButton(f"❌ حذف {p['name']}", callback_data=f"del_prod_{p['id']}")])

    keyboard.append([InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_back")])
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def delete_product_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    prod_id = int(query.data.replace("del_prod_", ""))
    await db_manager.delete_product(prod_id)
    await query.message.reply_text(f"✅ محصول با شناسه {prod_id} حذف شد.")
    await list_products_admin(update, context)

async def view_rates_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    rates = await db_manager.get_exchange_rates()

    text = "💵 **نرخ برابری ارزها به USD (ارز پایه):**\n\n"
    keyboard = []
    for code, info in rates.items():
        mode = "🔴 دستی" if info.get('is_manual') == 1 else "🟢 زنده/خودکار"
        text += f"• `{code}`: {info['rate_to_usd']} ({mode})\n"
        keyboard.append([InlineKeyboardButton(f"✏️ تغییر دستی نرخ {code}", callback_data=f"set_rate_{code}")])

    keyboard.append([InlineKeyboardButton("🔄 بروزرسانی آنلاین نرخ‌ها از API", callback_data="admin_fetch_live_rates")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_back")])
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def trigger_fetch_live_rates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("در حال بروزرسانی نرخ‌های زنده...")
    await fetch_and_update_exchange_rates()
    await view_rates_admin(update, context)

async def start_set_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    code = query.data.replace("set_rate_", "")
    context.user_data['edit_currency_code'] = code
    await query.message.edit_text(f"لطفاً نرخ جدید برابری **{code}** نسبت به 1 دلار (USD) را وارد کنید:\n(این کار حالت نرخ را به «دستی» تغییر می‌دهد)")
    return SET_CURRENCY_RATE

async def set_rate_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        rate = float(update.message.text.strip())
        code = context.user_data['edit_currency_code']
        await db_manager.set_exchange_rate(code, rate, is_manual=1)
        await update.message.reply_text(f"✅ نرخ ارز {code} به صورت دستی با موفقیت به {rate} به‌روزرسانی شد.")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ عدد وارد شده معتبر نیست. مجدداً تلاش کنید:")
        return SET_CURRENCY_RATE

async def view_orders_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    orders = await db_manager.get_all_orders()

    if not orders:
        await query.message.edit_text("هیچ سفارشی ثبت نشده است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data="admin_back")]]))
        return

    text = "📊 **لیست آخرین سفارشات و پیش‌فاکتورها:**\n\n"
    for o in orders[:10]:
        text += (
            f"🆔 کد سفارش: `{o['id']}` | کاربر: `{o['user_id']}`\n"
            f"محصول: {o['product_name']} ({o['quantity']} {o['unit']})\n"
            f"قیمت خام کل: ${o['raw_total_usd']:.2f}\n"
            f"قیمت نهایی کل: ${o['final_total_usd']:.2f} ({o['final_total_in_currency']:.2f} {o['currency']})\n"
            f"تاریخ: {o['created_at']}\n"
            f"-----------------------------------\n"
        )
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_back")]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def admin_broadcast_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        "📢 **ارسال پیام همگانی**\n\n"
        "برای ارسال پیام همگانی، لطفاً یک پیام به این شکل ارسال کنید:\n"
        "`/broadcast متن پیام شما`\n\n"
        "یا به پیام مورد نظرتان ریپلای (Reply) نموده و دستور `/broadcast` را بفرستید.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")]]),
        parse_mode='Markdown'
    )

async def cancel_admin_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END
