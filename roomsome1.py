import json
import re
import requests


def get_price(hotel_config, arrive, departure):
    url = hotel_config["url"]
    origin = hotel_config["origin"]
    referer = hotel_config["referer"]

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
        'room_persons[0][adult]': '2',
        #'room_persons[0][child]': '2',
        #'room_persons[0][child_ages][]': ['6', '10'],
        'arrival': arrive,
        'departure': departure,
        'rooms': '1',
        'promotion-code': '',
        'subpage_num': '1',
        'subpage_num_next': '2',
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        return f"A kérés sikertelen volt. HTTP státuszkód: {response.status_code}"

    text = response.text

    start_marker = '{"ecommerce":{"'
    end_marker = ']}});dataLayer.push'

    if start_marker not in text or end_marker not in text:
        return "Nincs szabad szoba vagy nem található a JSON blokk."

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
