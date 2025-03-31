import json
import re
from requests import Session

def get_price(hotel_config, arrive, departure):
    url = hotel_config["url"]
    session = Session()

    payload = {
        "room_persons[0][adult]": "2",
        "room_persons[0][child]": "2",
        "room_persons[0][child_ages][0]": "6",
        "room_persons[0][child_ages][1]": "10",
        "arrival": arrive,
        "departure": departure,
        "rooms": "1",
        "lang": "hu",
        "subpage_num": "1",
        "subpage_num_next": "2",
        "testcalcresresult": "1"
    }

    response = session.post(url, data=payload, allow_redirects=True)
    if response.status_code != 200:
        return f"A kérés sikertelen volt. HTTP státuszkód: {response.status_code}"

    text = response.text
    start_marker = '{"ecommerce":{"'
    end_marker = ']}});dataLayer.push'

    if start_marker not in text or end_marker not in text:
        return "Nincs szabad szoba a megadott dátumokra."

    try:
        start_index = text.find(start_marker)
        end_index = text.find(end_marker) + 4
        json_str = text[start_index:end_index]
        data = json.loads(json_str)

        impressions = data["ecommerce"]["impressions"]
        kulcsszavak = ["senior", "szenior", "nyugdíjas", "all inclusive", "all inkluzív"]

        arak = []
        for csomag in impressions.values():
            nev = csomag.get("name", "").lower()
            if any(k in nev for k in kulcsszavak):
                continue
            if "reggeli" in nev and "vacsor" not in nev:
                continue
            if ("reggeli" in nev and "vacsor" in nev) or "félpanzió" in nev:
                ar = csomag.get("price")
                if isinstance(ar, (int, float)):
                    arak.append(ar)
        if arak:
            return f"A legkedvezőbb ár: {int(min(arak)):,} Ft".replace(",", " ")
        else:
            return "Nem található megfelelő csomag a feltételek alapján."

    except Exception as e:
        return f"Hiba történt a válasz feldolgozása közben: {e}"
