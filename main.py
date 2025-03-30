from flask import Flask, request
from flask_cors import CORS
from requests import Session
import json
import os

app = Flask(__name__)
CORS(app)  # engedélyezi a GitHub Pages-ről jövő fetch kéréseket

@app.route("/", methods=["GET", "POST"])
def ar_lekeres():
    if request.method == "GET":
        return "Flask szerver él. Küldj POST-ot a dátumokkal. 😊"

    if request.method == "POST":
        try:
            adatok = request.get_json()
            arrive = adatok.get("arrive")
            departure = adatok.get("departure")

            if not arrive or not departure:
                return "Hiányzik az érkezési vagy távozási dátum!"

            session = Session()
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

            # REQUEST 1
            response1 = session.get(

                "http://api.scraperapi.com?api_key=c401c39c3f0f84264c25fb763591324f&url=https://booking.hotelessence.hu/hotels/hotelessence/iframe=1;lang=hu;ca_currency=HUF;iframe_key=1551",
                headers=HEADERS
            )
            sid = list(session.cookies)[0].value

            # REQUEST 2 – beillesztjük az érkezési és távozási dátumokat
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

            session.post(
                "http://api.scraperapi.com?api_key=c401c39c3f0f84264c25fb763591324f&url=https://hotelessence.nethotelbooking.net/ajax/booking/index",
                headers=HEADERS,
                data=data2
            )

            # REQUEST 3
            session.get(
                f"http://api.scraperapi.com?api_key=c401c39c3f0f84264c25fb763591324f&url=https://booking.hotelessence.hu/hotels/hotelessence/page=booking;roomNumber=0;loyaltyData=eyJzaG93TG9naW4iOmZhbHNlLCJwcm9wb3NhbElEIjpudWxsfQ==;sid={sid}",
                headers=HEADERS
            )

            # REQUEST 4
            data4 = {
                'sid': sid,
                'method[name]': 'getPriceData',
                'method[params][page]': 'booking',
                'method[params][room]': '0',
                'method[params][available]': '0',
                'method[params][pricetype]': 'pac',
                'method[params][priceindex]': '1',
                'method[params][roomID]': '5758',
                'method[params][priceID]': '21600',
                'method[params][lang]': 'hu',
                'method[params][hotelID]': '1198',
            }

            response4 = session.post(
                "http://api.scraperapi.com?api_key=c401c39c3f0f84264c25fb763591324f&url=https://hotelessence.nethotelbooking.net/ajax/booking/booking",
                headers=HEADERS,
                data=data4
            )

            adat = json.loads(response4.text)
            ar = adat.get("price", {}).get("roomPrice", {}).get("hotelPrice", 0)
            return f"A szoba ára: {int(ar):,} Ft".replace(",", " ")

        except Exception as e:
            return f"Hiba történt: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
