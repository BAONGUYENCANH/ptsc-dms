"""
Export SQLite Database to JSON for Static Web Deployment
Đọc project_data.db và export ra public/data.json với mapping chính xác
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def export_database_to_json(db_path='project_data.db', output_path='public/data.json'):
    """
    Export all documents from SQLite database to JSON file
    
    Args:
        db_path: Path to SQLite database file
        output_path: Path to output JSON file
    
    Returns:
        Dict with export results
    """
    
    print("\n" + "=" * 60)
    print("   PTSC - Export Database to JSON v2")
    print("=" * 60 + "\n")
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"[ERROR] Database file not found: {db_path}")
        print("\nAvailable databases:")
        for file in os.listdir('.'):
            if file.endswith('.db'):
                print(f"   - {file}")
        return None
    
    print(f"[INFO] Reading database: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()
        
        # Check table name (could be 'documents' or 'mdi_documents')
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        
        table_name = None
        if 'mdi_documents' in tables:
            table_name = 'mdi_documents'
        elif 'documents' in tables:
            table_name = 'documents'
        else:
            print(f"[ERROR] No documents table found. Available tables: {tables}")
            return None
        
        print(f"[INFO] Using table: {table_name}")
        
        # Check database structure
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row['name'] for row in cursor.fetchall()]
        print(f"[INFO] Database has {len(columns)} columns")
        
        # Detect database structure type
        has_json_dates = 'plan_dates' in columns and 'actual_dates' in columns
        has_separate_dates = 'ifi_plan_date' in columns
        
        if has_json_dates:
            print("[INFO] Database structure: JSON dates (plan_dates, actual_dates as JSON strings)")
        else:
            print("[INFO] Database structure: Separate date columns (ifi_plan_date, ifr_plan_date, etc.)")
        
        # Get all documents, sorted by stt
        # FILTER: Only MDI documents with companyDocNo or document_no (exclude supporting files)
        print("[INFO] Fetching MDI documents (with companyDocNo)...")
        
        # Check which column name exists
        if 'document_no' in columns:
            doc_no_col = 'document_no'
        elif 'companyDocNo' in columns:
            doc_no_col = 'companyDocNo'
        else:
            doc_no_col = None
        
        if doc_no_col:
            # Filter: Only documents with document number (MDI documents from Excel)
            cursor.execute(f"""
                SELECT * FROM {table_name} 
                WHERE {doc_no_col} IS NOT NULL AND {doc_no_col} != ''
                ORDER BY stt ASC
            """)
        else:
            # Fallback: Get all documents
            print("[WARNING] No document_no column found, fetching all documents")
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY stt ASC")
        
        rows = cursor.fetchall()
        
        # Convert rows to list of dictionaries with proper field mapping
        documents = []
        for i, row in enumerate(rows, 1):
            raw_doc = dict(row)
            
            # Parse plan_dates and actual_dates
            if has_json_dates:
                # Parse plan_dates (JSON string → Object)
                plan_dates = {}
                if raw_doc.get('plan_dates'):
                    try:
                        plan_dates = json.loads(raw_doc['plan_dates'])
                    except (json.JSONDecodeError, TypeError):
                        plan_dates = {}
                
                # Parse actual_dates (JSON string → Object)
                actual_dates = {}
                if raw_doc.get('actual_dates'):
                    try:
                        actual_dates = json.loads(raw_doc['actual_dates'])
                    except (json.JSONDecodeError, TypeError):
                        actual_dates = {}
            else:
                # Build from separate columns
                plan_dates = {
                    "ifi": raw_doc.get('ifi_plan_date'),
                    "ifr": raw_doc.get('ifr_plan_date'),
                    "ifa": raw_doc.get('ifa_plan_date'),
                    "ifc": raw_doc.get('ifc_plan_date'),
                    "iff": raw_doc.get('iff_plan_date')
                }
                
                actual_dates = {
                    "ifi": raw_doc.get('ifi_actual_date'),
                    "ifr": raw_doc.get('ifr_actual_date'),
                    "ifa": raw_doc.get('ifa_actual_date'),
                    "ifc": raw_doc.get('ifc_actual_date'),
                    "iff": raw_doc.get('iff_actual_date')
                }
            
            # Map database columns to frontend interface
            # Support both new structure (document_no, status, table_name) 
            # and old structure (companyDocNo, doc_status, table)
            doc = {
                # Key Identifiers
                "id": raw_doc.get('id') or raw_doc.get('localPath') or f"doc-{i}",
                "stt": raw_doc.get('stt') or i,
                "documentNo": raw_doc.get('document_no') or raw_doc.get('companyDocNo') or raw_doc.get('contractorDocNo') or '',
                "title": raw_doc.get('title') or raw_doc.get('name') or '',
                "revision": raw_doc.get('revision') or '',
                
                # Classification
                "discipline": raw_doc.get('discipline') or 'N/A',
                "scope": raw_doc.get('scope') or '',
                "docClass": raw_doc.get('doc_class') or '',
                "table": raw_doc.get('table_name') or raw_doc.get('table') or '',
                "item": raw_doc.get('item') or '',
                
                # Status & Progress
                "status": raw_doc.get('status') or raw_doc.get('doc_status') or raw_doc.get('feedbackStatus') or '',
                "ipiStatus": raw_doc.get('ipi_status') or '',
                "reviewCode": raw_doc.get('review_code') or '',
                
                # Dates
                "planDates": plan_dates,
                "actualDates": actual_dates,
                "targetMitigationDate": raw_doc.get('target_mitigation_date'),
                
                # Transmittals
                "transNo": raw_doc.get('transNo'),
                "dateReceived": raw_doc.get('dateReceived') or raw_doc.get('date_received'),
                "trnOutDate": raw_doc.get('trn_out_date'),
                "trnOutNo": raw_doc.get('trn_out_no'),
                "trnInDate": raw_doc.get('trn_in_date'),
                "trnInNo": raw_doc.get('trn_in_no'),
                
                # People (QUAN TRỌNG!)
                "picPtsc": raw_doc.get('pic_ptsc'),
                "picLsp": raw_doc.get('pic_lsp'),
                
                # System Paths
                "localPath": raw_doc.get('localPath'),
                "sharepointPath": raw_doc.get('sharepointPath'),
                
                # Computed fields (0/1 → boolean)
                "isOverdue": bool(raw_doc.get('is_overdue', 0)),
                "isCritical": bool(raw_doc.get('is_critical', 0))
            }
            
            documents.append(doc)
        
        print(f"[OK] Fetched {len(documents)} MDI documents")
        
        # Get statistics (only for MDI documents with companyDocNo)
        if doc_no_col:
            cursor.execute(f"""
                SELECT COUNT(*) as total FROM {table_name}
                WHERE {doc_no_col} IS NOT NULL AND {doc_no_col} != ''
            """)
        else:
            cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
        total_count = cursor.fetchone()['total']
        
        # Build WHERE clause for MDI documents filter
        where_clause = f"WHERE {doc_no_col} IS NOT NULL AND {doc_no_col} != ''" if doc_no_col else ""
        
        cursor.execute(f"""
            SELECT COUNT(DISTINCT discipline) as count FROM {table_name} 
            {where_clause}
            AND discipline IS NOT NULL AND discipline != ''
        """)
        discipline_count = cursor.fetchone()['count']
        
        # Check for status column (could be 'status' or 'doc_status')
        status_col = 'status' if 'status' in columns else 'doc_status'
        if status_col in columns:
            cursor.execute(f"""
                SELECT COUNT(*) as count FROM {table_name} 
                {where_clause}
                AND {status_col} = 'Approved'
            """)
            approved_count = cursor.fetchone()['count']
        else:
            approved_count = 0
        
        # Check for is_overdue column
        if 'is_overdue' in columns:
            cursor.execute(f"""
                SELECT COUNT(*) as count FROM {table_name} 
                {where_clause}
                AND is_overdue = 1
            """)
            overdue_count = cursor.fetchone()['count']
        else:
            overdue_count = 0
        
        # Create output structure with metadata
        now = datetime.now()
        output_data = {
            "metadata": {
                "exportDate": now.isoformat(),
                "totalDocuments": total_count,
                "lastUpdate": now.strftime('%Y-%m-%d %H:%M:%S'),
                "version": "1.0.0",
                "statistics": {
                    "total": total_count,
                    "approved": approved_count,
                    "overdue": overdue_count,
                    "disciplines": discipline_count
                }
            },
            "documents": documents
        }
        
        # Create public directory if not exists
        output_dir = Path(output_path).parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
            print(f"[INFO] Created directory: {output_dir}")
        
        # Write to JSON file
        print(f"\n[INFO] Writing to: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        # Get file size
        file_size = os.path.getsize(output_path)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"[OK] Export completed successfully!")
        print(f"\nEXPORT SUMMARY:")
        print(f"   File: {output_path}")
        print(f"   Size: {file_size_mb:.2f} MB")
        print(f"   Documents: {total_count}")
        print(f"   Approved: {approved_count}")
        print(f"   Overdue: {overdue_count}")
        print(f"   Disciplines: {discipline_count}")
        print(f"   Export Date: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show sample data
        if documents:
            print(f"\nSAMPLE DATA (first document):")
            sample = documents[0]
            print(f"   ID: {sample.get('id')}")
            print(f"   STT: {sample.get('stt')}")
            print(f"   Doc No: {sample.get('documentNo')}")
            print(f"   Title: {sample.get('title', '')[:50]}...")
            print(f"   Discipline: {sample.get('discipline')}")
            print(f"   Status: {sample.get('status')}")
            print(f"   PIC PTSC: {sample.get('picPtsc')}")
            print(f"   PIC LSP: {sample.get('picLsp')}")
            print(f"   Is Overdue: {sample.get('isOverdue')}")
            print(f"   Plan Dates: {list(sample.get('planDates', {}).keys())}")
            print(f"   Actual Dates: {list(sample.get('actualDates', {}).keys())}")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print(f"File ready for deployment: {output_path}")
        print("\nNext steps:")
        print("  1. Verify JSON structure")
        print("  2. Commit to GitHub: git add public/data.json")
        print("  3. Push: git push origin main")
        print("  4. Web app will load data from this JSON file")
        print("=" * 60 + "\n")
        
        return {
            "success": True,
            "file": output_path,
            "size": file_size,
            "count": total_count
        }
        
    except sqlite3.Error as e:
        print(f"\n[ERROR] DATABASE ERROR: {e}")
        return None
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function"""
    
    # Default paths
    db_path = 'project_data.db'
    output_path = 'public/data.json'
    
    # Allow custom paths from command line
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    
    print(f"\nArguments:")
    print(f"  Database: {db_path}")
    print(f"  Output: {output_path}")
    
    result = export_database_to_json(db_path, output_path)
    
    if result:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
