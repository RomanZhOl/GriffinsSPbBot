from aiogram.fsm.state import StatesGroup, State

class AddPlayerStates(StatesGroup):
    name = State()
    surname = State()
    tg_username = State()
    role = State()
    position = State()
    confirmation = State()

class CreatePollStates(StatesGroup):
    question = State()
    options = State()
    confirmation = State()