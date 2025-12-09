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

async def list_players(db_path=DB_PATH):
    """
    Получаем список всех игроков/тренеров с их ролями.
    Роли возвращаются как строка через запятую: "admin, coach"
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            query = """SELECT
                        t.id,
                        t.name,
                        t.surname,
                        t.middlename,
                        t.number,
                        t.tg_username,
                        t.tg_id,
                        t.status,
                        p.position,
                        GROUP_CONCAT(r.role, ', ') as roles
                    FROM team t
                    LEFT JOIN positions p ON t.position_id = p.id
                    LEFT JOIN player_roles pr ON t.id = pr.player_id
                    LEFT JOIN roles r ON pr.role_id = r.id
                    GROUP BY t.id
                    ORDER BY t.name
                """

            cursor = await db.execute(query)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    except Exception as e:
        print(f"Ошибка при получении списка игроков: {e}")
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
            "SELECT id, thread_id FROM chats WHERE position_id = ?",
            (position_id,)
        )
        chat_row = await cursor.fetchone()
        if not chat_row:
            return None, None