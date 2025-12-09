from aiogram.filters import BaseFilter
from aiogram.types import Message
from bot.utils.db import get_user_role


class RoleFilter(BaseFilter):
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, message: Message) -> bool:
        roles_str = await get_user_role(message.from_user.id)
        print(f"[RoleFilter] user_id={message.from_user.id}, roles_str={roles_str}")
        if not roles_str:
            return False
        user_roles = [r.strip() for r in roles_str.split(",")]
        result = any(role in self.allowed_roles for role in user_roles)
        print(f"[RoleFilter] user_roles={user_roles}, allowed_roles={self.allowed_roles}, pass={result}")
        return result