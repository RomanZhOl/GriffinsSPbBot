from bot.config import DB_PATH
from bot.utils.db import list_players

async def build_players_mention_text(position: str | None = None, db_path=DB_PATH) -> str:
    """
    Формирует текст с упоминаниями игроков.
    Если указан `position`, упоминаются только игроки с этой позицией.
    Если у игрока есть tg_username — тегаем через @username,
    иначе выводим 'Имя Фамилия'.
    """
    players = await list_players(db_path=db_path)
    mentions = []

    for p in players:
        if position and p.get("position") != position:
            continue  # пропускаем игроков, не соответствующих позиции

        tg_username = p.get("tg_username")
        if tg_username:
            mentions.append(f"@{tg_username}")
        else:
            name = p.get("name", "")
            surname = p.get("surname", "")
            mentions.append(f"{name} {surname}".strip())

    return ", ".join(mentions) if mentions else "Нет игроков для упоминания"