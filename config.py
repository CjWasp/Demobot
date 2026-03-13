import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
COURSE_NAME = "Финансовая грамотность — демо"
FULL_COURSE_URL = os.getenv("FULL_COURSE_URL", "https://t.me/sergofinance")
