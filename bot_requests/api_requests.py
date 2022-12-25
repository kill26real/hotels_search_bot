import requests


def api_request(method_endswith, params, method_type):
    url = f"https://hotels4.p.rapidapi.com/{method_endswith}"
    headers = {
        'content-type': 'application/json',
        'X-RapidAPI-Key': "d17b6fd198mshd3cfdcc33b8b250p15a640jsnf8b34aefa962",
        'X-RapidAPI-Host': "hotels4.p.rapidapi.com"
    }

    if method_type == 'GET':
        return get_request(
            url=url,
            params=params,
            headers=headers
        )
    else:
        return post_request(
            url=url,
            params=params,
            headers=headers
        )


def get_request(url, params, headers):
    response = requests.get(
        url=url,
        headers=headers,
        params=params,
        timeout=20
    )
    if response.status_code == requests.codes.ok:
        return response


def post_request(url, params, headers):
    response_1 = requests.request(
        method='POST',
        url=url,
        headers=headers,
        json=params,
        timeout=20
    )
    if response_1.status_code == requests.codes.ok:
        return response_1
