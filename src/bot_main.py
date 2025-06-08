import logging
from telegram.ext import (
    Application, CommandHandler, ConversationHandler,
    MessageHandler, CallbackQueryHandler, filters
)

from bot_config import TOKEN
import bot_handlers as handlers
import bot_database as database

def main() -> None:
    print("--- [main.py] Функція main() почала роботу ---")
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    database.init_db()
    application = Application.builder().token(TOKEN).post_init(handlers.post_init).build()

    set_conv = ConversationHandler(
        entry_points=[CommandHandler("set", handlers.set_reminder_start)],
        states={
            handlers.CHOOSE_TIME_OPTION: [CallbackQueryHandler(handlers.handle_level1_button)],
            handlers.CHOOSE_CUSTOM_TYPE: [CallbackQueryHandler(handlers.handle_level2_button)],
            handlers.GET_MINUTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_minutes)],
            handlers.GET_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_hours)],
            handlers.GET_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_days)],
            handlers.GET_SPECIFIC_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_specific_date)],
            handlers.GET_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_reminder_text)],
        },
        fallbacks=[CommandHandler("cancel", handlers.cancel)],
        per_message=False
    )
    delete_conv = ConversationHandler(
        entry_points=[CommandHandler("delete", handlers.delete_start)],
        states={handlers.DELETE_REMINDER: [CallbackQueryHandler(handlers.delete_confirm)]},
        fallbacks=[CommandHandler("cancel", handlers.cancel)],
        per_message=False
    )

    application.add_handler(set_conv)
    application.add_handler(delete_conv)
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("list", handlers.list_reminders))
    application.add_handler(CommandHandler("time", handlers.get_server_time))

    job_queue = application.job_queue
    job_queue.run_repeating(handlers.check_reminders, interval=30, first=10)
    
    print("--- [main.py] Все налаштовано, зараз буде запущено run_polling() ---")
    logging.info("Запускаємо бота...")
    application.run_polling()

if __name__ == "__main__":
    main()