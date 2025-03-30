from flask import Flask, request
from flask_cors import CORS
from requests import Session
import json
import codecs
import re

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET", "POST"])
def get_cheapest_price():
    if request.method == "GET":
        return "Használj POST kérést az érkezési és távozási dátum megadásához."

    adatok = request.get_json()
    arrive = adatok.get("arrive")
    departure = adatok.get("departure")

    session = Session()

    # REQUEST 1
    HEADERS = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'hu-HU,hu;q=0.9',
        'priority': 'u=0, i',
        'referer': 'https://hotelessence.hu/',
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'iframe',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-site',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    }

    response1 = session.get(
        'https://booking.hotelessence.hu/hotels/hotelessence/iframe=1;lang=hu;ca_currency=HUF;iframe_key=1551',
        headers=HEADERS,
    )

    sid = list(session.cookies)[0].value

    # REQUEST 2
    data2 = {
        'sid': sid,
        'method[name]': 'save_session_datas',
        'method[params][page]': 'index',
        'method[params][rooms][0][adults]': '2',
        'method[params][rooms][0][children][0]': '6',
        'method[params][rooms][0][children][1]': '10',
        'method[params][arrive]': arrive,
        'method[params][departure]': departure,
        'method[params][ca_currency]': 'HUF',
        'method[params][code]': '',
        'method[params][refpid]': '',
        'method[params][ref]': '',
        'method[params][refhash]': '',
        'method[params][target_origin]': 'https://hotelessence.hu',
        'method[params][hotelID]': '1198',
        'method[params][lang]': 'hu',
    }

    session.post('https://hotelessence.nethotelbooking.net/ajax/booking/index', headers=HEADERS, data=data2)

    # REQUEST 3
    response3 = session.get(
        f'https://booking.hotelessence.hu/hotels/hotelessence/page=booking;roomNumber=0;sid={sid}',
        headers=HEADERS,
    )

    html = response3.text

    start_marker = "window.rooms"
    end_marker = "window.room_selection"
    start_index = html.find(start_marker)
    end_index = html.find(end_marker)

    if start_index == -1 or end_index == -1:
        return "A szükséges szakasz nem található."

    kivagott = html[start_index + 27 : end_index - 6]

    try:
        decoded_str = codecs.decode(kivagott, 'unicode_escape')
        match = re.search(r'"roomID":(\d+)', decoded_str)
        if not match:
            return "Nem található roomID."
        room_id = match.group(1)

        parsed_json = json.loads(decoded_str)
    except Exception:
        return "Hiba a szobaadatok dekódolásánál."

    packages_start = decoded_str.find("packages")
    if packages_start == -1:
        return "A 'packages' kulcs nem található."

    slice_start = packages_start + 10
    slice_end = decoded_str.find("]", slice_start)
    if slice_end == -1:
        return "Nem található lezáró szögletes zárójel."

    packages_slice = decoded_str[slice_start : slice_end + 1]

    try:
        parsed_packages = json.loads(packages_slice)
        kulcsszavak = ['senior', 'szenior', 'nyugdíjas']
        talalatok = []
        for csomag in parsed_packages:
            nev = csomag.get("name", "").lower()
            etrend = csomag.get("visibleMealplan", {}).get("name", "").lower()
            if not any(k in nev for k in kulcsszavak) and "félpanzió" in etrend:
                price_type = csomag.get("priceType")
                price_index = csomag.get("priceIndex")
                talalatok.append((price_type, price_index))
    except Exception:
        return "Nem sikerült feldolgozni a 'packages' részt."

    # REQUEST 4
    ar_list = []
    for price_type, price_index in talalatok:
        data4 = {
            'sid': sid,
            'method[name]': 'getPriceData',
            'method[params][page]': 'booking',
            'method[params][room]': '0',
            'method[params][available]': '0',
            'method[params][pricetype]': price_type,
            'method[params][priceindex]': price_index,
            'method[params][roomID]': room_id,
            'method[params][lang]': 'hu',
            'method[params][hotelID]': '1198',
        }

        response4 = session.post(
            'https://hotelessence.nethotelbooking.net/ajax/booking/booking',
            headers=HEADERS,
            data=data4
        )

        try:
            room_price = response4.json().get("price", {}).get("roomPrice", {}).get("hotelPrice")
            if room_price is not None:
                ar_list.append(room_price)
        except Exception:
            continue

    if ar_list:
        legkisebb = min(ar_list)
        return f"A legkedvezőbb ár: {int(legkisebb):,} Ft".replace(",", " ")
    else:
        return "Egyik csomagra sem sikerült árat lekérni."

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
