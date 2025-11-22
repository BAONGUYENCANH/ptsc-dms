import pandas as pd
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

excel_file = 'LSPET_MDI_Status_Report - 251028.xlsx'

try:
    xl = pd.ExcelFile(excel_file)
    print("=== DANH SÁCH CÁC SHEET ===")
    for sheet_name in xl.sheet_names:
        print(f"- {sheet_name}")
    
    print("\n=== PHÂN TÍCH SHEET 'MDI_DetailStatus' ===")
    df = pd.read_excel(excel_file, sheet_name='MDI_DetailStatus')
    
    print(f"\nSố dòng: {len(df)}")
    print(f"\nSố cột: {len(df.columns)}")
    
    print("\n=== TÊN CÁC CỘT ===")
    for i, col in enumerate(df.columns, 1):
        print(f"{i}. {col}")
    
    print("\n=== 5 DÒNG ĐẦU TIÊN ===")
    print(df.head().to_string())
    
    print("\n=== THỐNG KÊ DỮ LIỆU ===")
    print(df.describe(include='all').to_string())
    
    print("\n=== CÁC GIÁ TRỊ UNIQUE CỦA MỘT SỐ CỘT QUAN TRỌNG ===")
    important_cols = ['TABLE No.', 'DISCIPLINE', 'CLASS', 'DOC. STATUS', 'REMARK']
    for col in important_cols:
        if col in df.columns:
            unique_vals = df[col].dropna().unique()
            print(f"\n{col}: {len(unique_vals)} giá trị unique")
            if len(unique_vals) <= 20:
                for val in unique_vals[:20]:
                    print(f"  - {val}")
            else:
                print(f"  (Quá nhiều giá trị, hiển thị 10 đầu)")
                for val in list(unique_vals)[:10]:
                    print(f"  - {val}")

except Exception as e:
    print(f"Lỗi: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
