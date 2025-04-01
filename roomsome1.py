import re
import requests
from urllib.parse import quote

def get_price(hotel_config, arrive, departure):
    base_url = hotel_config["url"]
    scraperapi_key = "iUAAEXdV5IFUa5v0HRtZtz52YiBg7sDn"

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

    post_url = base_url + "kereses"
    encoded_post_url = quote(post_url, safe="")
    full_post_url = f"https://api.webscrapingapi.com/v2?api_key={scraperapi_key}&url={encoded_post_url}"

    response_post = requests.post(full_post_url, data=payload)

    if response_post.status_code != 200:
        return f"❌ Az első POST kérés sikertelen volt. HTTP státuszkód: {response_post.status_code}"

    # --- Cookie-k kinyerése az objektumból ---
    cookies_dict = response_post.cookies.get_dict()
    phpsessid = cookies_dict.get("PHPSESSID")
    if not phpsessid:
        return f"❌ Nem található PHPSESSID a cookie-k között. Cookie-k: {cookies_dict}"

    cookie_header = f"PHPSESSID={phpsessid}"

    # --- Második request (GET) ---
    get_url = base_url + "szobavalasztas"
    encoded_get_url = quote(get_url, safe="")
    full_get_url = f"https://api.webscrapingapi.com/v2?api_key={scraperapi_key}&url={encoded_get_url}"

    headers = {
        "Cookie": cookie_header
    }

    response_get = requests.get(full_get_url, headers=headers)

    if response_get.status_code != 200:
        return f"❌ A GET kérés sikertelen volt. HTTP státuszkód: {response_get.status_code}"

    return f"✅ GET válasz első 1000 karaktere:\n{response_get.text[:1000]}"
