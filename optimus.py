import requests
import re
import json


def calculate_guest_counts(felnottek_szama, gyerekek_eletkora, kategoria_lista):
    vendeg_szamok = {sor["guestId"]: 0 for sor in kategoria_lista}
    kategoriak = sorted(kategoria_lista, key=lambda k: k["agelimitmin"])
    max_korhatar = max(k["agelimitmax"] for k in kategoriak)
    felnottek_guestId = max(k["guestId"] for k in kategoriak if k["agelimitmax"] == max_korhatar)
    teljes_felnottek = felnottek_szama

    for kor in gyerekek_eletkora:
        megfelelo = False
        for kategoria in kategoriak:
            if kategoria["agelimitmin"] <= kor <= kategoria["agelimitmax"]:
                vendeg_szamok[kategoria["guestId"]] += 1
                megfelelo = True
                break
        if not megfelelo:
            teljes_felnottek += 1

    vendeg_szamok[felnottek_guestId] += teljes_felnottek

    return [
        {"guestId": guestId, "count": vendeg_szamok[guestId]}
        for guestId in sorted(vendeg_szamok.keys(), reverse=True)
    ]


def get_price(szalloda, erkezes, tavozas, felnottek_szama, gyerekek_eletkora):
    session = requests.Session()

    try:
        r1 = session.get("https://foglalas.aquaticum.hu/")
        r1.raise_for_status()
        token_kereso = re.search(r'"csrfToken":"(.*?)"', r1.text)
        csrf_token = token_kereso.group(1) if token_kereso else ""

        r2 = session.get("https://foglalas.aquaticum.hu/api/reservation/hotel/init")
        r2.raise_for_status()
        folyam_azonosito = r2.json()["data"]["flowId"]

        vendeg_adatok = calculate_guest_counts(felnottek_szama, gyerekek_eletkora, szalloda["guest_categories"])

        foglalasi_adat = {
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

        fejlecek = {
            "Content-Type": "application/json",
            "X-Csrf-Token": csrf_token,
        }

        r3 = session.post(
            f"https://foglalas.aquaticum.hu/api/reservation/hotel/{folyam_azonosito}/rooms",
            json=foglalasi_adat,
            headers=fejlecek
        )
        r3.raise_for_status()

        r4 = session.get(f"https://foglalas.aquaticum.hu/api/reservation/hotel/{folyam_azonosito}/packages")
        r4.raise_for_status()
        csomagok = r4.json()["data"]

        if not csomagok:
            raise ValueError("Nem találhatók csomagok.")

        valasztott_csomag = csomagok[0]["id"]

        r5 = session.post(
            f"https://foglalas.aquaticum.hu/api/reservation/hotel/{folyam_azonosito}/package",
            json={"id": valasztott_csomag},
            headers=fejlecek
        )
        r5.raise_for_status()

        r6 = session.get(f"https://foglalas.aquaticum.hu/api/reservation/hotel/{folyam_azonosito}/rooms")
        r6.raise_for_status()
        szobak = r6.json()

        try:
            ar = szobak["data"]["calculatedRoomModels"][0][0]["serviceIds"][0]["price"]
        except (KeyError, IndexError):
            raise ValueError("Nem található ár a válaszban.")

        return f"A legkedvezőbb ár: {ar:,} Ft".replace(",", "\u202f")

    except Exception as hiba:
        return f"Hiba történt: {str(hiba)}"
