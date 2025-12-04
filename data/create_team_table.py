import aiosqlite
import asyncio
from bot.config import DB_PATH


ROLES = ["admin", "coach", "player"]
POSITIONS = ["OL", "QB", "RB", "TE", "WR", "DL", "LB", "CB", "Rookie"]

async def create_all_tables():
    async with aiosqlite.connect(DB_PATH) as db:
        # Создаём таблицу roles
        await db.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT UNIQUE NOT NULL
        )
        """)
        # Вставляем базовые роли
        await db.executemany(
            "INSERT OR IGNORE INTO roles (role) VALUES (?)",
            [(r,) for r in ROLES]
        )

        # Создаём таблицу positions
        await db.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position TEXT UNIQUE NOT NULL
        )
        """)
        # Вставляем базовые позиции
        await db.executemany(
            "INSERT OR IGNORE INTO positions (position) VALUES (?)",
            [(p,) for p in POSITIONS]
        )

        # Создаём таблицу team
        await db.execute("""
        CREATE TABLE IF NOT EXISTS team (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            surname TEXT NOT NULL,
            middlename TEXT,
            number TEXT,
            tg_username TEXT UNIQUE,
            tg_id INTEGER UNIQUE,
            role_id INTEGER NOT NULL,
            position_id INTEGER,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (role_id) REFERENCES roles(id),
            FOREIGN KEY (position_id) REFERENCES positions(id)
        )
        """)

        await db.commit()
        print("Все таблицы созданы и базовые данные вставлены")

if __name__ == "__main__":
    asyncio.run(create_all_tables())
