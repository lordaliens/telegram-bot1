import aiosqlite
import logging

DB_NAME = "bot_database.db"

logger = logging.getLogger(__name__)

# Pre-defined complete steel products
DEFAULT_PRODUCTS = [
    # Category 1: شرکت فولاد مبارکه اصفهان (محصولات تخت / mobarakeh_flat)
    ("mobarakeh_flat", "تختال (اسلب)", "ضخامت 200 تا 250 میلی‌متر | عرض 900 تا 2000 میلی‌متر | طول 4 تا 10.5 متر", 520.0, 5.0, "ton"),
    ("mobarakeh_flat", "ورق نورد گرم (ورق سیاه)", "ضخامت 1.2 تا 16 میلی‌متر | عرض 600 تا 1850 میلی‌متر (رول و شیت)", 610.0, 5.0, "ton"),
    ("mobarakeh_flat", "ورق اسیدشویی شده", "ضخامت 1.2 تا 6 میلی‌متر | عرض 600 تا 1530 میلی‌متر (رول)", 650.0, 5.0, "ton"),
    ("mobarakeh_flat", "ورق نورد سرد (ورق روغنی)", "ضخامت 0.3 تا 3 میلی‌متر | عرض 600 تا 1620 میلی‌متر (رول و شیت)", 720.0, 5.0, "ton"),
    ("mobarakeh_flat", "ورق گالوانیزه", "ضخامت 0.25 تا 3 میلی‌متر | عرض 750 تا 1500 میلی‌متر (رول و شیت)", 810.0, 5.0, "ton"),
    ("mobarakeh_flat", "ورق رنگی", "ضخامت 0.25 تا 1.5 میلی‌متر | عرض 750 تا 1300 میلی‌متر (رول)", 890.0, 5.0, "ton"),
    ("mobarakeh_flat", "ورق قلع‌اندود", "ضخامت 0.13 تا 0.5 میلی‌متر | عرض 600 تا 1000 میلی‌متر (رول و شیت)", 950.0, 5.0, "ton"),

    # Category 2: شرکت ذوب‌آهن اصفهان (مقاطع طویل / zobahan_long)
    ("zobahan_long", "تیرآهن معمولی (IPE)", "سایز 12 تا 30 سانتی‌متر | طول شاخه 12 متر", 580.0, 5.0, "ton"),
    ("zobahan_long", "تیرآهن بال‌پهن (هاش سبک و سنگین)", "سایز 14 تا 30 سانتی‌متر | طول شاخه 12 متر", 640.0, 5.0, "ton"),
    ("zobahan_long", "میلگرد آجدار (گریدهای A2 و A3)", "سایز 8 تا 32 میلی‌متر | طول شاخه 12 متر", 550.0, 5.0, "ton"),
    ("zobahan_long", "میلگرد ساده (گرید A1)", "سایز 14 تا 32 میلی‌متر | طول شاخه 12 متر", 540.0, 5.0, "ton"),
    ("zobahan_long", "کلاف و مفتول صنعتی", "سایز 5.5 تا 14 میلی‌متر (رول پیوسته)", 570.0, 5.0, "ton"),
    ("zobahan_long", "ریل راه‌آهن (UIC60 و U33)", "طول شاخه 18 تا 36 متر", 780.0, 5.0, "ton"),
    ("zobahan_long", "نبشی", "سایز 40 در 40 تا 150 در 150 میلی‌متر | طول شاخه 12 متر", 560.0, 5.0, "ton"),
    ("zobahan_long", "ناودانی (UPE و UPN)", "سایز 14 تا 30 سانتی‌متر | طول شاخه 12 متر", 575.0, 5.0, "ton"),
    ("zobahan_long", "شمش فولادی (بیلت)", "سایز 130 در 130 و 150 در 150 میلی‌متر | طول 6 تا 12 متر", 490.0, 5.0, "ton"),
]

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                referrer_id INTEGER,
                language TEXT DEFAULT 'fa',
                currency TEXT DEFAULT 'USD'
            )
        ''')

        async with db.execute("PRAGMA table_info(users)") as cursor:
            columns = [row[1] for row in await cursor.fetchall()]
            if 'language' not in columns:
                await db.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'fa'")
            if 'currency' not in columns:
                await db.execute("ALTER TABLE users ADD COLUMN currency TEXT DEFAULT 'USD'")

        await db.execute('''
            CREATE TABLE IF NOT EXISTS exchange_rates (
                currency_code TEXT PRIMARY KEY,
                rate_to_usd REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_manual INTEGER DEFAULT 0
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                specification TEXT,
                raw_price_usd REAL NOT NULL,
                tariff_percent REAL DEFAULT 0.0,
                unit TEXT DEFAULT 'ton',
                photo_file_id TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT,
                quantity REAL NOT NULL,
                unit TEXT DEFAULT 'ton',
                raw_total_usd REAL,
                final_total_usd REAL,
                currency TEXT NOT NULL,
                final_total_in_currency REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Default exchange rates
        async with db.execute("SELECT COUNT(*) FROM exchange_rates") as cursor:
            count = (await cursor.fetchone())[0]
            if count == 0:
                default_rates = [
                    ('USD', 1.0, 0),
                    ('IQD', 1310.0, 0),
                    ('GEL', 2.70, 0),
                    ('TJS', 10.90, 0),
                    ('AFN', 70.0, 0),
                    ('IRR', 650000.0, 0)
                ]
                await db.executemany(
                    'INSERT OR REPLACE INTO exchange_rates (currency_code, rate_to_usd, is_manual) VALUES (?, ?, ?)',
                    default_rates
                )

        # Seed default products if products table is empty
        async with db.execute("SELECT COUNT(*) FROM products") as cursor:
            prod_count = (await cursor.fetchone())[0]
            if prod_count == 0:
                await db.executemany(
                    'INSERT INTO products (category, name, specification, raw_price_usd, tariff_percent, unit) VALUES (?, ?, ?, ?, ?, ?)',
                    DEFAULT_PRODUCTS
                )
                logger.info("Pre-loaded 16 Mobarakeh & Zob Ahan steel products into products table.")

        await db.commit()

async def add_user(user_id, referrer_id=None, language='fa'):
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute(
                'INSERT INTO users (user_id, referrer_id, language) VALUES (?, ?, ?)',
                (user_id, referrer_id, language)
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            return False

async def update_user_language(user_id, language):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))
        await db.commit()

async def update_user_currency(user_id, currency):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE users SET currency = ? WHERE user_id = ?', (currency, user_id))
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_referral_count(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT user_id FROM users') as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

# Exchange Rates Management
async def set_exchange_rate(currency_code, rate_to_usd, is_manual=1):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            'INSERT OR REPLACE INTO exchange_rates (currency_code, rate_to_usd, is_manual, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)',
            (currency_code.upper(), rate_to_usd, is_manual)
        )
        await db.commit()

async def get_exchange_rates():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM exchange_rates') as cursor:
            rows = await cursor.fetchall()
            return {row['currency_code']: dict(row) for row in rows}

async def get_exchange_rate(currency_code):
    rates = await get_exchange_rates()
    curr = rates.get(currency_code.upper())
    return curr['rate_to_usd'] if curr else 1.0

# Products Management
async def add_product(category, name, specification, raw_price_usd, tariff_percent=0.0, unit='ton', photo_file_id=None):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'INSERT INTO products (category, name, specification, raw_price_usd, tariff_percent, unit, photo_file_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (category, name, specification, raw_price_usd, tariff_percent, unit, photo_file_id)
        )
        await db.commit()
        return cursor.lastrowid

async def update_product(product_id, category, name, specification, raw_price_usd, tariff_percent, unit='ton', photo_file_id=None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            'UPDATE products SET category=?, name=?, specification=?, raw_price_usd=?, tariff_percent=?, unit=?, photo_file_id=? WHERE id=?',
            (category, name, specification, raw_price_usd, tariff_percent, unit, photo_file_id, product_id)
        )
        await db.commit()

async def delete_product(product_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE products SET is_active = 0 WHERE id = ?', (product_id,))
        await db.commit()

async def get_products(category=None):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        if category:
            async with db.execute('SELECT * FROM products WHERE category = ? AND is_active = 1', (category,)) as cursor:
                rows = await cursor.fetchall()
        else:
            async with db.execute('SELECT * FROM products WHERE is_active = 1') as cursor:
                rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_product(product_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM products WHERE id = ?', (product_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

# Orders Management
async def create_order(user_id, product_id, product_name, quantity, unit, raw_total_usd, final_total_usd, currency, final_total_in_currency):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            '''INSERT INTO orders
               (user_id, product_id, product_name, quantity, unit, raw_total_usd, final_total_usd, currency, final_total_in_currency)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_id, product_id, product_name, quantity, unit, raw_total_usd, final_total_usd, currency, final_total_in_currency)
        )
        await db.commit()
        return cursor.lastrowid

async def get_user_orders(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC', (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_all_orders():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM orders ORDER BY created_at DESC') as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
