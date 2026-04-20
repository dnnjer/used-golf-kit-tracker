import requests
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

SHEET_NAME = "Golf Sets Tracker"
GOOGLE_CREDS_FILE = "service_account.json"
EBAY_ACCESS_TOKEN = "v^1.1#i^1#f^0#r^0#p^1#I^3#t^H4sIAAAAAAAA/+VYe2wURRjv9YUFyyM0gkDgWNBg6+3N7r1X7vTao7QE2tIrV2hC6tzubLt0b3fdmWt7PpuCGDBF0tBYwVAwvhKjxEQTSAmJGiBB1ATfj0jiG0jUBAyJSHD2Wsq1EkB6xCbeP5f55ptvft9vvsfsgK7CotLNVZvPF9sm5e7pAl25Nhs3BRQVFpRNzcudU5ADMhRse7oWd+V35/2yFMOEagj1CBu6hpG9M6FqWEgLg0zS1AQdYgULGkwgLBBRiIZXrRR4FgiGqRNd1FXGXh0JMpB3eSDHQ8B7EOD8gEq1yzYb9CDj9/jdUJLjcSgGgN8j0XmMk6hawwRqJMjwgPc6gNvBgwYuILh4gQuwfg/XxNhjyMSKrlEVFjChNFwhvdbMwHptqBBjZBJqhAlVhyujteHqyLKahqXODFuhYR6iBJIkHj2q0CVkj0E1ia69DU5rC9GkKCKMGWdoaIfRRoXwZTA3AT9NtYw4tyhxoo/3+n0AiFmhslI3E5BcG4clUSSHnFYVkEYUkroeo5SN+AYkkuFRDTVRHbFbf6uTUFVkBZlBZll5eF24ro4JhVsTUCqH2LEGI2m5rsqOuvqIw+cVOc7rhqKD47iA5Hd7hjcasjZM85idKnRNUizSsL1GJ+WIokZjueEzuKFKtVqtGZaJhShDj+cuc8gHmqxDHTrFJGnVrHNFCUqEPT28/gmMrCbEVOJJgkYsjJ1IU0TTyjAUiRk7mY7F4fDpxEGmlRBDcDo7OjrYDhermy1OHgDOuXbVyqjYihKQobpWrg/pK9df4FDSroiIrsSKQFIGxdJJY5UC0FqYkMfn4d1gmPfRsEJjpf8QZPjsHJ0R2coQiYceLk5zQ3bHJb/Pm40MCQ0HqdPCgeIw5UhAsw0RQ4Uicog0zpIJZCqS4PLIvMsvI4fkDcgOd0CWHXGP5HVwMkIAoXhcDPj/T4lyo6EeRaKJSFZiPWtxXt7UWbYislbHnfXmusZ1q7m2QHtlbFlnk+bzJKvCqxtFLDY2xoiH4OCNZsNVna9QFcpMA90/GwRYuZ49Eqp0TJA0Lveiom6gOl1VxNTEOmCXKdVBk6SiSFWpYFxOhg2jOju1Omvu/csycXN+Z69H/Uf96apeYStkJ5ZX1npMDUBDYa0OxIp6wmnlug7p9cMSN6dR26+qOEbJSWW0YYmIpX1JotfyNtZEUNI1NTUu3hR6851QrFE/h0hQpKErK5tmgsXtIvUY60nKAWZrrRtcg96GNNoPiamrKjJj3LjrQSKRJDCuoolWGLKQIAqcYM2a8/m8Ps7lcQXG5ZeYbsXNE62kWaU8v9t268t5PYJqYmL5bpi6lBStO+ot+ORwjn4ACeWkf1y37V3QbTuUa7OBpeAubhFYWJi3Jj/v9jlYIYhVoMxipUWj3/UmYttQyoCKmTsz59inX9bMH1zx6pYfZnU9udjZmzM14/1lz3owe+QFpiiPm5LxHAPmXZkp4KbNKua9wM0DLuDiuUATWHRlNp+7I78k2E52/HQo8HbLn883LV9bELh797lBUDyiZLMV5NBgyZmJy2MPfbA9xfezT8PUEaHx0t7HVv4297YTO058GJrXNzX88jdfFZdu+nGw5fBAf0dFbPr0i9s/Otlf9f6preTMqWm6/t6CDXU9hT3tfSWfbT2047XYPQt+nRtjnzmzsejO882Vivxib9X6Jfd3zX+45PUOuP/rw5OX7H5uzoPB3r/q/2go2R85uGtx2UtHd+18at+bPnnwtO3Y5+BS2ZrktsMzeo7iA7NrDhrvHH+8/Oe9A7sWtgvhnWdfCK060tcfnTy7894pG8/U9kXYLWe3Pfvohbc6WkOfzEiV2C4+ca7s2H1vzDi+sb7gEd/3paULpp0sPP3KF99+d+RgcKB0XxHzwKTe5gu1+b9v4gc+PjB0ln8Dq6S2tRkTAAA="

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SEARCH_TERMS = [
    "golf club set",
    "full golf set",
]

MAX_PRICE_GBP = 500

def connect_sheet():
    creds = Credentials.from_service_account_file(GOOGLE_CREDS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1
    return sheet

def get_existing_links(sheet):
    values = sheet.get_all_values()
    if len(values) <= 1:
        return {}
    rows = values[1:]
    existing = {}
    for idx, row in enumerate(rows, start=2):
        if len(row) >= 10:
            existing[row[9]] = idx
    return existing

def ebay_search(query):
    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    headers = {
        "Authorization": f"Bearer {EBAY_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB",
    }
    params = {
        "q": query,
        "limit": 50,
        "filter": f"price:[..{MAX_PRICE_GBP}],priceCurrency:GBP",
    }

    r = requests.get(url, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("itemSummaries", [])

def listing_to_row(item):
    title = item.get("title", "")
    price_info = item.get("price", {})
    price = ""
    if price_info:
        price_value = price_info.get("value")
        currency = price_info.get("currency")
        if price_value and currency:
            price = f"{price_value} {currency}"

    item_url = item.get("itemWebUrl", "")
    location_parts = []
    if item.get("itemLocation", {}).get("city"):
        location_parts.append(item["itemLocation"]["city"])
    if item.get("itemLocation", {}).get("country"):
        location_parts.append(item["itemLocation"]["country"])
    location = ", ".join(location_parts)

    condition = item.get("condition", "Unknown")
    title_lower = title.lower()

    if "parts" in title_lower or "spares" in title_lower:
        return None

    notes = ""
    if "london" in location.lower() or "london" in title_lower:
        notes = "London priority"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return [
        now,
        now,
        title,
        price,
        "eBay API",
        location,
        condition,
        "",
        "",
        item_url,
        "Active",
        notes,
    ]

def update_sheet(sheet, rows):
    existing_links = get_existing_links(sheet)
    updates = []
    new_rows = []

    for row in rows:
        link = row[9]
        if link in existing_links:
            row_num = existing_links[link]
            updates.append({
                "range": f"A{row_num}:L{row_num}",
                "values": [row]
            })
        else:
            new_rows.append(row)

    if updates:
        sheet.batch_update(updates)

    if new_rows:
        start_row = len(sheet.get_all_values()) + 1
        end_row = start_row + len(new_rows) - 1
        sheet.update(new_rows, f"A{start_row}:L{end_row}")

def main():
    print("Starting API search...")
    sheet = connect_sheet()
    rows = []

    for term in SEARCH_TERMS:
        print(f"Searching eBay API for: {term}")
        items = ebay_search(term)
        for item in items:
            row = listing_to_row(item)
            if row:
                rows.append(row)

    unique = {}
    for row in rows:
        unique[row[9]] = row
    final_rows = list(unique.values())

    if final_rows:
        print(f"Updating sheet with {len(final_rows)} listings...")
        update_sheet(sheet, final_rows)
        print("Done.")
    else:
        print("No listings found.")

if __name__ == "__main__":
    main()