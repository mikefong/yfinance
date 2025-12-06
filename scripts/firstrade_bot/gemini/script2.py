import gspread
import csv
from io import StringIO
import os

# --- Configuration ---
# 1. Sheet Details
SPREADSHEET_ID = "1ODfC3fbgCBIg4uMtdM8MywmMENRajLS2BR2KFdAEXA0"
TAB_NAME = "holdings"
ANALYSIS_FILE = "image_analysis_output.csv"
CREDENTIALS_FILE = "service_account.json"

# Define the sheet range (Rows 4 to 87)
SYMBOL_RANGE = "A4:A87"  # Symbols in the sheet (Column A)
QUANTITY_RANGE = "N4:N87" # Quantities to update (Column N)
START_ROW = 4
END_ROW = 87
TOTAL_ROWS = END_ROW - START_ROW + 1

def update_google_sheet_holdings(file_path, sheet_id, tab_name):
    """
    Reads data from a local file, updates the Google Sheet, 
    and reports any new symbols found in the file.
    """
    # --- 1. AUTHENTICATION & CONNECTION ---
    try:
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(tab_name)
    except Exception as e:
        print(f"Error during Google Sheets authentication or connection: {e}")
        print("Please ensure 'service_account.json' is configured and the sheet is shared with the service account email.")
        return

    # --- 2. READ LOCAL DATA FILE ---
    print(f"Reading data from {file_path}...")
    try:
        with open(file_path, 'r') as f:
            file_content = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return
    
    file_data = {}
    reader = csv.reader(StringIO(file_content), delimiter=',')
    
    # Process the rows from the file and store them
    for row in reader:
        cleaned_row = [item.strip() for item in row]
        if len(cleaned_row) >= 2 and cleaned_row[0]:
            symbol = cleaned_row[0]
            quantity = cleaned_row[1]
            file_data[symbol] = quantity
    
    print(f"Successfully read {len(file_data)} symbols from the local file.")
    
    # --- 3. READ EXISTING SHEET SYMBOLS (Column A) ---
    print(f"Reading symbols from Google Sheet range {SYMBOL_RANGE}...")
    try:
        # Get all cell values from the symbol column (A4:A87)
        sheet_symbols_data = worksheet.col_values(1)[START_ROW - 1 : END_ROW] 
        # Create a set for quick lookups and comparison later
        sheet_symbols_set = {s.strip() for s in sheet_symbols_data if s.strip()}
    except Exception as e:
        print(f"Error reading symbols from the sheet: {e}")
        return
    
    # --- 4. PREPARE NEW QUANTITY DATA (Column N) ---
    new_quantities = []
    
    for sheet_symbol in sheet_symbols_data:
        symbol_key = sheet_symbol.strip()
        
        if symbol_key in file_data:
            quantity_value = file_data[symbol_key]
        else:
            quantity_value = "" # Set to empty string if not found in file
        
        new_quantities.append([quantity_value])

    # --- 5. PERFORM BATCH UPDATE ---
    print(f"Updating quantities in Google Sheet range {QUANTITY_RANGE}...")
    try:
        worksheet.update(QUANTITY_RANGE, new_quantities)
        print("✅ Google Sheet update successful!")
    except Exception as e:
        print(f"Error during sheet update: {e}")
        
    # --- 6. IDENTIFY AND REPORT NEW SYMBOLS (THE NEW REQUIREMENT) ---
    
    # Find all symbols in the file that are NOT in the sheet's symbol set
    file_symbols_set = set(file_data.keys())
    new_symbols = file_symbols_set - sheet_symbols_set
    
    print("\n--- Change Summary Report ---")
    if new_symbols:
        print("⚠️ **NEW SYMBOLS DETECTED IN FILE, BUT NOT IN SHEET RANGE (A4:A87):**")
        # Format the list nicely
        print(", ".join(sorted(new_symbols)))
        print("\nThese symbols were ignored for updating, as they were not found in the sheet's Symbol column.")
    else:
        print("🟢 **No new symbols detected in the file.** All symbols matched existing entries in the sheet.")
    print("-----------------------------\n")

# --- EXECUTION BLOCK ---
if __name__ == "__main__":
    update_google_sheet_holdings(
        file_path=ANALYSIS_FILE,
        sheet_id=SPREADSHEET_ID,
        tab_name=TAB_NAME
    )
