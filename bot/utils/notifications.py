from bot.config import DB_PATH
from bot.utils.db import list_players

async def build_players_mention_list(
        position: str | None = None,
        db_path=DB_PATH
) -> list[str]:
    """
    Формирует текст с упоминаниями игроков.
    Если указан `position`, упоминаются только игроки с этой позицией.
    Если у игрока есть tg_username — тегаем через @username,
    иначе выводим 'Имя Фамилия'.
    """
    players = await list_players(db_path=db_path)
    mentions: list[str] = []

    for p in players:
        if position and p.get("position") != position:
            continue

        if p.get("tg_username"):
            mentions.append(f"@{p['tg_username']}")
        else:
            name = p.get("name", "")
            surname = p.get("surname", "")
            mentions.append(f"{name} {surname}".strip())

    return mentions


async def send_mentions_in_batches(
        bot,
        chat_id: int,
        thread_id: int | None,
        mentions: list[str],
        batch_size: int = 8
):
    for i in range(0, len(mentions), batch_size):
        chunk = mentions[i:i + batch_size]
        text = "Новый опрос! " + " ".join(chunk)

        await bot.send_message(
            chat_id=chat_id,
            message_thread_id=thread_id,
            text=text
        )