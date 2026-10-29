import json
from datetime import datetime
from bs4 import BeautifulSoup
import requests

# Define your target ski resorts with official conditions report URLs
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
    # Default fallback if data is unavailable, broken, or page is down
    default_data = {
        "name": resort["name"],
        "temp": "N/A",
        "snow24h": "N/A",
        "snowValue": 0.0
    }
    
    try:
        response = requests.get(resort["url"], headers=headers, timeout=10)
        if response.status_code != 200:
            return default_data
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for 24-hour snowfall labels on the page
        snow_label = soup.find(string=lambda t: t and ("24 Hours" in t or "Last 24 Hours" in t or "New Snow" in t))
        if snow_label:
            parent = snow_label.find_parent()
            if parent:
                text_content = parent.get_text(strip=True)
                # Clean up prefixes
                for prefix in ["24 Hours", "Last 24 Hours", "24 Hours.", "New Snow"]:
                    text_content = text_content.replace(prefix, "")
                snow_text = text_content.strip()
                
                if snow_text and ("cm" in snow_text.lower() or "in" in snow_text.lower()):
                    try:
                        val = float(''.join(c for c in snow_text if c.isdigit() or c == '.'))
                    except ValueError:
                        val = 0.0
                        
                    return {
                        "name": resort["name"],
                        "temp": "N/A",  # Or parse live temp if present on their block
                        "snow24h": snow_text,
                        "snowValue": val
                    }
                    
    except Exception as e:
        print(f"Scraping notice for {resort['name']}: {e}")

    # Return N/A if scraping fails or snow metrics aren't currently posted
    return default_data

def main():
    updated_data = []
    for resort in RESORTS:
        print(f"Checking conditions for {resort['name']}...")
        data = scrape_resort(resort)
        updated_data.append(data)

    # Sort resorts from highest numerical 24h snow to lowest (N/A items fall to the bottom)
    updated_data.sort(key=lambda x: x["snowValue"], reverse=True)

    payload = {
        "lastUpdated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "resorts": updated_data
    }

    # Save to JSON file for GitHub Actions to push to your repo
    with open("snow_report.json", "w") as f:
        json.dump(payload, f, indent=2)

    print("Snow report JSON successfully generated!")

if __name__ == "__main__":
    main()
