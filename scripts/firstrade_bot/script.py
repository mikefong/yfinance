import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load credentials
load_dotenv()

USERNAME = os.getenv("FIRSTRADE_USERNAME")
PASSWORD = os.getenv("FIRSTRADE_PASSWORD")

if not USERNAME or not PASSWORD:
    raise ValueError("Missing FIRSTRADE_USERNAME or FIRSTRADE_PASSWORD in .env")


def get_firstrade_holdings():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=True after debugging
        page = browser.new_page()

        # Go to login page
        page.goto("https://invest.firstrade.com/cgi-bin/login")

        # Wait for login fields
        page.wait_for_selector("#username")

        page.fill("#username", USERNAME)
        page.fill("#password", PASSWORD)
        page.click("#loginButton")

        # Wait until login succeeded (Portfolio menu appears)
        page.wait_for_selector("text=Portfolio", timeout=15000)

        # Navigate to portfolio page
        page.goto("https://invest.firstrade.com/cgi-bin/portfolio")

        # Wait for positions table
        page.wait_for_selector("table#positions tbody tr", timeout=15000)

        rows = page.query_selector_all("table#positions tbody tr")

        holdings = []
        for r in rows:
            cells = [c.inner_text().strip() for c in r.query_selector_all("td")]
            if len(cells) < 5:
                continue
            holdings.append({
                "symbol": cells[0],
                "description": cells[1],
                "quantity": cells[2],
                "last_price": cells[3],
                "market_value": cells[4],
            })

        browser.close()
        return holdings


if __name__ == "__main__":
    holdings = get_firstrade_holdings()
    for h in holdings:
        print(h)

