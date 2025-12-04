import aiosqlite
from bot.config import DB_PATH


async def insert_player(data: dict):
    """
    Вставляет игрока в таблицу team.
    data — словарь с ключами:
        name, surname, middlename, number, tg_username, tg_id, role_id, status
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверка на дубликат по tg_id или tg_username
        query = "SELECT id FROM team WHERE tg_id = ? OR tg_username = ?"
        async with db.execute(query, (data.get("tg_id"), data.get("tg_username"))) as cursor:
            exists = await cursor.fetchone()
            if exists:
                return False  # игрок уже есть

        # Вставка игрока
        await db.execute(
            """
            INSERT INTO team 
            (name, surname, middlename, number, tg_username, tg_id, role_id, position_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("name"),
                data.get("surname"),
                data.get("middlename"),
                data.get("number"),
                data.get("tg_username"),
                data.get("tg_id"),
                data.get("role_id"),
                data.get("position_id"),
                data.get("status", "active")
            )
        )
        await db.commit()
        return True

async def get_positions():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, position FROM positions ORDER BY id")
        rows = await cursor.fetchall()
        await cursor.close()

        # rows будет списком кортежей вида [(1, "OL"), (2, "QB"), ...]
        return rows

async def get_user_role(tg_id: int) -> str | None:
    """
    Возвращает роль пользователя по tg_id.
    Если игрок не найден — возвращает None.
    Если игрок найден — возвращает строку роли ('admin', 'coach', 'player').
    """

    query = """
        SELECT r.role
        FROM team t
        JOIN roles r ON t.role_id = r.id
        WHERE t.tg_id = ?
        LIMIT 1
    """

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(query, (tg_id,))
        row = await cursor.fetchone()
        await cursor.close()

        return row[0] if row else None