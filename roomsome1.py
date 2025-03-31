import json
import re
from requests import Session
from json import JSONDecoder

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
        end_index = text.find(end_marker)
        json_str = text[start_index:end_index + 3]  # +3 to include ]}}

        # Debug: adjuk vissza a kivágott JSON szöveget teljes egészében
        return f"Kivágott JSON:
{json_str}"

    except Exception as e:
        return f"Hiba történt a válasz feldolgozása közben: {e}"
