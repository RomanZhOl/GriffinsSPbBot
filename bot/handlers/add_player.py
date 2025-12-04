from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.utils.db import insert_player, get_positions
from bot.utils.role_filter import RoleFilter
from bot.utils.states import AddPlayerStates

# Константы для ролей
ROLE_COACH = 2
ROLE_PLAYER = 3

router = Router()


@router.message(F.text == "/add_player", RoleFilter(allowed_roles=["admin", "coach"]))
async def start_add_player(message: Message, state: FSMContext):
    await state.set_state(AddPlayerStates.name)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
        ]
    )
    await message.answer(
        "Начинаем добавление игрока.\n"
        "Введите имя игрока:",
         reply_markup=keyboard
    )

@router.callback_query(F.data == "cancel")
async def cancel_adding_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Добавление игрока отменено.")
    await callback.answer()

@router.message(F.text == "/cancel", StateFilter('*'))
async def cancel_adding(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Добавление игрока отменено.")


@router.message(AddPlayerStates.name)
async def process_name(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
        ]
    )
    name = message.text.strip()

    if not name or len(name) < 2:
        await message.answer("Имя должно содержать минимум 2 символа. Попробуйте ещё раз:",
                             reply_markup=keyboard)
        return

    await state.update_data(name=name)
    await state.set_state(AddPlayerStates.surname)
    await message.answer("Введите фамилию игрока:",
                         reply_markup=keyboard)


@router.message(AddPlayerStates.surname)
async def process_surname(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
        ]
    )
    surname = message.text.strip()

    if not surname or len(surname) < 2:
        await message.answer("Фамилия должна содержать минимум 2 символа. Попробуйте ещё раз:",
                             reply_markup=keyboard)
        return

    await state.update_data(surname=surname)
    await state.set_state(AddPlayerStates.tg_username)
    await message.answer("Введите никнейм Telegram игрока (с @ или без):",
                         reply_markup=keyboard)


@router.message(AddPlayerStates.tg_username)
async def process_tg_username(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
        ]
    )
    tg_username = message.text.strip().lstrip("@")

    if not tg_username or len(tg_username) < 5:
        await message.answer("Никнейм Telegram должен содержать минимум 5 символов. Попробуйте ещё раз:",
                             reply_markup=keyboard)
        return

    await state.update_data(tg_username=tg_username)
    await state.set_state(AddPlayerStates.role)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Тренер", callback_data=f"role:{ROLE_COACH}")],
            [InlineKeyboardButton(text="Игрок", callback_data=f"role:{ROLE_PLAYER}")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
        ]
    )
    await message.answer("Выберите роль:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("role:"), AddPlayerStates.role)
async def process_role_callback(callback: CallbackQuery, state: FSMContext):
    role_id = int(callback.data.split(":")[1])
    await state.update_data(role_id=role_id)

    if role_id == ROLE_COACH:
        await show_confirmation(callback, state)
    else:
        try:
            positions = await get_positions()
            if not positions:
                await callback.message.edit_text("Ошибка: список позиций пуст. Обратитесь к администратору.")
                await state.clear()
                await callback.answer()
                return

            position_buttons = [
                [InlineKeyboardButton(text=pos[1], callback_data=f"position:{pos[0]}")]
                for pos in positions
            ]
            position_buttons.append([InlineKeyboardButton(text="Отмена", callback_data="cancel")])
            keyboard = InlineKeyboardMarkup(inline_keyboard=position_buttons)

            await state.set_state(AddPlayerStates.position)
            await callback.message.edit_text("Выберите позицию игрока:", reply_markup=keyboard)
        except Exception as e:
            await callback.message.edit_text(f"Ошибка при загрузке позиций: {str(e)}")
            await state.clear()

    await callback.answer()


@router.callback_query(F.data.startswith("position:"), AddPlayerStates.position)
async def process_position_callback(callback: CallbackQuery, state: FSMContext):
    position_id = int(callback.data.split(":")[1])
    positions = await get_positions()
    for pos in positions:
        if pos[0] == position_id:
            position_name = pos[1]
            break
    await state.update_data(position_id=position_id, position_name=position_name)
    await show_confirmation(callback, state)
    await callback.answer()


async def show_confirmation(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    role_text = "Тренер" if data["role_id"] == ROLE_COACH else "Игрок"
    position_text = f"\nПозиция: {data.get('position_name', 'н/д')}" if data["role_id"] == ROLE_PLAYER else ""

    confirmation_text = (
        f"Проверьте данные:\n\n"
        f"Имя: {data['name']}\n"
        f"Фамилия: {data['surname']}\n"
        f"Telegram: @{data['tg_username']}\n"
        f"Роль: {role_text}{position_text}\n\n"
        f"Всё верно?"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm:yes"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="confirm:no")
            ]
        ]
    )

    await state.set_state(AddPlayerStates.confirmation)
    await callback.message.edit_text(confirmation_text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("confirm:"), AddPlayerStates.confirmation)
async def process_confirmation(callback: CallbackQuery, state: FSMContext):
    if callback.data == "confirm:no":
        await state.clear()
        await callback.message.edit_text("Добавление игрока отменено.")
        await callback.answer()
        return

    data = await state.get_data()

    try:
        success = await insert_player(data)

        if success:
            await callback.message.edit_text(
                f"✅ Пользователь успешно добавлен:\n"
                f"{data['name']} {data['surname']} (@{data['tg_username']})"
            )
        else:
            await callback.message.edit_text(
                f"❌ Игрок с никнеймом @{data['tg_username']} уже существует!"
            )
    except Exception as e:
        await callback.message.edit_text(f"Ошибка при сохранении: {str(e)}")
    finally:
        await state.clear()

    await callback.answer()