from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.filters import Command
from aiogram.types import Message

from bot.utils.role_filter import RoleFilter

router = Router()

@router.callback_query(F.data == "cancel")
async def cancel_adding_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Действие отменено.")
    await callback.answer()

@router.message(Command("cancel"), RoleFilter(allowed_roles=["admin", "coach"]))
async def cancel_adding(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.")