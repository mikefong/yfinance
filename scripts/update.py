import gspread
from oauth2client.service_account import ServiceAccountCredentials
import yfinance as yf
import time

# --- Configuration ---
# 1. PATH TO YOUR CREDENTIALS FILE (from Setup Step 2)
CREDENTIALS_FILE = 'service_account.json' 

# 2. GOOGLE SHEET ID (The unique identifier from your URL)
# Your URL: https://docs.google.com/spreadsheets/d/1ODfC3fbgCBIg4uMtdM8MywmMENRajLS2BR2KFdAEXA0/edit...
SHEET_ID = '1ODfC3fbgCBIg4uMtdM8MywmMENRajLS2BR2KFdAEXA0' 

# 3. WORKSHEET NAME (The name of your tab)
WORKSHEET_NAME = 'holdings' 
# ---------------------

def update_google_sheet_prices():
    """
    Connects to Google Sheets, fetches stock prices using yfinance,
    and updates the specified columns, backing up old data.
    """
    try:
        # 1. Authenticate and authorize the client
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        
        # 2. Open the spreadsheet and get the specific worksheet
        spreadsheet = client.open_by_key(SHEET_ID)
        try:
            sheet = spreadsheet.worksheet(WORKSHEET_NAME)
        except gspread.WorksheetNotFound:
            print(f"❌ Error: Worksheet named '{WORKSHEET_NAME}' not found.")
            return

        print(f"✅ Connected to Google Sheet: {spreadsheet.title} and tab: {sheet.title}")

        # 3. Define the rows to process (1-based Excel row numbers)
        valid_rows = (
            list(range(4, 61)) + # 4-60 (range(4, 61) includes 60)
            list(range(63, 65)) + # 63-64
            [71, 79, 80, 81, 82, 83, 84, 85, 86, 87] # 71 and 79-84
        )
        
        # Define columns as 1-based indices
        SYMBOL_COL = 1  # Column A
        PRICE_COL = 17  # Column Q
        BACKUP_COL = 18 # Column R

        print(f"➡️ Processing {len(valid_rows)} rows for stock updates...")
        
        # 4. Read all symbols and current prices from the required columns
        # Fetching a range is more efficient than individual cell reads
        
        # Determine the maximum row needed (Row 84) and columns A, Q, R
        max_row = max(valid_rows)
        range_to_fetch = f'A1:R{max_row}'
        data = sheet.get_all_values(range_to_fetch)

        # List to hold all updates for a single batch operation (more efficient)
        updates = []

        # 5. Iterate through the valid rows, fetch prices, and prepare updates
        for row_num in valid_rows:
            # gspread data list is 0-indexed, so row index is row_num - 1
            row_index = row_num - 1
            
            # Check if row index is within the fetched data bounds
            if row_index >= len(data):
                 print(f"⚠️ Skip: Row {row_num} is outside the fetched range.")
                 continue

            try:
                # Get symbol from Column A (index 0)
                # Ensure the column index is within the row's data length
                symbol_col_index = SYMBOL_COL - 1
                if len(data[row_index]) <= symbol_col_index:
                    symbol = ""
                else:
                    symbol = data[row_index][symbol_col_index].strip().upper()
                
                if not symbol:
                    print(f"⚠️ Skip: Row {row_num} has no valid symbol in column A.")
                    continue
                
                # Get old price from Column Q (index 16)
                price_col_index = PRICE_COL - 1
                if len(data[row_index]) <= price_col_index:
                    old_price = ""
                else:
                    old_price = data[row_index][price_col_index]

                # Fetch the latest price using yfinance
                ticker = yf.Ticker(symbol)
                ticker_info = ticker.info
                latest_price = ticker_info.get('regularMarketPrice')

                if latest_price is None:
                    # Fallback to previous close if market is closed/no recent price
                    latest_price = ticker_info.get('previousClose')
                
                if latest_price is None:
                    print(f"❌ Fail: Could not fetch price for symbol **{symbol}** in row {row_num}.")
                    continue
                
                # Convert the price to a string for updating the sheet
                latest_price_str = str(latest_price)
                
                # 6. Prepare the list of updates: (cell address, new value)
                
                # Backup old data: Column R (index 18)
                backup_cell = gspread.utils.rowcol_to_a1(row_num, BACKUP_COL)
                updates.append({'range': backup_cell, 'values': [[old_price]]})
                
                # Update new price: Column Q (index 17)
                price_cell = gspread.utils.rowcol_to_a1(row_num, PRICE_COL)
                updates.append({'range': price_cell, 'values': [[latest_price_str]]})

                print(f"✅ Success: Row {row_num} | Symbol: **{symbol}** | New Price: **{latest_price_str}** | Old Price backed up.")
                
                # Optional: Add a brief sleep to respect API limits (yfinance and Google Sheets)
                time.sleep(0.5)

            except Exception as e:
                print(f"🚨 An error occurred processing row {row_num}: {e}")
                
        # 7. Execute the batch update operation (more efficient than individual cell updates)
        if updates:
             sheet.batch_update(updates)
             print("\n🎉 **All stock prices have been updated in a single batch operation!**")
        else:
            print("\n⚠️ No successful price updates to write to the sheet.")

    except FileNotFoundError:
        print(f"❌ Error: Credentials file '{CREDENTIALS_FILE}' not found. Check Setup Step 2.")
    except Exception as e:
        print(f"❌ A critical error occurred during sheet connection or processing: {e}")

# Run the function
update_google_sheet_prices()
