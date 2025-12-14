from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

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

# Inline-кнопки для подтверждения/отката
EDIT_FIELD_INLINE = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="💾 Сохранить", callback_data="save")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ]
)
