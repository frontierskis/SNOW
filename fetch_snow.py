import json
from datetime import datetime
from bs4 import BeautifulSoup
import requests

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
        "url": "https://www.skicastle.ca/snowreport/"
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
        "url": "https://kickinghorseresort.com/conditions/snow-report/"
    },
    {
        "id": "panorama", 
        "name": "Panorama Mountain Resort", 
        "url": "https://www.panoramaresort.com/panorama-today/daily-snow-report"
    }
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_snow_value(text):
    """Helper to pull the numeric float out of strings like '15 CM' or '3 cm'."""
    if not text:
        return 0.0
    try:
        filtered = ''.join(c for c in text if c.isdigit() or c == '.')
        return float(filtered) if filtered else 0.0
    except ValueError:
        return 0.0

def scrape_resort(resort):
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
        snow_24h = "N/A"
        snow_multi = "N/A"

        # --- 1. FERNIE ---
        if resort["id"] == "fernie":
            lbl_24 = soup.find(string=lambda t: t and "LAST 24 HOURS" in t.upper())
            if lbl_24 and lbl_24.find_parent():
                # Usually text is structured right above/below the label in RCR layouts
                parent = lbl_24.find_parent()
                # Grab preceding sibling or text node containing the measurement
                prev = parent.find_previous_sibling()
                if prev:
                    snow_24h = prev.get_text(strip=True)
            
            lbl_7d = soup.find(string=lambda t: t and "LAST 7 DAYS" in t.upper())
            if lbl_7d and lbl_7d.find_parent():
                parent = lbl_7d.find_parent()
                prev = parent.find_previous_sibling()
                if prev:
                    snow_multi = prev.get_text(strip=True)

        # --- 2. CASTLE MOUNTAIN ---
        elif resort["id"] == "castle":
            lbl_24 = soup.find(string=lambda t: t and "Fresh Snow (24 hrs)" in t)
            if lbl_24 and lbl_24.find_parent():
                # Castle uses table rows or clear label-value pairs
                parent = lbl_24.find_parent()
                nxt = parent.find_next_sibling()
                if nxt:
                    snow_24h = f"{nxt.get_text(strip=True)} cm"
            
            lbl_7d = soup.find(string=lambda t: t and "Last 7 days" in t)
            if lbl_7d and lbl_7d.find_parent():
                parent = lbl_7d.find_parent()
                nxt = parent.find_next_sibling()
                if nxt:
                    snow_multi = f"{nxt.get_text(strip=True)} cm"

        # --- 3. BANFF SUNSHINE ---
        elif resort["id"] == "sunshine":
            lbl_24 = soup.find(string=lambda t: t and "24hr" in t.lower())
            if lbl_24 and lbl_24.find_parent():
                nxt = lbl_24.find_parent().find_next_sibling()
                if nxt:
                    snow_24h = nxt.get_text(strip=True)
            
            lbl_5d = soup.find(string=lambda t: t and "5 Day" in t)
            if lbl_5d and lbl_5d.find_parent():
                nxt = lbl_5d.find_parent().find_next_sibling()
                if nxt:
                    snow_multi = nxt.get_text(strip=True)

        # --- 4. MT. NORQUAY ---
        elif resort["id"] == "norquay":
            lbl_24 = soup.find(string=lambda t: t and "Last 24 Hours" in t)
            if lbl_24 and lbl_24.find_parent():
                nxt = lbl_24.find_parent().find_next_sibling()
                if nxt:
                    snow_24h = nxt.get_text(strip=True)
            
            lbl_7d = soup.find(string=lambda t: t and "Last 7 Days" in t)
            if lbl_7d and lbl_7d.find_parent():
                nxt = lbl_7d.find_parent().find_next_sibling()
                if nxt:
                    snow_multi = nxt.get_text(strip=True)

        # --- 5. KICKING HORSE ---
        elif resort["id"] == "kickinghorse":
            lbl_24 = soup.find(string=lambda t: t and "LAST 24 HOURS" in t.upper())
            if lbl_24 and lbl_24.find_parent():
                parent = lbl_24.find_parent()
                prev = parent.find_previous_sibling()
                if prev:
                    snow_24h = prev.get_text(strip=True)

        # --- 6. KIMBERLEY ---
        elif resort["id"] == "kimberley":
            lbl_24 = soup.find(string=lambda t: t and "LAST 24 HOURS" in t.upper())
            if lbl_24 and lbl_24.find_parent():
                parent = lbl_24.find_parent()
                prev = parent.find_previous_sibling()
                if prev:
                    snow_24h = prev.get_text(strip=True)

        # --- 7. PANORAMA ---
        elif resort["id"] == "panorama":
            lbl_24 = soup.find(string=lambda t: t and "24 Hours" in t)
            if lbl_24 and lbl_24.find_parent():
                nxt = lbl_24.find_parent().find_next_sibling()
                if nxt:
                    snow_24h = nxt.get_text(strip=True)
            
            lbl_7d = soup.find(string=lambda t: t and "7 Days" in t)
            if lbl_7d and lbl_7d.find_parent():
                nxt = lbl_7d.find_parent().find_next_sibling()
                if nxt:
                    snow_multi = nxt.get_text(strip=True)

        # --- 8. LAKE LOUISE (General fallback check) ---
        else:
            lbl_24 = soup.find(string=lambda t: t and "24 Hours" in t)
            if lbl_24 and lbl_24.find_parent():
                nxt = lbl_24.find_parent().find_next_sibling()
                if nxt:
                    snow_24h = nxt.get_text(strip=True)

        # Fallback to generic keyword search if specific block missed anything
        if snow_24h == "N/A":
            generic_lbl = soup.find(string=lambda t: t and "24 Hours" in t)
            if generic_lbl and generic_lbl.find_parent():
                snow_24h = generic_lbl.find_parent().get_text(strip=True).replace("24 Hours", "").strip()

        val = clean_snow_value(snow_24h)

        return {
            "name": resort["name"],
            "temp": "N/A",
            "snow24h": snow_24h if snow_24h else "N/A",
            "snowMulti": snow_multi if snow_multi else "N/A",
            "snowValue": val
        }
                    
    except Exception as e:
        print(f"Scraping notice for {resort['name']}: {e}")

    return default_data

def main():
    updated_data = []
    for resort in RESORTS:
        print(f"Scraping precise metrics for {resort['name']}...")
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

    print("Snow report JSON successfully generated with site-specific rules!")

if __name__ == "__main__":
    main()
