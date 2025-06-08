import sqlite3
import logging
from datetime import datetime
import pytz

DB_NAME = "reminders.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            reminder_time TEXT NOT NULL,
            reminder_text TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()
    logging.info("Базу даних ініціалізовано.")

def add_reminder_to_db(chat_id: int, reminder_time: datetime, reminder_text: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    time_utc = reminder_time.astimezone(pytz.utc)
    time_str = time_utc.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO reminders (chat_id, reminder_time, reminder_text) VALUES (?, ?, ?)",
        (chat_id, time_str, reminder_text)
    )
    conn.commit()
    conn.close()

def get_pending_reminders(chat_id: int) -> list:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, reminder_time, reminder_text FROM reminders WHERE chat_id = ? AND status = 'pending' ORDER BY reminder_time ASC",
        (chat_id,)
    )
    reminders = cursor.fetchall()
    conn.close()
    return reminders

def delete_reminder_from_db(reminder_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()
    logging.info(f"Нагадування ID {reminder_id} видалено.")

def get_all_pending_reminders_for_check() -> list:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now_utc_str = datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("SELECT id, chat_id, reminder_text FROM reminders WHERE reminder_time <= ? AND status = 'pending'", (now_utc_str,))
    reminders = cursor.fetchall()
    conn.close()
    return reminders

def mark_reminder_sent(reminder_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE reminders SET status = 'sent' WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()