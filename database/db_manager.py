import aiosqlite
import logging

DB_NAME = "bot_database.db"

logger = logging.getLogger(__name__)

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

        # Check if columns exist in case db existed before
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

        async with db.execute("PRAGMA table_info(exchange_rates)") as cursor:
            columns = [row[1] for row in await cursor.fetchall()]
            if 'is_manual' not in columns:
                await db.execute("ALTER TABLE exchange_rates ADD COLUMN is_manual INTEGER DEFAULT 0")

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

        async with db.execute("PRAGMA table_info(products)") as cursor:
            columns = [row[1] for row in await cursor.fetchall()]
            if 'photo_file_id' not in columns:
                await db.execute("ALTER TABLE products ADD COLUMN photo_file_id TEXT")

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

        # Insert default exchange rates if table is empty
        async with db.execute("SELECT COUNT(*) FROM exchange_rates") as cursor:
            count = (await cursor.fetchone())[0]
            if count == 0:
                default_rates = [
                    ('USD', 1.0, 0),
                    ('IQD', 1310.0, 0),    # Iraqi Dinar per USD
                    ('GEL', 2.70, 0),      # Georgian Lari per USD
                    ('TJS', 10.90, 0),     # Tajikistani Somoni per USD
                    ('AFN', 70.0, 0),      # Afghan Afghani per USD
                    ('IRR', 650000.0, 0)   # Iranian Toman/Rial representation
                ]
                await db.executemany(
                    'INSERT OR REPLACE INTO exchange_rates (currency_code, rate_to_usd, is_manual) VALUES (?, ?, ?)',
                    default_rates
                )

        await db.commit()
        logger.info("Database initialized with photo_file_id and auto exchange rate metadata.")

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
