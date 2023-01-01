from telebot.types import Message
from telebot.apihelper import ApiTelegramException, ApiInvalidJSONException
from loader import bot
from states.price_state import PriceStates
from keyboards.inline.locations import city_markup
from keyboards.inline.date import calendar, calendar_1, MyTranslationCalendar
from keyboards.inline.correct import correct
from keyboards.inline.hotels import hotels
from keyboards.inline.get_photo import get_photo, photo_amount
from bot_requests.hotels_request import find_hotels, find_best_hotel
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from datetime import date
import datetime
from requests.exceptions import ReadTimeout, ConnectTimeout, ConnectionError
import os
import sqlite3 as sq
from handlers.hotel_search.history import history


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def price(message: Message) -> None:
    """Функция-хэндлер. Обрабатывает команды с поиском отелей, присваивает состояние и спрашивает город."""
    try:
        for file in os.listdir():
            if file.endswith(".jpg"):
                os.remove(file)
    except PermissionError:
        pass
    bot.set_state(message.from_user.id, PriceStates.city, message.chat.id)
    bot.send_message(message.from_user.id,
                     f"{message.from_user.first_name}, напишите город или страну в котором хотите посмотреть отели")
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['command'] = message.text
        data['com'] = message
        data['command_date'] = datetime.datetime.now()


@bot.message_handler(state=PriceStates.city)
def city(message: Message) -> None:
    """Функция-хэндлер. Ловит состояние пользователя,
    вызывает функцию, создающую кнопки с локациями и выводит пользователю."""
    bot.send_message(message.from_user.id, f"Вы выбрали: {message.text}")
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        com = data['com']
    animation = bot.send_animation(message.chat.id, r'https://i.gifer.com/7kRE.gif')

    try:
        bot.set_state(message.from_user.id, PriceStates.city_id, message.chat.id)
        bot.send_message(message.from_user.id, 'Уточните, пожалуйста:', reply_markup=city_markup(message.text))
        bot.delete_message(message.chat.id, animation.id)

    except TypeError:
        bot.delete_message(message.chat.id, animation.id)
        bot.send_message(message.from_user.id, 'К сожалению, я не знаю такой локации')
        price(com)

    except (NameError, AttributeError):
        bot.delete_message(message.chat.id, animation.id)
        bot.send_message(message.from_user.id, 'К сожалению, из-за санкций, РФ нельзя использовать')
        price(com)

    except (ReadTimeout, ApiTelegramException, ApiInvalidJSONException, ConnectTimeout, ConnectionError):
        bot.delete_message(message.chat.id, animation.id)
        bot.send_message(message.from_user.id, "К сожалению, возникла ошибка на сервере. Попробуйте еще раз!")
        price(com)


@bot.callback_query_handler(func=lambda call: True, state=PriceStates.city_id)
def city_callback(call) -> None:
    """Функция, ловит callback нажатой пользователем кнопки с локацией и вызывает функцию, создающую кнопки с датой заселения"""
    if call.data == 'back':
        bot.set_state(call.from_user.id, PriceStates.city, call.message.chat.id)
        bot.edit_message_text(
            f"{call.from_user.first_name}, напишите город или страну в котором хотите посмотреть отели",
            call.message.chat.id,
            call.message.message_id)
    else:
        location_and_id = call.data.split(', ')
        bot.edit_message_text(f"Вы выбрали локацию: {location_and_id[0]}", call.message.chat.id,
                              call.message.message_id)
        bot.set_state(call.from_user.id, PriceStates.date_in, call.message.chat.id)
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data['city_id'] = location_and_id[1]
            data['location_name'] = location_and_id[0]
        bot.send_message(call.message.chat.id, 'Выберите дату заезда:', reply_markup=calendar())


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(), state=PriceStates.date_in)
def date_in_callback(c):
    """Функция, ловит callback нажатой пользователем кнопки с датой и вызывает функцию, создающую кнопки с датой выселения"""
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
    """Функция, ловит callback нажатой пользователем кнопки с датой и вызывает функцию,
     создающую кнопки с подтверждением корректности данных"""
    with bot.retrieve_data(c.from_user.id, c.message.chat.id) as data:
        date = data['date_in']
    dates = str(date).split('-')

    result, key, step = MyTranslationCalendar(min_date=datetime.date(int(dates[0]), int(dates[1]), int(dates[2]) + 1),
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
    """Функция, ловит callback нажатой пользователем кнопки: если данные корректны - вызывает функцию,
     создающую кнопки с количеством отелей, если нет - спрашивает все заново"""
    if call.data == 'yes':
        bot.edit_message_text("Данные записал!", call.message.chat.id, call.message.message_id)
        bot.set_state(call.from_user.id, PriceStates.hotels, call.message.chat.id)
        bot.send_message(call.message.chat.id, 'Выберите количество отелей которые необходимо вывести: ',
                         reply_markup=hotels())
    elif call.data == 'no':
        bot.edit_message_text("Давайте попробуем еще раз", call.message.chat.id, call.message.message_id)
        bot.set_state(call.from_user.id, PriceStates.city, call.message.chat.id)
        bot.send_message(call.from_user.id,
                         f"{call.from_user.first_name}, напишите город в котором хотите посмотреть отели")


@bot.callback_query_handler(func=lambda call: True, state=PriceStates.hotels)
def hotels_callback(call) -> None:
    """Функция, ловит callback нажатой пользователем кнопки с количеством отелей и вызывает функцию,
     создающую кнопки с выводом фотографий"""
    bot.edit_message_text(f"Вы выбрали {call.data} отелей", call.message.chat.id, call.message.message_id)
    bot.set_state(call.from_user.id, PriceStates.photo, call.message.chat.id)
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data['hotels'] = int(call.data)
    bot.send_message(call.message.chat.id, 'Нужно ли выводить фотографии?', reply_markup=get_photo())


@bot.callback_query_handler(func=lambda call: True, state=PriceStates.photo)
def photo_callback(call) -> None:
    """Функция, ловит callback нажатой пользователем кнопки с выводом фотографий и если выводить фотографии нужно,
     вызывает функцию, создающую кнопки с количеством фотографий.
     Если нет - выводить результат или спрашивает минимальную цену"""
    bot.delete_message(call.message.chat.id, call.message.message_id)

    if call.data == 'yes':
        bot.set_state(call.from_user.id, PriceStates.photo_amount, call.message.chat.id)
        bot.send_message(call.message.chat.id, 'Сколько фотографий выводим?', reply_markup=photo_amount())

    elif call.data == 'no':
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data['photo_amount'] = 0
            command = data['command']

        if command == "/bestdeal":
            bot.set_state(call.from_user.id, PriceStates.min_price, call.message.chat.id)
            bot.send_message(call.from_user.id, f"Введите минимальную цену за одну ночь (в долларах США)")
        else:
            bot.send_message(call.message.chat.id, 'Вывожу результаты: ')
            with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
                region = data['city_id']
                date_in = data['date_in']
                date_out = data['date_out']
                command = data['command']
                hotels = data['hotels']
                command_date = data['command_date']
                city = data['location_name']

            photos = 0
            hotels_names = ''
            for i in range(hotels):
                bot.send_message(call.from_user.id, f"{i + 1}-й отель:")
                animation = bot.send_animation(call.message.chat.id, r'https://i.gifer.com/7kRE.gif')

                try:
                    hotel_data, photo_data = find_hotels(region, date_in, date_out, command, photos, i)

                except (
                ReadTimeout, ConnectTimeout, ConnectionError, ApiTelegramException, ApiInvalidJSONException, TypeError):
                    bot.delete_message(call.message.chat.id, animation.id)
                    bot.send_message(call.message.from_user.id,
                                     f"К сожалению, возникла ошибка на сервере. Попробуйте еще раз!\n"
                                     f"{call.from_user.first_name}, напишите город или страну в котором хотите посмотреть отели")
                    bot.set_state(call.from_user.id, PriceStates.city, call.message.chat.id)

                else:
                    hotels_names += hotel_data["name"].replace(' ', '_') + '!'
                    text = f'Название отеля - {hotel_data["name"]}\n' \
                           f'Цена за одну ночь - {hotel_data["price"]}\n' \
                           f'Цена за весь период - {hotel_data["total_price"]}\n' \
                           f'Местоположение :'
                    bot.send_message(call.from_user.id, f"{text}")
                    bot.send_location(call.message.chat.id, latitude=hotel_data['lat'], longitude=hotel_data['long'])
                    bot.delete_message(call.message.chat.id, animation.id)

            full_name = str(call.from_user.full_name).replace(' ', '_')
            str_command = command[1:]
            dir = os.path.abspath('database')
            db_path = os.path.join(dir, "history.db")
            hotels_names = hotels_names[:-1]
            with sq.connect(db_path) as base:
                cur = base.cursor()

                cur.execute(f"""
                    INSERT INTO history VALUES
                    ('{full_name}', '{str_command}', '{command_date}', '{city}', '{hotels_names}')
                """)


@bot.callback_query_handler(func=lambda call: True, state=PriceStates.photo_amount)
def photo_amount_callback(call) -> None:
    """Функция, ловит callback нажатой пользователем кнопки с количеством фотографий и выводить результат или спрашивает минимальную цену"""
    bot.edit_message_text(f"Вы выбрали {call.data} фотографий", call.message.chat.id, call.message.message_id)
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data['photo_amount'] = int(call.data)
        command = data['command']

    if command == "/bestdeal":
        bot.set_state(call.from_user.id, PriceStates.min_price, call.message.chat.id)
        bot.send_message(call.from_user.id, f"Введите минимальную цену за одну ночь (в долларах США)")

    else:
        bot.send_message(call.message.chat.id, 'Вывожу результаты:')
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            region = data['city_id']
            date_in = data['date_in']
            date_out = data['date_out']
            command = data['command']
            hotels = data['hotels']
            photos = int(call.data)
            command_date = data['command_date']
            city = data['location_name']

        hotels_names = ''
        for i in range(hotels):
            bot.send_message(call.from_user.id, f"{i + 1}-й отель:")
            animation = bot.send_animation(call.message.chat.id, r'https://i.gifer.com/7kRE.gif')

            try:
                hotel_data, photo_data = find_hotels(region, date_in, date_out, command, photos, i)

            except (
            ReadTimeout, ConnectTimeout, ConnectionError, ApiTelegramException, ApiInvalidJSONException, TypeError):
                bot.delete_message(call.message.chat.id, animation.id)
                bot.send_message(call.message.from_user.id,
                                 f"К сожалению, возникла ошибка на сервере. Попробуйте еще раз!\n\n"
                                 f"{call.from_user.first_name}, напишите город или страну в котором хотите посмотреть отели")
                bot.set_state(call.from_user.id, PriceStates.city, call.message.chat.id)

            else:
                if len(photo_data) < photos:
                    bot.send_message(call.from_user.id, f"К сожалению, я нашел только {len(photo_data)} фотографий")
                bot.send_media_group(call.message.chat.id, photo_data)

                hotels_names += hotel_data["name"].replace(' ', '_') + '!'

                text = f'Название отеля - {hotel_data["name"]}\n' \
                       f'Цена за одну ночь - {hotel_data["price"]}\n' \
                       f'Цена за весь период - {hotel_data["total_price"]}\n' \
                       f'Местоположение :'
                bot.send_message(call.from_user.id, f"{text}")
                bot.send_location(call.message.chat.id, latitude=hotel_data['lat'], longitude=hotel_data['long'])
                bot.delete_message(call.message.chat.id, animation.id)

        full_name = str(call.from_user.full_name).replace(' ', '_')
        str_command = command[1:]
        dir = os.path.abspath('database')
        db_path = os.path.join(dir, "history.db")
        hotels_names = hotels_names[:-1]
        with sq.connect(db_path) as base:
            cur = base.cursor()
            cur.execute(f"""
                INSERT INTO history VALUES
                ('{full_name}', '{str_command}', '{command_date}', '{city}', '{hotels_names}')
            """)


@bot.message_handler(state=PriceStates.min_price)
def min_price(message: Message) -> None:
    """Функция, ловит cсообщение пользователя с минимальной ценой и спрашивает максимальную цену"""
    try:
        bot.delete_message(message.chat.id, message.message_id - 1)
    except ApiTelegramException:
        pass
    if message.text.isdigit():
        bot.send_message(message.from_user.id, f"Минимальная цена: ${message.text}")
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['min_price'] = int(message.text)
        bot.set_state(message.from_user.id, PriceStates.max_price, message.chat.id)
        bot.send_message(message.from_user.id, f"Введите максимальную цену за одну ночь (в долларах США)")
    else:
        bot.send_message(message.from_user.id,
                         f"Вводить можно только целые числа!Попробуйте еще раз!\n\nВведите минимальную цену за одну ночь (в долларах США)")
        bot.set_state(message.from_user.id, PriceStates.min_price, message.chat.id)


@bot.message_handler(state=PriceStates.max_price)
def max_price(message: Message) -> None:
    """Функция, ловит cсообщение пользователя с максимальной ценой и спрашивает максимальное расстояние от центра"""
    try:
        bot.delete_message(message.chat.id, message.message_id - 1)
    except ApiTelegramException:
        pass
    if message.text.isdigit():
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['max_price'] = int(message.text)
            min_price = data['min_price']
        if int(message.text) > min_price:
            bot.send_message(message.from_user.id, f"Максимальная цена: ${message.text}")
            bot.set_state(message.from_user.id, PriceStates.max_dist, message.chat.id)
            bot.send_message(message.from_user.id, f"Введите максимальное расстояние от цента локации (в км)")
        else:
            bot.send_message(message.from_user.id,
                             f"Максимальная цена должна быть больше минимальной. Попробуйте еще раз!\n\n"
                             f"Введите максимальную цену за одну ночь (в долларах США)")
            bot.set_state(message.from_user.id, PriceStates.max_price, message.chat.id)
    else:
        bot.send_message(message.from_user.id,
                         f"Вводить можно только целые числа. Попробуйте еще раз!\n\n"
                         f"Введите максимальную цену за одну ночь (в долларах США)")
        bot.set_state(message.from_user.id, PriceStates.max_price, message.chat.id)


@bot.message_handler(state=PriceStates.max_dist)
def max_dist(message: Message) -> None:
    """Функция, ловит cсообщение пользователя с максимальным расстоянием и выводит результат"""
    try:
        bot.delete_message(message.chat.id, message.message_id - 1)
    except ApiTelegramException:
        pass
    if message.text.isdigit():
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['max_dist'] = int(message.text)
            max_price = data['max_price']
            min_price = data['min_price']
            region = data['city_id']
            date_in = data['date_in']
            date_out = data['date_out']
            hotels = data['hotels']
            photos = data['photo_amount']
            location = data['location_name']
            command = data['command']
            command_date = data['command_date']
            city = data['location_name']
        bot.send_message(message.from_user.id, f"Максимальная расстояние от центра {location}: {message.text} км")
        mesg = bot.send_message(message.from_user.id, "Ищу... (Это может занять до 30 сек)")
        animation = bot.send_animation(message.chat.id, r'https://i.gifer.com/7kRE.gif')

        try:
            find_best_hotel(1, region, date_in, date_out, photos, min_price, max_price,
                            int(message.text))

        except TypeError:
            bot.delete_message(message.chat.id, mesg.id)
            bot.delete_message(message.chat.id, animation.id)
            bot.send_message(message.from_user.id,
                             f"По данным ценам и расстоянию от центра ничего не удалось найти. Попробуйте еще раз!\n\n"
                             f"Введите минимальную цену за одну ночь (в долларах США)")
            bot.set_state(message.from_user.id, PriceStates.min_price, message.chat.id)

        except (ReadTimeout, ConnectTimeout, ConnectionError, ApiTelegramException, ApiInvalidJSONException, TypeError):
            bot.delete_message(message.chat.id, mesg.id)
            bot.delete_message(message.chat.id, animation.id)
            bot.send_message(message.from_user.id,
                             f"К сожалению, возникла ошибка на сервере. Попробуйте еще раз!\n\n"
                             f"{message.from_user.first_name}, напишите город или страну в котором хотите посмотреть отели")
            bot.set_state(message.from_user.id, PriceStates.city, message.chat.id)

        else:
            bot.delete_message(message.chat.id, mesg.id)
            bot.delete_message(message.chat.id, animation.id)
            bot.send_message(message.from_user.id, "Я что-то нашел!\nВывожу результаты :")
            animation = bot.send_animation(message.chat.id, r'https://i.gifer.com/7kRE.gif')

            try:
                hotels_data = find_best_hotel(hotels, region, date_in, date_out, photos, min_price, max_price,
                                              int(message.text))

            except (
            ReadTimeout, ConnectTimeout, ConnectionError, ApiTelegramException, ApiInvalidJSONException, TypeError):
                bot.delete_message(message.chat.id, animation.id)
                bot.send_message(message.from_user.id,
                                 f"К сожалению, возникла ошибка на сервере. Попробуйте еще раз!\n\n"
                                 f"{message.from_user.first_name}, напишите город или страну в котором хотите посмотреть отели")
                bot.set_state(message.from_user.id, PriceStates.city, message.chat.id)

            else:
                bot.delete_message(message.chat.id, animation.id)
                if len(hotels_data) < hotels:
                    bot.send_message(message.from_user.id, f"К сожалению, я нашел только {len(hotels_data)} отеля")
                j = 1
                hotels_names = ''
                for i in hotels_data:
                    bot.send_message(message.from_user.id, f"{j}-й отель:")
                    animation = bot.send_animation(message.chat.id, r'https://i.gifer.com/7kRE.gif')

                    hotel_data = i[0]
                    photo_data = i[1]

                    hotels_names += hotel_data["name"].replace(' ', '_') + '!'

                    if len(photo_data) < photos:
                        bot.send_message(message.from_user.id, f"К сожалению, я нашел только {len(photo_data)} фотографий")
                    bot.send_media_group(message.chat.id, photo_data)

                    text = f'Название отеля - {hotel_data["name"]}\n' \
                           f'Цена за одну ночь - {hotel_data["price"]}\n' \
                           f'Цена за весь период - {hotel_data["total_price"]}\n' \
                           f'Расстояние от центра {location} - {hotel_data["dist"]} киллометров\n' \
                           f'Местоположение: '
                    bot.send_message(message.from_user.id, f"{text}")
                    bot.send_location(message.chat.id, latitude=hotel_data['lat'], longitude=hotel_data['long'])
                    j += 1
                    bot.delete_message(message.chat.id, animation.id)

                full_name = str(message.from_user.full_name).replace(' ', '_')
                str_command = command[1:]
                dir = os.path.abspath('database')
                db_path = os.path.join(dir, "history.db")
                hotels_names = hotels_names[:-1]
                with sq.connect(db_path) as base:
                    cur = base.cursor()

                    cur.execute(f"""
                        INSERT INTO history VALUES
                        ('{full_name}', '{str_command}', '{command_date}', '{city}', '{hotels_names}')
                    """)
    else:
        bot.send_message(message.from_user.id,
                         f"Вводить можно только целые числа.Попробуйте еще раз!\n\nВведите максимальное расстояние от цента локации (в км)")
        bot.set_state(message.from_user.id, PriceStates.max_dist, message.chat.id)
