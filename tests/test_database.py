import os
import sys
import sqlite3
from datetime import datetime, timedelta
import pytz
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import bot_database as database
from bot_config import TIMEZONE

database.DB_NAME = "test_reminders.db"

@pytest.fixture(autouse=True)
def setup_and_teardown():
    if os.path.exists(database.DB_NAME):
        os.remove(database.DB_NAME)
    database.init_db()
    yield
    if os.path.exists(database.DB_NAME):
        os.remove(database.DB_NAME)


def test_add_and_get_reminder():
    """Тестуємо, що нагадування правильно додається і зчитується."""
    chat_id = 12345
    reminder_time = datetime.now(TIMEZONE) + timedelta(hours=1)
    reminder_text = "Тестове нагадування"
    
    database.add_reminder_to_db(chat_id, reminder_time, reminder_text)
    reminders = database.get_pending_reminders(chat_id)
    
    assert len(reminders) == 1
    rem_id, rem_time_str, rem_text = reminders[0]
    
    assert rem_text == reminder_text
    
    rem_time_from_db = pytz.utc.localize(datetime.strptime(rem_time_str, "%Y-%m-%d %H:%M:%S"))
    
    assert rem_time_from_db.strftime("%Y-%m-%d %H:%M") == reminder_time.astimezone(pytz.utc).strftime("%Y-%m-%d %H:%M")

def test_delete_reminder():
    """Тестуємо, що нагадування правильно видаляється."""
    chat_id = 54321
    reminder_time = datetime.now(TIMEZONE) + timedelta(days=1)
    database.add_reminder_to_db(chat_id, reminder_time, "Нагадування для видалення")
    
    reminders_before = database.get_pending_reminders(chat_id)
    assert len(reminders_before) == 1
    reminder_id_to_delete = reminders_before[0][0]
    
    database.delete_reminder_from_db(reminder_id_to_delete)
    
    reminders_after = database.get_pending_reminders(chat_id)
    assert len(reminders_after) == 0

def test_check_reminders_logic():
    """Тестуємо логіку вибірки нагадувань, час яких настав."""
    chat_id = 999
    
    time_past = datetime.now(TIMEZONE) - timedelta(minutes=5)
    database.add_reminder_to_db(chat_id, time_past, "Минуле нагадування")

    time_future = datetime.now(TIMEZONE) + timedelta(minutes=5)
    database.add_reminder_to_db(chat_id, time_future, "Майбутнє нагадування")
    
    ready_reminders = database.get_all_pending_reminders_for_check()
    
    assert len(ready_reminders) == 1
    assert ready_reminders[0][2] == "Минуле нагадування"

def test_mark_reminder_sent():
    """Тестуємо, що статус нагадування правильно змінюється на 'sent'."""
    chat_id = 777
    time_past = datetime.now(TIMEZONE) - timedelta(minutes=1)
    database.add_reminder_to_db(chat_id, time_past, "Нагадування для відправки")
    
    ready_reminders = database.get_all_pending_reminders_for_check()
    assert len(ready_reminders) == 1
    reminder_id = ready_reminders[0][0]
    
    database.mark_reminder_sent(reminder_id)
    
    still_ready = database.get_all_pending_reminders_for_check()
    assert len(still_ready) == 0


def test_get_reminders_for_empty_user():
    """НОВИЙ ТЕСТ: Перевіряємо, що для користувача без нагадувань повертається порожній список."""
    reminders = database.get_pending_reminders(chat_id=11111)
    assert reminders == []
    assert len(reminders) == 0

def test_delete_non_existent_reminder():
    """НОВИЙ ТЕСТ: Перевіряємо, що видалення неіснуючого ID не викликає помилки."""
    try:
        database.delete_reminder_from_db(99999)

        assert True
    except Exception as e:

        pytest.fail(f"Видалення неіснуючого нагадування викликало помилку: {e}")

def test_time_is_stored_in_utc():
    """НОВИЙ ТЕСТ: Перевіряємо, що час зберігається в базі даних саме в UTC."""
    chat_id = 222

    local_time = datetime.now(TIMEZONE) + timedelta(days=5)
    
    database.add_reminder_to_db(chat_id, local_time, "Перевірка UTC")
    
    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT reminder_time FROM reminders WHERE chat_id = ?", (chat_id,))
    time_str_from_db = cursor.fetchone()[0]
    conn.close()

    expected_utc_str = local_time.astimezone(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    
    assert time_str_from_db == expected_utc_str