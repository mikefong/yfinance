from playwright.sync_api import sync_playwright

def save_firstrade_session():
    with sync_playwright() as p:
        # USE WEBKIT INSTEAD OF CHROMIUM
        browser = p.webkit.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://invest.firstrade.com/cgi-bin/login")

        print("\n--- Please log in manually. ---")
        print("Solve CAPTCHA / verification / 2FA as needed.")
        print("When you reach the dashboard, press ENTER here.")
        input()

        context.storage_state(path="firstrade_state.json")
        print("Session saved to firstrade_state.json")

        browser.close()


if __name__ == "__main__":
    save_firstrade_session()

