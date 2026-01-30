from bot.config import DB_PATH
from bot.utils.db import list_players

async def build_players_mention_list(
        position: str | None = None,
        db_path=DB_PATH
) -> list[str]:
    """
    Формирует список упоминаний игроков.
    - Если указан `position`, фильтрует по позиции.
    - Если есть tg_username — упоминание через @username.
    - Если нет username, но есть tg_id — упоминание через tg://user?id=.
    - Если нет и tg_id — вывод 'Имя Фамилия'.
    """
    players = await list_players(
        db_path=db_path,
        only_active=True
    )
    mentions: list[str] = []

    for p in players:
        if position and p.get("position") != position:
            continue

        username = p.get("tg_username")
        tg_id = p.get("tg_id")
        name = p.get("name", "")
        surname = p.get("surname", "")
        full_name = f"{name} {surname}".strip()

        if username:
            mentions.append(f"@{username}")

        elif tg_id:
            # HTML-формат упоминания по ID
            mentions.append(f'<a href="tg://user?id={tg_id}">{full_name}</a>')

        else:
            mentions.append(full_name)

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
            text=text,
            parse_mode="HTML"   # обязательно для упоминаний через tg_id
        )
