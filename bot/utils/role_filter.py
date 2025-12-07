from aiogram.filters import BaseFilter
from aiogram.types import Message
from bot.utils.db import get_user_role


class RoleFilter(BaseFilter):
    def __init__(self, allowed_roles: list[str]):  # Изменено: list[int] → list[str]
        self.allowed_roles = allowed_roles

    async def __call__(self, message: Message) -> bool:
        user_roles = await get_user_role(message.from_user.id)

        if user_roles is None:
            return False  # пользователь без ролей не допускается

        # Проверяем, есть ли хотя бы одна разрешённая роль у пользователя
        return any(role in self.allowed_roles for role in user_roles)