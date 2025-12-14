from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()
#Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Получаем путь к корню проекта (родитель папки bot/)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "team.db"

#Данные дефолтного админа
DEFAULT_ADMIN = {
    "name": os.getenv("ADMIN_NAME", "Admin"),
    "surname": os.getenv("ADMIN_SURNAME", "User"),
    "middlename": os.getenv("ADMIN_MIDDLENAME"),
    "number": os.getenv("ADMIN_NUMBER"),
    "tg_username": os.getenv("ADMIN_TG_USERNAME"),
    "tg_id": int(os.getenv("ADMIN_TG_ID", 0)),  # Важно: преобразуем в int!
    "position_id": int(os.getenv("ADMIN_POSITION_ID", 1)),
    "status": os.getenv("ADMIN_STATUS", "active")
}

# Константы для ролей
ROLE_COACH = 2
ROLE_PLAYER = 3