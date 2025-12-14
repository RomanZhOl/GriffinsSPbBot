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
    chat = State()
    notify_players =State()

class UpdatePlayerStates(StatesGroup):
    id = State()
    menu = State()
    edit_name = State()
    edit_surname = State()
    edit_middlename = State()
    edit_number = State()
    edit_tg_username = State()
    edit_position = State()
    edit_status = State()
    edit_field = State()
