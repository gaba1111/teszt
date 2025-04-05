import requests
import re
import time
import random
from datetime import datetime

# Ez a függvény a szerverről hívódik meg, paraméterként kapja a szálloda konfigurációját,
# valamint az érkezési és távozási dátumot

def get_price(hotel_config, arrival, departure, adults=2, children=[]):
    rooms = hotel_config["rooms"]
    hotelcode = hotel_config["hotelcode"]
    url_get_1 = hotel_config["url_get_1"]
    url_offers = hotel_config["url_offers"]
    path = hotel_config["path"]
    referer = hotel_config["referer"]

    # Kiszámoljuk a tartózkodás hosszát (éjszakák száma)
    date_format = "%Y-%m-%d"
    number_of_nights = (datetime.strptime(departure, date_format) - datetime.strptime(arrival, date_format)).days

    # A 18 év feletti gyerekeket felnőttként számoljuk
    adjusted_children = []
    for age in children:
        if age >= 18:
            adults += 1
        else:
            adjusted_children.append(age)

    # Létrehozunk egy session-t, amiben a cookie-k automatikusan megmaradnak
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    })

    def send_requests(room):
        try:
            roomcode = room["code"]

            # 1. GET kérés – első oldal betöltése
            headers_1 = {
                "authority": "www.hunguesthotels.hu",
                "path": path,
                "scheme": "https",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*",
                "Referer": referer
            }
            session.get(url_get_1, headers=headers_1)
            time.sleep(1)

            # 2. POST – SAVE_TIMES
            data2 = {
                "v1": "SAVE_TIMES",
                "v2": f"{departure}_{departure}_{number_of_nights}_{arrival}_{departure}_{arrival}_{departure}",
                "v3": arrival,
                "v4": departure,
                "v5": str(number_of_nights),
                "v6": "",
                "v7": "",
                "v8": "/_sys/_ele/100/save_data"
            }
            session.post("https://www.hunguesthotels.hu/_sys/ajax.php", data=data2, headers={"Referer": url_get_1})
            time.sleep(1)

            # 3. POST – GET_ROOM
            data3 = {
                "v1": "GET_ROOM",
                "v2": roomcode,
                "v3": "HU",
                "v4": hotelcode,
                "v5": "",
                "v6": "",
                "v7": "",
                "v8": "/_sys/_ele/100/roomselection"
            }
            session.post("https://www.hunguesthotels.hu/_sys/ajax.php", data=data3, headers={"Referer": url_get_1})
            time.sleep(1)

            # 4. POST – SAVE_ROOMS
            config_str = f"{adults}f"
            if adjusted_children:
                config_str += f"{len(adjusted_children)}g"

            if config_str not in room["configuration"]:
                return None

            for age in adjusted_children:
                if not (room["childagemin"] <= age <= room["childagemax"]):
                    return None

            child_str = "_".join([str(age) for age in adjusted_children] + ["0"] * (6 - len(adjusted_children)))
            v2_rooms = f"{roomcode}<->{config_str}<->{child_str}<->{roomcode}_{adults}_{child_str}<->0<->0<->0<->0<->0<->1"

            data4 = {
                "v1": "SAVE_ROOMS",
                "v2": v2_rooms,
                "v3": "",
                "v4": "",
                "v5": "",
                "v6": "",
                "v7": "",
                "v8": "/_sys/_ele/100/save_data"
            }
            session.post("https://www.hunguesthotels.hu/_sys/ajax.php", data=data4, headers={"Referer": url_get_1})
            time.sleep(1)

            # 5. GET – ajánlatok
            res5 = session.get(url_offers)
            time.sleep(random.randint(4, 6))
            prices = re.findall(r'(?<=data-price=")[^"]+(?=")', res5.text)

            if prices:
                numeric_prices = [int(p.replace(" ", "").replace("\u202f", "").replace(",", "")) for p in prices]
                return min(numeric_prices)
            return None

        except Exception:
            return None

    for idx, room in enumerate(rooms):
        result = send_requests(room)
        if result is not None:
            # Próbáljunk még egyet a következő rankú szobával is
            if idx + 1 < len(rooms):
                next_result = send_requests(rooms[idx + 1])
                if next_result is not None:
                    return f"A legkedvezőbb ár: {min(result, next_result):,} Ft".replace(",", " ")
            return f"A legkedvezőbb ár: {int(result):,} Ft".replace(",", " ")
        if idx < len(rooms) - 1:
            

    return "Nem található ár egyik szobára sem."
