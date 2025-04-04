import requests
import json
import re
from requests import Session

# Segédfüggvény a vendégek számításához

def calculate_guests(adults, children_ages, guest_categories):
    guest_counts = {entry["guestId"]: 0 for entry in guest_categories}
    guest_categories_sorted = sorted(guest_categories, key=lambda g: g["agelimitmin"])
    max_age_limit = max(entry["agelimitmax"] for entry in guest_categories_sorted)
    guest_id_for_adult = max(
        entry["guestId"] for entry in guest_categories_sorted if entry["agelimitmax"] == max_age_limit
    )
    total_adults = adults
    for age in children_ages:
        matched = False
        for entry in guest_categories_sorted:
            if entry["agelimitmin"] <= age <= entry["agelimitmax"]:
                guest_counts[entry["guestId"]] += 1
                matched = True
                break
        if not matched:
            total_adults += 1
    guest_counts[guest_id_for_adult] += total_adults
    guests = [
        {"guestId": guestId, "count": guest_counts[guestId]}
        for guestId in sorted(guest_counts.keys(), reverse=True)
    ]
    return guests

# Ez a függvény fogadja a frontendről érkező érkezési és távozási dátumot

def get_price(arrival, departure, adults=1, children=[]):
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

    # Vendégkategóriák beolvasása a JSON fájlból
    with open("optimus.json", "r", encoding="utf-8") as f:
        hotel_data = json.load(f)
    guest_categories = hotel_data[0]["guest_categories"]
    guests = calculate_guests(adults, children, guest_categories)

    json_data3 = {
        'checkIn': arrival,
        'checkOut': departure,
        'roomCount': 1,
        'rooms': [
            {
                'guests': guests
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
            return f"A legkedvezőbb ár: {minprice:,} Ft".replace(",", "\u202f")
    except Exception:
        pass

    return "Nem található ár."
