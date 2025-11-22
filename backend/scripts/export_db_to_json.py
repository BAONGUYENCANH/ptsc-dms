"""
Export SQLite Database to JSON for Static Web Deployment
Đọc project_data.db và export ra public/data.json
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
    print("   PTSC - Export Database to JSON")
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
        
        # Get all documents
        print("[INFO] Fetching documents...")
        cursor.execute("SELECT * FROM documents ORDER BY stt")
        rows = cursor.fetchall()
        
        # Convert rows to list of dictionaries with proper field mapping
        documents = []
        for i, row in enumerate(rows, 1):
            raw_doc = dict(row)
            
            # Map database columns to frontend interface
            doc = {
                # Key Identifiers
                "id": raw_doc.get('localPath') or f"doc-{i}",
                "stt": raw_doc.get('stt') or i,
                "documentNo": raw_doc.get('companyDocNo') or raw_doc.get('contractorDocNo') or '',
                "title": raw_doc.get('name') or '',
                "revision": raw_doc.get('revision') or '',
                
                # Classification
                "discipline": raw_doc.get('discipline') or 'N/A',
                "scope": raw_doc.get('scope') or '',
                "docClass": raw_doc.get('doc_class') or '',
                "table": raw_doc.get('table') or '',
                "item": raw_doc.get('item') or '',
                
                # Status & Progress
                "status": raw_doc.get('doc_status') or raw_doc.get('feedbackStatus') or '',
                "ipiStatus": raw_doc.get('ipi_status') or '',
                "reviewCode": raw_doc.get('review_code') or '',
                
                # Plan Dates
                "planDates": {
                    "ifi": raw_doc.get('ifi_plan_date'),
                    "ifr": raw_doc.get('ifr_plan_date'),
                    "ifa": raw_doc.get('ifa_plan_date'),
                    "ifc": raw_doc.get('ifc_plan_date'),
                    "iff": raw_doc.get('iff_plan_date')
                },
                
                # Actual Dates
                "actualDates": {
                    "ifi": raw_doc.get('ifi_actual_date'),
                    "ifr": raw_doc.get('ifr_actual_date'),
                    "ifa": raw_doc.get('ifa_actual_date'),
                    "ifc": raw_doc.get('ifc_actual_date'),
                    "iff": raw_doc.get('iff_actual_date')
                },
                
                "targetMitigationDate": raw_doc.get('target_mitigation_date'),
                
                # Transmittals
                "transNo": raw_doc.get('transNo'),
                "dateReceived": raw_doc.get('dateReceived'),
                "trnOutDate": raw_doc.get('trn_out_date'),
                "trnOutNo": raw_doc.get('trn_out_no'),
                "trnInDate": raw_doc.get('trn_in_date'),
                "trnInNo": raw_doc.get('trn_in_no'),
                
                # People
                "picPtsc": raw_doc.get('pic_ptsc'),
                "picLsp": raw_doc.get('pic_lsp'),
                
                # System Paths
                "localPath": raw_doc.get('localPath'),
                "sharepointPath": raw_doc.get('sharepointPath'),
                
                # Computed fields (frontend will recalculate)
                "isOverdue": False,
                "isCritical": False
            }
            
            documents.append(doc)
        
        print(f"[OK] Fetched {len(documents)} documents")
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) as total FROM documents")
        total_count = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(DISTINCT discipline) as count FROM documents WHERE discipline IS NOT NULL")
        discipline_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM documents WHERE doc_status = 'Approved'")
        approved_count = cursor.fetchone()['count']
        
        # Note: isOverdue is computed in frontend, not stored in DB
        # For stats, we'll compute it here or set to 0
        overdue_count = 0  # Will be computed by frontend
        
        # Create output structure with metadata (matching frontend interface)
        output_data = {
            "metadata": {
                "exportDate": datetime.now().isoformat(),
                "totalDocuments": total_count,
                "lastUpdate": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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
        print(f"   Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show sample data
        if documents:
            print(f"\nSAMPLE DATA (first document):")
            sample = documents[0]
            print(f"   STT: {sample.get('stt')}")
            print(f"   Doc No: {sample.get('companyDocNo')}")
            print(f"   Name: {sample.get('name', '')[:50]}...")
            print(f"   Discipline: {sample.get('discipline')}")
            print(f"   Status: {sample.get('doc_status')}")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print(f"File ready for deployment: {output_path}")
        print("\nNext steps:")
        print("  1. Copy public/data.json to your web server")
        print("  2. Or commit to GitHub (will auto-deploy)")
        print("  3. Web app will load data from this JSON file")
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
    import sys
    
    # Default paths
    db_path = 'project_data.db'
    output_path = 'public/data.json'
    
    # Allow custom paths from command line
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    
    result = export_database_to_json(db_path, output_path)
    
    if result:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
