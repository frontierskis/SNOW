import json
from datetime import datetime
import urllib.request
import urllib.error
from bs4 import BeautifulSoup
import requests

# Define your target ski resorts with official conditions report URLs and fallback coordinates
RESORTS = [
    {
        "id": "sunshine", 
        "name": "Banff Sunshine", 
        "url": "https://www.skibanff.com/the-mountain/mountain-report/current-conditions",
        "lat": 51.1091, "lon": -115.7797
    },
    {
        "id": "louise", 
        "name": "Lake Louise", 
        "url": "https://www.skilouise.com/conditions/snow-report",
        "lat": 51.4414, "lon": -116.1773
    },
    {
        "id": "norquay", 
        "name": "Mt. Norquay", 
        "url": "https://banffnorquay.com/conditions/",
        "lat": 51.1897, "lon": -115.5907
    },
    {
        "id": "castle", 
        "name": "Castle Mountain", 
        "url": "https://www.skicastle.ca/conditions/",
        "lat": 49.3241, "lon": -114.4034
    },
    {
        "id": "fernie", 
        "name": "Fernie Alpine Resort", 
        "url": "https://skifernie.com/conditions/snow-report/",
        "lat": 49.4633, "lon": -115.0877
    },
    {
        "id": "kimberley", 
        "name": "Kimberley Alpine Resort", 
        "url": "https://skikimberley.com/conditions/snow-report/",
        "lat": 49.6644, "lon": -115.9757
    },
    {
        "id": "kickinghorse", 
        "name": "Kicking Horse Mountain Resort", 
        "url": "https://kickinghorseresort.com/conditions/",
        "lat": 51.2976, "lon": -117.0483
    },
    {
        "id": "panorama", 
        "name": "Panorama Mountain Resort", 
        "url": "https://panoramaresort.com/on-the-mountain/conditions",
        "lat": 50.4572, "lon": -116.2415
    }
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_weather_via_api(lat, lon):
    """Fallback weather API query using Open-Meteo if website scraping is unavailable."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=snowfall,temperature_2m&timezone=auto"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'ESP32-SnowTracker/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            hourly_snow = data.get("hourly", {}).get("snowfall", [0])
            
            # 24-hour total
            recent_snow_24h = round(sum(hourly_snow[-24:]) if len(hourly_snow) >= 24 else 0, 1)
            # Multi-day total (e.g., last 7 days = 168 hours)
            recent_snow_multi = round(sum(hourly_snow[-168:]) if len(hourly_snow) >= 168 else sum(hourly_snow), 1)
            
            hourly_temps = data.get("hourly", {}).get("temperature_2m", [0])
            current_temp = hourly_temps[-1] if hourly_temps else 0.0
            
            return {
                "snow24h": f"{recent_snow_24h} cm",
                "snowMulti": f"{recent_snow_multi} cm (7-Day)",
                "snowValue": recent_snow_24h,
                "temp": f"{round(current_temp, 1)}°C"
            }
    except Exception:
        return None

def scrape_resort(resort):
    default_data = {
        "name": resort["name"],
        "temp": "N/A",
        "snow24h": "N/A",
        "snowMulti": "N/A",
        "snowValue": 0.0
    }
    
    try:
        response = requests.get(resort["url"], headers=headers, timeout=10)
        if response.status_code != 200:
            return fetch_fallback_or_default(resort)
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Scrape 24-hr snow
        snow_24h_text = "N/A"
        snow_label = soup.find(string=lambda t: t and ("24 Hours" in t or "Last 24 Hours" in t or "New Snow" in t))
        if snow_label:
            parent = snow_label.find_parent()
            if parent:
                tc = parent.get_text(strip=True)
                for prefix in ["24 Hours", "Last 24 Hours", "24 Hours.", "New Snow"]:
                    tc = tc.replace(prefix, "")
                snow_24h_text = tc.strip()

        # 2. Scrape Multi-day snow (checking for 5 Days, 7 Days, Weekly, etc.)
        snow_multi_text = "N/A"
        multi_label = soup.find(string=lambda t: t and any(term in t for term in ["5 Days", "7 Days", "Weekly", "Past 7 Days", "Last 7 Days"]))
        if multi_label:
            mparent = multi_label.find_parent()
            if mparent:
                mtc = mparent.get_text(strip=True)
                for prefix in ["5 Days", "7 Days", "Weekly", "Past 7 Days", "Last 7 Days", "7 Days."]:
                    mtc = mtc.replace(prefix, "")
                snow_multi_text = mtc.strip()

        # Extract numeric value for sorting from 24h string if available
        val = 0.0
        if snow_24h_text != "N/A":
            try:
                val = float(''.join(c for c in snow_24h_text if c.isdigit() or c == '.'))
            except ValueError:
                val = 0.0

        # If scraping found valid data, return it; otherwise trigger fallback
        if snow_24h_text != "N/A" or snow_multi_text != "N/A":
            return {
                "name": resort["name"],
                "temp": "N/A",
                "snow24h": snow_24h_text if snow_24h_text != "" else "N/A",
                "snowMulti": snow_multi_text if snow_multi_text != "" else "N/A",
                "snowValue": val
            }
            
    except Exception as e:
        print(f"Scraping notice for {resort['name']}: {e}")

    return fetch_fallback_or_default(resort)

def fetch_fallback_or_default(resort):
    fallback = fetch_weather_via_api(resort["lat"], resort["lon"])
    if fallback:
        return {
            "name": resort["name"],
            "temp": fallback["temp"],
            "snow24h": fallback["snow24h"],
            "snowMulti": fallback["snowMulti"],
            "snowValue": fallback["snowValue"]
        }
    return {
        "name": resort["name"],
        "temp": "N/A",
        "snow24h": "N/A",
        "snowMulti": "N/A",
        "snowValue": 0.0
    }

def main():
    updated_data = []
    for resort in RESORTS:
        print(f"Checking conditions for {resort['name']}...")
        data = scrape_resort(resort)
        updated_data.append(data)

    # Sort resorts from highest 24h snow to lowest
    updated_data.sort(key=lambda x: x["snowValue"], reverse=True)

    payload = {
        "lastUpdated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "resorts": updated_data
    }

    with open("snow_report.json", "w") as f:
        json.dump(payload, f, indent=2)

    print("Snow report JSON successfully generated with multi-day snow fields!")

if __name__ == "__main__":
    main()
