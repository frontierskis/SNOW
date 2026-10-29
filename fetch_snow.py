import json
from datetime import datetime
from bs4 import BeautifulSoup
import requests

# Define your 8 target resorts with their precise official conditions/snow report URLs
RESORTS = [
    {
        "id": "sunshine", 
        "name": "Banff Sunshine", 
        "url": "https://www.skibanff.com/the-mountain/mountain-report/current-conditions"
    },
    {
        "id": "louise", 
        "name": "Lake Louise", 
        "url": "https://www.skilouise.com/conditions/snow-report"
    },
    {
        "id": "norquay", 
        "name": "Mt. Norquay", 
        "url": "https://banffnorquay.com/conditions/"
    },
    {
        "id": "castle", 
        "name": "Castle Mountain", 
        "url": "https://www.skicastle.ca/conditions/"
    },
    {
        "id": "fernie", 
        "name": "Fernie Alpine Resort", 
        "url": "https://skifernie.com/conditions/snow-report/"
    },
    {
        "id": "kimberley", 
        "name": "Kimberley Alpine Resort", 
        "url": "https://skikimberley.com/conditions/snow-report/"
    },
    {
        "id": "kickinghorse", 
        "name": "Kicking Horse Mountain Resort", 
        "url": "https://kickinghorseresort.com/conditions/"
    },
    {
        "id": "panorama", 
        "name": "Panorama Mountain Resort", 
        "url": "https://panoramaresort.com/on-the-mountain/conditions"
    }
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def scrape_resort(resort):
    # Default fallback values if data is unavailable, broken, or out of season
    default_data = {
        "name": resort["name"],
        "temp": "N/A",
        "snow24h": "N/A",
        "snowMulti": "N/A",
        "snowValue": 0.0
    }
    
    try:
        response = requests.get(resort["url"], headers=headers, timeout=12)
        if response.status_code != 200:
            return default_data
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Helper to extract clean text values near labels
        def find_metric_value(keywords):
            for kw in keywords:
                label = soup.find(string=lambda t: t and kw.lower() in t.lower())
                if label:
                    # Look for parent or sibling containers holding the value
                    parent = label.find_parent()
                    if parent:
                        text = parent.get_text(strip=True)
                        for prefix in keywords:
                            text = text.replace(prefix, "").replace(prefix.lower(), "").strip()
                        if text and any(unit in text.lower() for unit in ["cm", "in", "°"]):
                            return text
            return "N/A"

        # Extract 24-hr snowfall
        snow_24h = find_metric_value(["24 Hours", "Last 24 Hours", "New Snow", "24hr"])
        
        # Extract Multi-day / Weekly snowfall (5 Day, 7 Day, Weekly)
        snow_multi = find_metric_value(["7 Days", "5 Days", "Weekly", "Past 7 Days", "7 Day"])

        # Parse numerical value from 24h string for sorting
        val = 0.0
        if snow_24h != "N/A":
            try:
                val = float(''.join(c for c in snow_24h if c.isdigit() or c == '.'))
            except ValueError:
                val = 0.0

        return {
            "name": resort["name"],
            "temp": "N/A",  # Can be mapped if temp label is scraped, defaults to N/A cleanly
            "snow24h": snow_24h,
            "snowMulti": snow_multi,
            "snowValue": val
        }
                    
    except Exception as e:
        print(f"Scraping notice for {resort['name']}: {e}")

    return default_data

def main():
    updated_data = []
    for resort in RESORTS:
        print(f"Checking mid-mountain / conditions report for {resort['name']}...")
        data = scrape_resort(resort)
        updated_data.append(data)

    # Sort resorts from highest 24h snow to lowest (N/A items safely cascade to the bottom)
    updated_data.sort(key=lambda x: x["snowValue"], reverse=True)

    payload = {
        "lastUpdated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "resorts": updated_data
    }

    # Save to JSON file for GitHub Actions
    with open("snow_report.json", "w") as f:
        json.dump(payload, f, indent=2)

    print("Snow report JSON successfully generated with 24h and multi-day metrics!")

if __name__ == "__main__":
    main()
