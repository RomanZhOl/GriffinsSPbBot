"""
Тесты для модуля список игроков -- команда /coaches
"""

import pytest
from bot.handlers.list_players import show_coaches
from bot.utils.role_filter import RoleFilter
from tests.list_players_players import mock_players_data

@pytest.mark.asyncio
@pytest.mark.parametrize("roles", [
    ['coach'],
    ['admin'],
    ['coach', 'admin'],
    ['player', 'admin'],
])
async def test_show_all_coaches(roles, message, mock_db_functions, mock_role_filter):
    """
    Тест: команда /coaches без параметров возвращает всех игроков.

    Сценарий:
    1. В БД есть 2 игрока , 1 тренер и 1 тренер + игрок
    2. Вызываем /coaches без параметров
    3. Проверяем, что возвращаются только 2 тренера (игроки исключены)
    """

    # ========== ARRANGE (Подготовка) ==========
    # Настраиваем мок list_players
    mock_role_filter['get_user_role'].return_value = roles
    mock_db_functions['list_players'].return_value = mock_players_data

    # Команда без параметров
    message.text = "/coaches"


    # ========== ACT (Действие) ==========

    await show_coaches(message)


    # ========== ASSERT (Проверка) ==========

    # 1. Проверяем, что list_players был вызван
    mock_db_functions['list_players'].assert_called_once()

    # 2. Проверяем, что message.answer был вызван один раз
    message.answer.assert_called_once()

    # 3. Получаем текст ответа
    response_text = message.answer.call_args[0][0]

    # 4. Проверяем, что в ответе есть заголовок
    assert "Список тренеров" in response_text

    # 5. Проверяем, что в ответе есть все тренера
    assert "Алексей" in response_text
    assert "Иванов" in response_text
    assert "Николай" in response_text
    assert "Петрович" in response_text

    # 6. Проверяем, что игроки НЕ включён в список
    assert "Пётр" not in response_text
    assert "Сидоров" not in response_text

    # 7. Проверяем наличие username'ов игроков
    assert "@alex_coach" in response_text
    assert "@nick_player_coach" in response_text

    # 8. Проверяем наличие позиции для игрока и тренера
    assert "LB" in response_text

    # 9. Проверяем наличие номера для игрока и тренера
    assert "#69" in response_text

    # 10. Проверяем статусы (эмодзи или текст)
    assert "В строю" in response_text
    assert "В запасе" in response_text

    # 11. Проверяем, что используется HTML форматирование
    call_kwargs = message.answer.call_args[1]
    assert call_kwargs.get('parse_mode') == "HTML"

@pytest.mark.asyncio
async def test_show_coaches_empty_db(message, mock_db_functions):
    """
    Тест: команда /coaches когда БД полностью пустая.

    Сценарий:
    1. В БД нет ни одной записи
    2. Вызываем /coaches
    3. Проверяем сообщение "📭 В базе пока нет ни одного тренера."
    """

    # ========== ARRANGE (Подготовка) ==========

    # Мокаем пустую БД
    mock_db_functions['list_players'].return_value = []

    # Команда без параметров
    message.text = "/coaches"


    # ========== ACT (Действие) ==========

    await show_coaches(message)


    # ========== ASSERT (Проверка) ==========

    # 1. Проверяем, что list_players был вызван
    mock_db_functions['list_players'].assert_called_once()

    # 2. Проверяем, что message.answer был вызван один раз
    message.answer.assert_called_once()

    # 3. Получаем текст ответа
    response_text = message.answer.call_args[0][0]

    # 4. Проверяем точное сообщение
    assert response_text == "📭 В базе пока нет ни одного тренера."

@pytest.mark.asyncio
async def test_show_players_only_player_db(message, mock_db_functions):
    """
    Тест: команда /coaches без параметров когда в БД толкьо тренера.

    Сценарий:
    1. 1 тренер
    2. Вызываем /coaches без параметров
    3. Проверяем, что "📭 В базе пока нет ни одного тренера."
    """

    # ========== ARRANGE (Подготовка) ==========

    # Мокаем данные из БД: 1 игрок
    mock_players_data = [
        {
            'id': 1,
            'name': 'Алексей',
            'surname': 'Иванов',
            'tg_username': 'alexу',
            'position': 'QB',
            'number': '11',
            'status': 'active',
            'roles': 'player'  # Только игрок (должен быть исключён)
        }
    ]

    # Настраиваем мок list_players
    mock_db_functions['list_players'].return_value = mock_players_data

    # Команда без параметров
    message.text = "/coaches"


    # ========== ACT (Действие) ==========

    await show_coaches(message)


    # ========== ASSERT (Проверка) ==========

    # 1. Проверяем, что list_players был вызван
    mock_db_functions['list_players'].assert_called_once()

    # 2. Проверяем, что message.answer был вызван один раз
    message.answer.assert_called_once()

    # 3. Получаем текст ответа
    response_text = message.answer.call_args[0][0]

    # 4. Проверяем точное сообщение
    assert response_text == "📭 В базе пока нет ни одного тренера."