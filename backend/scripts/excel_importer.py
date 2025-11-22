"""
Excel MDI Status Report Importer
Imports data from Excel MDI Status Report into the database
"""

import pandas as pd
import sqlite3
import sys
import json
import io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def parse_date(date_value):
    """Convert Excel date to string format"""
    if pd.isna(date_value):
        return None
    if isinstance(date_value, datetime):
        return date_value.strftime('%Y-%m-%d')
    return str(date_value)

def import_from_excel(db_path, excel_path, sheet_name='MDI_DetailStatus'):
    """Import MDI data from Excel into database"""
    try:
        print(f"Reading Excel file: {excel_path}", file=sys.stderr)
        
        # Read Excel with proper header row (skip first 3 rows which are summary/headers)
        df = pd.read_excel(excel_path, sheet_name=sheet_name, skiprows=3)
        
        print(f"Total rows read: {len(df)}", file=sys.stderr)
        print(f"Columns: {list(df.columns)[:10]}", file=sys.stderr)
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Statistics
        stats = {
            'total_rows': len(df),
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                # Extract data from Excel row
                scope = str(row.get('Scope', '')).strip() if not pd.isna(row.get('Scope')) else None
                table = str(row.get('Table', '')).strip() if not pd.isna(row.get('Table')) else None
                item = str(row.get('Item', '')).strip() if not pd.isna(row.get('Item')) else None
                org = str(row.get('Org.', '')).strip() if not pd.isna(row.get('Org.')) else None
                company_doc_no = str(row.get('CompanyDoc.No.', '')).strip() if not pd.isna(row.get('CompanyDoc.No.')) else None
                contractor_doc_no = str(row.get('ContractorDoc.No.', '')).strip() if not pd.isna(row.get('ContractorDoc.No.')) else None
                doc_name = str(row.get('DocumentName', '')).strip() if not pd.isna(row.get('DocumentName')) else None
                doc_class = str(row.get('Class', '')).strip() if not pd.isna(row.get('Class')) else None
                revision = str(row.get('Rev', '')).strip() if not pd.isna(row.get('Rev')) else None
                ipi_status = str(row.get('IPI', '')).strip() if not pd.isna(row.get('IPI')) else None
                
                # TRN tracking
                trn_out_date = parse_date(row.get('DateTRNOut'))
                trn_out_no = str(row.get('TRNOutNo.', '')).strip() if not pd.isna(row.get('TRNOutNo.')) else None
                date_receive_trn_out = parse_date(row.get('DateReciveTRNOut'))
                trn_in_date = parse_date(row.get('DateTRNIn'))
                trn_in_no = str(row.get('TRNInNo.', '')).strip() if not pd.isna(row.get('TRNInNo.')) else None
                review_code = str(row.get('Code', '')).strip() if not pd.isna(row.get('Code')) else None
                
                # Plan dates
                ifi_plan = parse_date(row.get('IFI\nPlan Date'))
                ifr_plan = parse_date(row.get('IFR\nPlan Date'))
                ifa_plan = parse_date(row.get('IFA\nPlan Date'))
                ifc_plan = parse_date(row.get('IFC\nPlan Date'))
                iff_plan = parse_date(row.get('IFF/ASB\nPlan Date'))
                
                # Actual dates
                ifi_actual = parse_date(row.get('IFI\nActual Date'))
                ifr_actual = parse_date(row.get('IFR\nActual Date'))
                ifa_actual = parse_date(row.get('IFA\nActual Date'))
                ifc_actual = parse_date(row.get('IFC\nActual Date'))
                iff_actual = parse_date(row.get('IFF/ASB\nActual Date'))
                
                # Management
                target_date = parse_date(row.get('Target Mitigation Date'))
                pic_ptsc = str(row.get('PIC PTSC', '')).strip() if not pd.isna(row.get('PIC PTSC')) else None
                pic_lsp = str(row.get('PIC LSP', '')).strip() if not pd.isna(row.get('PIC LSP')) else None
                doc_status = str(row.get('Status', '')).strip() if not pd.isna(row.get('Status')) else None
                
                # Skip if no company doc number (key field)
                if not company_doc_no or company_doc_no == 'nan':
                    stats['skipped'] += 1
                    continue
                
                # Check if document exists in database by companyDocNo
                cursor.execute('SELECT localPath FROM documents WHERE companyDocNo = ?', (company_doc_no,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing document
                    cursor.execute('''
                        UPDATE documents SET
                            scope = ?, item = ?, contractorDocNo = ?,
                            ipi_status = ?, review_code = ?,
                            trn_out_date = ?, trn_out_no = ?, date_receive_trn_out = ?,
                            trn_in_date = ?, trn_in_no = ?,
                            ifi_plan_date = ?, ifr_plan_date = ?, ifa_plan_date = ?, ifc_plan_date = ?, iff_plan_date = ?,
                            ifi_actual_date = ?, ifr_actual_date = ?, ifa_actual_date = ?, ifc_actual_date = ?, iff_actual_date = ?,
                            target_mitigation_date = ?, pic_ptsc = ?, pic_lsp = ?, doc_status = ?
                        WHERE companyDocNo = ?
                    ''', (
                        scope, item, contractor_doc_no,
                        ipi_status, review_code,
                        trn_out_date, trn_out_no, date_receive_trn_out,
                        trn_in_date, trn_in_no,
                        ifi_plan, ifr_plan, ifa_plan, ifc_plan, iff_plan,
                        ifi_actual, ifr_actual, ifa_actual, ifc_actual, iff_actual,
                        target_date, pic_ptsc, pic_lsp, doc_status,
                        company_doc_no
                    ))
                    stats['updated'] += 1
                else:
                    # Insert new record (without localPath, will be added when file is scanned)
                    # Use company_doc_no as temporary localPath placeholder
                    temp_path = f"IMPORT_{company_doc_no}"
                    cursor.execute('''
                        INSERT INTO documents (
                            localPath, name, "table", description, discipline,
                            scope, item, companyDocNo, contractorDocNo, doc_class, revision,
                            ipi_status, review_code,
                            trn_out_date, trn_out_no, date_receive_trn_out,
                            trn_in_date, trn_in_no,
                            ifi_plan_date, ifr_plan_date, ifa_plan_date, ifc_plan_date, iff_plan_date,
                            ifi_actual_date, ifr_actual_date, ifa_actual_date, ifc_actual_date, iff_actual_date,
                            target_mitigation_date, pic_ptsc, pic_lsp, doc_status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        temp_path, doc_name, table, '', org,
                        scope, item, company_doc_no, contractor_doc_no, doc_class, revision,
                        ipi_status, review_code,
                        trn_out_date, trn_out_no, date_receive_trn_out,
                        trn_in_date, trn_in_no,
                        ifi_plan, ifr_plan, ifa_plan, ifc_plan, iff_plan,
                        ifi_actual, ifr_actual, ifa_actual, ifc_actual, iff_actual,
                        target_date, pic_ptsc, pic_lsp, doc_status
                    ))
                    stats['imported'] += 1
                
                # Commit every 100 rows for progress
                if (idx + 1) % 100 == 0:
                    conn.commit()
                    print(f"Processed {idx + 1}/{len(df)} rows...", file=sys.stderr)
            
            except Exception as e:
                error_msg = f"Row {idx}: {str(e)}"
                stats['errors'].append(error_msg)
                print(f"Error: {error_msg}", file=sys.stderr)
        
        # Final commit
        conn.commit()
        conn.close()
        
        print(json.dumps({
            "success": True,
            "stats": stats
        }))
        
    except Exception as e:
        import traceback
        print(json.dumps({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python excel_importer.py <db_path> <excel_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    excel_path = sys.argv[2]
    
    import_from_excel(db_path, excel_path)
