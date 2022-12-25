from telebot.types import Message
from loader import bot
from states.price_state import PriceStates
from keyboards.inline.locations import city_markup
from keyboards.inline.date import calendar, calendar_1, MyTranslationCalendar
from keyboards.inline.correct import correct
from keyboards.inline.hotels import hotels
from keyboards.inline.get_photo import get_photo, photo_amount
from bot_requests.hotels_request import find_hotels
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from datetime import date
import datetime


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def price(message: Message) -> None:
    """Функция-хэндлер. Присваивает пользователю состояние и спрашивает город."""
    bot.set_state(message.from_user.id, PriceStates.city, message.chat.id)
    bot.send_message(message.from_user.id,
                     f"{message.from_user.first_name}, напишите город или страну в котором хотите посмотреть отели")
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['command'] = message.text
        data['com'] = message


@bot.message_handler(state=PriceStates.city)
def city(message: Message) -> None:
    """Функция-хэндлер. Ловит состояние пользователя,
    вызывает функцию, создающую кнопки и выводит пользователю."""
    bot.send_message(message.from_user.id, f"Вы выбрали: {message.text}")
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
         com = data['com']
    animation = bot.send_animation(message.chat.id, r'https://i.gifer.com/7kRE.gif')
    try:
        city_markup(message.text)
    except Exception:
        bot.send_message(message.from_user.id, 'К сожалению, я не знаю такого города')
        price(com)
    else:
        bot.set_state(message.from_user.id, PriceStates.city_id, message.chat.id)
        bot.send_message(message.from_user.id, 'Уточните, пожалуйста:', reply_markup=city_markup(message.text))
    bot.delete_message(message.chat.id, animation.id)


@bot.callback_query_handler(func=lambda call: True, state=PriceStates.city_id)
def city_callback(call) -> None:
    """Функция, ловит callback нажатой пользователем кнопки"""
    location_and_id = call.data.split(', ')
    bot.edit_message_text(f"Вы выбрали локацию: {location_and_id[0]}", call.message.chat.id, call.message.message_id)
    bot.set_state(call.from_user.id, PriceStates.date_in, call.message.chat.id)
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data['city_id'] = location_and_id[1]
    bot.send_message(call.message.chat.id, 'Выберите дату заезда:', reply_markup=calendar())


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(), state=PriceStates.date_in)
def date_in_callback(c):
    result, key, step = MyTranslationCalendar(min_date=date.today(), max_date=datetime.date(2024, 12, 31)).process(
        c.data)
    if not result and key:
        word = 'дату'
        if LSTEP[step] == 'year':
            word = 'год'
        elif LSTEP[step] == 'month':
            word = 'месяц'
        elif LSTEP[step] == 'day':
            word = 'день'
        bot.edit_message_text(f"Выберите {word}", c.message.chat.id, c.message.message_id, reply_markup=key)
    elif result:
        bot.edit_message_text(f"Дата заезда: {result}", c.message.chat.id, c.message.message_id)
        bot.set_state(c.from_user.id, PriceStates.date_out, c.message.chat.id)
        with bot.retrieve_data(c.from_user.id, c.message.chat.id) as data:
            data['date_in'] = result
        bot.send_message(c.message.chat.id, 'Выберите дату выезда:', reply_markup=calendar_1(result))


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(), state=PriceStates.date_out)
def date_out_callback(c):
    with bot.retrieve_data(c.from_user.id, c.message.chat.id) as data:
        date = data['date_in']
    dates = str(date).split('-')

    result, key, step = MyTranslationCalendar(min_date=datetime.date(int(dates[0]), int(dates[1]), int(dates[2])),
                                              max_date=datetime.date(2024, 12, 31)).process(c.data)
    if not result and key:
        word = 'дату'
        if LSTEP[step] == 'year':
            word = 'год'
        elif LSTEP[step] == 'month':
            word = 'месяц'
        elif LSTEP[step] == 'day':
            word = 'день'
        bot.edit_message_text(f"Выберите {word}", c.message.chat.id, c.message.message_id, reply_markup=key)

    elif result:
        bot.edit_message_text(f"Дата выезда: {result}", c.message.chat.id, c.message.message_id)
        bot.set_state(c.from_user.id, PriceStates.correct, c.message.chat.id)
        with bot.retrieve_data(c.from_user.id, c.message.chat.id) as data:
            data['date_out'] = result
        bot.send_message(c.message.chat.id, 'Данные верны?', reply_markup=correct())


@bot.callback_query_handler(func=lambda call: True, state=PriceStates.correct)
def correct_callback(call) -> None:
    """Функция, ловит callback нажатой пользователем кнопки"""
    if call.data == 'yes':
        bot.edit_message_text(f"Подтверждаю!", call.message.chat.id, call.message.message_id)
        bot.set_state(call.from_user.id, PriceStates.hotels, call.message.chat.id)
        bot.send_message(call.message.chat.id, 'Выберите количество отелей которые необходимо вывести: ',
                         reply_markup=hotels())
    elif call.data == 'no':
        bot.send_message(call.message.chat.id, 'Давайте попробуем еще раз')
        bot.set_state(call.from_user.id, PriceStates.city, call.message.chat.id)
        bot.send_message(call.from_user.id,
                         f"{call.from_user.first_name}, напишите город в котором хотите посмотреть отели")


@bot.callback_query_handler(func=lambda call: True, state=PriceStates.hotels)
def hotels_callback(call) -> None:
    """Функция, ловит callback нажатой пользователем кнопки"""
    bot.edit_message_text(f"Вы выбрали {call.data} отелей", call.message.chat.id, call.message.message_id)
    bot.set_state(call.from_user.id, PriceStates.photo, call.message.chat.id)
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data['hotels'] = int(call.data)
    bot.send_message(call.message.chat.id, 'Нужно ли выводить фотографии?', reply_markup=get_photo())


@bot.callback_query_handler(func=lambda call: True, state=PriceStates.photo)
def photo_callback(call) -> None:
    """Функция, ловит callback нажатой пользователем кнопки"""
    if call.data == 'yes':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.set_state(call.from_user.id, PriceStates.photo_amount, call.message.chat.id)
        bot.send_message(call.message.chat.id, 'Сколько фотографий выводим?', reply_markup=photo_amount())
    elif call.data == 'no':
        bot.send_message(call.message.chat.id, 'Выводим результат')
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            region = data['city_id']
            date_in = data['date_in']
            date_out = data['date_out']
            command = data['command']
            hotels = data['hotels']
            photos = 0

        for i in range(hotels):
            bot.send_message(call.from_user.id, f"{i + 1}-й отель:")
            animation = bot.send_animation(call.message.chat.id, r'https://i.gifer.com/7kRE.gif')

            hotel_data, photo_data = find_hotels(i, region, date_in, date_out, command, photos)

            text = f'Название отеля - {hotel_data["name"]}\n' \
                   f'Цена за одну ночь - {hotel_data["price"]}\n' \
                   f'Цена за весь период - {hotel_data["total_price"]}\n' \
                   f'Местоположение :'
            bot.send_message(call.from_user.id, f"{text}")
            bot.send_location(call.message.chat.id, latitude=hotel_data['lat'], longitude=hotel_data['long'])

            bot.delete_message(call.message.chat.id, animation.id)


@bot.callback_query_handler(func=lambda call: True, state=PriceStates.photo_amount)
def photo_amount_callback(call) -> None:
    """Функция, ловит callback нажатой пользователем кнопки"""
    bot.edit_message_text(f"Вы выбрали {call.data} фотографий", call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, 'Выводим результат')
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data['photo_amount'] = int(call.data)
        region = data['city_id']
        date_in = data['date_in']
        date_out = data['date_out']
        command = data['command']
        hotels = data['hotels']
        photos = int(call.data)

    for i in range(hotels):
        bot.send_message(call.from_user.id, f"{i + 1}-й отель:")
        animation = bot.send_animation(call.message.chat.id, r'https://i.gifer.com/7kRE.gif')

        hotel_data, photo_data = find_hotels(i, region, date_in, date_out, command, photos)

        if photo_data:
            bot.send_media_group(call.message.chat.id, photo_data)

        text = f'Название отеля - {hotel_data["name"]}\n' \
               f'Цена за одну ночь - {hotel_data["price"]}\n' \
               f'Цена за весь период - {hotel_data["total_price"]}\n' \
               f'Местоположение :'
        bot.send_message(call.from_user.id, f"{text}")
        bot.send_location(call.message.chat.id, latitude=hotel_data['lat'], longitude=hotel_data['long'])

        bot.delete_message(call.message.chat.id, animation.id)
