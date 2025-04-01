import json
import re
from requests import Session
from urllib.parse import urlencode


def get_price(hotel_config, arrive, departure):
    base_url = hotel_config["url"]
    session = Session()

    # --- Első request (POST) ---
    payload_dict = {
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

    # Kézi URL-enkódolás
    payload_encoded = urlencode(payload_dict)

    scraperapi_key = "c401c39c3f0f84264c25fb763591324f"
    post_url = f"{base_url}kereses"
    encoded_post_url = urlencode({"api_key": scraperapi_key, "url": post_url})
    full_post_url = f"http://api.scraperapi.com?{encoded_post_url}"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response_post = session.post(full_post_url, data=payload_encoded, headers=headers, allow_redirects=True)

    if response_post.status_code != 200:
        return f"Az első POST kérés sikertelen volt. HTTP státuszkód: {response_post.status_code}"

    return response_post.text[:1000]
