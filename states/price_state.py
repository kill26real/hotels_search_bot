from telebot.handler_backends import StatesGroup, State


class PriceStates(StatesGroup):
    """Функция, создающая кастомные состояния"""
    city = State()
    city_id = State()
    date_in = State()
    date_out = State()
    correct = State()
    hotels = State()
    photo = State()
    photo_amount = State()
    min_price = State()
    max_price = State()
    max_dist = State()
