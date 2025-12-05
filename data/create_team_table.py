import aiosqlite
import asyncio
from bot.config import DB_PATH, DEFAULT_ADMIN

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

        # Создаём таблицу team (БЕЗ role_id!)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS team (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            surname TEXT NOT NULL,
            middlename TEXT,
            number TEXT,
            tg_username TEXT UNIQUE,
            tg_id INTEGER UNIQUE,
            position_id INTEGER,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (position_id) REFERENCES positions(id)
        )
        """)

        # Создаём таблицу связей player_roles (many-to-many)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS player_roles (
            player_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            PRIMARY KEY (player_id, role_id),
            FOREIGN KEY (player_id) REFERENCES team(id) ON DELETE CASCADE,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        )
        """)

        # Добавляем дефолтного администратора (если его ещё нет)
        cursor = await db.execute(
            "SELECT id FROM team WHERE tg_id = ?",
            (DEFAULT_ADMIN["tg_id"],)
        )
        existing_admin = await cursor.fetchone()

        if not existing_admin:
            print("Создаём дефолтного администратора...")

            # Вставляем админа в таблицу team
            cursor = await db.execute("""
                INSERT INTO team (name, surname, middlename, number, tg_username, tg_id, position_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                DEFAULT_ADMIN["name"],
                DEFAULT_ADMIN["surname"],
                DEFAULT_ADMIN["middlename"],
                DEFAULT_ADMIN["number"],
                DEFAULT_ADMIN["tg_username"],
                DEFAULT_ADMIN["tg_id"],
                DEFAULT_ADMIN["position_id"],
                DEFAULT_ADMIN["status"]
            ))

            admin_id = cursor.lastrowid

            # Назначаем все три роли (admin, coach, player)
            await db.executemany(
                "INSERT OR IGNORE INTO player_roles (player_id, role_id) VALUES (?, ?)",
                [(admin_id, 1), (admin_id, 2), (admin_id, 3)]  # 1=admin, 2=coach, 3=player
            )

            print(f"✅ Дефолтный администратор создан с ID={admin_id}")
        else:
            print("ℹ️ Дефолтный администратор уже существует")

        await db.commit()
        print("✅ Все таблицы созданы и базовые данные вставлены")

if __name__ == "__main__":
    asyncio.run(create_all_tables())