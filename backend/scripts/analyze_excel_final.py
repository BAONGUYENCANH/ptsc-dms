import pandas as pd
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

excel_file = 'LSPET_MDI_Status_Report - 251028.xlsx'

try:
    # Đọc dòng đầu tiên là data, dòng 0 là header thực
    df_raw = pd.read_excel(excel_file, sheet_name='MDI_DetailStatus', header=None, nrows=10)
    
    print("=== XEM CẤU TRÚC HEADER ===")
    print("\nDòng 0 (Header level 1):")
    print(df_raw.iloc[0, :20].to_dict())
    
    print("\nDòng 1 (Header level 2):")
    print(df_raw.iloc[1, :20].to_dict())
    
    print("\nDòng 2 (Header level 3 - Headers thực):")
    print(df_raw.iloc[2, :20].to_dict())
    
    print("\nDòng 3 (Dữ liệu đầu tiên):")
    print(df_raw.iloc[3, :20].to_dict())
    
    # Đọc lại với header đúng (dòng 2 là header)
    df = pd.read_excel(excel_file, sheet_name='MDI_DetailStatus', header=2)
    
    # Lấy tên cột từ dòng đầu tiên của dataframe (đây là header thực)
    actual_headers = df.iloc[0].values
    
    print("\n=== HEADER THỰC SỰ CỦA FILE ===")
    for i, header in enumerate(actual_headers[:30]):
        print(f"{i}: {header}")
    
    # Đọc lại data bỏ qua 3 dòng header
    df_data = pd.read_excel(excel_file, sheet_name='MDI_DetailStatus', skiprows=3)
    
    print(f"\n=== DỮ LIỆU CHÍNH ===")
    print(f"Tổng số tài liệu: {len(df_data)}")
    print(f"Tổng số cột: {len(df_data.columns)}")
    
    print("\n=== TÊN CÁC CỘT (20 cột đầu) ===")
    for i, col in enumerate(list(df_data.columns)[:20], 1):
        print(f"{i}. {col}")
    
    print("\n=== MẪU DỮ LIỆU ===")
    print(df_data.iloc[:5, :12].to_string())
    
    # Phân tích các cột chính
    print("\n=== PHÂN TÍCH CHI TIẾT ===")
    
    col_names = df_data.columns.tolist()
    
    # Tìm các cột chính dựa vào tên
    key_columns = []
    keywords = ['Scope', 'Table', 'Item', 'Org', 'Doc', 'Name', 'Class', 'Rev', 'IPI', 'Date', 'TRN', 'Code', 'Status', 'Remark']
    
    for col in col_names[:30]:
        col_str = str(col)
        if any(keyword.lower() in col_str.lower() for keyword in keywords):
            key_columns.append(col)
    
    print(f"\nCác cột chính được xác định ({len(key_columns)}):")
    for col in key_columns:
        print(f"\n- {col}")
        unique_count = df_data[col].nunique()
        null_count = df_data[col].isnull().sum()
        print(f"  Unique: {unique_count}, Null: {null_count}/{len(df_data)}")
        
        if unique_count <= 15:
            samples = df_data[col].value_counts().head(10)
            print(f"  Top values:\n{samples}")
    
    # Xuất ra file CSV để dễ phân tích
    output_csv = 'excel_structure_analysis.csv'
    df_data.iloc[:100, :30].to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"\n=== ĐÃ XUẤT MẪU DỮ LIỆU ===")
    print(f"File: {output_csv} (100 dòng đầu, 30 cột đầu)")

except Exception as e:
    print(f"Lỗi: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
