import re
import json
import time
import requests
from datetime import datetime
from requests import Session

def get_price(hotel_config, arrive, departure, adults=2, children=[]):
    session = Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    })

    try:
        # Request 1
        response1 = session.get(hotel_config["step1_url"])
        time.sleep(4)

        # Request 2
        data2 = hotel_config["step2_data"]
        data2.update({
            "checkIn": arrive,
            "checkOut": departure,
            "number_of_nights": str((datetime.strptime(departure, "%Y-%m-%d") - datetime.strptime(arrive, "%Y-%m-%d")).days)
        })
        session.post(hotel_config["step2_url"], data=data2)
        time.sleep(4)

        # Request 3
        session.post(hotel_config["step3_url"], data=hotel_config["step3_data"])
        time.sleep(4)

        # Request 4
        session.post(hotel_config["step4_url"], data=hotel_config["step4_data"])
        time.sleep(4)

        # Request 5 - GET árak
        response5 = session.get(hotel_config["step5_url"])
        text = response5.text

        prices = []
        price_pattern = r'(?<=data-price=")[^"]+(?=")'
        description_pattern = r'<li>(.*?)</li>'

        price_matches = list(re.finditer(price_pattern, text))

        for match in price_matches:
            price_str = match.group()
            try:
                price_value = int(price_str)
            except ValueError:
                continue

            # nézzük meg a maradék szöveget, van-e benne "félpanzió" <li> szakaszban
            remaining_text = text[match.end():]
            li_match = re.search(description_pattern, remaining_text, re.DOTALL)
            if li_match:
                description = li_match.group(1).lower()
                if "félpanzió" in description:
                    prices.append(price_value)

        if prices:
            return f"A legkedvezőbb ár: {min(prices):,} Ft".replace(",", " ")
        else:
            return "Nem található ár félpanziós csomaghoz."

    except Exception as e:
        return f"Hiba történt: {e}"
