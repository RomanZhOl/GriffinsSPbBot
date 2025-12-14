from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from bot.utils.db import get_player_by_id, get_user_role, update_player_field, get_positions
from bot.utils.role_filter import RoleFilter
from bot.utils.states import UpdatePlayerStates
from bot.handlers.cancel import cancel_adding
from bot.utils.keyboards import EDIT_FIELD_INLINE

router = Router()

async def get_positions_keyboard():
    positions = await get_positions()  # [(1, "OL"), (2, "QB"), ...]

    # строим кнопки по строкам (по 2 кнопки в ряд)
    inline_keyboard = []
    row = []
    for i, (pos_id, pos_name) in enumerate(positions, start=1):
        row.append(InlineKeyboardButton(text=pos_name, callback_data=f"position_{pos_id}"))
        if i % 2 == 0:
            inline_keyboard.append(row)
            row = []
    if row:
        inline_keyboard.append(row)  # оставшиеся кнопки

    # добавляем кнопку "Назад" в отдельной строке
    inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    return keyboard

# Inline-кнопки для выбора поля
def get_field_inline_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Имя", callback_data="edit_name"),
             InlineKeyboardButton(text="✏️ Фамилия", callback_data="edit_surname")],
            [InlineKeyboardButton(text="✏️ Отчество", callback_data="edit_middlename"),
             InlineKeyboardButton(text="🔢 Номер", callback_data="edit_number")],
            [InlineKeyboardButton(text="👤 TG username", callback_data="edit_tg_username"),
             InlineKeyboardButton(text="🧭 Позиция", callback_data="edit_position")],
            [InlineKeyboardButton(text="🚦 Статус", callback_data="edit_status")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
        ]
    )

STATUS_INLINE_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ В строю", callback_data="status_active"),
            InlineKeyboardButton(text="💤 В запасе", callback_data="status_inactive"),
            InlineKeyboardButton(text="🤕 Травма", callback_data="status_injured")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back")
        ]
    ]
)

def has_role(roles: str | None, role: str) -> bool:
    if not roles:
        return False
    return role in [r.strip() for r in roles.split(",")]

# --- Начало FSM ---
@router.message(Command("update"), RoleFilter(allowed_roles=["admin", "coach"]))
async def start_update_player(message: Message, state: FSMContext):
    await state.set_state(UpdatePlayerStates.id)
    await message.answer(
        "Начинаем редактирование игрока.\nВведите ID игрока:"
    )

@router.message(UpdatePlayerStates.id)
async def process_player_id(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("ID должен быть числом. Введите корректный ID:")
        return

    player_id = int(text)
    player = await get_player_by_id(player_id)
    if not player:
        await message.answer(f"Игрок с ID {player_id} не найден. Введите другой ID:")
        return

    caller_roles = await get_user_role(message.from_user.id)
    target_roles = player.get("roles")
    if has_role(target_roles, "coach") and not has_role(caller_roles, "admin"):
        await message.answer("Редактирование тренера доступно только администратору.")
        return

    await state.update_data(player_id=player_id)
    await state.set_state(UpdatePlayerStates.menu)

    info = (
        f"ID: {player['id']}\n"
        f"Имя: {player['surname']} {player['name']} {player['middlename']}\n"
        f"Номер: {player['number'] or '—'}\n"
        f"TG username: {player['tg_username'] or '—'}\n"
        f"Позиция: {player['position'] or '—'}\n"
        f"Статус: {player['status']}\n\n"
        "Выберите, что хотите изменить:"
    )
    await message.answer(info, reply_markup=get_field_inline_menu())

# --- Обработка выбора поля через Inline ---
from aiogram.types import CallbackQuery

@router.callback_query(F.data.startswith("edit_") |
                       F.data.startswith("status_") |
                       F.data.startswith("position_") |
                       F.data.in_(["save", "back", "cancel"]))
async def handle_edit_callbacks(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    player_id = data.get("player_id")
    field = data.get("field")
    new_value = data.get("new_value")
    action = query.data

    # Выбор поля
    if action.startswith("edit_"):
        field_name = action[5:]
        await state.update_data(field=field_name, new_value=None)
        await state.set_state(UpdatePlayerStates.edit_field)

        if field_name == "status":
            await query.message.answer("Выберите новый статус:", reply_markup=STATUS_INLINE_KEYBOARD)
        elif field_name == "position":
            keyboard = await get_positions_keyboard()
            await query.message.answer("Выберите новую позицию:", reply_markup=keyboard)
        else:
            await query.message.answer(f"Введите новое значение для {field_name}:", reply_markup=EDIT_FIELD_INLINE)

        await query.answer()
        return

    # Выбор статуса
    if action.startswith("status_"):
        status_value = action[7:]
        await state.update_data(new_value=status_value)
        if field == "status" and player_id:
            await update_player_field(player_id, "status", status_value)
            await state.set_state(UpdatePlayerStates.menu)
            await state.update_data(new_value=None)
            await query.message.answer(f"Статус успешно обновлён: {status_value}", reply_markup=get_field_inline_menu())
        await query.answer()
        return


    if action.startswith("position_"):
        position_id = int(action.split("_")[1])
    await state.update_data(new_value=position_id)
    if player_id:
        await update_player_field(player_id, "position_id", position_id)
        await state.set_state(UpdatePlayerStates.menu)
        await state.update_data(new_value=None)
        await query.message.answer(f"Позиция успешно обновлена.", reply_markup=get_field_inline_menu())
    await query.answer()
    return


    # Сохранение
    if action == "save":
        if not field or new_value is None:
            await query.message.answer("Сначала введите новое значение.")
            await query.answer()
            return
        await update_player_field(player_id, field, new_value)
        await state.set_state(UpdatePlayerStates.menu)
        await state.update_data(new_value=None)
        await query.message.answer(f"{field.capitalize()} успешно обновлено: {new_value}", reply_markup=get_field_inline_menu())
        await query.answer()
        return

    # Назад
    if action == "back":
        await state.set_state(UpdatePlayerStates.menu)
        await state.update_data(new_value=None)
        await query.message.answer(f"Изменение {field} отменено.", reply_markup=get_field_inline_menu())
        await query.answer()
        return

    # Полная отмена
    if action == "cancel":
        await cancel_adding(query.message, state)
        await query.answer()
        return


# --- Ввод нового значения ---
@router.message(UpdatePlayerStates.edit_field)
async def input_field_value(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("field")

    text = message.text.strip()

    # Проверка длины
    if len(text) > 50:
        await message.answer("Слишком длинное значение. Введите корректное значение:", reply_markup=EDIT_FIELD_INLINE)
        return

    # Проверки по типу поля
    if field in ["name", "surname", "middlename"]:
        if not text.isalpha():
            await message.answer(
                "Имя, фамилия или отчество должны содержать только буквы. Попробуйте ещё раз:",
                reply_markup=EDIT_FIELD_INLINE
            )
            return
    elif field == "number":
        if not text.isdigit():
            await message.answer(
                "Номер должен содержать только цифры. Попробуйте ещё раз:",
                reply_markup=EDIT_FIELD_INLINE
            )
            return
    elif field == "tg_username":
        if not all(c.isalnum() or c in "._" for c in text):
            await message.answer(
                "TG username может содержать только буквы, цифры, точки и подчёркивания. Попробуйте ещё раз:",
                reply_markup=EDIT_FIELD_INLINE
            )
            return

    # Для обычных текстовых полей сохраняем значение и показываем кнопки Сохранить/Назад
    await state.update_data(new_value=text)
    await message.answer(
        f"Новое значение: {text}\nНажмите 💾 Сохранить или ⬅️ Назад.",
        reply_markup=EDIT_FIELD_INLINE
    )