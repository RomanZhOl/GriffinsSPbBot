import logging

import aiosqlite
from bot.config import DB_PATH


async def insert_player(data: dict, role_ids: list[int] | None = None, db_path: str = DB_PATH) -> bool:
    """
    Вставляет игрока в таблицу team и роли в player_roles.
    data — словарь с ключами:
        name, surname, middlename, number, tg_username, tg_id, position_id, status
    role_ids — список id ролей (из таблицы roles), например [2] или [2,3]
    Возвращает True, если игрок создан; False если игрок уже существует (по tg_id или tg_username).
    """

    async with aiosqlite.connect(DB_PATH) as db:
        # Проверка на дубликат по tg_id или tg_username
        query = "SELECT id FROM team WHERE tg_id = ? OR tg_username = ?"
        async with db.execute(query, (data.get("tg_id"), data.get("tg_username"))) as cursor:
            exists = await cursor.fetchone()
            if exists:
                return False  # игрок уже есть

        # Вставка игрока
        cursor = await db.execute(
            """
            INSERT INTO team 
            (name, surname, middlename, number, tg_username, tg_id, position_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("name"),
                data.get("surname"),
                data.get("middlename"),
                data.get("number"),
                data.get("tg_username"),
                data.get("tg_id"),
                data.get("position_id"),
                data.get("status", "active")
            )
        )

        player_id = cursor.lastrowid

        # Вставка ролей (если есть)
        if role_ids:
            # Формируем кортежи (player_id, role_id)
            values = [(player_id, int(rid)) for rid in role_ids]
            await db.executemany(
                "INSERT OR IGNORE INTO player_roles (player_id, role_id) VALUES (?, ?)",
                values
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
            SELECT GROUP_CONCAT(r.role, ', ') as roles
            FROM team t
            LEFT JOIN player_roles pr ON t.id = pr.player_id
            LEFT JOIN roles r ON pr.role_id = r.id
            WHERE t.tg_id = ?
            GROUP BY t.id
            LIMIT 1
        """

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(query, (tg_id,))
        row = await cursor.fetchone()
        await cursor.close()

        return row[0] if row else None

async def list_players(db_path=DB_PATH, only_active: bool = False):
    """
    Получаем список всех игроков/тренеров с их ролями.
    Роли возвращаются как строка через запятую: "admin, coach"
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row

            where_clause = ""
            params = []

            if only_active:
                where_clause = "WHERE t.status = ?"
                params.append("active")

            query = f"""
                SELECT
                    t.id,
                    t.name,
                    t.surname,
                    t.middlename,
                    t.number,
                    t.tg_username,
                    t.tg_id,
                    t.status,
                    p.position,
                    COALESCE(GROUP_CONCAT(r.role, ', '), '') as roles
                FROM team t
                LEFT JOIN positions p ON t.position_id = p.id
                LEFT JOIN player_roles pr ON t.id = pr.player_id
                LEFT JOIN roles r ON pr.role_id = r.id
                {where_clause}
                GROUP BY t.id
                ORDER BY t.name
            """
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            result = [dict(row) for row in rows]
            return result

    except Exception as e:
        logging.error(f"Ошибка при получении списка игроков: {e}")
        return []

async def get_chat_by_position(position_name: str):
    """Возвращает кортеж (chat_id, thread_id) по названию позиции."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM positions WHERE position = ?",
            (position_name,)
        )
        pos_row = await cursor.fetchone()
        if not pos_row:
            return None, None
        position_id = pos_row[0]

        cursor = await db.execute(
            "SELECT chat_id, thread_id FROM chats WHERE position_id = ?",
            (position_id,)
        )
        chat_row = await cursor.fetchone()
        if not chat_row:
            return None, None

        return chat_row[0], chat_row[1]

async def get_all_chats(db_path: str = DB_PATH) -> list[tuple[int, int, str]]:
    """
    Возвращает список всех чатов для опросов.

    Каждая запись — кортеж (chat_id, thread_id, chat_name)
    """
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT chat_id, thread_id, chat_name FROM chats ORDER BY id"
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [(row[0], row[1], row[2]) for row in rows]