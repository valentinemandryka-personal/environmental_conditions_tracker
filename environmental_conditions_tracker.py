import os
import requests
import time

# ==========================================
# ⚙️ CONFIGURATION (WILD NATURE EDITION)
# ==========================================

LOCATIONS = [
    {"name": "Marymoor Park", "zip": "98052"},
    {"name": "Juanita Bay Park", "zip": "98033"},  
    {"name": "Lake Sammamish State Park", "zip": "98027"}, 
    {"name": "Mercer Slough Nature Park", "zip": "98005"}, 
    {"name": "Log Boom Park & Heronry", "zip": "98028"},
    {"name": "Carnation Marsh", "zip": "98014"}, 
    {"name": "Stillwater Wildlife Area", "zip": "98019"}, 
    {"name": "Tolt MacDonald Park", "zip": "98014"},
    {"name": "Snoqualmie Valley", "zip": "98065"}, 
    {"name": "Paradise Valley Conservation", "zip": "98072"},
    {"name": "Bob Heirman Wildlife Park", "zip": "98290"} 
]

COUNTRY_CODE = "US"
CLOUD_MIN = 10
CLOUD_MAX = 60
SEARCH_RADIUS_KM = 10 
DAYS_BACK = 1     

# Ключи берем из GitHub Secrets
OWM_API_KEY = os.environ.get("OWM_API_KEY")
EBIRD_API_KEY = os.environ.get("EBIRD_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# ==========================================
# 🛠️ CORE LOGIC
# ==========================================

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Missing Telegram credentials. Aborting alert.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
        print("Alert sent to Telegram.")
    except Exception as e:
        print(f"Error sending alert: {e}")

def check_conditions():
    for loc in LOCATIONS:
        name = loc["name"]
        zip_code = loc["zip"]
        
        print(f"Scanning telemetry for: {name} ({zip_code})...")

        weather_url = f"https://api.openweathermap.org/data/2.5/weather?zip={zip_code},{COUNTRY_CODE}&appid={OWM_API_KEY}"
        
        try:
            weather_res = requests.get(weather_url).json()
            if weather_res.get("cod") != 200: continue

            clouds = weather_res["clouds"]["all"]
            lat = weather_res["coord"]["lat"]
            lon = weather_res["coord"]["lon"]

            if CLOUD_MIN <= clouds <= CLOUD_MAX:
                headers = {"X-eBirdApiToken": EBIRD_API_KEY}
                ebird_url = f"https://api.ebird.org/v2/data/obs/geo/recent?lat={lat}&lng={lon}&dist={SEARCH_RADIUS_KM}&back={DAYS_BACK}"
                
                ebird_res = requests.get(ebird_url, headers=headers).json()
                
                if isinstance(ebird_res, list) and len(ebird_res) > 0:
                    # Вытаскиваем уникальные названия локаций из отчетов eBird
                    hotspots = list(set([obs['locName'] for obs in ebird_res[:3]]))
                    hotspots_str = ", ".join(hotspots)

                    alert_text = (
                        f"🟢 ALERT: Area Observer\n"
                        f"Target: {name}\n"
                        f"Clouds: {clouds}%\n"
                        f"Activity at: {hotspots_str}\n"
                        f"Action: GO TO {name.upper()} NOW."
                    )
                    send_telegram_alert(alert_text)
                    # Сделаем небольшую паузу, чтобы не спамить Telegram
                    time.sleep(2) 
        except Exception as e:
            print(f"Error scanning {name}: {e}")

if __name__ == "__main__":
    check_conditions()
