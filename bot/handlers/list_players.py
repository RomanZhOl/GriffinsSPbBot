from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from bot.utils.db import list_players
from bot.utils.role_filter import RoleFilter
import logging

router = Router()

STATUS_MAP = {
    "active": "В строю",
    "injured": "Травма",
    "inactive": "В запасе",
}

STATUS_EMOJI = {
    "active": "✅ ",
    "injured": "🤕 ",
    "inactive": "💤 ",
}

@router.message(Command("players"), RoleFilter(allowed_roles=["admin", "coach"]))
async def show_players(message: Message):
    all_players = await list_players()
    logging.info(f"Запрошен список из {len(all_players)} игроков")

    # ✅ Если БД пустая
    if not all_players:
        await message.answer("📭 В базе пока нет ни одного игрока.")
        return

    # ✅ ФИЛЬТРУЕМ ТОЛЬКО ТЕХ, У КОГО ЕСТЬ ROLE = player
    players = [
        p for p in all_players
        if p.get("roles") and "player" in p["roles"].split(", ")
    ]

    # ✅ Формируем красивый текст
    text = ["📋 <b>Список игроков:</b>\n"]

    for i, player in enumerate(players, start=1):
        # Статус
        status_text = STATUS_MAP.get(player['status'], "Неизвестно")
        status_emoji = STATUS_EMOJI.get(player['status'], "❓")
        # Формируем основную строку
        name_part = f"<b>{player['name']} {player['surname']}</b>"

        # Добавляем username если есть
        if player.get("tg_username"):
            name_part += f" (@{player['tg_username']})"

        # Позиция (только для игроков)
        position_part = f" {player['position']}" if player.get('position') else ""

        # Номер (если есть)
        number_part = f" #{player['number']}" if player.get('number') else ""

        # Собираем всё вместе
        line = f"{status_emoji}{i}. {name_part} — {position_part}{number_part} [{status_text}]\n"
        text.append(line)

    await message.answer("\n".join(text), parse_mode="HTML")

@router.message(Command("coaches"), RoleFilter(allowed_roles=["admin", "coach"]))
async def show_coaches(message: Message):
    all_players = await list_players()
    logging.info(f"Запрошен список из {len(all_players)} игроков")

    # ✅ ФИЛЬТРУЕМ ТОЛЬКО ТЕХ, У КОГО ЕСТЬ ROLE = player
    coaches = [
        c for c in all_players
        if c.get("roles") and "coach" in c["roles"].split(", ")
    ]

    # ✅ Проверяем наличие тренеров
    if not coaches:
        await message.answer("📭 В базе пока нет ни одного тренера.")
        return

    # ✅ Формируем красивый текст
    text = ["📋 <b>Список тренеров:</b>\n"]

    for i, coach in enumerate(coaches, start=1):
        # Статус
        status_text = STATUS_MAP.get(coach['status'], "Неизвестно")
        status_emoji = STATUS_EMOJI.get(coach['status'], "❓")
        # Формируем основную строку
        name_part = f"<b>{coach['name']} {coach['surname']}</b>"

        # Добавляем username если есть
        if coach.get("tg_username"):
            name_part += f" (@{coach['tg_username']})"

        # Позиция (только для игроков)
        position_part = f" {coach['position']}" if coach.get('position') else ""

        # Собираем всё вместе
        line = f"{status_emoji}{i}. {name_part}{position_part} [{status_text}]\n"
        text.append(line)

    await message.answer("\n".join(text), parse_mode="HTML")