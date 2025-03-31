import json
import codecs
import re
from requests import Session

HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'hu-HU,hu;q=0.9',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'iframe',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-site',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
}

def get_price(hotel_config, arrive, departure):
    session = Session()
    requests_cfg = hotel_config["requests"]

    # REQUEST 1 - GET
    response1 = session.get(requests_cfg[0]["url"], headers=HEADERS)
    if response1.status_code != 200:
        return f"Az 1. request sikertelen volt. HTTP státuszkód: {response1.status_code}"

    if not session.cookies:
        return "A szerver nem küldött vissza session cookie-t (sid). Ellenőrizd az 1. request URL-jét vagy fejléceit."

    try:
        sid = list(session.cookies)[0].value
    except IndexError:
        return "Nem sikerült lekérni a session ID-t (sid)."

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

    session.post(requests_cfg[1]["url"], headers=HEADERS, data=data2)

    # REQUEST 3 - GET
    url3 = requests_cfg[2]["url_template"].replace("{sid}", sid)
    response3 = session.get(url3, headers=HEADERS)

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
    except Exception as e:
        return f"Nem sikerült feldolgozni a 'packages' részt. Hiba: {e} — Részlet: {packages_slice[:300]}"

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

        response4 = session.post(requests_cfg[3]["url"], headers=HEADERS, data=data4)
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
