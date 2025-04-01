import json
import re
from requests import Session
from urllib.parse import quote

def get_price(hotel_config, arrive, departure):
    base_url = hotel_config["url"]
    session = Session()

    # --- Első request (POST) ---
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

    scraperapi_key = "iUAAEXdV5IFUa5v0HRtZtz52YiBg7sDn"
    post_url = f"{base_url}kereses"
    encoded_post_url = quote(post_url, safe="")
    full_post_url = f"https://api.webscrapingapi.com/v2?api_key={scraperapi_key}&url={encoded_post_url}"

    response_post = session.post(full_post_url, data=payload, allow_redirects=True)

    if response_post.status_code != 200:
        return f"Az első POST kérés sikertelen volt. HTTP státuszkód: {response_post.status_code}"

    return response_post.text[:1000]
