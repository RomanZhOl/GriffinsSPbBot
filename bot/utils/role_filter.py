from aiogram.filters import BaseFilter
from aiogram.types import Message
from bot.utils.db import get_user_role


class RoleFilter(BaseFilter):
    def __init__(self, allowed_roles: list[int]):
        self.allowed_roles = allowed_roles

    async def __call__(self, message: Message) -> bool:
        user_role = await get_user_role(message.from_user.id)

        if user_role is None:
            return False  # пользователь без роли не допускается

        return user_role in self.allowed_roles
