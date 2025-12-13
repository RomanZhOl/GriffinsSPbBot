from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from bot.utils.db import list_players, get_positions
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

def has_role(person: dict, role: str) -> bool:
    """Проверяет, есть ли у человека указанная роль"""
    roles = person.get("roles", "")
    return role in [r.strip() for r in roles.split(",")]

def format_person_line(person: dict, index: int, show_position: bool = True) -> str:
    """
    Форматирует одну строку для человека (игрока или тренера).

    Args:
        person: словарь с данными человека
        index: номер в списке
        show_position: показывать ли позицию (для игроков True, для тренеров может быть True/False)

    Returns:
        Отформатированная строка
    """
    status_text = STATUS_MAP.get(person['status'], "Неизвестно")
    status_emoji = STATUS_EMOJI.get(person['status'], "❓")

    name_part = f"<b>{person['name']} {person['surname']}</b>"

    if person.get("tg_username"):
        name_part += f" (@{person['tg_username']})"

    position_part = f" {person['position']}" if show_position and person.get('position') else ""
    number_part = f" #{person['number']}" if person.get('number') else ""

    return f"{status_emoji}{index}. {name_part} — {position_part}{number_part} [{status_text}] -- ID {person['id']} \n"



@router.message(Command("players"), RoleFilter(allowed_roles=["admin", "coach"]))
async def show_players(message: Message):
    logging.info(f"[show_players] Вызов команды от {message.from_user.id}, текст: {message.text}")
    all_players = await list_players()
    logging.info(f"[show_players] Список игроков получен: {all_players}")

    # Фильтруем только игроков
    players = [p for p in all_players if has_role(p, "player")]

    if not players:
        await message.answer("📭 В базе пока нет ни одного игрока.")
        return

    # Получаем все позиции из БД
    positions_rows = await get_positions()
    valid_positions = {pos[1].upper() for pos in positions_rows}

    # Разбор аргумента команды
    args = None
    if message.text:
        parts = message.text.strip().split(maxsplit=1)
        if len(parts) == 2:
            args = parts[1].strip().upper()

    if args and args not in valid_positions:
        await message.answer(
            f"❌ Неверная позиция '{args}'.\n"
            f"Выберите из списка: {', '.join(valid_positions)}\n"
            f"Или отправьте команду без параметра, чтобы получить всех игроков."
        )
        return

    # Если указан аргумент, фильтруем по позиции
    if args:
        players = [p for p in players if p.get("position", "").upper() == args]

    if not players:
        await message.answer("📭 Игроков с такой позицией не найдено.")
        return

    # Формируем красивый текст
    text = ["📋 <b>Список игроков:</b>\n"]

    for i, player in enumerate(players, start=1):
        line = format_person_line(player, i, show_position=True)
        text.append(line)

    await message.answer("\n".join(text), parse_mode="HTML")

@router.message(Command("coaches"), RoleFilter(allowed_roles=["admin", "coach"]))
async def show_coaches(message: Message):
    # Разбор аргумента команды
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) > 1:
        await message.answer("❌ Команда /coaches не принимает аргументы.")
        return
    
    all_players = await list_players()
    logging.info(f"Запрошен список тренеров")

    # Фильтруем только тренеров
    coaches = [c for c in all_players if has_role(c, "coach")]

    if not coaches:
        await message.answer("📭 В базе пока нет ни одного тренера.")
        return

    # Формируем красивый текст
    text = ["📋 <b>Список тренеров:</b>\n"]

    for i, coach in enumerate(coaches, start=1):
        # Показываем позицию, если тренер одновременно игрок
        line = format_person_line(coach, i, show_position=True)
        text.append(line)

    await message.answer("\n".join(text), parse_mode="HTML")