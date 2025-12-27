import gspread
import csv
from io import StringIO
import os

# --- Configuration ---
# 1. Sheet Details
SPREADSHEET_ID = "1ODfC3fbgCBIg4uMtdM8MywmMENRajLS2BR2KFdAEXA0"
TAB_NAME = "holdings"
CREDENTIALS_FILE = "service_account.json"

# --- UPDATED CONFIGURATION ---
ANALYSIS_FILE = "image_analysis_output.csv"  # <-- Changed file name
START_ROW = 4
END_ROW = 72                                 # <-- Changed end row
TOTAL_ROWS = END_ROW - START_ROW + 1         # 72 - 4 + 1 = 84 rows

# Define the sheet range
SYMBOL_RANGE = f"A{START_ROW}:A{END_ROW}"    # e.g., A4:A72
QUANTITY_RANGE = f"N{START_ROW}:N{END_ROW}"  # e.g., N4:N72
# -----------------------------

def update_google_sheet_holdings_with_formatting(file_path, sheet_id, tab_name):
    """
    Reads data from a local CSV file, updates the Google Sheet (rows 4-72), 
    ensuring quantities are sent as numbers, and reports new symbols.
    """
    # --- 1. AUTHENTICATION & CONNECTION ---
    try:
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(tab_name)
    except Exception as e:
        print(f"Error during Google Sheets authentication or connection: {e}")
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
    # Since the file is explicitly named .csv, we use the csv reader
    reader = csv.reader(StringIO(file_content), delimiter=',')
    
    for row in reader:
        cleaned_row = [item.strip() for item in row]
        if len(cleaned_row) >= 2 and cleaned_row[0]:
            symbol = cleaned_row[0]
            quantity = cleaned_row[1]
            file_data[symbol] = quantity
    
    # --- 3. READ EXISTING SHEET SYMBOLS (Column A, Rows 4-72) ---
    print(f"Reading symbols from Google Sheet range {SYMBOL_RANGE}...")
    try:
        # Get column A values, slicing to match the START_ROW and END_ROW indices
        sheet_symbols_data = worksheet.col_values(1)[START_ROW - 1 : END_ROW] 
        sheet_symbols_set = {s.strip() for s in sheet_symbols_data if s.strip()}
    except Exception as e:
        print(f"Error reading symbols from the sheet: {e}")
        return
    
    # --- 4. PREPARE NEW QUANTITY DATA (Column N) with Formatting Fix ---
    new_quantities = []
    
    for sheet_symbol in sheet_symbols_data:
        symbol_key = sheet_symbol.strip()
        
        if symbol_key in file_data:
            quantity_string = file_data[symbol_key]
            
            # Convert quantity to a number (float) for correct formatting in the sheet
            try:
                quantity_value = float(quantity_string.replace(',', '')) 
            except ValueError:
                quantity_value = quantity_string # Keep as string if conversion fails
        else:
            quantity_value = "" # Set to empty string if not found in file
        
        new_quantities.append([quantity_value])

    # --- 5. PERFORM BATCH UPDATE ---
    print(f"Updating quantities in Google Sheet range {QUANTITY_RANGE}...")
    try:
        worksheet.update(
            QUANTITY_RANGE, 
            new_quantities, 
            value_input_option='USER_ENTERED'
        )
        print("✅ Google Sheet update successful!")
    except Exception as e:
        print(f"Error during sheet update: {e}")
        
    # --- 6. IDENTIFY AND REPORT NEW SYMBOLS ---
    file_symbols_set = set(file_data.keys())
    new_symbols = file_symbols_set - sheet_symbols_set
    
    print("\n--- Change Summary Report ---")
    if new_symbols:
        print(f"⚠️ **NEW SYMBOLS DETECTED IN FILE, BUT NOT IN SHEET RANGE ({SYMBOL_RANGE}):**")
        print(", ".join(sorted(new_symbols)))
        print("\nThese symbols were ignored for updating.")
    else:
        print("🟢 **No new symbols detected in the file.**")
    print("-----------------------------\n")

# --- EXECUTION BLOCK ---
if __name__ == "__main__":
    update_google_sheet_holdings_with_formatting(
        file_path=ANALYSIS_FILE,
        sheet_id=SPREADSHEET_ID,
        tab_name=TAB_NAME
    )
