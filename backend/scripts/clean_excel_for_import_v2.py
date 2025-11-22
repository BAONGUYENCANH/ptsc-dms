"""
Script để clean Excel file MDI - Version 2
- Hỗ trợ command line arguments
- Tự động detect file name
- Output đến cùng thư mục với file gốc
"""

import pandas as pd
import sys
import io
import os
from pathlib import Path
from datetime import datetime
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def convert_excel_date(value):
    """
    Convert Excel serial date to string format YYYY-MM-DD
    
    Excel lưu dates dưới dạng số (serial date):
    - 1 = 1900-01-01
    - 45835 = 2025-06-15
    
    Args:
        value: Excel cell value (có thể là số, string, hoặc datetime)
    
    Returns:
        String YYYY-MM-DD hoặc None nếu không phải date
    """
    # Handle NaN, None, empty
    if pd.isna(value) or value == '' or value == 'N/A':
        return None
    
    # Nếu đã là datetime object
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.strftime('%Y-%m-%d')
    
    # Nếu là string, kiểm tra có phải date format không
    if isinstance(value, str):
        try:
            # Thử parse string date
            dt = pd.to_datetime(value, errors='coerce')
            if pd.notna(dt):
                return dt.strftime('%Y-%m-%d')
            return None
        except:
            return None
    
    # Nếu là số (Excel serial date)
    if isinstance(value, (int, float)):
        # Excel serial dates thường từ 1 đến ~50000 (years 1900-2136)
        if 1 <= value <= 60000:
            try:
                # Convert Excel serial date to datetime
                # Excel epoch là 1899-12-30 (không phải 1900-01-01 do Excel bug)
                dt = pd.to_datetime(value, origin='1899-12-30', unit='D')
                return dt.strftime('%Y-%m-%d')
            except:
                return None
    
    return None

def format_date_columns(df):
    """
    Tự động detect và format tất cả date columns
    
    Args:
        df: DataFrame
    
    Returns:
        DataFrame với dates đã được format
    """
    # Danh sách các date columns cần check
    date_column_keywords = [
        'date', 'plan', 'actual', 'ifi', 'ifr', 'ifa', 'ifc', 'iff',
        'trn', 'received', 'mitigation'
    ]
    
    # Tìm các columns có tên chứa keywords
    date_columns = []
    for col in df.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in date_column_keywords):
            date_columns.append(col)
    
    print(f"\n📅 FORMATTING DATE COLUMNS ({len(date_columns)} columns):")
    
    converted_count = 0
    for col in date_columns:
        # Skip nếu column không tồn tại
        if col not in df.columns:
            continue
        
        # Đếm số cells là Excel serial dates (numbers)
        numeric_dates = df[col].apply(lambda x: isinstance(x, (int, float)) and 1 <= x <= 60000).sum()
        
        if numeric_dates > 0:
            print(f"   ⚙️  {col}: Converting {numeric_dates} serial dates...")
            
            # Apply conversion
            df[col] = df[col].apply(convert_excel_date)
            converted_count += numeric_dates
        else:
            # Vẫn cố gắng format nếu là datetime objects
            df[col] = df[col].apply(convert_excel_date)
    
    if converted_count > 0:
        print(f"\n✅ Đã convert {converted_count} Excel serial dates sang YYYY-MM-DD format")
    else:
        print(f"\n✅ Date columns đã ở định dạng chuẩn")
    
    return df

def clean_excel_file(input_file, output_file=None):
    """
    Clean Excel file to make it compatible with React SheetJS parser
    
    Args:
        input_file: Path to input Excel file
        output_file: Path to output Excel file (optional, auto-generated if None)
    
    Returns:
        Path to output file
    """
    print(f"📂 Đang đọc file: {input_file}")
    print("=" * 60)
    
    # Check if input file exists
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Không tìm thấy file: {input_file}")
    
    # Auto-generate output file name if not provided
    if output_file is None:
        input_path = Path(input_file)
        output_file = input_path.parent / f"{input_path.stem}_CLEAN{input_path.suffix}"
    
    # Đọc file Excel, bỏ qua 3 dòng header phức tạp
    df = pd.read_excel(input_file, sheet_name='MDI_DetailStatus', skiprows=3)
    
    print(f"✅ Đã đọc {len(df)} dòng dữ liệu")
    print(f"📊 Số cột: {len(df.columns)}")
    
    # Normalize column names - loại bỏ \n và khoảng trắng thừa
    new_columns = []
    for col in df.columns:
        # Replace \n với space, strip whitespace
        clean_col = str(col).replace('\n', ' ').strip()
        # Remove multiple spaces
        clean_col = ' '.join(clean_col.split())
        new_columns.append(clean_col)
    
    df.columns = new_columns
    
    print("\n📋 CÁC CỘT SAU KHI CLEAN (20 cột đầu):")
    for i, col in enumerate(df.columns[:20], 1):
        print(f"   {i}. {col}")
    
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
    
    # ===== FORMAT DATE COLUMNS =====
    df = format_date_columns(df)
    
    # Thêm cột STT nếu chưa có
    if 'stt' not in df.columns:
        df.insert(0, 'stt', range(1, len(df) + 1))
    
    print(f"\n💾 ĐANG LƯU FILE...")
    print(f"   Output: {output_file}")
    
    # Tạo sheet mới tên "MDI_DetailStatus" 
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='MDI_DetailStatus', index=False)
    
    print(f"\n✅ ĐÃ LƯU FILE THÀNH CÔNG!")
    print(f"   📁 File: {output_file}")
    print(f"   📊 Số dòng: {len(df)}")
    print(f"   📋 Số cột: {len(df.columns)}")
    
    # Show sample data
    print(f"\n📝 MẪU DỮ LIỆU (5 dòng đầu):")
    sample_cols = ['stt', 'companyDocNo', 'name', 'discipline', 'doc_status']
    available_cols = [col for col in sample_cols if col in df.columns]
    if available_cols:
        print(df[available_cols].head().to_string(index=False))
    
    # Show sample date data để verify
    date_sample_cols = ['ifi_plan_date', 'ifr_plan_date', 'ifi_actual_date']
    date_available = [col for col in date_sample_cols if col in df.columns]
    if date_available:
        print(f"\n📅 MẪU DATE COLUMNS (để verify format):")
        print(df[date_available].head().to_string(index=False))
    
    print("\n" + "=" * 60)
    print("🎉 HOÀN TẤT!")
    print(f"📌 Bây giờ upload file '{os.path.basename(output_file)}' vào React app!")
    
    return output_file

def main():
    """Main function để xử lý command line arguments"""
    
    print("\n" + "=" * 60)
    print("   PTSC MDI - Excel Cleaner v2.0")
    print("=" * 60 + "\n")
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("❌ CÁCH SỬ DỤNG:")
        print("   python clean_excel_for_import_v2.py <input_file.xlsx>")
        print("\nVÍ DỤ:")
        print("   python clean_excel_for_import_v2.py \"LSPET_MDI_Status_Report - 251028.xlsx\"")
        print("\nHOẶC:")
        print("   Kéo thả file Excel vào file .bat")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Optional: output file can be specified
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result_file = clean_excel_file(input_file, output_file)
        print(f"\n✅ SUCCESS: {result_file}")
        sys.exit(0)
        
    except FileNotFoundError as e:
        print(f"\n❌ LỖI - Không tìm thấy file:")
        print(f"   {e}")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ LỖI:")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
