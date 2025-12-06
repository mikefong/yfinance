from playwright.sync_api import sync_playwright

def get_firstrade_holdings():
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir="/Users/bytedance/Library/Application Support/Google/Chrome/Default",
            headless=False,
            channel="chrome"   # important — use real Chrome!
        )

        page = browser.new_page()

        # You’re already logged in, just go straight to portfolio
        page.goto("https://invest.firstrade.com/cgi-bin/portfolio")

        page.wait_for_selector("table#positions tbody tr", timeout=20000)

        rows = page.query_selector_all("table#positions tbody tr")

        data = []
        for r in rows:
            cells = [c.inner_text().strip() for c in r.query_selector_all("td")]
            if len(cells) < 5:
                continue
            data.append({
                "symbol": cells[0],
                "description": cells[1],
                "quantity": cells[2],
                "last_price": cells[3],
                "market_value": cells[4],
            })

        browser.close()
        return data


if __name__ == "__main__":
    print(get_firstrade_holdings())
