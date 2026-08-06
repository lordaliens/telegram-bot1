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
                referrer_id INTEGER
            )
        ''')

        # Migrations to add new columns safely if they don't exist
        try:
            await db.execute('ALTER TABLE users ADD COLUMN message_count INTEGER DEFAULT 0')
        except aiosqlite.OperationalError:
            pass # Column already exists

        try:
            await db.execute('ALTER TABLE users ADD COLUMN pending_message TEXT')
        except aiosqlite.OperationalError:
            pass # Column already exists

        await db.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        await db.commit()
        logger.info("Database initialized.")

async def add_user(user_id, referrer_id=None):
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute(
                'INSERT INTO users (user_id, referrer_id) VALUES (?, ?)',
                (user_id, referrer_id)
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            # User already exists
            return False
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            return False

async def get_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
            return await cursor.fetchone()

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

async def increment_message_count(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            'UPDATE users SET message_count = message_count + 1 WHERE user_id = ?',
            (user_id,)
        )
        await db.commit()

async def get_message_count(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT message_count FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def set_pending_message(user_id, message):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            'UPDATE users SET pending_message = ? WHERE user_id = ?',
            (message, user_id)
        )
        await db.commit()

async def get_pending_message(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT pending_message FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def clear_pending_message(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            'UPDATE users SET pending_message = NULL WHERE user_id = ?',
            (user_id,)
        )
        await db.commit()

async def add_history(user_id, role, content):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            'INSERT INTO history (user_id, role, content) VALUES (?, ?, ?)',
            (user_id, role, content)
        )
        await db.commit()

async def get_history(user_id, limit=20):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            'SELECT role, content FROM history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?',
            (user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            # Reverse to get chronological order for the model
            return [{"role": row[0], "content": row[1]} for row in reversed(rows)]
