import pandas as pd
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

excel_file = 'LSPET_MDI_Status_Report - 251028.xlsx'

try:
    # Read Summary sheet
    print("=== ANALYZING SUMMARY SHEET ===\n")
    
    # Try different approaches to read the Summary sheet
    xl = pd.ExcelFile(excel_file)
    print(f"Available sheets: {xl.sheet_names}\n")
    
    # Read Summary sheet without header first to see structure
    df_raw = pd.read_excel(excel_file, sheet_name='Summary', header=None, nrows=50)
    
    print("=== RAW CONTENT (First 50 rows) ===")
    print(df_raw.to_string())
    
    print("\n\n=== EXTRACTING KEY TABLES ===")
    
    # Find "Count of Detail Status" table
    for idx, row in df_raw.iterrows():
        if 'Count of Detail Status' in str(row.values):
            print(f"\n📊 COUNT OF DETAIL STATUS (Row {idx}):")
            # Get next 10 rows for the table
            detail_status_table = df_raw.iloc[idx:idx+15]
            print(detail_status_table.to_string())
            break
    
    # Find Status/PIC table
    for idx, row in df_raw.iterrows():
        if 'Status Overdue' in str(row.values) or (idx > 40 and 'PIC' in str(row.values)):
            print(f"\n📊 STATUS BY PIC TABLE (Row {idx}):")
            pic_table = df_raw.iloc[idx:idx+20]
            print(pic_table.to_string())
            break
    
    # Extract status distribution (rows 36-44)
    print("\n📊 STATUS DISTRIBUTION (Rows 36-44):")
    status_dist = df_raw.iloc[36:45, :25]  # Get relevant columns
    print(status_dist.to_string())

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
