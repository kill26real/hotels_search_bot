from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
from bot_requests.api_requests import api_request


def city_founding(city):
    """Функция, которая ищет варианты локакций и отправляет их в функцию создающую кнопки"""
    querystring = {'q': city, 'locale': 'ru_RU'}

    response = api_request(method_endswith='locations/v3/search', params=querystring, method_type='GET')

    hotel_json = json.loads(response.text)

    if response:
        cities = list()
        for dest in hotel_json["sr"]:
            if dest["type"] in ("CITY", "NEIGHBORHOOD", "LANDMARK_GROUP"):
                location_name = dest["regionNames"]["fullName"]
                loc = location_name.split(', ')
                need_loc = loc[0]
                location_id = dest["gaiaId"]
                cities.append({'city_name': need_loc, 'destination_id': location_id})
        return cities


def city_markup(city):
    """Функция, создающая кнопки"""
    cities = city_founding(city)
    if cities:
        destinations = InlineKeyboardMarkup(row_width=2)
        for city in cities:
            name = city['city_name']
            destination_id = city["destination_id"]
            data = name + ', ' + destination_id
            destinations.add(InlineKeyboardButton(text=city['city_name'],
                                                  callback_data=f"{data}"))
        return destinations
    else:
        raise Exception
