import requests
import json


def calculate_guest_data(adults, children_ages):
    data = {
        "Reservation[room_persons][0][adults]": str(adults)
    }

    if children_ages:
        data["Reservation[room_persons][0][children_count]"] = str(len(children_ages))
        for i, age in enumerate(children_ages):
            data[f"Reservation[room_persons][0][children][{i}][age]"] = str(age)
            data[f"Reservation[room_persons][0][children][{i}][baby_bed]"] = "0"

    return data


def get_price(hotel_config, arrive, departure, adults=2, children=[]):
    post_url = hotel_config["post_url"]
    base_url = hotel_config["base_url"]

    headers_post = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0"
    }

    guest_data = calculate_guest_data(adults, children)

    data = {
        "Reservation[arrival]": arrive,
        "Reservation[departure]": departure,
        "Reservation[room_count]": "1",
        "Reservation[currency_code]": "HUF"
    }
    data.update(guest_data)

    try:
        response_post = requests.post(post_url, headers=headers_post, data=data)
        if response_post.status_code != 200:
            return f"A POST kérés sikertelen volt. HTTP státuszkód: {response_post.status_code}"

        cookies_header = response_post.headers.get("Set-Cookie")
        if not cookies_header:
            return "Nem érkezett Set-Cookie fejléc."

        cookie_list = [c.strip().split(";")[0] for c in cookies_header.split(",")]
        cookie_string = "; ".join(cookie_list)

        resp_json = response_post.json()
        redirect_url = resp_json["data"]["redirect_url"].replace("\\/", "/")
        full_get_url = f"{base_url}{redirect_url}"

        headers_get = {
            "Cookie": cookie_string,
            "User-Agent": "Mozilla/5.0"
        }

        response_get = requests.get(full_get_url, headers=headers_get)
        if response_get.status_code != 200:
            return f"A GET kérés sikertelen volt. HTTP státuszkód: {response_get.status_code}"

        text = response_get.text
        start_marker = '"rs_reservation_data"'
        end_marker = '"errors":'

        if start_marker not in text or end_marker not in text:
            return "Nem található a JSON blokk."

        start_index = text.find(start_marker) + 22
        end_index = text.find(end_marker) + 12
        snippet = text[start_index:end_index].strip()

        try:
            adatok = json.loads(snippet)
            calculated_room_models = adatok.get("calculatedRoomModels", {})

            if "0" not in calculated_room_models:
                return "Nincs szoba adat."

            room_data = calculated_room_models["0"].get("0", {})
            price_ranges = room_data.get("calculatedPriceRangeModels", {})

            kizart_szavak = ["senior", "szenior", "nyugdíjas", "all inclusive", "all inkluzív", "reggelis", "önellátással", "kemping"]
            arak = []

            for csomag in price_ranges.values():
                name = csomag.get("name", "").lower()
                sub_name = csomag.get("subName", "").lower()

                if any(tiltott in name or tiltott in sub_name for tiltott in kizart_szavak):
                    continue

                ar = csomag.get("price")
                if isinstance(ar, (int, float)):
                    arak.append(ar)

            if arak:
                return f"A legkedvezőbb ár: {int(min(arak)):,} Ft".replace(",", " ")
            else:
                return "Nem található megfelelő ár (nem senior, nem all inclusive, nem reggelis, nem önellátással, nem kemping)."

        except Exception as e:
            return f"Hiba a JSON feldolgozása közben: {e}"

    except Exception as e:
        return f"Hiba történt: {e}"
