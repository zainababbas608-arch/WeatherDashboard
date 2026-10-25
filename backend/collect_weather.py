"""
Deliverable 1: Weather data collector.

Fetches min/max temperature, current conditions and sunshine status for
seven Pakistani cities from Open-Meteo (no API key needed) and stores them
in Firebase Firestore.

Firestore layout:
  cities/{city}            -> latest reading (overwritten on each run)
  readings/{city}_{date}   -> one document per city per day (history)

Run:  python collect_weather.py
"""
import os
from datetime import datetime, timezone

import requests
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

CITIES = {
    "Karachi":    (24.8607, 67.0011),
    "Lahore":     (31.5204, 74.3587),
    "Islamabad":  (33.6844, 73.0479),
    "Peshawar":   (34.0151, 71.5249),
    "Quetta":     (30.1798, 66.9750),
    "Multan":     (30.1575, 71.4243),
    "Faisalabad": (31.4504, 73.1350),
}

API_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes -> readable text
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow",
    80: "Rain showers", 81: "Heavy rain showers", 82: "Violent rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Severe thunderstorm with hail",
}


def sunshine_status(sunshine_s, daylight_s):
    """Turn sunshine/daylight seconds into a simple status label + percentage."""
    if not daylight_s:
        return "Unknown", 0.0
    pct = round(100 * (sunshine_s or 0) / daylight_s, 1)
    if pct >= 65:
        label = "Sunny"
    elif pct >= 35:
        label = "Partly sunny"
    else:
        label = "Mostly cloudy"
    return label, pct


def fetch_city(name, lat, lon):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weather_code,is_day",
        "daily": "temperature_2m_max,temperature_2m_min,sunshine_duration,daylight_duration",
        "timezone": "Asia/Karachi",
        "forecast_days": 1,
    }
    resp = requests.get(API_URL, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    cur, daily = data["current"], data["daily"]
    label, pct = sunshine_status(daily["sunshine_duration"][0], daily["daylight_duration"][0])

    return {
        "city": name,
        "latitude": lat,
        "longitude": lon,
        "date": daily["time"][0],
        "temp_min_c": daily["temperature_2m_min"][0],
        "temp_max_c": daily["temperature_2m_max"][0],
        "temp_current_c": cur["temperature_2m"],
        "condition": WMO_CODES.get(cur["weather_code"], f"Code {cur['weather_code']}"),
        "is_day": bool(cur["is_day"]),
        "sunshine_hours": round((daily["sunshine_duration"][0] or 0) / 3600, 2),
        "daylight_hours": round((daily["daylight_duration"][0] or 0) / 3600, 2),
        "sunshine_pct": pct,
        "sunshine_status": label,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


def init_firestore():
    key_path = os.getenv("FIREBASE_KEY_PATH", "serviceAccountKey.json")
    if not os.path.isabs(key_path):
        # Resolve relative to this script, not the folder you ran Python from
        key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), key_path)
    if not os.path.exists(key_path):
        raise SystemExit(
            f"Firebase key not found at:\n  {key_path}\n"
            "Download it from Firebase console -> Project settings -> Service accounts -> "
            "Generate new private key, then rename it to serviceAccountKey.json and put it in the backend/ folder."
        )
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(key_path))
    return firestore.client()


def main():
    db = init_firestore()
    for name, (lat, lon) in CITIES.items():
        try:
            record = fetch_city(name, lat, lon)
        except Exception as exc:
            print(f"[skip] {name}: {exc}")
            continue
        db.collection("cities").document(name).set(record)
        db.collection("readings").document(f"{name}_{record['date']}").set(record)
        print(f"[ok]   {name}: {record['temp_min_c']}-{record['temp_max_c']}°C, "
              f"{record['condition']}, {record['sunshine_status']}")


if __name__ == "__main__":
    main()
