import pytest

from bot.utils.role_filter import RoleFilter


@pytest.mark.asyncio
async def test_role_filter_blocks_player(message, mock_role_filter):
    # Пользователь = только player
    mock_role_filter['get_user_role'].return_value = ['player']

    role_filter = RoleFilter(allowed_roles=["admin", "coach"])

    result = await role_filter(message)

    assert result is False