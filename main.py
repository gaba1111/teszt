from flask import Flask, request
from flask_cors import CORS
import json
import resnweb

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET", "POST"])
def get_price():
    if request.method == "GET":
        return "Használj POST kérést a szálloda és dátumok megadásához."

    adatok = request.get_json()
    hotel_nev = adatok.get("hotel")
    arrive = adatok.get("arrive")
    departure = adatok.get("departure")

    with open("hotels.json", encoding="utf-8") as f:
        hotels = json.load(f)

    hotel = next((h for h in hotels if h["name"] == hotel_nev), None)
    if not hotel:
        return "A megadott szálloda nem található."

    engine = hotel.get("engine")
    if engine == "resnweb":
        with open("resnweb.json", encoding="utf-8") as f:
            resnweb_hotels = json.load(f)
        resnweb_hotel = next((h for h in resnweb_hotels if h["name"] == hotel_nev), None)
        if not resnweb_hotel:
            return "A szálloda nem található a resnweb konfigurációban."
        return resnweb.get_price(resnweb_hotel, arrive, departure)
    else:
        return "Nem támogatott foglalómotor: " + engine

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
