import json
import re
from requests import Session
from json import JSONDecoder
from urllib.parse import quote

def get_price(hotel_config, arrive, departure):
    base_url = hotel_config["url"]
    session = Session()

    # --- Első request (POST) ---
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

    scraperapi_key = "iUAAEXdV5IFUa5v0HRtZtz52YiBg7sDn"
    post_url = f"{base_url}kereses"
    encoded_post_url = quote(post_url, safe="")
    full_post_url = f"https://api.webscrapingapi.com/v2?api_key={scraperapi_key}&url={encoded_post_url}"

    response_post = session.post(full_post_url, data=payload, allow_redirects=True)

    if response_post.status_code != 200:
        return f"Az első POST kérés sikertelen volt. HTTP státuszkód: {response_post.status_code}"

    # Cookie-k összefűzése
    cookies_list = response_post.headers.getlist("Set-Cookie") if hasattr(response_post.headers, 'getlist') else response_post.headers.get("Set-Cookie", "").split(',')
    cookie_header = "; ".join([c.split(";")[0] for c in cookies_list])

    # Debug: Kiírjuk a cookie-kat
    debug_cookies = "\n".join([f"{i+1}. {c.strip()}" for i, c in enumerate(cookies_list)])

    # --- Második request (GET) ---
    get_url = base_url + "szobavalasztas"
    encoded_get_url = quote(get_url, safe="")
    full_get_url = f"https://api.webscrapingapi.com/v2?api_key={scraperapi_key}&url={encoded_get_url}"

    headers = {"Cookie": cookie_header}

    response_get = session.get(full_get_url, headers=headers)

    if response_get.status_code != 200:
        return f"A GET kérés sikertelen volt. HTTP státuszkód: {response_get.status_code}"

    text = response_get.text
    start_marker = '{"ecommerce":{"'
    end_marker = ']}});dataLayer.push'

    if start_marker not in text or end_marker not in text:
        return f"Nincs szabad szoba vagy nem található a JSON blokk.\n\nÁtadott cookie-k:\n{debug_cookies}"

    try:
        start_index = text.find(start_marker)
        end_index = text.find(end_marker) + 3  # a záró ]}} + ) miatt
        json_str = text[start_index:end_index + 1]  # teljes JSON blokk

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
