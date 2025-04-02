import requests
import re
import time
import random
from datetime import datetime

# Ez a függvény a szerverről hívódik meg, paraméterként kapja a szálloda konfigurációját,
# valamint az érkezési és távozási dátumot
def get_price(hotel_config, arrival, departure):
    # Kinyerjük a konfigurációs adatokat
    roomcodes = hotel_config["roomcodes"]  # Többféle szobakód, sorrendben próbáljuk őket
    hotelcode = hotel_config["hotelcode"]
    url_get_1 = hotel_config["url_get_1"]
    url_offers = hotel_config["url_offers"]
    path = hotel_config["path"]
    referer = hotel_config["referer"]

    # Kiszámoljuk a tartózkodás hosszát (éjszakák száma)
    date_format = "%Y-%m-%d"
    number_of_nights = (datetime.strptime(departure, date_format) - datetime.strptime(arrival, date_format)).days

    # Létrehozunk egy session-t, amiben a cookie-k automatikusan megmaradnak
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    })

    # Ez a belső függvény küld el 5 egymás utáni kérést egy adott szobakódra
    def send_requests_for_roomcode(roomcode):
        try:
            # 1. GET kérés – első oldal betöltése, fontos a sütik miatt
            headers_1 = {
                "authority": "www.hunguesthotels.hu",
                "path": path,
                "scheme": "https",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*",
                "Referer": referer
            }
            res1 = session.get(url_get_1, headers=headers_1)
            time.sleep(2)

            # 2. POST – SAVE_TIMES adatmentés
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
            res2 = session.post("https://www.hunguesthotels.hu/_sys/ajax.php", data=data2, headers={"Referer": url_get_1})
            time.sleep(2)

            # 3. POST – GET_ROOM adatlekérés
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
            res3 = session.post("https://www.hunguesthotels.hu/_sys/ajax.php", data=data3, headers={"Referer": url_get_1})
            time.sleep(2)

            # 4. POST – SAVE_ROOMS lekérés
            v2_rooms = f"{roomcode}<->2f2g<->6_10_0_0_0_0<->{roomcode}_2_6_10_0_0_0_0<->0<->0<->0<->0<->0<->1"
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
            res4 = session.post("https://www.hunguesthotels.hu/_sys/ajax.php", data=data4, headers={"Referer": url_get_1})
            time.sleep(2)

            # 5. GET kérés – az ajánlatok betöltése
            res5 = session.get(url_offers)

            # Árak kinyerése reguláris kifejezéssel
            pattern = r'(?<=data-price=")[^\"]+(?=")'
            prices = re.findall(pattern, res5.text)

            # Ha van ár, a legkisebb értéket visszaadjuk
            if prices:
                numeric_prices = [int(p.replace(" ", "").replace("\u202f", "").replace(",", "")) for p in prices]
                return min(numeric_prices)
            else:
                return None

        except Exception:
            return None

    # Sorban végigpróbáljuk a szobakódokat, amíg nem találunk érvényes árat
    for idx, code in enumerate(roomcodes):
        result = send_requests_for_roomcode(code)
        if result is not None:
            return f"A legkedvezőbb ár: {int(result):,} Ft".replace(",", " ")
        # Ha nem ez volt az utolsó szobakód, várunk 4–6 másodpercet a következő próbálkozásig
        if idx < len(roomcodes) - 1:
            delay = random.randint(4, 6)
            time.sleep(delay)

    return "Nem található ár egyik szobakódra sem."
