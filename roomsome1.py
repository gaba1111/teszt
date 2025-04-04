import json
import re
import requests


def calculate_guest_counts(adults, children_ages, age_limit):
    adult_count = adults
    child_count = 0
    for age in children_ages:
        if age <= age_limit:
            child_count += 1
        else:
            adult_count += 1
    return adult_count, child_count


def get_price(hotel_config, arrive, departure, adults=1, children=[]):
    url = hotel_config["url"]
    origin = hotel_config["origin"]
    referer = hotel_config["referer"]
    age_limit = hotel_config["children"]

    adult_count, child_count = calculate_guest_counts(adults, children, age_limit)

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'hu-HU,hu;q=0.9',
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': origin,
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'referer': referer,
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    }

    data = {
        'room_persons[0][adult]': str(adult_count),
        'arrival': arrive,
        'departure': departure,
        'rooms': '1',
        'promotion-code': '',
        'subpage_num': '1',
        'subpage_num_next': '2',
    }

    if child_count > 0:
        data['room_persons[0][child]'] = str(child_count)
        if child_count == 1:
            data['room_persons[0][child_ages][]'] = str(children[0])
        else:
            data['room_persons[0][child_ages][]'] = [str(age) for age in children]

    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        return f"A kérés sikertelen volt. HTTP státuszkód: {response.status_code}"

    text = response.text

    start_marker = '{"ecommerce":{"'
    end_marker = ']}});dataLayer.push'

    if start_marker not in text or end_marker not in text:
        return "Nincs szabad szoba vagy nem teljesül a minimum éjszakaszám."

    try:
        start_index = text.find(start_marker)
        end_index = text.find(end_marker) + 3
        json_str = text[start_index:end_index]
        data = json.loads(json_str)

        impressions = data["ecommerce"]["impressions"]
        kizart_szavak = ["senior", "szenior", "nyugdíjas", "all inclusive", "all inkluzív"]

        arak = []
        for csomag in impressions:
            nev = csomag.get("name", "").lower()
            if any(k in nev for k in kizart_szavak):
                continue
            if "reggeli" in nev and "vacsor" not in nev:
                continue
            ar = csomag.get("price")
            if isinstance(ar, (int, float)):
                arak.append(ar)

        if arak:
            return f"A legkedvezőbb ár: {int(min(arak)):,} Ft".replace(",", " ")
        else:
            return "Nem található megfelelő csomag a feltételek alapján."

    except Exception as e:
        return f"Hiba történt a válasz feldolgozása közben: {e}"
