"""
Тесты для модуля список игроков -- команда /players
"""

import pytest
from bot.handlers.list_players import show_players
from bot.utils.role_filter import RoleFilter

mock_players_data = [
    {
        'id': 1,
        'name': 'Иван',
        'surname': 'Петров',
        'tg_username': 'ivan_p',
        'position': 'QB',
        'number': '10',
        'status': 'active',
        'roles': 'player'
    },
    {
        'id': 2,
        'name': 'Пётр',
        'surname': 'Сидоров',
        'tg_username': 'petr_s',
        'position': 'QB',
        'number': '12',
        'status': 'injured',
        'roles': 'player'
    },
    {
        'id': 3,
        'name': 'Алексей',
        'surname': 'Иванов',
        'tg_username': 'alex_coach',
        'position': None,
        'number': None,
        'status': 'active',
        'roles': 'coach'
    },
    {
        'id': 4,
        'name': 'Николай',
        'surname': 'Петрович',
        'tg_username': 'nick_player_coach',
        'position': 'LB',
        'number': '69',
        'status': 'inactive',
        'roles': 'coach, player, admin'
    }
]

@pytest.mark.asyncio
@pytest.mark.parametrize("roles", [
    ['coach'],
    ['admin'],
    ['coach', 'admin'],
    ['player', 'admin'],
])
async def test_show_all_players(roles, message, mock_db_functions,mock_role_filter):
    """
    Тест: команда /players без параметров возвращает всех игроков.

    Сценарий:
    1. В БД есть 2 игрока , 1 тренер и 1 тренер + игрок
    2. Вызываем /players без параметров
    3. Проверяем, что возвращаются только 3 игрока (тренер исключён)
    """

    # ========== ARRANGE (Подготовка) ==========
    # Настраиваем мок list_players
    mock_role_filter['get_user_role'].return_value = roles
    mock_db_functions['list_players'].return_value = mock_players_data

    # Команда без параметров
    message.text = "/players"


    # ========== ACT (Действие) ==========

    await show_players(message)


    # ========== ASSERT (Проверка) ==========

    # 1. Проверяем, что list_players был вызван
    mock_db_functions['list_players'].assert_called_once()

    # 2. Проверяем, что message.answer был вызван один раз
    message.answer.assert_called_once()

    # 3. Получаем текст ответа
    response_text = message.answer.call_args[0][0]

    # 4. Проверяем, что в ответе есть заголовок
    assert "Список игроков" in response_text

    # 5. Проверяем, что в ответе есть все игроки
    assert "Иван" in response_text
    assert "Петров" in response_text
    assert "Пётр" in response_text
    assert "Сидоров" in response_text
    assert "Николай" in response_text
    assert "Петрович" in response_text

    # 6. Проверяем, что тренер НЕ включён в список
    assert "Алексей" not in response_text
    assert "Иванов" not in response_text

    # 7. Проверяем наличие username'ов игроков
    assert "@ivan_p" in response_text
    assert "@petr_s" in response_text
    assert "@nick_player_coach" in response_text

    # 8. Проверяем наличие позиций
    assert "QB" in response_text
    assert "LB" in response_text

    # 9. Проверяем наличие номеров
    assert "#10" in response_text
    assert "#12" in response_text
    assert "#69" in response_text

    # 10. Проверяем статусы (эмодзи или текст)
    assert "В строю" in response_text
    assert "Травма" in response_text
    assert "В запасе" in response_text

    # 11. Проверяем, что используется HTML форматирование
    call_kwargs = message.answer.call_args[1]
    assert call_kwargs.get('parse_mode') == "HTML"

@pytest.mark.asyncio
async def test_show_players_empty_db(message, mock_db_functions):
    """
    Тест: команда /players когда БД полностью пустая.

    Сценарий:
    1. В БД нет ни одной записи
    2. Вызываем /players
    3. Проверяем сообщение "📭 В базе пока нет ни одного игрока."
    """

    # ========== ARRANGE (Подготовка) ==========

    # Мокаем пустую БД
    mock_db_functions['list_players'].return_value = []

    # Команда без параметров
    message.text = "/players"


    # ========== ACT (Действие) ==========

    await show_players(message)


    # ========== ASSERT (Проверка) ==========

    # 1. Проверяем, что list_players был вызван
    mock_db_functions['list_players'].assert_called_once()

    # 2. Проверяем, что message.answer был вызван один раз
    message.answer.assert_called_once()

    # 3. Получаем текст ответа
    response_text = message.answer.call_args[0][0]

    # 4. Проверяем точное сообщение
    assert response_text == "📭 В базе пока нет ни одного игрока."

@pytest.mark.asyncio
async def test_show_players_only_coach_db(message, mock_db_functions):
    """
    Тест: команда /players без параметров когда в БД толкьо тренера.

    Сценарий:
    1. 1 тренер
    2. Вызываем /players без параметров
    3. Проверяем, что "📭 В базе пока нет ни одного игрока."
    """

    # ========== ARRANGE (Подготовка) ==========

    # Мокаем данные из БД: 1 тренер
    mock_players_data = [
        {
            'id': 1,
            'name': 'Алексей',
            'surname': 'Иванов',
            'tg_username': 'alex_coach',
            'position': None,
            'number': None,
            'status': 'active',
            'roles': 'coach'  # Только тренер (должен быть исключён)
        }
    ]

    # Настраиваем мок list_players
    mock_db_functions['list_players'].return_value = mock_players_data

    # Команда без параметров
    message.text = "/players"


    # ========== ACT (Действие) ==========

    await show_players(message)


    # ========== ASSERT (Проверка) ==========

    # 1. Проверяем, что list_players был вызван
    mock_db_functions['list_players'].assert_called_once()

    # 2. Проверяем, что message.answer был вызван один раз
    message.answer.assert_called_once()

    # 3. Получаем текст ответа
    response_text = message.answer.call_args[0][0]

    # 4. Проверяем точное сообщение
    assert response_text == "📭 В базе пока нет ни одного игрока."


@pytest.mark.asyncio
@pytest.mark.parametrize("command_text", [
    "/players QB",
    "/players qb",
    "/players qB",
    "/players Qb"
])
async def test_show_all_players_with_args(command_text, message, mock_db_functions):
    """
    Тест: команда /players QB возвращает все записи с QB.

    Сценарий:
    1. В БД есть 2 игрока , 1 тренер и 1 тренер + игрок
    2. Вызываем /players без параметров
    3. Проверяем, что возвращаются только 2 игрока (QB)
    """

    # ========== ARRANGE (Подготовка) ==========
    # Настраиваем мок list_players
    mock_db_functions['list_players'].return_value = mock_players_data

    # Команда без параметров
    message.text = command_text


    # ========== ACT (Действие) ==========

    await show_players(message)


    # ========== ASSERT (Проверка) ==========

    # 1. Проверяем, что list_players был вызван
    mock_db_functions['list_players'].assert_called_once()

    # 2. Проверяем, что message.answer был вызван один раз
    message.answer.assert_called_once()

    # 3. Получаем текст ответа
    response_text = message.answer.call_args[0][0]

    # 4. Проверяем, что в ответе есть заголовок
    assert "Список игроков" in response_text

    # 5. Проверяем, что в ответе есть все игроки
    assert "Иван" in response_text
    assert "Петров" in response_text
    assert "Пётр" in response_text
    assert "Сидоров" in response_text

    # 6. Проверяем, что тренер НЕ включён в список
    assert "Алексей" not in response_text
    assert "Иванов" not in response_text

    # 7. Проверяем, что LB НЕ включён в список
    assert "Николай" not in response_text
    assert "Петрович" not in response_text

    # 7. Проверяем наличие username'ов игроков
    assert "@ivan_p" in response_text
    assert "@petr_s" in response_text
    assert "@nick_player_coach" not in response_text

    # 8. Проверяем наличие позиций
    assert "QB" in response_text
    assert response_text.count("QB") == 2
    assert "LB" not in response_text

    # 9. Проверяем наличие номеров
    assert "#10" in response_text
    assert "#12" in response_text
    assert "#69" not in response_text

    # 10. Проверяем статусы (эмодзи или текст)
    assert "В строю" in response_text
    assert "Травма" in response_text
    assert "В запасе" not in response_text

    # 11. Проверяем, что используется HTML форматирование
    call_kwargs = message.answer.call_args[1]
    assert call_kwargs.get('parse_mode') == "HTML"

@pytest.mark.asyncio
async def test_show_all_players_with_invalid_args(message, mock_db_functions):
    """
    Тест: команда /players ABC с неверным аргументом

    Сценарий:
    1. Вызываем /players ABC с неверным аргументом
    3. Проверяем, что возвращается ошибка
    """

    # ========== ACT (Действие) ==========
    # Настраиваем мок list_players
    mock_db_functions['list_players'].return_value = mock_players_data

    # Команда с нвеерным параметром
    message.text = "/players ABC"

    # ========== ACT (Действие) ==========
    await show_players(message)


    # ========== ASSERT (Проверка) ==========

    # 1. Проверяем, что list_players был вызван
    mock_db_functions['list_players'].assert_called_once()

    # 2. Проверяем, что message.answer был вызван один раз
    message.answer.assert_called_once()

    # 3. Получаем текст ответа
    response_text = message.answer.call_args[0][0]

    assert "f❌ Неверная позиция '{args}'.\n"
    f"Выберите из списка: OL, QB, DL, TE, RB, CB, ROOKIE, WR, LB\n"
    f"Или отправьте команду без параметра, чтобы получить всех игроков." in response_text

@pytest.mark.asyncio
async def test_show_players_with_args_zero_OL(message, mock_db_functions):
    """
    Тест: команда /players OL вслучае когда в БД нет игркоов спозицией OL

    Сценарий:
    1. В БД есть 2 игрока QB , 1 тренер и 1 тренер + игрок LB
    2. Вызываем /players OL
    3. Проверяем, что возвращаются ошибка
    """

    # ========== ARRANGE (Подготовка) ==========
    # Настраиваем мок list_players
    mock_db_functions['list_players'].return_value = mock_players_data

    # Команда без параметров
    message.text = "/players OL"


    # ========== ACT (Действие) ==========

    await show_players(message)

    # ========== ASSERT (Проверка) ==========

    # 1. Проверяем, что list_players был вызван
    mock_db_functions['list_players'].assert_called_once()

    # 2. Проверяем, что message.answer был вызван один раз
    message.answer.assert_called_once()

    # 3. Получаем текст ответа
    response_text = message.answer.call_args[0][0]

    # 4. Проверяем точное сообщение
    assert response_text == "📭 Игроков с такой позицией не найдено."