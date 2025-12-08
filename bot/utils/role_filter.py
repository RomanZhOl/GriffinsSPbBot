from aiogram.filters import BaseFilter
from aiogram.types import Message
from bot.utils.db import get_user_role


class RoleFilter(BaseFilter):
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, message: Message) -> bool:
        roles_str = await get_user_role(message.from_user.id)

        if not roles_str:
            return False  # пользователь без ролей не допускается

        # Преобразуем строку 'admin, coach' в список ['admin', 'coach']
        user_roles = [r.strip() for r in roles_str.split(",")]

        # Проверяем, есть ли хотя бы одна разрешённая роль у пользователя
        return any(role in self.allowed_roles for role in user_roles)