import os
import pytz
from dotenv import load_dotenv


load_dotenv()


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if TOKEN is None:

    raise ValueError("Не знайдено TELEGRAM_BOT_TOKEN. Переконайтесь, що у вас є .env файл з цим значенням.")

TIMEZONE_STR = "Europe/Kyiv"
TIMEZONE = pytz.timezone(TIMEZONE_STR)