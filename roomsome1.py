import requests
import json


def calculate_guest_counts(adults, children_ages, age_limit):
    adult_count = adults
    child_count = 0
    for age in children_ages:
        if age <= age_limit:
            child_count += 1
        else:
            adult_count += 1
    return adult_count, child_count


def get_price(config, arrive, departure, adults=1, children=[]):
    origin = config.get("origin")
    referer = config.get("referer")
    hotelID = config.get("hotelID")
    child_age_limit = config["children"]  # kötelezően megadva a JSON-ban

    adult_count, child_count = calculate_guest_counts(adults, children, child_age_limit)

    data = {
        'arrival': arrive,
        'departure': departure,
        'rooms': '1',
        'promotion-code': '',
        'subpage_num': '1',
        'subpage_num_next': '2',
        'room_persons[0][adult]': str(adult_count),
    }

    if child_count > 0:
        data['room_persons[0][child]'] = str(child_count)
        if child_count == 1:
            data['room_persons[0][child_ages][]'] = str(children[0])
        else:
            data['room_persons[0][child_ages][]'] = [str(age) for age in children]

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': origin,
        'Referer': referer,
        'X-Requested-With': 'XMLHttpRequest'
    }

    url = f"https://roomsome.com/ajax/hotel/{hotelID}/search/step2"
    response = requests.post(url, data=data, headers=headers)

    try:
        result = response.json()
        prices = []
        for room in result.get("rooms", []):
            for service in room.get("services", []):
                prices.append(service.get("price", 0))
        if prices:
            best_price = min(prices)
            return f"A legkedvezőbb ár: {best_price:,} Ft".replace(",", "\u202f")
    except Exception:
        return "Hiba történt az ár lekérdezés során."

    return "Nem található ár."
