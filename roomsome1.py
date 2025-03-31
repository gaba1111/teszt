import json
import re
from requests import Session
from json import JSONDecoder


def get_price(hotel_config, arrive, departure):
    base_url = hotel_config["url"].rstrip("/")
    post_url = f"https://api.webscrapingapi.com/v2?api_key=iUAAEXdV5IFUa5v0HRtZtz52YiBg7sDn&url={base_url}%2Fkereses"
    get_url = f"https://api.webscrapingapi.com/v2?api_key=iUAAEXdV5IFUa5v0HRtZtz52YiBg7sDn&url={base_url}%2Fszobavalasztas"

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

    response_post = session.post(post_url, data=payload, allow_redirects=True)
    if response_post.status_code != 200:
        return f"A POST kérés sikertelen volt. HTTP státuszkód: {response_post.status_code}"

    response_get = session.get(get_url, allow_redirects=True)
    if response_get.status_code != 200:
        return f"A GET kérés sikertelen volt. HTTP státuszkód: {response_get.status_code}"

    return f"GET válasz első 500 karaktere:\n{response_get.text[:500]}"
