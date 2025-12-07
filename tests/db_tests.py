import pytest
from bot.utils import db as db_module

@pytest.mark.asyncio
async def test_get_user_role(temp_db):

    roles = await db_module.get_user_role(123)
    assert set(roles) == {'player', 'coach'}

    roles = await db_module.get_user_role(456)
    assert roles == ['admin']

    roles = await db_module.get_user_role(999)
    assert roles is None

@pytest.mark.asyncio
async def test_get_positions(temp_db):
    """
    Тестируем функцию get_positions:
    - Должна возвращать список кортежей (id, position)
    - Для временной базы проверяем наличие вставленных позиций
    """

    # Получаем позиции
    positions = await db_module.get_positions(temp_db)

    # Проверяем, что вернулся список
    assert isinstance(positions, list)

    # Проверяем, что список не пустой
    assert len(positions) > 0

    # Проверяем конкретные значения (если мы вставляли их в фикстуре)
    expected_positions = [(1, 'Rookie'), (2, 'QB'), (3, 'WR')]
    assert positions == expected_positions

@pytest.mark.asyncio
async def test_list_players(temp_db):
    """
    Тестируем функцию list_players:
    - Должна возвращать список кортежей (id, position)
    - Для временной базы проверяем наличие вставленных позиций
    """

    # Получаем список игроков
    players = await db_module.list_players(temp_db)

    # Проверяем, что вернулся список
    assert isinstance(players, list)
    assert all(isinstance(item, dict) for item in players)

    # Проверяем, что словарь не пустой
    assert all(len(item) > 0 for item in players)

    # Проверяем конкретные значения (если мы вставляли их в фикстуре)
    assert players[0]["tg_id"] == 123
    assert players[1]["tg_id"] == 456
