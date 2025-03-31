from flask import Flask, request
from flask_cors import CORS
import json
import os
import resnweb
import roomsome1

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET", "POST"])
def get_price():
    if request.method == "GET":
        return "Használj POST kérést a szálloda, motor és dátumok megadásához."

    adatok = request.get_json()
    hotel_nev = adatok.get("hotel")
    engine = adatok.get("engine")
    arrive = adatok.get("arrive")
    departure = adatok.get("departure")

    if not hotel_nev or not engine:
        return "Hiányzó szálloda vagy motor típus."

    json_file = f"{engine}.json"

    if not os.path.exists(json_file):
        return f"Nincs konfigurációs fájl a(z) {engine} motorhoz."

    with open(json_file, encoding="utf-8") as f:
        engine_hotels = json.load(f)

    engine_hotel = next((h for h in engine_hotels if h["name"] == hotel_nev), None)
    if not engine_hotel:
        return f"A(z) {hotel_nev} szálloda nem található a {engine} konfigurációban."

    if engine == "resnweb":
        return resnweb.get_price(engine_hotel, arrive, departure)
    elif engine == "roomsome1":
        return roomsome1.get_price(engine_hotel, arrive, departure)
    else:
        return f"Nem támogatott foglalómotor: {engine}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
