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

# Define the sheet range (Rows 4 to 60)
SYMBOL_RANGE = "A4:A60"  # Symbols in the sheet (Column A)
QUANTITY_RANGE = "N4:N60" # Quantities to update (Column N)
START_ROW = 4
END_ROW = 60
TOTAL_ROWS = END_ROW - START_ROW + 1

def update_google_sheet_holdings(file_path, sheet_id, tab_name):
    """
    Reads data from a local file and updates the specified Google Sheet range.
    """
    # --- 1. AUTHENTICATION & CONNECTION ---
    try:
        # Authenticate using the service account file
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
            # Assuming the file uses a simple comma delimiter (CSV format)
            file_content = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return
    
    # Store file data as {Symbol: Quantity}
    file_data = {}
    # Use StringIO to read the content like a file, then use the csv reader
    reader = csv.reader(StringIO(file_content), delimiter=',')
    
    # Process the rows from the file
    for row in reader:
        # Clean up row by stripping whitespace
        cleaned_row = [item.strip() for item in row]
        
        # Check for non-empty symbols and at least two columns
        if len(cleaned_row) >= 2 and cleaned_row[0]:
            symbol = cleaned_row[0]
            quantity = cleaned_row[1]
            file_data[symbol] = quantity
    
    print(f"Successfully read {len(file_data)} symbols from the local file.")
    
    # --- 3. READ EXISTING SHEET SYMBOLS (Column A) ---
    print(f"Reading symbols from Google Sheet range {SYMBOL_RANGE}...")
    try:
        # Get all cell values from the symbol column (A4:A60)
        # Using row 1 as index, as gspread col_values is 1-indexed
        sheet_symbols_data = worksheet.col_values(1)[START_ROW - 1 : END_ROW] 
    except Exception as e:
        print(f"Error reading symbols from the sheet: {e}")
        return
    
    # --- 4. PREPARE NEW QUANTITY DATA (Column N) ---
    new_quantities = []
    
    # Iterate through the symbols currently in the sheet (rows 4 to 60)
    for sheet_symbol in sheet_symbols_data:
        symbol_key = sheet_symbol.strip()
        
        # Check against the data read from the local file
        if symbol_key in file_data:
            # 🟢 MATCH: Update with the corresponding quantity value
            quantity_value = file_data[symbol_key]
        else:
            # 🔴 NO MATCH: Set to empty string as requested
            quantity_value = ""
        
        # Append the new value (must be a list of lists for gspread update)
        new_quantities.append([quantity_value])
        
    # Verify the size matches the target range
    if len(new_quantities) != TOTAL_ROWS:
        print(f"Warning: Prepared {len(new_quantities)} rows, expected {TOTAL_ROWS}. Check sheet indexing.")

    # --- 5. PERFORM BATCH UPDATE ---
    print(f"Updating quantities in Google Sheet range {QUANTITY_RANGE}...")
    try:
        # Update the entire range N4:N60 in a single call for efficiency
        worksheet.update(QUANTITY_RANGE, new_quantities)
        print("✅ Google Sheet update successful!")
    except Exception as e:
        print(f"Error during sheet update: {e}")

# --- EXECUTION BLOCK ---
if __name__ == "__main__":
    update_google_sheet_holdings(
        file_path=ANALYSIS_FILE,
        sheet_id=SPREADSHEET_ID,
        tab_name=TAB_NAME
    )
