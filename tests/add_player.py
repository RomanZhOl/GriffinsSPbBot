"""
Тесты для модуля добавления игроков
"""
import pytest
from bot.handlers.add_player import (
    start_add_player,
    process_name,
    process_surname,
    process_tg_username,
    process_role_callback,
    process_position_callback,
    process_confirmation, cancel_adding, cancel_adding_callback
)
from bot.utils.states import AddPlayerStates

ROLE_COACH = 2
ROLE_PLAYER = 3

@pytest.mark.asyncio
async def test_successful_add_player_with_position(message, callback, state, mock_db_functions):
    """
    Тест: Успешное добавление игрока с выбором позиции

    Сценарий:
    1. Запускаем команду /add_player
    2. Вводим имя
    3. Вводим фамилию
    4. Вводим никнейм
    5. Выбираем роль "Игрок"
    6. Выбираем позицию "QB"
    7. Подтверждаем
    8. Проверяем, что данные сохранились
    """

    # ========== ШАГ 1: Начало добавления ==========
    message.text = "/add_player"
    await start_add_player(message, state)

    # Проверки:
    # - Вызван метод answer для отправки сообщения
    message.answer.assert_called_once()
    # - Состояние изменилось на "ввод имени"
    current_state = await state.get_state()
    assert current_state == AddPlayerStates.name.state
    # - В сообщении есть текст про ввод имени
    call_args = message.answer.call_args[0][0]
    assert "имя игрока" in call_args.lower()


    # ========== ШАГ 2: Ввод имени ==========
    message.answer.reset_mock()  # Сбрасываем счётчик вызовов
    message.text = "Иван"
    await process_name(message, state)

    # Проверки:
    message.answer.assert_called_once()
    current_state = await state.get_state()
    assert current_state == AddPlayerStates.surname.state
    # Проверяем, что имя сохранилось в state
    data = await state.get_data()
    assert data['name'] == "Иван"


    # ========== ШАГ 3: Ввод фамилии ==========
    message.answer.reset_mock()
    message.text = "Петров"
    await process_surname(message, state)

    # Проверки:
    message.answer.assert_called_once()
    current_state = await state.get_state()
    assert current_state == AddPlayerStates.tg_username.state
    data = await state.get_data()
    assert data['surname'] == "Петров"


    # ========== ШАГ 4: Ввод никнейма ==========
    message.answer.reset_mock()
    message.text = "@ivan_petrov"
    await process_tg_username(message, state)

    # Проверки:
    message.answer.assert_called_once()
    current_state = await state.get_state()
    assert current_state == AddPlayerStates.role.state
    data = await state.get_data()
    # Проверяем, что @ был удалён
    assert data['tg_username'] == "ivan_petrov"
    # Проверяем, что показаны кнопки выбора роли
    call_kwargs = message.answer.call_args[1]
    assert 'reply_markup' in call_kwargs


    # ========== ШАГ 5: Выбор роли "Игрок" (role_id=3) ==========
    callback.message.edit_text.reset_mock()
    callback.data = "role:3"
    await process_role_callback(callback, state)

    # Проверки:
    callback.message.edit_text.assert_called_once()
    current_state = await state.get_state()
    assert current_state == AddPlayerStates.position.state
    data = await state.get_data()
    assert data['role_id'] == ROLE_PLAYER
    # Проверяем, что показаны кнопки с позициями
    call_kwargs = callback.message.edit_text.call_args[1]
    assert 'reply_markup' in call_kwargs


    # ========== ШАГ 6: Выбор позиции "QB" (position_id=1) ==========
    callback.message.edit_text.reset_mock()
    callback.data = "position:1"
    await process_position_callback(callback, state)

    # Проверки:
    callback.message.edit_text.assert_called_once()
    current_state = await state.get_state()
    assert current_state == AddPlayerStates.confirmation.state
    data = await state.get_data()
    assert data['position_id'] == 1
    assert data['position_name'] == 'QB'
    # Проверяем, что показано подтверждение с правильными данными
    call_text = callback.message.edit_text.call_args[0][0]
    assert "Иван" in call_text
    assert "Петров" in call_text
    assert "ivan_petrov" in call_text
    assert "QB" in call_text


    # ========== ШАГ 7: Подтверждение ==========
    callback.message.edit_text.reset_mock()
    callback.data = "confirm:yes"
    await process_confirmation(callback, state)

    # Проверки:
    # - Функция insert_player была вызвана
    mock_db_functions['insert_player'].assert_called_once()
    # - В БД отправлены правильные данные
    saved_data = mock_db_functions['insert_player'].call_args[0][0]
    assert saved_data['name'] == "Иван"
    assert saved_data['surname'] == "Петров"
    assert saved_data['tg_username'] == "ivan_petrov"
    assert saved_data['role_id'] == 3
    assert saved_data['position_id'] == 1
    assert saved_data['position_name'] == 'QB'
    # - Состояние очищено
    current_state = await state.get_state()
    assert current_state is None
    # - Показано сообщение об успехе
    callback.message.edit_text.assert_called_once()
    call_text = callback.message.edit_text.call_args[0][0]
    assert "успешно" in call_text.lower() or "✅" in call_text

@pytest.mark.asyncio
async def test_successful_add_coach(message, callback, state, mock_db_functions):
    """
    Тест: Успешное добавление тренера

    Сценарий:
    1. Запускаем команду /add_player
    2. Вводим имя
    3. Вводим фамилию
    4. Вводим никнейм
    5. Выбираем роль "Тренер"
    6. Подтверждаем
    7. Проверяем, что данные сохранились
    """

    # ========== ШАГ 1: Начало добавления ==========
    message.text = "/add_player"
    await start_add_player(message, state)

    # Проверки:
    # - Вызван метод answer для отправки сообщения
    message.answer.assert_called_once()
    # - Состояние изменилось на "ввод имени"
    current_state = await state.get_state()
    assert current_state == AddPlayerStates.name.state
    # - В сообщении есть текст про ввод имени
    call_args = message.answer.call_args[0][0]
    assert "имя игрока" in call_args.lower()


    # ========== ШАГ 2: Ввод имени ==========
    message.answer.reset_mock()  # Сбрасываем счётчик вызовов
    message.text = "Пал"
    await process_name(message, state)

    # Проверки:
    message.answer.assert_called_once()
    current_state = await state.get_state()
    assert current_state == AddPlayerStates.surname.state
    # Проверяем, что имя сохранилось в state
    data = await state.get_data()
    assert data['name'] == "Пал"


    # ========== ШАГ 3: Ввод фамилии ==========
    message.answer.reset_mock()
    message.text = "Саныч"
    await process_surname(message, state)

    # Проверки:
    message.answer.assert_called_once()
    current_state = await state.get_state()
    assert current_state == AddPlayerStates.tg_username.state
    data = await state.get_data()
    assert data['surname'] == "Саныч"


    # ========== ШАГ 4: Ввод никнейма ==========
    message.answer.reset_mock()
    message.text = "@pal_sanych"
    await process_tg_username(message, state)

    # Проверки:
    message.answer.assert_called_once()
    current_state = await state.get_state()
    assert current_state == AddPlayerStates.role.state
    data = await state.get_data()
    # Проверяем, что @ был удалён
    assert data['tg_username'] == "pal_sanych"
    # Проверяем, что показаны кнопки выбора роли
    call_kwargs = message.answer.call_args[1]
    assert 'reply_markup' in call_kwargs


    # ========== ШАГ 5: Выбор роли "Тренер" (role_id=1) ==========
    callback.message.edit_text.reset_mock()
    callback.data = "role:2"
    await process_role_callback(callback, state)

    # Проверки:
    callback.message.edit_text.assert_called_once()
    current_state = await state.get_state()
    assert current_state == AddPlayerStates.confirmation.state
    data = await state.get_data()
    assert data['role_id'] == ROLE_COACH


    # ========== ШАГ 6: Подтверждение ==========
    callback.message.edit_text.reset_mock()
    callback.data = "confirm:yes"
    await process_confirmation(callback, state)

    # Проверки:
    # - Функция insert_player была вызвана
    mock_db_functions['insert_player'].assert_called_once()
    # - В БД отправлены правильные данные
    saved_data = mock_db_functions['insert_player'].call_args[0][0]
    assert saved_data['name'] == "Пал"
    assert saved_data['surname'] == "Саныч"
    assert saved_data['tg_username'] == "pal_sanych"
    assert saved_data['role_id'] == 2
    # Проверяем, что у тренера НЕТ позиции
    assert 'position_id' not in saved_data
    assert 'position_name' not in saved_data
    # - Состояние очищено
    current_state = await state.get_state()
    assert current_state is None
    # - Показано сообщение об успехе
    callback.message.edit_text.assert_called_once()
    call_text = callback.message.edit_text.call_args[0][0]
    assert "успешно" in call_text.lower() or "✅" in call_text


@pytest.mark.asyncio
async def test_process_name_too_short(message, state):
    """Тест: короткое имя (1 символ) отклоняется"""
    # Устанавливаем состояние
    await state.set_state(AddPlayerStates.name)

    # Вводим короткое имя
    message.text = "А"
    await process_name(message, state)
    current_state = await state.get_state()
    text = message.answer.call_args[0][0]

    # Проверки:
    # 1. Показано сообщение об ошибке
    assert "Имя должно содержать минимум 2 символа" in text
    # 2. Состояние НЕ изменилось (остались в AddPlayerStates.name)
    assert current_state == AddPlayerStates.name.state
    # 3. Данные НЕ сохранились в state.
    data = await state.get_data()
    assert 'name' not in data or data['name'] is None

@pytest.mark.asyncio
async def test_process_surname_too_short(message, state):
    """Тест: короткая фамилия (1 символ) отклоняется"""
    # Устанавливаем состояние
    await state.set_state(AddPlayerStates.surname)

    # Вводим короткую фамилию
    message.text = "А"
    await process_surname(message, state)
    current_state = await state.get_state()
    text = message.answer.call_args[0][0]

    # Проверки:
    # 1. Показано сообщение об ошибке
    assert "Фамилия должна содержать минимум 2 символа" in text
    # 2. Состояние НЕ изменилось (остались в AddPlayerStates.name)
    assert current_state == AddPlayerStates.surname.state
    # 3. Данные НЕ сохранились в state.
    data = await state.get_data()
    assert 'surname' not in data or data['surname'] is None

@pytest.mark.asyncio
async def test_process_nickname_too_short(message, state):
    """Тест: короткий никнейм (менее 5 символов) отклоняется"""
    # Устанавливаем состояние
    await state.set_state(AddPlayerStates.tg_username)

    # Вводим короткий ник
    message.text = "АAAA"
    await process_tg_username(message, state)
    current_state = await state.get_state()
    text = message.answer.call_args[0][0]

    # Проверки:
    # 1. Показано сообщение об ошибке
    assert "Никнейм Telegram должен содержать минимум 5 символов" in text
    # 2. Состояние НЕ изменилось (остались в AddPlayerStates.name)
    assert current_state == AddPlayerStates.tg_username.state
    # 3. Данные НЕ сохранились в state.
    data = await state.get_data()
    assert 'tg_username' not in data or data['tg_username'] is None

@pytest.mark.asyncio
async def test_process_nickname_strip(message, state):
    """Тест: Обработка @ в никнейме — если пользователь вводит @username, символ @ убирается"""
    # Устанавливаем состояние
    await state.set_state(AddPlayerStates.tg_username)

    # Вводим ybrytqv c @
    message.text = "@АAAAA"
    await process_tg_username(message, state)
    current_state = await state.get_state()

    # Проверки:
    # 2. Состояние изменилось (перешло в AddPlayerStates.role)
    assert current_state == AddPlayerStates.role.state
    # 3. Данные сохранились в state.
    data = await state.get_data()
    assert data['tg_username'] == "АAAAA"

cancel_params = [
    ("message", "/cancel"), # отмена по команде
    ("callback", "cancel"), # отмена по кнопке
]

cancel_states_params = [
    AddPlayerStates.name,
    AddPlayerStates.surname,
    AddPlayerStates.tg_username,
    AddPlayerStates.role,
    AddPlayerStates.position,
    AddPlayerStates.confirmation
]

@pytest.mark.parametrize("state_to_test", cancel_states_params)
@pytest.mark.parametrize("event_type,set_value", cancel_params)
@pytest.mark.asyncio
async def test_process_cancel(event_type, set_value, state_to_test, message, callback, state):
    """Проверяет отмену добавления игрока на любом этапе через сообщение или кнопку."""

    message.answer.reset_mock()
    callback.answer.reset_mock()
    callback.message.edit_text.reset_mock()

    # Устанавливаем состояние
    await state.set_state(state_to_test)
    # Добавляем мусор чтобы проверить реальную очистку
    await state.update_data(role="admin", name="Test")

    if event_type == "message":
        # эмулируем ввод "/cancel"
        message.text = set_value
        await cancel_adding(message, state)

        # Проверяем ответ для message
        message.answer.assert_called_once()
        text = message.answer.call_args.args[0]
        assert "Добавление игрока отменено." in text
        callback.answer.assert_not_called()
        callback.message.edit_text.assert_not_called()

    else:  # event_type == "callback"
        # эмулируем нажатие кнопки "cancel"
        callback.data = set_value
        await cancel_adding_callback(callback, state)

        # Проверяем реакцию на callback
        callback.answer.assert_called_once()
        callback.message.edit_text.assert_called_once()
        sent_text = callback.message.edit_text.call_args.args[0]
        assert "Добавление игрока отменено." in sent_text
        message.answer.assert_not_called()

    # Стейт сброшен
    assert await state.get_state() is None

    # Данные очищены
    assert await state.get_data() == {}

