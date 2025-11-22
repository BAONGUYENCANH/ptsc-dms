"""
Check data count discrepancy between database and Excel import
"""

import sqlite3
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def check_counts():
    conn = sqlite3.connect('project_data.db')
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("  DATABASE ANALYSIS - Count Discrepancy Check")
    print("="*60 + "\n")
    
    # Total rows
    cursor.execute('SELECT COUNT(*) FROM documents')
    total = cursor.fetchone()[0]
    print(f"Total rows in database: {total}")
    
    # Rows with STT
    cursor.execute('SELECT COUNT(*) FROM documents WHERE stt IS NOT NULL')
    with_stt = cursor.fetchone()[0]
    print(f"Rows with STT: {with_stt}")
    
    # Rows without STT (null)
    cursor.execute('SELECT COUNT(*) FROM documents WHERE stt IS NULL')
    no_stt = cursor.fetchone()[0]
    print(f"Rows without STT (NULL): {no_stt}")
    
    # Rows with name
    cursor.execute('SELECT COUNT(*) FROM documents WHERE name IS NOT NULL AND name != ""')
    with_name = cursor.fetchone()[0]
    print(f"Rows with name: {with_name}")
    
    # Rows without name (empty/null)
    cursor.execute('SELECT COUNT(*) FROM documents WHERE name IS NULL OR name = ""')
    no_name = cursor.fetchone()[0]
    print(f"Rows without name (empty/NULL): {no_name}")
    
    # Unique names
    cursor.execute('SELECT COUNT(DISTINCT name) FROM documents WHERE name IS NOT NULL')
    unique_names = cursor.fetchone()[0]
    print(f"Unique names: {unique_names}")
    
    # Check for duplicates
    duplicates = total - unique_names
    print(f"Possible duplicates: {duplicates}")
    
    print("\n" + "-"*60)
    print("POSSIBLE REASONS FOR DISCREPANCY:")
    print("-"*60)
    
    if no_stt > 0:
        print(f"[!] Found {no_stt} rows WITHOUT STT")
        print("  -> These might be non-MDI documents or metadata rows")
    
    if no_name > 0:
        print(f"[!] Found {no_name} rows WITHOUT name")
        print("  -> These might be empty/placeholder rows")
    
    if duplicates > 0:
        print(f"[!] Found {duplicates} possible duplicate names")
        print("  -> Same document might be imported multiple times")
    
    # Check document types
    print("\n" + "-"*60)
    print("DOCUMENT TYPES:")
    print("-"*60)
    
    # Documents by source (check if there are non-Excel imports)
    cursor.execute('SELECT COUNT(*) FROM documents WHERE transNo IS NOT NULL AND transNo != ""')
    with_trans = cursor.fetchone()[0]
    print(f"Documents with Transmittal No: {with_trans}")
    
    cursor.execute('SELECT COUNT(*) FROM documents WHERE companyDocNo IS NOT NULL AND companyDocNo != ""')
    with_doc_no = cursor.fetchone()[0]
    print(f"Documents with Company Doc No: {with_doc_no}")
    
    # Sample of rows without STT
    if no_stt > 0:
        print("\n" + "-"*60)
        print("SAMPLE ROWS WITHOUT STT (first 5):")
        print("-"*60)
        cursor.execute('SELECT name, transNo, companyDocNo FROM documents WHERE stt IS NULL LIMIT 5')
        for i, row in enumerate(cursor.fetchall(), 1):
            print(f"{i}. Name: {row[0][:60] if row[0] else 'NULL'}...")
            print(f"   TransNo: {row[1] or 'NULL'}")
            print(f"   DocNo: {row[2] or 'NULL'}")
    
    print("\n" + "="*60)
    print(f"SUMMARY: {total} total rows, expected {total - no_stt} MDI documents")
    print("="*60 + "\n")
    
    conn.close()

if __name__ == '__main__':
    check_counts()
