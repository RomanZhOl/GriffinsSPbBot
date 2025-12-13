from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

from bot.utils.db import get_chat_by_position, get_all_chats
from bot.utils.notifications import build_players_mention_text, send_mentions_in_batches
from bot.utils.poll_question import get_training_poll_question
from bot.utils.role_filter import RoleFilter
from bot.utils.states import CreatePollStates


router = Router()

CANCEL_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
    ]
)

@router.callback_query(F.data == "cancel", StateFilter(CreatePollStates))
async def cancel_adding_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Создание опроса отменено.")
    await callback.answer()

@router.message(Command("cancel"), RoleFilter(allowed_roles=["admin", "coach"]))
async def cancel_adding(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Создание опроса отменено.")

#Вход в FSM
@router.message(Command("poll"), RoleFilter(allowed_roles=["admin", "coach"]))
async def start_create_poll(message: Message, state: FSMContext):
    # Разбираем аргумент, если есть
    parts = message.text.split(maxsplit=1)
    args = parts[1].strip() if len(parts) > 1 else None

    if args:
        await quick_poll(message, args)
    else:
        await interactive_poll(message, state)

async def quick_poll(message: Message, topic: str, notify_players: bool = False):
    """Быстрое создание опроса с предустановкой"""
    topic = topic.upper().strip()

    chat_id, thread_id = await get_chat_by_position(topic)
    if not chat_id:
        await message.answer(f"Не удалось найти чат для топика {topic}.")
        return

    question = get_training_poll_question(topic)
    options = ["Буду", "Не буду", "Тренер"]

    await message.bot.send_poll(
        chat_id=chat_id,
        message_thread_id=thread_id,
        question=question,
        options=options,
        is_anonymous=False
    )

    await message.answer(f"Опрос для {topic} отправлен.")

    if notify_players:
        mentions = await build_players_mention_list(position=topic)

        if mentions:
            await send_mentions_in_batches(
                bot=message.bot,
                chat_id=chat_id,
                thread_id=thread_id,
                mentions=mentions
            )


async def interactive_poll(message: Message, state: FSMContext):
    """Интерактивное создание опроса через FSM"""
    await state.set_state(CreatePollStates.question)
    keyboard = CANCEL_KEYBOARD
    await message.answer("Введите вопрос для опроса:",
                         reply_markup=keyboard
                         )

#Шаг ввода вопроса опроса
@router.message(CreatePollStates.question)
async def process_poll_question(message: Message, state: FSMContext):
    keyboard = CANCEL_KEYBOARD
    question = message.text.strip()

    if not question:
        await message.answer("Вопрос не может быть пустым. Введите ещё раз:")
        return

    await state.update_data(question=question)
    await state.set_state(CreatePollStates.options)
    await message.answer("Введите варианты ответа через ;",
                         reply_markup=keyboard)


# Шаг: ввод вариантов опроса
@router.message(CreatePollStates.options)
async def process_poll_options(message: Message, state: FSMContext):
    options_text = message.text.strip()
    if not options_text:
        await message.answer("Варианты ответа не могут быть пустыми. Введите ещё раз:")
        return

    options = [opt.strip() for opt in options_text.split(";") if opt.strip()]
    if len(options) < 2:
        await message.answer("Должно быть как минимум 2 варианта. Попробуйте ещё раз:")
        return
    if len(options) > 10:
        await message.answer("Максимум 10 вариантов. Попробуйте ещё раз:")
        return

    # Сохраняем варианты в FSM
    await state.update_data(options=options)
    await state.set_state(CreatePollStates.chat)

    # Получаем список чатов из БД
    chats = await get_all_chats()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
                            [InlineKeyboardButton(text=name, callback_data=f"chats:{chat_id}:{thread_id}:{name}")]
                            for chat_id, thread_id, name in chats
                        ] + [[InlineKeyboardButton(text="Отмена", callback_data="cancel")]]
    )
    await message.answer("Выберите для кого опрос:", reply_markup=keyboard)


# Шаг: выбор чата
@router.callback_query(F.data.startswith("chats:"), CreatePollStates.chat)
async def process_chat_choice(callback: CallbackQuery, state: FSMContext):
    _, chat_id, thread_id_raw, chat_name = callback.data.split(":")

    # thread_id может быть пустым -> None
    thread_id = int(thread_id_raw) if thread_id_raw.isdigit() else None

    await state.update_data(chat_id=int(chat_id), thread_id=thread_id, chat_name=chat_name)
    await state.set_state(CreatePollStates.notify_players)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="notify:yes")],
            [InlineKeyboardButton(text="Нет", callback_data="notify:no")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
        ]
    )
    await callback.message.edit_text(
        f"Вы выбрали чат: {chat_name}\n\n"
        "Хотите уведомить игроков о новом опросе?",
        reply_markup=keyboard
    )
    await callback.answer()


# Шаг: выбор уведомления
@router.callback_query(F.data.startswith("notify:"), CreatePollStates.notify_players)
async def process_notify_choice(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.split(":")[1]
    notify = choice == "yes"
    await state.update_data(notify_players=notify)
    await state.set_state(CreatePollStates.confirmation)

    data = await state.get_data()
    question = data.get("question")
    options = data.get("options", [])
    chat_name = data.get("chat_name", "не указан")

    options_display = "\n".join(f"{idx+1}. {opt}" for idx, opt in enumerate(options))
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm:yes"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="confirm:no")
            ]
        ]
    )

    await callback.message.edit_text(
        f"Проверьте опрос перед созданием:\n\n"
        f"Вопрос: {question}\n"
        f"Варианты:\n{options_display}\n"
        f"Чат: {chat_name}\n"
        f"Уведомить игроков: {'Да' if notify else 'Нет'}",
        reply_markup=keyboard
    )
    await callback.answer()

# Шаг: подтверждение создания опроса
@router.callback_query(F.data.startswith("confirm:"), CreatePollStates.confirmation)
async def confirm_poll_callback(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]

    if action == "no":
        await state.clear()
        await callback.message.edit_text("Создание опроса отменено.")
        await callback.answer()
        return

    # Если yes — создаём опрос
    data = await state.get_data()
    question = data.get("question")
    options = data.get("options", [])
    chat_id = data.get("chat_id")
    thread_id = data.get("thread_id")
    chat_name = data.get("chat_name")
    notify_players = data.get("notify_players", False)

    if not question or not options or not chat_id:
        await callback.message.edit_text("Ошибка: нет данных для опроса.")
        await state.clear()
        await callback.answer()
        return

    if thread_id:
        sent_poll = await callback.bot.send_poll(
            chat_id=chat_id,
            message_thread_id=thread_id,
            question=question,
            options=options,
            is_anonymous=False
        )
    else:
        sent_poll = await callback.bot.send_poll(
            chat_id=chat_id,
            question=question,
            options=options,
            is_anonymous=False
            )

    # Уведомление игроков
    if notify_players:
        if chat_name == "ALL":
            mention_text = await build_players_mention_text()  # без фильтра по позиции
        else:
            mention_text = await build_players_mention_text(position=chat_name)

        await callback.bot.send_message(
            chat_id=chat_id,
            message_thread_id=thread_id,
            text=f"Новый опрос! {mention_text}"
        )

    await callback.message.edit_text(f"Опрос создан! ID: {sent_poll.message_id}")
    await state.clear()
    await callback.answer()