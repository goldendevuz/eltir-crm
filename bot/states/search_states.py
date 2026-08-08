from aiogram.dispatcher.filters.state import State, StatesGroup


class SearchStates(StatesGroup):
    QUERY = State()
