from bot_requests.api_requests import api_request
import json
from telebot.types import InputMediaPhoto
import urllib
from urllib import request


def find_photos(hotel_id, photos):
    payload_2 = {
        "currency": "USD",
        "eapid": 1,
        "locale": "ru_RU",
        "siteId": 300000001,
        "propertyId": hotel_id
    }

    response = api_request(method_endswith='properties/v2/detail', params=payload_2, method_type='POST')

    hotel_data = json.loads(response.text)

    photos_data = hotel_data['data']['propertyInfo']['propertyGallery']['images']

    photos_list = list()

    for j in range(photos):
        photo_url = photos_data[j]["image"]["url"][:-34]

        f = open(f'{j}.jpg', 'wb')
        f.write(urllib.request.urlopen(photo_url).read())
        f.close()

        photo = InputMediaPhoto(open(f'{j}.jpg', 'rb'))

        photos_list.append(photo)

    return photos_list


def get_data(hotel):
    data = dict()
    data['id'] = hotel['id']
    data['name'] = hotel['name']
    data['lat'] = hotel['mapMarker']['latLong']['latitude']
    data['long'] = hotel['mapMarker']['latLong']['longitude']
    data['total_price'] = hotel['price']['displayMessages'][1]['lineItems'][0]['value'][:-5]
    # data['price'] = hotel['price']['strikeOut']['formatted']
    data['price'] = hotel['mapMarker']['label']

    return data


def find_hotels(i, region, date_in, date_out, low_high, photos):
    date_1_in = str(date_in).split('-')
    date_1_out = str(date_out).split('-')
    min, max = 1, 200
    if low_high == '/lowprice':
        min = 1
        max = 200
    elif low_high == '/highprice':
        min = 100
        max = 1500

    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "ru_RU",
        "siteId": 300000001,
        "destination": {"regionId": f"{region}"},
        "checkInDate": {
            "day": int(date_1_in[2]),
            "month": int(date_1_in[1]),
            "year": int(date_1_in[0])
        },
        "checkOutDate": {
            "day": int(date_1_out[2]),
            "month": int(date_1_out[1]),
            "year": int(date_1_out[0])
        },
        "rooms": [
            {
                "adults": 2
            }
        ],
        "resultsStartingIndex": 0,
        "resultsSize": 200,
        "sort": "PRICE_LOW_TO_HIGH",
        "filters": {"price": {
            "max": max,
            "min": min
        }}
    }

    response = api_request(method_endswith='properties/v2/list', params=payload, method_type='POST')
    hotels_data = json.loads(response.text)

    hotels = hotels_data['data']['propertySearch']['properties']

    if low_high == '/lowprice':
        data = get_data(hotels[i])
        data_2 = list()
        if photos != 0:
            data_2 = find_photos(hotels[i]['id'], photos)
        return data, data_2

    elif low_high == '/highprice':
        data = get_data(hotels[- i - 1])
        data_2 = list()
        if photos != 0:
            data_2 = find_photos(hotels[- i - 1]['id'], photos)
        return data, data_2

    elif low_high == '/bestdeal':
        pass
