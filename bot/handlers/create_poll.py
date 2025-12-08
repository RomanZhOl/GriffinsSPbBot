from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

from bot.utils.role_filter import RoleFilter
from bot.utils.states import CreatePollStates

router = Router()

POLL_CHANNEL_ID = -1003400681585
THREAD_CHANNEL_ID = 2

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
@router.message(Command("create_poll"), RoleFilter(allowed_roles=["admin", "coach"]))
async def start_create_poll(message: Message, state: FSMContext):
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
    await state.set_state(CreatePollStates.confirmation)

    # Получаем вопрос из FSM
    data = await state.get_data()
    question = data.get("question")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm:yes"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="confirm:no")
            ]
        ]
    )

    # Отправляем сообщение с подтверждением
    options_display = "\n".join(f"{idx+1}. {opt}" for idx, opt in enumerate(options))
    await message.answer(
        f"Проверьте опрос перед созданием:\n\n"
        f"Вопрос: {question}\n"
        f"Варианты:\n{options_display}",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("confirm:"), CreatePollStates.confirmation)
async def confirm_poll_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
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

    if not question or not options:
        await callback.message.edit_text("Ошибка: нет данных для опроса.")
        await state.clear()
        await callback.answer()
        return

    sent_poll = await bot.send_poll(
        chat_id=POLL_CHANNEL_ID,
        message_thread_id=THREAD_CHANNEL_ID,
        question=question,
        options=options,
        is_anonymous=True
    )

    await callback.message.edit_text(f"Опрос создан! ID: {sent_poll.message_id}")
    await state.clear()
    await callback.answer()