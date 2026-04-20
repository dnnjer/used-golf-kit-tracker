import os
import json
import requests
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

SHEET_NAME = os.environ["SHEET_NAME"]
EBAY_ACCESS_TOKEN = os.environ["EBAY_ACCESS_TOKEN"]
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

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
    service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
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
