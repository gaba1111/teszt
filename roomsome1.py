import json
import re
from requests import Session
from json import JSONDecoder
from urllib.parse import quote

def get_price(hotel_config, arrive, departure):
    base_url = hotel_config["url"].rstrip("/")  # pl. https://calimbrawellnesshotel.hu/online-foglalas
    post_url = f"https://api.webscrapingapi.com/v2?api_key=YOUR_API_KEY&url={quote(base_url + '/kereses', safe='')}"
    get_url = f"https://api.webscrapingapi.com/v2?api_key=YOUR_API_KEY&url={quote(base_url + '/szobavalasztas', safe='')}"


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
        "subpage_num_next": "2"
    }

    response1 = session.post(post_url, data=payload, allow_redirects=True)

    if response1.status_code != 200:
        return f"❌ Az első POST kérés sikertelen volt. HTTP státuszkód: {response1.status_code}"

    # 🔐 Cookie-k manuális összefűzése
    cookies = response1.headers.getlist("Set-Cookie") if hasattr(response1.headers, 'getlist') else response1.headers.get("Set-Cookie", "")
    if isinstance(cookies, str):
        cookies = [cookies]
    cookie_header = "; ".join(cookie.split(";")[0] for cookie in cookies)

    headers = {
        "Cookie": cookie_header
    }

    response2 = session.get(get_url, headers=headers)

    if response2.status_code != 200:
        return f"❌ A GET kérés sikertelen volt. HTTP státuszkód: {response2.status_code}"

    text = response2.text
    start_marker = '{"ecommerce":{"'
    end_marker = ']}});dataLayer.push'

    if start_marker not in text or end_marker not in text:
        return "❌ Nincs szabad szoba vagy nem található a JSON blokk."

    try:
        start_index = text.find(start_marker)
        end_index = text.find(end_marker)
        json_str = text[start_index:end_index + 3]  # +3 hogy benne legyen a lezáró ]}}

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
            # Ha átmegy a szűrésen
            ar = csomag.get("price")
            if isinstance(ar, (int, float)):
                arak.append(ar)

        if arak:
            return f"A legkedvezőbb ár: {int(min(arak)):,} Ft".replace(",", " ")
        else:
            return "❌ Nem található megfelelő csomag a feltételek alapján."

    except Exception as e:
        return f"❌ Hiba történt a válasz feldolgozása közben: {e}"
