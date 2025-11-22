import pandas as pd
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

excel_file = 'LSPET_MDI_Status_Report - 251028.xlsx'

try:
    # Đọc với skiprows để bỏ qua các dòng header phức tạp
    df = pd.read_excel(excel_file, sheet_name='MDI_DetailStatus', header=2)
    
    print("=== CẤU TRÚC DỮ LIỆU CHÍNH ===")
    print(f"Tổng số tài liệu: {len(df)}")
    print(f"Tổng số cột: {len(df.columns)}")
    
    print("\n=== 10 CỘT ĐẦU TIÊN ===")
    for i, col in enumerate(list(df.columns)[:10], 1):
        print(f"{i}. {col}")
    
    print("\n=== MẪU DỮ LIỆU (5 DÒNG ĐẦU) ===")
    # Lấy các cột quan trọng để xem
    important_cols = []
    for col in df.columns[:15]:
        if not str(col).startswith('Unnamed') or col in df.columns[:10]:
            important_cols.append(col)
    
    if important_cols:
        print(df[important_cols].head(10).to_string())
    
    print("\n=== PHÂN TÍCH CÁC CỘT QUAN TRỌNG ===")
    
    # Tìm các cột có tên rõ ràng
    named_cols = [col for col in df.columns if not str(col).startswith('Unnamed')]
    print(f"\nSố cột có tên: {len(named_cols)}")
    print("Danh sách các cột có tên:")
    for col in named_cols[:30]:  # Hiển thị 30 cột đầu
        print(f"  - {col}")
        if col in df.columns:
            unique_count = df[col].nunique()
            null_count = df[col].isnull().sum()
            print(f"    + Unique: {unique_count}, Null: {null_count}/{len(df)}")
            
            # Hiển thị một số giá trị mẫu nếu ít giá trị unique
            if unique_count <= 10 and unique_count > 0:
                samples = df[col].dropna().unique()[:10]
                print(f"    + Mẫu: {list(samples)}")
    
    print("\n=== PHÂN TÍCH THEO SCOPE ===")
    if 'Scope' in df.columns:
        scope_counts = df['Scope'].value_counts()
        print(scope_counts)
    
    print("\n=== PHÂN TÍCH THEO TABLE ===")
    if 'Table' in df.columns:
        table_counts = df['Table'].value_counts().head(20)
        print(table_counts)
    
    print("\n=== PHÂN TÍCH THEO CLASS ===")
    if 'Class' in df.columns:
        class_counts = df['Class'].value_counts()
        print(class_counts)
    
    print("\n=== PHÂN TÍCH THEO DISCIPLINE (ORG) ===")
    if 'Org.' in df.columns:
        org_counts = df['Org.'].value_counts()
        print(org_counts)
    
    # Phân tích cấu trúc revision tracking
    print("\n=== CẤU TRÚC TRACKING REVISION ===")
    rev_related = [col for col in df.columns if 'Rev' in str(col) or 'IPI' in str(col) or 'Code' in str(col)]
    print(f"Số cột liên quan revision/IPI/Code: {len(rev_related)}")
    print("Các cột:")
    for col in rev_related[:20]:
        print(f"  - {col}")

except Exception as e:
    print(f"Lỗi: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
