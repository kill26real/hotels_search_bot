from telebot.handler_backends import StatesGroup, State


class PriceStates(StatesGroup):
    city = State()
    city_id = State()
    date_in = State()
    date_out = State()
    correct = State()
    hotels = State()
    photo = State
    photo_amount = State()
