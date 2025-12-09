from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.utils.db import insert_player, get_positions
from bot.utils.role_filter import RoleFilter
from bot.utils.states import AddPlayerStates
import logging

# Константы для ролей
ROLE_COACH = 2
ROLE_PLAYER = 3

router = Router()

CANCEL_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
    ]
)

SKIP_KEYBOARD = keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Пропустить", callback_data="skip")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
    ]
)

@router.callback_query(F.data == "cancel")
async def cancel_adding_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Добавление игрока отменено.")
    await callback.answer()

@router.message(Command("cancel"), RoleFilter(allowed_roles=["admin", "coach"]))
async def cancel_adding(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Добавление игрока отменено.")

@router.callback_query(F.data == "skip", AddPlayerStates.tg_username)
async def skip_tg_username(callback: CallbackQuery, state: FSMContext):
    await state.update_data(tg_username=None)
    await callback.answer()
    await move_to_role_step(callback.message, state)

#Вход в FSM
@router.message(Command("add_player"), RoleFilter(allowed_roles=["admin", "coach"]))
async def start_add_player(message: Message, state: FSMContext):
    await state.set_state(AddPlayerStates.name)
    keyboard = CANCEL_KEYBOARD
    await message.answer(
        "Начинаем добавление игрока.\n"
        "Введите имя игрока:",
         reply_markup=keyboard
    )

#Шаг добавления имени
@router.message(AddPlayerStates.name)
async def process_name(message: Message, state: FSMContext):
    keyboard = CANCEL_KEYBOARD
    name = message.text.strip()

    if not name or len(name) < 2:
        await message.answer("Имя должно содержать минимум 2 символа. Попробуйте ещё раз:",
                             reply_markup=keyboard)
        return

    await state.update_data(name=name)
    await state.set_state(AddPlayerStates.surname)
    await message.answer("Введите фамилию игрока:",
                         reply_markup=keyboard)

#Шаг добавления фамилии
@router.message(AddPlayerStates.surname)
async def process_surname(message: Message, state: FSMContext):
    keyboard = CANCEL_KEYBOARD
    surname = message.text.strip()

    if not surname or len(surname) < 2:
        await message.answer("Фамилия должна содержать минимум 2 символа. Попробуйте ещё раз:",
                             reply_markup=keyboard)
        return

    await state.update_data(surname=surname)
    await state.set_state(AddPlayerStates.tg_username)
    await message.answer("Введите никнейм Telegram игрока (с @ или без):",
                         reply_markup=SKIP_KEYBOARD)

#Шаг добавления tg_username
@router.message(AddPlayerStates.tg_username)
async def process_tg_username(message: Message, state: FSMContext):
    keyboard = SKIP_KEYBOARD

    tg_username = message.text.strip().lstrip("@")

    if tg_username:
        if len(tg_username) < 5:
            await message.answer(
                "Никнейм Telegram должен содержать минимум 5 символов.\n"
                "Либо нажмите «Пропустить».",
                reply_markup=keyboard
            )
            return

        await state.update_data(tg_username=tg_username)
    else:
        # Пустой ввод → показываем кнопку пропуска
        await message.answer(
            "Введите никнейм Telegram (минимум 5 символов) или нажмите «Пропустить».",
            reply_markup=keyboard
        )
        return

    # Переход к выбору роли
    await move_to_role_step(message, state)

async def move_to_role_step(message: Message, state: FSMContext):
    await state.set_state(AddPlayerStates.role)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Только игрок", callback_data="role:player")],
            [InlineKeyboardButton(text="Только тренер", callback_data="role:coach")],
            [InlineKeyboardButton(text="Игрок + тренер", callback_data="role:both")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
        ]
    )
    await message.answer("Выберите роль для пользователя:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("role:"), AddPlayerStates.role)
async def process_role_choice(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.split(":")[1]

    role_ids = []
    if choice == "player":
        role_ids.append(ROLE_PLAYER)
    elif choice == "coach":
        role_ids.append(ROLE_COACH)
    elif choice == "both":
        role_ids.extend([ROLE_PLAYER, ROLE_COACH])

    await state.update_data(role_ids=role_ids)

    # ✅ подтверждаем коллбек сразу
    await callback.answer()

    if ROLE_PLAYER in role_ids:
        # Спрашиваем позицию
        await state.set_state(AddPlayerStates.position)
        positions = await get_positions()
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                                [InlineKeyboardButton(text=pos[1], callback_data=f"position:{pos[0]}")]
                                for pos in positions
                            ] + [[InlineKeyboardButton(text="Отмена", callback_data="cancel")]]
        )
        await callback.message.edit_text("Выберите позицию игрока:", reply_markup=keyboard)
    else:
        # Только тренер — формируем текст подтверждения напрямую
        data = await state.get_data()
        roles_text = ", ".join(["Игрок" if r==ROLE_PLAYER else "Тренер" for r in role_ids])
        await show_confirmation(callback, state)
        await state.set_state(AddPlayerStates.confirmation)



@router.callback_query(F.data.startswith("position:"), AddPlayerStates.position)
async def process_position_callback(callback: CallbackQuery, state: FSMContext):
    position_id = int(callback.data.split(":")[1])
    positions = await get_positions()
    positions_dict = {pos[0]: pos[1] for pos in positions}
    position_name = positions_dict.get(position_id)
    await state.update_data(position_id=position_id, position_name=position_name)
    await show_confirmation(callback, state)
    await callback.answer()


ROLE_MAP = {
    ROLE_PLAYER: "Игрок",
    ROLE_COACH: "Тренер"
}

async def show_confirmation(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    role_ids = data.get("role_ids", [])
    role_text = ", ".join([ROLE_MAP.get(rid, str(rid)) for rid in role_ids])

    # Позиция только если есть роль игрока
    position_text = f"\nПозиция: {data.get('position_name', 'н/д')}" if ROLE_PLAYER in role_ids else ""

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
    role_ids = data.get("role_ids", [])

    if not role_ids:
        await callback.message.edit_text("Ошибка: роль не выбрана")
        await state.clear()
        await callback.answer()
        return

    logging.debug(f"Player data: {data}")  # debug вместо info для отладочных сообщений

    try:
        success = await insert_player(data, role_ids)

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
