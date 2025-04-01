import requests
from urllib.parse import quote

# Alapadatok
scraperapi_key = "c401c39c3f0f84264c25fb763591324f"
real_url = "https://calimbrawellnesshotel.hu/online-foglalas/kereses"
encoded_url = quote(real_url, safe="")
full_url = f"https://api.scraperapi.com?api_key={scraperapi_key}&url={encoded_url}"

# Payload
payload = {
    "room_persons[0][adult]": "2",
    "room_persons[0][child]": "2",
    "room_persons[0][child_ages][0]": "6",
    "room_persons[0][child_ages][1]": "10",
    "arrival": "2025-04-18",
    "departure": "2025-04-22",
    "rooms": "1",
    "lang": "hu",
    "subpage_num": "1",
    "subpage_num_next": "2"
}

# Kérés
session = requests.Session()
response = session.post(full_url, data=payload, allow_redirects=False)

print(f"\nHTTP status: {response.status_code}\n")

# Headers kiírása
print("=== RESPONSE HEADERS ===")
for k, v in response.headers.items():
    print(f"{k}: {v}")

# Cookie-k ellenőrzése
print("\n=== COOKIE HEADER ===")
cookie_header = response.headers.get("Set-Cookie")
if cookie_header:
    print(cookie_header)
else:
    print("Nincs Set-Cookie header.")
