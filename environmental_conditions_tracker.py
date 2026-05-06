import os
import requests
import time

# ==========================================
# ⚙️ CONFIGURATION (ТЕХНИЧЕСКИЕ ПАРАМЕТРЫ)
# ==========================================

ZIP_CODE = "98052"
COUNTRY_CODE = "US"
CLOUD_MIN = 0
CLOUD_MAX = 70
SEARCH_RADIUS_KM = 25  
DAYS_BACK = 3          

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
    print(f"Initiating telemetry scan for ZIP: {ZIP_CODE}...")

    if not OWM_API_KEY or not EBIRD_API_KEY:
         print("API keys are missing in environment! Check GitHub Secrets.")
         return

    weather_url = f"https://api.openweathermap.org/data/2.5/weather?zip={ZIP_CODE},{COUNTRY_CODE}&appid={OWM_API_KEY}"
    
    try:
        weather_res = requests.get(weather_url).json()
        if weather_res.get("cod") != 200:
            print(f"Weather API Error: {weather_res.get('message')}")
            return 

        clouds = weather_res["clouds"]["all"]
        lat = weather_res["coord"]["lat"]
        lon = weather_res["coord"]["lon"]
        
        print(f"Current cloud cover: {clouds}%")

        if CLOUD_MIN <= clouds <= CLOUD_MAX:
            print("Cloud cover optimal. Scanning for biological targets...")
            
            headers = {"X-eBirdApiToken": EBIRD_API_KEY}
            ebird_url = f"https://api.ebird.org/v2/data/obs/geo/recent?lat={lat}&lng={lon}&dist={SEARCH_RADIUS_KM}&back={DAYS_BACK}"
            
            ebird_res = requests.get(ebird_url, headers=headers).json()
            
            if isinstance(ebird_res, list) and len(ebird_res) > 0:
                print("Target species detected!")
                alert_text = (
                    f"🟢 ALERT: Area Observer\n"
                    f"Location: {ZIP_CODE}\n"
                    f"Clouds: {clouds}%\n"
                    f"Target species ({TARGET_SPECIES}) detected nearby.\n"
                    f"Conditions: OPTIMAL."
                )
                send_telegram_alert(alert_text)
            else:
                print("No target species detected in the area.")
        else:
            print("Cloud cover out of optimal range. Standing by.")

    except Exception as e:
        print(f"System exception during scan: {e}")

if __name__ == "__main__":
    check_conditions()
