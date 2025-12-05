import aiosqlite
from bot.config import DB_PATH

async def get_user_role(tg_id: int, db_path: str | None = None) -> list[str] | None:
    """
    Возвращает список ролей пользователя по tg_id.
    Если игрок не найден — возвращает None.
    Если игрок найден — возвращает список строк ролей (['admin', 'coach', 'player']).
    """
    db_path = db_path or DB_PATH
    query = """
        SELECT r.role
        FROM team t
        JOIN player_roles pr ON t.id = pr.player_id
        JOIN roles r ON pr.role_id = r.id
        WHERE t.tg_id = ?
    """

    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(query, (tg_id,))
            rows = await cursor.fetchall()  # fetchall вместо fetchone!
            await cursor.close()

            if rows:
                # Возвращаем список всех ролей
                return [row[0] for row in rows]
            return None
    except Exception as e:
        print(f"Ошибка при получении ролей пользователя {tg_id}: {e}")
        return None



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

async def insert_player(data: dict, role_ids: list[int], db_path=DB_PATH):
    """
    Вставляет игрока в таблицу team и назначает ему роли.
    data — словарь с ключами:
        name, surname, middlename, number, tg_username, tg_id, position_id, status
    role_ids — список ID ролей, например [3] или [2,3]
    """
    if not role_ids:
        raise ValueError("Игрок должен иметь хотя бы одну роль")

    try:
        async with aiosqlite.connect(db_path) as db:
            conditions = []
            params = []

            if data.get("tg_id"):
                conditions.append("tg_id = ?")
                params.append(data["tg_id"])

            if data.get("tg_username"):
                conditions.append("tg_username = ?")
                params.append(data["tg_username"])

            if conditions:
                # Проверка на дубликат по tg_id или tg_username
                query = f"SELECT id FROM team WHERE {' OR '.join(conditions)}"
                async with db.execute(query, tuple(params)) as cursor:
                    exists = await cursor.fetchone()
                    if exists:
                        return False # игрок уже есть

            # Вставка игрока в team (БЕЗ role_id)
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

            player_id = cursor.lastrowid  # ✅ ID нового игрока

            # Вставка ролей в player_roles (many-to-many)
            if role_ids:
                await db.executemany(
                    "INSERT INTO player_roles (player_id, role_id) VALUES (?, ?)",
                    [(player_id, rid) for rid in role_ids]
                )

            await db.commit()
            return True

    except Exception as e:
        print(f"Ошибка при добавлении игрока: {e}")
        return False

async def get_positions(db_path=DB_PATH):
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT id, position FROM positions ORDER BY id")
        rows = await cursor.fetchall()
        await cursor.close()
        # rows будет списком кортежей вида [(1, "OL"), (2, "QB"), ...]
        return rows

