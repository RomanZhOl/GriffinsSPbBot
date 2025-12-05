"""
Фикстуры для тестирования Telegram бота
"""
import aiosqlite
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import User, Chat, Message, CallbackQuery
from aiogram.fsm.storage.base import StorageKey
from bot.utils import db as db_module


@pytest.fixture
def bot():
    """
    Фикстура: создаёт мок объекта Bot

    Зачем: Bot нужен для работы aiogram, но мы не хотим
    отправлять реальные запросы к Telegram API
    """
    return Bot(token="123456:TEST_TOKEN")


@pytest.fixture
def storage():
    """
    Фикстура: создаёт in-memory хранилище для FSM

    Зачем: FSM нужно где-то хранить состояния и данные.
    В тестах используем память вместо Redis/файлов
    """
    return MemoryStorage()


@pytest_asyncio.fixture
async def state(storage, bot):
    """
    Фикстура: создаёт FSMContext для работы с состояниями
    """
    user = User(id=12345, is_bot=False, first_name="Test")
    chat = Chat(id=12345, type="private")

    # Создаём ключ для хранилища
    key = StorageKey(
        bot_id=bot.id,
        chat_id=chat.id,
        user_id=user.id
    )

    context = FSMContext(
        storage=storage,
        key=key
    )

    yield context

    await context.clear()


@pytest.fixture
def user():
    """
    Фикстура: создаёт мок пользователя Telegram

    Зачем: Объекты Message и CallbackQuery содержат информацию
    о пользователе. Используем одного тестового пользователя везде
    """
    return User(
        id=12345,
        is_bot=False,
        first_name="Иван",
        last_name="Иванов",
        username="test_user"
    )


@pytest.fixture
def chat():
    """
    Фикстура: создаёт мок чата Telegram

    Зачем: Message и CallbackQuery также содержат информацию о чате
    """
    return Chat(id=12345, type="private")


@pytest.fixture
def message(bot, user, chat):
    """
    Фикстура: создаёт мок объекта Message

    Зачем: Обработчики принимают Message как параметр.
    Мокаем методы answer() и другие, чтобы не отправлять реальные сообщения
    """
    msg = MagicMock(spec=Message)
    msg.bot = bot
    msg.from_user = user
    msg.chat = chat
    msg.text = ""  # По умолчанию пустой текст

    # Мокаем асинхронные методы
    msg.answer = AsyncMock()
    msg.reply = AsyncMock()
    msg.edit_text = AsyncMock()

    return msg


@pytest.fixture
def callback(bot, user, chat, message):
    """
    Фикстура: создаёт мок объекта CallbackQuery

    Зачем: Обработчики кнопок принимают CallbackQuery.
    Мокаем методы answer() и edit_text()
    """
    cb = MagicMock(spec=CallbackQuery)
    cb.bot = bot
    cb.from_user = user
    cb.message = message
    cb.data = ""  # По умолчанию пустые данные callback

    # Мокаем асинхронные методы
    cb.answer = AsyncMock()
    cb.message.edit_text = AsyncMock()

    return cb


@pytest.fixture
def mock_db_functions():
    """
    Фикстура: мокает все функции работы с БД
    """
    with patch('bot.handlers.add_player.insert_player', new_callable=AsyncMock) as mock_insert, \
            patch('bot.handlers.add_player.get_positions', new_callable=AsyncMock) as mock_get_pos:

        # Настраиваем дефолтные возвращаемые значения
        mock_insert.return_value = True
        mock_get_pos.return_value = [
            (1, 'QB'),
            (2, 'RB'),
            (3, 'WR')
        ]

        yield {
            'insert_player': mock_insert,
            'get_positions': mock_get_pos
        }


@pytest.fixture
def mock_role_filter():
    """
    Фикстура: мокает RoleFilter

    Зачем: RoleFilter проверяет права доступа через БД.
    В тестах мы хотим контролировать, пропускает он пользователя или нет
    """
    with patch('bot.handlers.add_player.RoleFilter') as mock_filter:
        # По умолчанию фильтр пропускает всех
        mock_filter.return_value.__call__ = AsyncMock(return_value=True)
        yield mock_filter

@pytest_asyncio.fixture
async def temp_db(tmp_path):
    db_file = tmp_path / "test.db"

    async with aiosqlite.connect(db_file) as conn:
        await conn.executescript("""
        CREATE TABLE team (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER UNIQUE
        );

        CREATE TABLE roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT
        );

        CREATE TABLE player_roles (
            player_id INTEGER,
            role_id INTEGER
        );
        
        CREATE TABLE positions (
            id INTEGER,
            position TEXT
        );

        INSERT INTO roles (role) VALUES ('player'), ('coach'), ('admin');
        INSERT INTO team (tg_id) VALUES (123), (456);
        INSERT INTO team (position_id) VALUES (2), (3);
        INSERT INTO player_roles (player_id, role_id) VALUES
            (1, 1),  -- player_id=1 => player
            (1, 2),  -- player_id=1 => coach
            (2, 3);  -- player_id=2 => admin
        INSERT INTO positions (id, position) VALUES
            (1, 'Rookie'),  
            (2, 'QB'),  
            (3, "WR"); 
        """)
        await conn.commit()

    original_db_path = db_module.DB_PATH
    db_module.DB_PATH = str(db_file)
    try:
        yield db_file
    finally:
        db_module.DB_PATH = original_db_path