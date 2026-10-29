import json
from datetime import datetime
import urllib.request
import urllib.error

# Define your 8 target resorts with exact GPS coordinates
RESORTS = [
    {"id": "sunshine", "name": "Banff Sunshine", "lat": 51.1091, "lon": -115.7797},
    {"id": "louise", "name": "Lake Louise", "lat": 51.4414, "lon": -116.1773},
    {"id": "norquay", "name": "Mt. Norquay", "lat": 51.1897, "lon": -115.5907},
    {"id": "castle", "name": "Castle Mountain", "lat": 49.3241, "lon": -114.4034},
    {"id": "fernie", "name": "Fernie Alpine Resort", "lat": 49.4633, "lon": -115.0877},
    {"id": "kimberley", "name": "Kimberley Alpine Resort", "lat": 49.6644, "lon": -115.9757},
    {"id": "kickinghorse", "name": "Kicking Horse Mountain Resort", "lat": 51.2976, "lon": -117.0483},
    {"id": "panorama", "name": "Panorama Mountain Resort", "lat": 50.4572, "lon": -116.2415}
]

def fetch_weather_data():
    updated_data = []
    
    for resort in RESORTS:
        # Open-Meteo query requesting hourly snowfall and temperatures with local timezone adjustment
        url = (f"https://api.open-meteo.com/v1/forecast?"
               f"latitude={resort['lat']}&longitude={resort['lon']}&"
               f"hourly=snowfall,temperature_2m&timezone=auto")
        
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'ESP32-SnowTracker/1.0'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                hourly_snow = data.get("hourly", {}).get("snowfall", [0])
                
                # Calculate precise 24-hour snowfall in cm (summing last 24 hours)
                recent_24h = round(sum(hourly_snow[-24:]) if len(hourly_snow) >= 24 else 0, 1)
                
                # Calculate 7-day multi-day snowfall in cm (summing last 168 hours)
                recent_7d = round(sum(hourly_snow[-168:]) if len(hourly_snow) >= 168 else sum(hourly_snow), 1)
                
                hourly_temps = data.get("hourly", {}).get("temperature_2m", [0])
                current_temp = hourly_temps[-1] if hourly_temps else 0.0

                resort_info = {
                    "name": resort["name"],
                    "temp": f"{round(current_temp, 1)}°C",
                    "snow24h": f"{int(recent_24h) if recent_24h.is_integer() else recent_24h} cm",
                    "snowMulti": f"{int(recent_7d) if recent_7d.is_integer() else recent_7d} cm",
                    "snowValue": recent_24h  # Used for automated sorting
                }
                updated_data.append(resort_info)
                
        except (urllib.error.URLError, TimeoutError, Exception) as e:
            print(f"Warning: Could not fetch data for {resort['name']}: {e}")
            updated_data.append({
                "name": resort["name"],
                "temp": "N/A",
                "snow24h": "0 cm",
                "snowMulti": "0 cm",
                "snowValue": 0.0
            })

    # Sort resorts from highest 24h snow to lowest so the powder winner is always index [0]
    updated_data.sort(key=lambda x: x["snowValue"], reverse=True)

    payload = {
        "lastUpdated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "resorts": updated_data
    }

    with open("snow_report.json", "w") as f:
        json.dump(payload, f, indent=2)

    print("Snow report JSON successfully generated and sorted in clean centimeters!")

if __name__ == "__main__":
    fetch_weather_data()
