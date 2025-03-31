import json
from requests import Session
from json import JSONDecoder
from urllib.parse import quote_plus

def get_price(hotel_config, arrive, departure):
    base_url = hotel_config["url"]  # pl. https://calimbrawellnesshotel.hu/online-foglalas/
    api_key = "iUAAEXdV5IFUa5v0HRtZtz52YiBg7sDn"
    session = Session()

    # 1️⃣ POST request a 'kereses' végponttal
    post_url = f"https://api.webscrapingapi.com/v2?api_key={api_key}&url={quote_plus(base_url + 'kereses')}"
    payload = {
        "room_persons[0][adult]": 2,
        "room_persons[0][child]": 2,
        "room_persons[0][child_ages][0]": 6,
        "room_persons[0][child_ages][1]": 10,
        "arrival": arrive,
        "departure": departure,
        "rooms": 1,
        "lang": "hu",
        "subpage_num": 1,
        "subpage_num_next": 2
    }

    response1 = session.post(post_url, data=payload, allow_redirects=True)
    if response1.status_code != 200:
        return f"A POST kérés sikertelen volt. HTTP státuszkód: {response1.status_code}"

    # 2️⃣ GET kérés a 'szobavalasztas' oldalra ugyanazzal a base URL-lel
    get_url = f"https://api.webscrapingapi.com/v2?api_key={api_key}&url={quote_plus(base_url + 'szobavalasztas')}"
    response2 = session.get(get_url)
    if response2.status_code != 200:
        return f"A GET kérés sikertelen volt. HTTP státuszkód: {response2.status_code}"

    text = response2.text
    start_marker = '{"ecommerce":{"'
    end_marker = ']}});dataLayer.push'

    if start_marker not in text or end_marker not in text:
        return "Nincs szabad szoba a megadott dátumokra."

    try:
        start_index = text.find(start_marker)
        end_index = text.find(end_marker)
        json_str = text[start_index:end_index + 3]  # +3 to include ]}}

        decoder = JSONDecoder()
        data, _ = decoder.raw_decode(json_str)

        impressions = data["ecommerce"]["impressions"]
        kizart_szavak = ["senior", "szenior", "nyugdíjas", "all inclusive", "all inkluzív"]

        arak = []
        for csomag in impressions:
            nev = csomag.get("name", "").lower()
            if any(k in nev for k in kizart_szavak):
                continue
            if "reggeli" in nev and "vacsor" not in nev:
                continue
            # Ha egyik kizáró feltétel sem áll fenn, az ár mehet
            ar = csomag.get("price")
            if isinstance(ar, (int, float)):
                arak.append(ar)

        if arak:
            return f"A legkedvezőbb ár: {int(min(arak)):,} Ft".replace(",", " ")
        else:
            return "Nem található megfelelő csomag a feltételek alapján."

    except Exception as e:
        return f"Hiba történt a válasz feldolgozása közben: {e}"
