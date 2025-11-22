"""
Script để clean Excel file MDI cho React app
- Bỏ 3 dòng header phức tạp
- Normalize column names (loại bỏ \n, spaces)
- Export ra file Excel sạch
"""

import pandas as pd
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def clean_excel_file(input_file, output_file):
    """
    Clean Excel file to make it compatible with React SheetJS parser
    """
    print(f"Đang đọc file: {input_file}...")
    
    # Đọc file Excel, bỏ qua 3 dòng header phức tạp
    df = pd.read_excel(input_file, sheet_name='MDI_DetailStatus', skiprows=3)
    
    print(f"Đã đọc {len(df)} dòng dữ liệu")
    print(f"Số cột: {len(df.columns)}")
    
    # Normalize column names - loại bỏ \n và khoảng trắng thừa
    new_columns = []
    for col in df.columns:
        # Replace \n với space, strip whitespace
        clean_col = str(col).replace('\n', ' ').strip()
        # Remove multiple spaces
        clean_col = ' '.join(clean_col.split())
        new_columns.append(clean_col)
    
    df.columns = new_columns
    
    print("\n=== CÁC CỘT SAU KHI CLEAN ===")
    for i, col in enumerate(df.columns[:30], 1):
        print(f"{i}. {col}")
    
    # Mapping tên cột để frontend dễ parse
    column_mapping = {
        'Org.': 'discipline',
        'CompanyDoc.No.': 'companyDocNo',
        'DocumentName': 'name',
        'Class': 'doc_class',
        'Rev': 'revision',
        'Status': 'doc_status',
        'Scope': 'scope',
        'Table': 'table',
        'Item': 'item',
        'IPI': 'ipi_status',
        'Code': 'review_code',
        'DateTRNOut': 'trn_out_date',
        'TRNOutNo.': 'trn_out_no',
        'DateTRNIn': 'trn_in_date',
        'TRNInNo.': 'trn_in_no',
        'DateReciveTRNOut': 'dateReceived',
        'IFI Plan Date': 'ifi_plan_date',
        'IFR Plan Date': 'ifr_plan_date',
        'IFA Plan Date': 'ifa_plan_date',
        'IFC Plan Date': 'ifc_plan_date',
        'IFF/ASB Plan Date': 'iff_plan_date',
        'IFI Actual Date': 'ifi_actual_date',
        'IFR Actual Date': 'ifr_actual_date',
        'IFA Actual Date': 'ifa_actual_date',
        'IFC Actual Date': 'ifc_actual_date',
        'IFF/ASB Actual Date': 'iff_actual_date',
        'Target Mitigation Date': 'target_mitigation_date',
        'PIC PTSC': 'pic_ptsc',
        'PIC LSP': 'pic_lsp',
    }
    
    # Rename columns nếu tồn tại
    rename_dict = {}
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            rename_dict[old_name] = new_name
    
    df.rename(columns=rename_dict, inplace=True)
    
    # Thêm cột STT nếu chưa có
    if 'stt' not in df.columns:
        df.insert(0, 'stt', range(1, len(df) + 1))
    
    print(f"\n=== LƯU FILE ===")
    print(f"Output: {output_file}")
    
    # Tạo sheet mới tên "MDI_DetailStatus" 
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='MDI_DetailStatus', index=False)
    
    print(f"✅ Đã lưu file sạch: {output_file}")
    print(f"   - Số dòng: {len(df)}")
    print(f"   - Số cột: {len(df.columns)}")
    print(f"\n📌 Bây giờ upload file '{output_file}' vào React app!")
    
    return df

if __name__ == '__main__':
    input_file = 'LSPET_MDI_Status_Report.xlsx'
    output_file = 'LSPET_MDI_Status_Report_CLEAN.xlsx'
    
    try:
        df = clean_excel_file(input_file, output_file)
        
        # Show sample data
        print("\n=== MẪU DỮ LIỆU (5 dòng đầu) ===")
        print(df[['stt', 'companyDocNo', 'name', 'discipline', 'doc_status']].head().to_string())
        
    except Exception as e:
        print(f"\n❌ LỖI: {e}")
        import traceback
        traceback.print_exc()
