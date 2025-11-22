"""
Database Migration Script - Upgrade schema to support MDI tracking
Adds new fields from Excel MDI Status Report to existing database
"""

import sqlite3
import sys
import json
import io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def backup_database(db_path):
    """Create a backup of the database before migration"""
    try:
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"Backup failed: {e}")
        return False

def get_column_names(cursor, table_name):
    """Get existing column names from a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]

def migrate_database(db_path):
    """Migrate database to new schema"""
    try:
        print(f"Starting migration for: {db_path}")
        
        # Backup first
        if not backup_database(db_path):
            return {"success": False, "error": "Backup failed"}
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get existing columns
        existing_cols = get_column_names(cursor, 'documents')
        print(f"Existing columns: {len(existing_cols)}")
        
        # Define new columns to add
        new_columns = {
            'scope': 'TEXT',  # PTSC or TCC
            'item': 'TEXT',  # Item code like A19, B01, etc.
            'companyDocNo': 'TEXT',  # CompanyDoc.No. from Excel
            'contractorDocNo': 'TEXT',  # ContractorDoc.No. from Excel
            'ipi_status': 'TEXT',  # IFI, IFR, IFA, IFC, IFF
            'review_code': 'TEXT',  # A1, A2, A3, A4, R1, R2
            
            # TRN Out tracking
            'trn_out_date': 'TEXT',
            'trn_out_no': 'TEXT',
            'date_receive_trn_out': 'TEXT',
            
            # TRN In tracking
            'trn_in_date': 'TEXT',
            'trn_in_no': 'TEXT',
            
            # IPI Plan Dates
            'ifi_plan_date': 'TEXT',
            'ifr_plan_date': 'TEXT',
            'ifa_plan_date': 'TEXT',
            'ifc_plan_date': 'TEXT',
            'iff_plan_date': 'TEXT',
            
            # IPI Actual Dates
            'ifi_actual_date': 'TEXT',
            'ifr_actual_date': 'TEXT',
            'ifa_actual_date': 'TEXT',
            'ifc_actual_date': 'TEXT',
            'iff_actual_date': 'TEXT',
            
            # Management
            'target_mitigation_date': 'TEXT',
            'pic_ptsc': 'TEXT',
            'pic_lsp': 'TEXT',
            'doc_status': 'TEXT',  # Status from Excel (Not yet issued, Waiting cmt, Re-issue IFC, etc.)
        }
        
        # Add new columns if they don't exist
        added_columns = []
        for col_name, col_type in new_columns.items():
            if col_name not in existing_cols:
                try:
                    cursor.execute(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type}")
                    added_columns.append(col_name)
                    print(f"Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    print(f"Column {col_name} might already exist: {e}")
        
        # Create index for better query performance
        indexes = [
            ('idx_doc_status', 'doc_status'),
            ('idx_ipi_status', 'ipi_status'),
            ('idx_scope', 'scope'),
            ('idx_company_doc', 'companyDocNo'),
            ('idx_contractor_doc', 'contractorDocNo'),
            ('idx_review_code', 'review_code'),
        ]
        
        for idx_name, col_name in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON documents({col_name})")
                print(f"Created index: {idx_name}")
            except Exception as e:
                print(f"Index creation warning: {e}")
        
        conn.commit()
        
        # Verify migration
        new_cols = get_column_names(cursor, 'documents')
        print(f"Total columns after migration: {len(new_cols)}")
        
        conn.close()
        
        return {
            "success": True,
            "columns_added": len(added_columns),
            "total_columns": len(new_cols),
            "added_list": added_columns
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def check_migration_status(db_path):
    """Check if migration is needed"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        existing_cols = get_column_names(cursor, 'documents')
        
        # Check if new columns exist
        new_fields = ['scope', 'ipi_status', 'review_code', 'trn_out_date', 'companyDocNo']
        needs_migration = any(field not in existing_cols for field in new_fields)
        
        conn.close()
        
        return {
            "needs_migration": needs_migration,
            "current_columns": len(existing_cols),
            "columns": existing_cols
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python database_migration.py <db_path> <command>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    command = sys.argv[2]
    
    if command == "check":
        result = check_migration_status(db_path)
        print(json.dumps(result, indent=2))
    elif command == "migrate":
        result = migrate_database(db_path)
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({"error": f"Unknown command: {command}"}))
