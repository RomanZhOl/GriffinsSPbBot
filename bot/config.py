from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
# Получаем путь к корню проекта (родитель папки bot/)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "team.db"