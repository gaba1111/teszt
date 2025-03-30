import json
import codecs
import re
from requests import Session

def get_price(hotel_config, arrive, departure):
    session = Session()
    requests_cfg = hotel_config["requests"]

    # REQUEST 1 - GET
    response1 = session.get(requests_cfg[0]["url"])
    sid = list(session.cookies)[0].value

    # REQUEST 2 - POST
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
    }
    data2.update(requests_cfg[1].get("params", {}))

    session.post(requests_cfg[1]["url"], data=data2)

    # REQUEST 3 - GET
    url3 = requests_cfg[2]["url_template"].replace("{sid}", sid)
    response3 = session.get(url3)

    html = response3.text
    start_marker = "window.rooms"
    end_marker = "window.room_selection"
    start_index = html.find(start_marker)
    end_index = html.find(end_marker)
    if start_index == -1 or end_index == -1:
        return "A szobaadat szakasz nem található."

    kivagott = html[start_index + 27 : end_index - 6]

    try:
        decoded_str = codecs.decode(kivagott, 'unicode_escape')
        match = re.search(r'"roomID":(\d+)', decoded_str)
        if not match:
            return "Nem található roomID."
        room_id = match.group(1)
        parsed_json = json.loads(decoded_str)
    except Exception:
        return "Hiba a szobaadatok feldolgozása közben."

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

    # REQUEST 4 - POST
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
        }
        data4.update(requests_cfg[3].get("params", {}))

        response4 = session.post(requests_cfg[3]["url"], data=data4)
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
