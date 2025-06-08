import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pytest
from datetime import datetime, timedelta
import pytz

import bot_database as database
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
    chat_id = 12345
    reminder_time = datetime.now(pytz.utc) + timedelta(hours=1)
    reminder_text = "Тестове нагадування"
    database.add_reminder_to_db(chat_id, reminder_time, reminder_text)
    reminders = database.get_pending_reminders(chat_id)
    assert len(reminders) == 1
    rem_id, rem_time_str, rem_text = reminders[0]
    assert rem_text == reminder_text
    rem_time_from_db = datetime.strptime(rem_time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)
    assert rem_time_from_db.strftime("%Y-%m-%d %H:%M") == reminder_time.strftime("%Y-%m-%d %H:%M")

def test_delete_reminder():
    chat_id = 54321
    reminder_time = datetime.now(pytz.utc) + timedelta(days=1)
    database.add_reminder_to_db(chat_id, reminder_time, "Нагадування для видалення")
    reminders_before = database.get_pending_reminders(chat_id)
    assert len(reminders_before) == 1
    reminder_id_to_delete = reminders_before[0][0]
    database.delete_reminder_from_db(reminder_id_to_delete)
    reminders_after = database.get_pending_reminders(chat_id)
    assert len(reminders_after) == 0

def test_check_reminders_logic():
    chat_id = 999
    time_past = datetime.now(pytz.utc) - timedelta(minutes=5)
    database.add_reminder_to_db(chat_id, time_past, "Минуле нагадування")
    time_future = datetime.now(pytz.utc) + timedelta(minutes=5)
    database.add_reminder_to_db(chat_id, time_future, "Майбутнє нагадування")
    ready_reminders = database.get_all_pending_reminders_for_check()
    assert len(ready_reminders) == 1
    assert ready_reminders[0][2] == "Минуле нагадування"

def test_mark_reminder_sent():
    chat_id = 777
    time_past = datetime.now(pytz.utc) - timedelta(minutes=1)
    database.add_reminder_to_db(chat_id, time_past, "Нагадування для відправки")
    ready_reminders = database.get_all_pending_reminders_for_check()
    assert len(ready_reminders) == 1
    reminder_id = ready_reminders[0][0]
    database.mark_reminder_sent(reminder_id)
    still_ready = database.get_all_pending_reminders_for_check()
    assert len(still_ready) == 0