import requests
import json
import re

def calculate_guest_counts(adults, children_ages, guest_categories):
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
    guests = [{"guestId": guestId, "count": count} for guestId, count in sorted(guest_counts.items(), reverse=True)]
    return guests


def get_price(config, arrival, departure, adults, children):
    session = requests.Session()

    try:
        r1 = session.get("https://foglalas.aquaticum.hu/")
        r1.raise_for_status()
        token_match = re.search(r'"csrfToken":"(.*?)"', r1.text)
        csrf_token = token_match.group(1) if token_match else ""

        r2 = session.get("https://foglalas.aquaticum.hu/api/reservation/hotel/init")
        r2.raise_for_status()
        flow_id = r2.json()["data"]["flowId"]

        guest_data = calculate_guest_counts(adults, children, config["guest_categories"])

        payload_room = {
            "checkIn": arrival,
            "checkOut": departure,
            "roomCount": 1,
            "rooms": [
                {
                    "guests": guest_data
                }
            ],
        }

        headers = {
            "Content-Type": "application/json",
            "X-Csrf-Token": csrf_token,
        }

        r3 = session.post(
            f"https://foglalas.aquaticum.hu/api/reservation/hotel/{flow_id}/rooms",
            json=payload_room,
            headers=headers,
        )
        r3.raise_for_status()

        r4 = session.get(f"https://foglalas.aquaticum.hu/api/reservation/hotel/{flow_id}/packages")
        r4.raise_for_status()
        packages = r4.json()["data"]

        if not packages:
            raise ValueError("Nem találhatók csomagok.")

        selected_package = packages[0]["id"]

        r5 = session.post(
            f"https://foglalas.aquaticum.hu/api/reservation/hotel/{flow_id}/package",
            json={"id": selected_package},
            headers=headers,
        )
        r5.raise_for_status()

        r6 = session.get(f"https://foglalas.aquaticum.hu/api/reservation/hotel/{flow_id}/rooms")
        r6.raise_for_status()
        rooms_data = r6.json()

        try:
            price = (
                rooms_data["data"]["calculatedRoomModels"][0][0]["serviceIds"][0]["price"]
            )
        except (KeyError, IndexError):
            raise ValueError("Nem található ár a válaszban.")

        return f"A legkedvezőbb ár: {price:,} Ft".replace(",", "\u202f")

    except Exception as e:
        return f"Hiba történt: {str(e)}"
