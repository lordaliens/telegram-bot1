import sqlite3
import logging
from typing import List, Dict, Any, Optional

DB_NAME = "poweryoga.db"

logger = logging.getLogger(__name__)

def get_connection(db_path: str = DB_NAME) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DB_NAME):
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        # Clients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                age INTEGER NOT NULL,
                height REAL NOT NULL,
                weight REAL NOT NULL,
                training_history TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Progress history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                weight REAL NOT NULL,
                notes TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
            )
        ''')

        # AI Generated Plans table (Workout & Diet)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                plan_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
            )
        ''')
        conn.commit()
        logger.info("Power Yoga database initialized successfully.")

def add_client(first_name: str, last_name: str, age: int, height: float, weight: float, training_history: str, db_path: str = DB_NAME) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO clients (first_name, last_name, age, height, weight, training_history)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (first_name, last_name, age, height, weight, training_history)
        )
        client_id = cursor.lastrowid
        cursor.execute(
            '''INSERT INTO progress (client_id, weight, notes) VALUES (?, ?, ?)''',
            (client_id, weight, "ثبت اولیه وزن و مشخصات")
        )
        conn.commit()
        return client_id

def get_all_clients(db_path: str = DB_NAME) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clients ORDER BY created_at DESC')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_client_by_id(client_id: int, db_path: str = DB_NAME) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_client(client_id: int, first_name: str, last_name: str, age: int, height: float, weight: float, training_history: str, db_path: str = DB_NAME) -> bool:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''UPDATE clients SET first_name = ?, last_name = ?, age = ?, height = ?, weight = ?, training_history = ?
               WHERE id = ?''',
            (first_name, last_name, age, height, weight, training_history, client_id)
        )
        conn.commit()
        return True

def delete_client(client_id: int, db_path: str = DB_NAME) -> bool:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM clients WHERE id = ?', (client_id,))
        conn.commit()
        return True

def add_progress(client_id: int, weight: float, notes: str, db_path: str = DB_NAME) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO progress (client_id, weight, notes) VALUES (?, ?, ?)''',
            (client_id, weight, notes)
        )
        progress_id = cursor.lastrowid
        cursor.execute(
            '''UPDATE clients SET weight = ? WHERE id = ?''',
            (weight, client_id)
        )
        conn.commit()
        return progress_id

def get_client_progress(client_id: int, db_path: str = DB_NAME) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM progress WHERE client_id = ? ORDER BY recorded_at ASC', (client_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def save_plan(client_id: int, plan_type: str, title: str, content: str, db_path: str = DB_NAME) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO plans (client_id, plan_type, title, content) VALUES (?, ?, ?, ?)''',
            (client_id, plan_type, title, content)
        )
        plan_id = cursor.lastrowid
        conn.commit()
        return plan_id

def get_client_plans(client_id: int, db_path: str = DB_NAME) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM plans WHERE client_id = ? ORDER BY created_at DESC', (client_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
