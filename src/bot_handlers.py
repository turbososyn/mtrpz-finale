import logging
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ContextTypes, ConversationHandler

import bot_database as database

from bot_config import TIMEZONE

(
    CHOOSE_TIME_OPTION, CHOOSE_CUSTOM_TYPE, GET_DAYS, GET_HOURS,
    GET_MINUTES, GET_SPECIFIC_DATE, GET_TEXT, DELETE_REMINDER
) = range(8)

def get_current_time():
    return datetime.now(TIMEZONE)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        f"Привіт, {user.mention_html()}!\n\n"
        f"Я твій бот-нагадувач. Переглянути команди можна через меню."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Як користуватися ботом:\n"
        "/set - створити нове нагадування.\n"
        "/list - показати активні нагадування.\n"
        "/delete - видалити нагадування.\n"
        "/cancel - скасувати поточну дію."
    )
    
async def get_server_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_time = get_current_time()
    await update.message.reply_text(
        f"Мій поточний час: {current_time.strftime('%H:%M:%S')}"
    )

async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    reminders = database.get_pending_reminders(chat_id)
    if not reminders:
        await update.message.reply_text("У вас немає активних нагадувань.")
        return

    message_text = "Ваші активні нагадування:\n\n"
    for idx, (rem_id, rem_time_utc_str, rem_text) in enumerate(reminders, 1):
        rem_time_utc = pytz.utc.localize(datetime.strptime(rem_time_utc_str, "%Y-%m-%d %H:%M:%S"))
        rem_time_local = rem_time_utc.astimezone(TIMEZONE)
        message_text += f"*{idx}.* {rem_text}\n"
        message_text += f"   `{rem_time_local.strftime('%d.%m.%Y о %H:%M')}`\n\n"
    await update.message.reply_text(message_text, parse_mode='Markdown')

async def set_reminder_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("⏰ На хвилину", callback_data="1_min"), InlineKeyboardButton("⏰ На годину", callback_data="1_hour")],
        [InlineKeyboardButton("✍️ Ввести свій час", callback_data="custom_time")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Коли нагадати?", reply_markup=reply_markup)
    return CHOOSE_TIME_OPTION

async def handle_level1_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data
    now = get_current_time()
    if choice == "1_min":
        context.user_data['reminder_time'] = now + timedelta(minutes=1)
        await query.edit_message_text(text="Чудово! Тепер введіть текст нагадування.")
        return GET_TEXT
    elif choice == "1_hour":
        context.user_data['reminder_time'] = now + timedelta(hours=1)
        await query.edit_message_text(text="Чудово! Тепер введіть текст нагадування.")
        return GET_TEXT
    elif choice == "custom_time":
        keyboard = [
            [InlineKeyboardButton("Через ... хвилин", callback_data="in_minutes")],
            [InlineKeyboardButton("Через ... годин", callback_data="in_hours")],
            [InlineKeyboardButton("Через ... днів", callback_data="in_days")],
            [InlineKeyboardButton("Ввести точну дату", callback_data="specific_date")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Як саме ви хочете вказати час?", reply_markup=reply_markup)
        return CHOOSE_CUSTOM_TYPE
    return ConversationHandler.END

async def handle_level2_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data
    if choice == "in_minutes":
        await query.edit_message_text(text="Введіть кількість хвилин:")
        return GET_MINUTES
    elif choice == "in_hours":
        await query.edit_message_text(text="Введіть кількість годин:")
        return GET_HOURS
    elif choice == "in_days":
        await query.edit_message_text(text="Введіть кількість днів:")
        return GET_DAYS
    elif choice == "specific_date":
        await query.edit_message_text(text="Введіть дату та час у форматі `ДД.ММ.РРРР ГГ:ХХ`")
        return GET_SPECIFIC_DATE
    return ConversationHandler.END

async def get_relative_time(update: Update, context: ContextTypes.DEFAULT_TYPE, unit: str) -> int:
    user_input = update.message.text
    try:
        value = int(user_input)
        if value <= 0: raise ValueError
        now = get_current_time()
        if unit == "minutes": context.user_data['reminder_time'] = now + timedelta(minutes=value)
        elif unit == "hours": context.user_data['reminder_time'] = now + timedelta(hours=value)
        elif unit == "days": context.user_data['reminder_time'] = now + timedelta(days=value)
        await update.message.reply_text("Чудово! Тепер введіть текст нагадування.")
        return GET_TEXT
    except ValueError:
        await update.message.reply_text("Будь ласка, введіть додатне число.")
        if unit == "minutes": return GET_MINUTES
        if unit == "hours": return GET_HOURS
        if unit == "days": return GET_DAYS
    return ConversationHandler.END

async def get_minutes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: return await get_relative_time(update, context, "minutes")
async def get_hours(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: return await get_relative_time(update, context, "hours")
async def get_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: return await get_relative_time(update, context, "days")

async def get_specific_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        naive_time = datetime.strptime(update.message.text, "%d.%m.%Y %H:%M")
        aware_time = TIMEZONE.localize(naive_time)
        if aware_time < get_current_time():
            raise ValueError("Час вже минув")
        context.user_data['reminder_time'] = aware_time
        await update.message.reply_text("Чудово! Тепер введіть текст нагадування.")
        return GET_TEXT
    except (ValueError, AssertionError):
        await update.message.reply_text("Неправильний формат або час вже минув.")
        return GET_SPECIFIC_DATE

async def get_reminder_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reminder_text = update.message.text
    reminder_time = context.user_data['reminder_time']
    chat_id = update.effective_chat.id
    database.add_reminder_to_db(chat_id, reminder_time, reminder_text)
    await update.message.reply_text(
        f"Гаразд! Я нагадаю тобі:\n*{reminder_text}*\n_{reminder_time.strftime('%d %B %Y року о %H:%M')}_",
        parse_mode='Markdown'
    )
    context.user_data.clear()
    return ConversationHandler.END

async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    reminders = database.get_pending_reminders(chat_id)
    if not reminders:
        await update.message.reply_text("У вас немає активних нагадувань для видалення.")
        return ConversationHandler.END
    
    keyboard = []
    for rem_id, rem_time_utc_str, rem_text in reminders:
        rem_time_utc = pytz.utc.localize(datetime.strptime(rem_time_utc_str, "%Y-%m-%d %H:%M:%S"))
        rem_time_local = rem_time_utc.astimezone(TIMEZONE)
        button_text = f"❌ {rem_text[:20]}... ({rem_time_local.strftime('%d.%m')})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"del_{rem_id}")])
    keyboard.append([InlineKeyboardButton("Скасувати", callback_data="cancel_delete")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Яке нагадування ви хочете видалити?", reply_markup=reply_markup)
    return DELETE_REMINDER

async def delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "cancel_delete":
        await query.edit_message_text("Видалення скасовано.")
        return ConversationHandler.END
    try:
        reminder_id_to_delete = int(data.split("_")[1])
        database.delete_reminder_from_db(reminder_id_to_delete)
        await query.edit_message_text("Нагадування успішно видалено!")
    except (IndexError, ValueError) as e:
        logging.error(f"Помилка при видаленні нагадування: {e}")
        await query.edit_message_text("Сталася помилка. Спробуйте ще раз.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.edit_message_text(text="Дію скасовано.")
    else:
        await update.message.reply_text("Дію скасовано.")
    context.user_data.clear()
    return ConversationHandler.END

async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
    reminders_to_send = database.get_all_pending_reminders_for_check()
    for rem_id, chat_id, rem_text in reminders_to_send:
        try:
            await context.bot.send_message(chat_id=chat_id, text=f"🔔 *НАГАДУВАННЯ* 🔔\n\n{rem_text}", parse_mode='Markdown')
            database.mark_reminder_sent(rem_id)
            logging.info(f"Надіслано нагадування ID {rem_id} для чату {chat_id}")
        except Exception as e:
            logging.error(f"Не вдалося надіслати нагадування ID {rem_id}: {e}")

async def post_init(application):
    commands = [
        BotCommand("start", "Перезапустити бота"),
        BotCommand("set", "Створити нове нагадування"),
        BotCommand("list", "Показати мої нагадування"),
        BotCommand("delete", "Видалити нагадування"),
        BotCommand("time", "Показати поточний час бота"),
        BotCommand("help", "Отримати допомогу"),
        BotCommand("cancel", "Скасувати поточну дію"),
    ]
    await application.bot.set_my_commands(commands)
    logging.info("Меню команд налаштовано.")