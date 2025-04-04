import requests
import json
import re
from requests import Session

# Ez a függvény fogadja a frontendről érkező érkezési és távozási dátumot
def get_price(arrival, departure):
    session = Session()
    session.headers.update({
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    })

    # 1. GET kérés az alapoldalra a CSRF token megszerzéséhez
    response = session.get("https://booking.aquaticum.hu")
    match = re.search(r'name="_csrf" value="([^"]+)"', response.text)
    csrf_token = match.group(1) if match else None
    if not csrf_token:
        return "Nem található CSRF token."

    # 2. GET kérés a hotel init endpointra
    headers2 = {
        "X-CSRF-TOKEN": csrf_token,
        "Accept": "application/json"
    }
    response2 = session.get("https://booking.aquaticum.hu/booking/hotel/init", headers=headers2)
    flow_id = response2.headers.get("flow_id")
    if not flow_id:
        return "Nem található flow_id."

    # 3. POST kérés a szobák lekéréséhez
    headers3 = {
        'flow_id': flow_id,
        'X-CSRF-TOKEN': csrf_token,
        'Referer': 'https://booking.aquaticum.hu/booking/hotel',
        'Accept': 'application/json; charset=utf-8',
        'Content-Type': 'application/json; charset=UTF-8',
    }
    json_data3 = {
        'checkIn': arrival,
        'checkOut': departure,
        'roomCount': 1,
        'rooms': [
            {
                'guests': [
                    {"guestId": 4, "count": 2},
                    {"guestId": 3, "count": 1},
                    {"guestId": 2, "count": 1},
                    {"guestId": 1, "count": 0},
                ]
            },
        ],
    }
    response3 = session.post('https://booking.aquaticum.hu/booking/hotel/init', headers=headers3, json=json_data3)

    # 4. GET kérés a csomagokhoz
    headers4 = {
        'Accept': 'application/json; charset=utf-8',
        'X-CSRF-TOKEN': csrf_token,
        'flow_id': flow_id,
    }
    response4 = session.get('https://booking.aquaticum.hu/booking/hotel/package', headers=headers4)
    try:
        jsonPayload = response4.json()['presentationData']['choices'][0]
    except Exception:
        return "Nem sikerült kinyerni a csomagválasztékot."

    # 5. POST kérés a kiválasztott csomag elfogadásához
    headers5 = {
        'Accept': 'application/json; charset=utf-8',
        'Content-Type': 'application/json; charset=UTF-8',
        'X-CSRF-TOKEN': csrf_token,
        'flow_id': flow_id,
    }
    response5 = session.post('https://booking.aquaticum.hu/booking/hotel/package', headers=headers5, json=jsonPayload)

    # 6. GET kérés a szobák árához
    headers6 = {
        'Accept': 'application/json; charset=utf-8',
        'X-CSRF-TOKEN': csrf_token,
        'flow_id': flow_id,
    }
    response6 = session.get('https://booking.aquaticum.hu/booking/hotel/rooms', headers=headers6)

    # Ár kinyerése
    try:
        json_data = response6.json()
        rooms = json_data.get("bookingData", {}).get("initForm", {}).get("rooms", [])
        if rooms and "serviceIds" in rooms[0] and rooms[0]["serviceIds"]:
            minprice = round(rooms[0]["serviceIds"][0].get("price", 0))
            return f"A legkedvezőbb ár: {minprice:,} Ft".replace(",", " ")
    except Exception:
        pass

    return "Nem található ár."
