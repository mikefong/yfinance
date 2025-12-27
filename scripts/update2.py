import gspread
from oauth2client.service_account import ServiceAccountCredentials
import yfinance as yf
import time
from datetime import datetime

# --- Configuration ---
CREDENTIALS_FILE = 'service_account.json'
SHEET_ID = '1ODfC3fbgCBIg4uMtdM8MywmMENRajLS2BR2KFdAEXA0'
WORKSHEET_NAME = 'holdings'
HISTORY_SHEET_NAME = 'history'
TOTAL_VALUE_CELL = 'O1'
# ---------------------

def update_history_tab(spreadsheet):
    """Update the history tab with today's total value"""
    try:
        history_sheet = spreadsheet.worksheet(HISTORY_SHEET_NAME)
        holdings_sheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        print(f"❌ Error: Worksheet '{HISTORY_SHEET_NAME}' not found.")
        return

    today_str = datetime.now().strftime('%Y-%m-%d')
    total_value = holdings_sheet.acell(TOTAL_VALUE_CELL).value

    if not total_value:
        print("⚠️ Total value missing in holdings!O1, skip history update.")
        return

    a2_value = history_sheet.acell('A2').value

    if a2_value == today_str:
        # ✅ FIX: must be 2D list
        history_sheet.update('B2', [[total_value]])
        print(f"🔄 History updated | {today_str} | {total_value}")
    else:
        history_sheet.insert_row([today_str, total_value], index=2)
        print(f"🆕 History row added | {today_str} | {total_value}")

def update_google_sheet_prices():
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            CREDENTIALS_FILE, scope
        )
        client = gspread.authorize(creds)

        spreadsheet = client.open_by_key(SHEET_ID)
        sheet = spreadsheet.worksheet(WORKSHEET_NAME)

        print(f"✅ Connected to Sheet: {spreadsheet.title} | Tab: {sheet.title}")

        valid_rows = (
            list(range(4, 61)) +
            list(range(63, 65)) +
            [71, 79, 80, 81, 82, 83, 84, 85, 86, 87]
        )

        SYMBOL_COL = 1   # A
        PRICE_COL = 17  # Q
        BACKUP_COL = 18 # R

        max_row = max(valid_rows)
        data = sheet.get_all_values(f'A1:R{max_row}')

        updates = []

        for row_num in valid_rows:
            row_index = row_num - 1

            if row_index >= len(data):
                continue

            try:
                symbol = data[row_index][SYMBOL_COL - 1].strip().upper()
                if not symbol:
                    continue

                old_price_raw = data[row_index][PRICE_COL - 1] if len(data[row_index]) >= PRICE_COL else ""
                try:
                    old_price = float(old_price_raw)
                except (ValueError, TypeError):
                    old_price = None

                ticker = yf.Ticker(symbol)
                info = ticker.info

                latest_price = info.get('regularMarketPrice') or info.get('previousClose')
                if latest_price is None:
                    print(f"❌ {symbol} | price fetch failed")
                    continue

                latest_price = float(latest_price)

                # Determine price direction
                if old_price is None:
                    mark = "➖"
                elif latest_price > old_price:
                    mark = "📈"
                elif latest_price < old_price:
                    mark = "📉"
                else:
                    mark = "➖"

                # Backup old price
                updates.append({
                    'range': gspread.utils.rowcol_to_a1(row_num, BACKUP_COL),
                    'values': [[old_price_raw]]
                })

                # Update new price
                updates.append({
                    'range': gspread.utils.rowcol_to_a1(row_num, PRICE_COL),
                    'values': [[latest_price]]
                })

                print(
                    f"{mark} Row {row_num} | {symbol} | "
                    f"{old_price if old_price is not None else 'N/A'} → {latest_price}"
                )

                time.sleep(0.5)

            except Exception as e:
                print(f"🚨 Row {row_num} | Error: {e}")

        if updates:
            sheet.batch_update(updates)
            print("\n🎉 All prices updated successfully!")

            # Update history AFTER holdings update
            update_history_tab(spreadsheet)
        else:
            print("⚠️ No updates to apply.")

    except Exception as e:
        print(f"❌ Critical error: {e}")

# Run
update_google_sheet_prices()

