# doc_processor.py

import os
import sys
import json
import re
from datetime import datetime
import shutil
import pandas as pd
import sqlite3

# --- CONFIGURATION AND DATABASE SETUP ---

# The database name is now passed as a command-line argument
DB_NAME = sys.argv[1] 

def get_script_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.dirname(sys.executable))
    else:
        # In development, the script's directory is the 'source' folder
        return os.path.dirname(os.path.abspath(__file__))

def load_config():
    """Loads configuration from config.json."""
    try:
        # Config file is always relative to the script's resources
        config_path = os.path.join(get_script_dir(), 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config.json: {e}", file=sys.stderr)
        return {}

CONFIG = load_config()
DISCIPLINE_MAP = CONFIG.get("discipline_map", {})

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            localPath TEXT PRIMARY KEY,
            stt INTEGER,
            name TEXT,
            "table" TEXT,
            description TEXT,
            discipline TEXT,
            transNo TEXT,
            dateReceived TEXT,
            revision TEXT,
            doc_class TEXT,
            sharepointPath TEXT,
            feedbackStatus TEXT,
            scope TEXT,
            item TEXT,
            companyDocNo TEXT,
            contractorDocNo TEXT,
            ipi_status TEXT,
            review_code TEXT,
            trn_out_date TEXT,
            trn_out_no TEXT,
            date_receive_trn_out TEXT,
            trn_in_date TEXT,
            trn_in_no TEXT,
            ifi_plan_date TEXT,
            ifr_plan_date TEXT,
            ifa_plan_date TEXT,
            ifc_plan_date TEXT,
            iff_plan_date TEXT,
            ifi_actual_date TEXT,
            ifr_actual_date TEXT,
            ifa_actual_date TEXT,
            ifc_actual_date TEXT,
            iff_actual_date TEXT,
            target_mitigation_date TEXT,
            pic_ptsc TEXT,
            pic_lsp TEXT,
            doc_status TEXT
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS generic_files (
            localPath TEXT PRIMARY KEY, stt INTEGER, name TEXT, format TEXT,
            dateReceived TEXT, revision TEXT
        )''')
        
        conn.commit()
        conn.close()
        print(json.dumps({"success": True, "message": "Database initialized successfully."}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}), file=sys.stderr)

def db_connect():
    return sqlite3.connect(DB_NAME)

def load_mdi_mapping():
    try:
        mapping_file_path = os.path.join(get_script_dir(), 'mdi_mapping.json')
        with open(mapping_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading MDI mapping: {e}", file=sys.stderr)
        return {}

MDI_MAPPING = load_mdi_mapping()
SORTED_MDI_KEYS = sorted(list(MDI_MAPPING.keys()), key=len, reverse=True) if MDI_MAPPING else []


# --- CORE LOGIC (No changes needed here) ---
# ... (All core logic functions remain the same)
def get_discipline_info(lookup_char):
    return DISCIPLINE_MAP.get(lookup_char.upper(), ["N/A", "N/A", "N/A"])

def parse_revision_from_name(base_name):
    doc_revision = "N/A"
    rev_parts = base_name.split('_')
    for part in rev_parts:
        if len(part) == 1 and (part.isalpha() or part.isdigit()):
            doc_revision = part.upper()
            break
    return doc_revision

def parse_filename(base_name):
    doc_table_name, doc_description, doc_discipline = "N/A", "N/A", "N/A"
    lookup_char = ""
    if base_name.startswith("TF1_2") and len(base_name) > 5:
        temp_char = base_name[5]
        if not temp_char.isdigit():
            lookup_char = temp_char
    if not lookup_char:
        parts = base_name.split('-')
        if len(parts) >= 2:
            code_part = parts[1]
            match = re.search(r'\D', code_part)
            if match:
                lookup_char = match.group(0)
    if lookup_char:
        doc_table_name, doc_description, doc_discipline = get_discipline_info(lookup_char)
    doc_revision = parse_revision_from_name(base_name)
    return doc_table_name, doc_description, doc_discipline, doc_revision

def scan_documents(root_folder):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute('SELECT localPath, sharepointPath, feedbackStatus, scope, companyDocNo, contractorDocNo, ipi_status, review_code, trn_out_date, trn_out_no, date_receive_trn_out, trn_in_date, trn_in_no, ifi_plan_date, ifr_plan_date, ifa_plan_date, ifc_plan_date, iff_plan_date, ifi_actual_date, ifr_actual_date, ifa_actual_date, ifc_actual_date, iff_actual_date, target_mitigation_date, pic_ptsc, pic_lsp, doc_status FROM documents')
    existing_data = {}
    for row in cursor.fetchall():
        existing_data[row[0]] = {
            'sp': row[1], 'fb': row[2], 'scope': row[3], 'companyDocNo': row[4], 'contractorDocNo': row[5],
            'ipi_status': row[6], 'review_code': row[7], 'trn_out_date': row[8], 'trn_out_no': row[9],
            'date_receive_trn_out': row[10], 'trn_in_date': row[11], 'trn_in_no': row[12],
            'ifi_plan_date': row[13], 'ifr_plan_date': row[14], 'ifa_plan_date': row[15],
            'ifc_plan_date': row[16], 'iff_plan_date': row[17], 'ifi_actual_date': row[18],
            'ifr_actual_date': row[19], 'ifa_actual_date': row[20], 'ifc_actual_date': row[21],
            'iff_actual_date': row[22], 'target_mitigation_date': row[23], 'pic_ptsc': row[24],
            'pic_lsp': row[25], 'doc_status': row[26]
        }
    documents_to_upsert = []
    allowed_extensions = ('.pdf', '.doc', '.docx', '.xls', '.xlsx')
    normalized_root_folder = os.path.abspath(root_folder)
    class_cache = {}
    for dirpath, _, filenames in os.walk(root_folder):
        project_trans_no = "N/A"
        current_search_path = os.path.abspath(dirpath)
        while True:
            folder_name = os.path.basename(current_search_path)
            trans_match = re.search(r'(LSPET-TCPT-T- ?\w{2}-\d{4})', folder_name)
            if trans_match:
                project_trans_no = trans_match.group(1).replace(' ', '')
                break
            try:
                if os.path.samefile(current_search_path, normalized_root_folder):
                    break
            except FileNotFoundError:
                break
            parent_path = os.path.dirname(current_search_path)
            if parent_path == current_search_path:
                break
            current_search_path = parent_path
        level_1_folder = "N/A"
        relative_path = os.path.relpath(dirpath, normalized_root_folder)
        if relative_path != '.':
            level_1_folder = relative_path.split(os.sep)[0]
        for filename in filenames:
            if not filename.lower().endswith(allowed_extensions):
                continue
            base_name, _ = os.path.splitext(filename)
            file_path = os.path.join(dirpath, filename)
            table, desc, disc, rev = "N/A", "N/A", "N/A", "N/A"
            doc_class = "N/A"
            if base_name.startswith("LSPET-TCPT-T-") or base_name.startswith("TCPT-LSPET-T-"):
                rev = parse_revision_from_name(base_name)
            else:
                table, desc, disc, rev = parse_filename(base_name)
            found_key = next((key for key in SORTED_MDI_KEYS if base_name.startswith(key)), None)
            if found_key:
                class_value = MDI_MAPPING.get(found_key, "N/A")
                if class_value and class_value != "N/A":
                    doc_class = class_value[0]
                    if level_1_folder != "N/A" and level_1_folder not in class_cache:
                        class_cache[level_1_folder] = doc_class
            else:
                if level_1_folder != "N/A":
                    doc_class = class_cache.get(level_1_folder, "N/A")
            creation_date = datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
            existing_info = existing_data.get(file_path, {})
            sharepoint_path = existing_info.get('sp')
            feedback_status = existing_info.get('fb')
            
            # Extract item code from base_name (e.g., A19, B01, M90)
            item_code = "N/A"
            if base_name.startswith("TF1-2"):
                parts = base_name.split('-')
                if len(parts) >= 3:
                    # Format: TF1-2{ITEM}-...
                    potential_item = parts[2][:3]  # Get first 3 chars (e.g., A19, B01)
                    if len(potential_item) >= 2:
                        item_code = potential_item
            
            # Try to extract company doc number (base_name might be the doc number)
            company_doc_no = base_name if base_name.startswith("TF1-2") or base_name.startswith("TCPT-") or base_name.startswith("LSPET-") else existing_info.get('companyDocNo')
            
            # Preserve all existing tracked data
            documents_to_upsert.append((
                file_path, base_name, table, desc, disc, project_trans_no, 
                creation_date, rev, doc_class, sharepoint_path, feedback_status,
                existing_info.get('scope'), item_code, company_doc_no, existing_info.get('contractorDocNo'),
                existing_info.get('ipi_status'), existing_info.get('review_code'),
                existing_info.get('trn_out_date'), existing_info.get('trn_out_no'), existing_info.get('date_receive_trn_out'),
                existing_info.get('trn_in_date'), existing_info.get('trn_in_no'),
                existing_info.get('ifi_plan_date'), existing_info.get('ifr_plan_date'), existing_info.get('ifa_plan_date'),
                existing_info.get('ifc_plan_date'), existing_info.get('iff_plan_date'),
                existing_info.get('ifi_actual_date'), existing_info.get('ifr_actual_date'), existing_info.get('ifa_actual_date'),
                existing_info.get('ifc_actual_date'), existing_info.get('iff_actual_date'),
                existing_info.get('target_mitigation_date'), existing_info.get('pic_ptsc'), existing_info.get('pic_lsp'),
                existing_info.get('doc_status')
            ))
    if documents_to_upsert:
        cursor.executemany('''
        REPLACE INTO documents (
            localPath, name, "table", description, discipline, transNo, dateReceived, revision, doc_class, 
            sharepointPath, feedbackStatus, scope, item, companyDocNo, contractorDocNo,
            ipi_status, review_code, trn_out_date, trn_out_no, date_receive_trn_out,
            trn_in_date, trn_in_no, ifi_plan_date, ifr_plan_date, ifa_plan_date, ifc_plan_date, iff_plan_date,
            ifi_actual_date, ifr_actual_date, ifa_actual_date, ifc_actual_date, iff_actual_date,
            target_mitigation_date, pic_ptsc, pic_lsp, doc_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', documents_to_upsert)
    conn.commit()
    conn.close()
    load_all_docs()

def scan_generic_files(root_folder):
    conn = db_connect()
    cursor = conn.cursor()
    allowed_extensions = ('.pdf', '.doc', '.docx', '.xls', '.xlsx')
    files_to_upsert = []
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if not filename.lower().endswith(allowed_extensions):
                continue
            base_name, extension = os.path.splitext(filename)
            file_format = extension.replace('.', '').lower()
            file_path = os.path.join(dirpath, filename)
            creation_date = datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
            revision = parse_revision_from_name(base_name)
            files_to_upsert.append((
                file_path, base_name, file_format, creation_date, revision
            ))
    if files_to_upsert:
        cursor.executemany('''
        REPLACE INTO generic_files (localPath, name, format, dateReceived, revision)
        VALUES (?, ?, ?, ?, ?)
        ''', files_to_upsert)
    conn.commit()
    conn.close()
    load_all_generic_files()

def load_all_docs():
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM documents ORDER BY stt, name')
    rows = cursor.fetchall()
    docs = [dict(row) for row in rows]
    for i, doc in enumerate(docs):
        doc['stt'] = i + 1
    print(json.dumps(docs))
    conn.close()

def load_all_generic_files():
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM generic_files ORDER BY name')
    rows = cursor.fetchall()
    files = [dict(row) for row in rows]
    for i, file_item in enumerate(files):
        file_item['stt'] = i + 1
    print(json.dumps(files))
    conn.close()

def upload_to_sharepoint(documents_json, sp_root_path):
    documents = json.loads(documents_json)
    if not os.path.isdir(sp_root_path):
        print(json.dumps({"status": "error", "message": "Đường dẫn SharePoint không tồn tại."}))
        return
    conn = db_connect()
    cursor = conn.cursor()
    for doc in documents:
        local_path = doc.get("localPath", "")
        discipline = doc.get("discipline", "N/A")
        if os.path.exists(local_path) and discipline != "N/A":
            dest_folder = os.path.join(sp_root_path, discipline)
            os.makedirs(dest_folder, exist_ok=True)
            file_name = os.path.basename(local_path)
            dest_path = os.path.join(dest_folder, file_name)
            try:
                shutil.copy2(local_path, dest_path)
                cursor.execute('UPDATE documents SET sharepointPath = ? WHERE localPath = ?', (dest_path, local_path))
            except Exception:
                cursor.execute('UPDATE documents SET sharepointPath = ? WHERE localPath = ?', ("Lỗi Upload", local_path))
    conn.commit()
    conn.close()
    load_all_docs()

def process_feedback(documents_json, feedback_folder, subcon_folder):
    documents = json.loads(documents_json)
    if not os.path.isdir(feedback_folder) or not os.path.isdir(subcon_folder):
        print(json.dumps({"status": "error", "message": "Thư mục không hợp lệ."}))
        return
    conn = db_connect()
    cursor = conn.cursor()
    doc_map = {doc['name']: doc for doc in documents}
    for filename in os.listdir(feedback_folder):
        feedback_name, _ = os.path.splitext(filename)
        found_doc = next((doc_data for doc_name, doc_data in doc_map.items() if feedback_name in doc_name or doc_name in feedback_name), None)
        if found_doc:
            discipline = found_doc.get("discipline", "N/A")
            local_path = found_doc.get("localPath")
            if discipline != "N/A" and local_path:
                dest_folder = os.path.join(subcon_folder, discipline)
                os.makedirs(dest_folder, exist_ok=True)
                source_path = os.path.join(feedback_folder, filename)
                dest_path = os.path.join(dest_folder, filename)
                try:
                    shutil.move(source_path, dest_path)
                    cursor.execute('UPDATE documents SET feedbackStatus = ? WHERE localPath = ?', ("Đã nhận phản hồi", local_path))
                except Exception:
                    pass
    conn.commit()
    conn.close()
    load_all_docs()
    
def export_to_excel(documents_json, output_path):
    try:
        documents = json.loads(documents_json)
        if not documents:
            print(json.dumps({"success": False, "error": "Không có dữ liệu để xuất."}), flush=True)
            return

        sanitized_documents = []
        excel_dir = os.path.dirname(output_path) # Get directory where Excel file is saved

        for doc in documents:
            sanitized_doc = {}
            for key, value in doc.items():
                if isinstance(value, str):
                    sanitized_doc[key] = value.encode('utf-8', 'surrogateescape').decode('utf-8', 'replace')
                else:
                    sanitized_doc[key] = value
            
            # --- START: RELATIVE PATH LOGIC ---
            local_path = sanitized_doc.get("localPath")
            if local_path:
                try:
                    relative_path = os.path.relpath(local_path, excel_dir)
                    sanitized_doc['localLink'] = relative_path.replace('\\', '/')
                except ValueError:
                    # Fallback for different drives on Windows
                    sanitized_doc['localLink'] = local_path.replace('\\', '/')
            # --- END: RELATIVE PATH LOGIC ---
            sanitized_documents.append(sanitized_doc)

        df = pd.DataFrame(sanitized_documents)
        
        columns_map = {
            "stt": "STT",
            "scope": "Scope",
            "table": "Table",
            "item": "Item",
            "discipline": "Bộ môn",
            "companyDocNo": "Company Doc No",
            "contractorDocNo": "Contractor Doc No",
            "name": "Tên tài liệu",
            "doc_class": "Class",
            "revision": "Phiên bản",
            "ipi_status": "IPI Status",
            "transNo": "Trans No",
            "dateReceived": "Ngày nhận",
            "trn_out_date": "TRN Out Date",
            "trn_out_no": "TRN Out No",
            "date_receive_trn_out": "Date Receive TRN Out",
            "trn_in_date": "TRN In Date",
            "trn_in_no": "TRN In No",
            "review_code": "Review Code",
            "ifi_plan_date": "IFI Plan",
            "ifr_plan_date": "IFR Plan",
            "ifa_plan_date": "IFA Plan",
            "ifc_plan_date": "IFC Plan",
            "iff_plan_date": "IFF Plan",
            "ifi_actual_date": "IFI Actual",
            "ifr_actual_date": "IFR Actual",
            "ifa_actual_date": "IFA Actual",
            "ifc_actual_date": "IFC Actual",
            "iff_actual_date": "IFF Actual",
            "target_mitigation_date": "Target Date",
            "pic_ptsc": "PIC PTSC",
            "pic_lsp": "PIC LSP",
            "doc_status": "Status",
            "description": "Description",
            "sharepointPath": "Đường dẫn (SharePoint)",
            "feedbackStatus": "Trạng thái Phản hồi",
            "localLink": "Đường dẫn Local"
        }
        
        cols_to_export = [key for key in columns_map if key in df.columns]
        df_export = df[cols_to_export].rename(columns=columns_map)

        writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
        df_export.to_excel(writer, sheet_name='Sheet1', index=False)
        
        workbook  = writer.book
        worksheet = writer.sheets['Sheet1']
        url_format = workbook.add_format({'font_color': 'blue', 'underline': 1})
        
        # Find the index of our new link column
        try:
            link_col_idx = df_export.columns.get_loc("Đường dẫn Local")
            # Write hyperlink formula for each row
            for index, row in df_export.iterrows():
                link_path = row["Đường dẫn Local"]
                if link_path:
                    worksheet.write_url(index + 1, link_col_idx, link_path, string='Mở File', cell_format=url_format)
        except KeyError:
            pass # Column wasn't there, do nothing

        writer.close()
        
        print(json.dumps({"success": True, "path": output_path}), flush=True)

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}), flush=True)

def export_generic_to_excel(documents_json, output_path):
    # (Applying the same relative path logic here)
    try:
        documents = json.loads(documents_json)
        if not documents:
            return print(json.dumps({"success": False, "error": "Không có dữ liệu để xuất."}))

        excel_dir = os.path.dirname(output_path)
        for doc in documents:
            local_path = doc.get("localPath")
            if local_path:
                try:
                    doc['localLink'] = os.path.relpath(local_path, excel_dir).replace('\\', '/')
                except ValueError:
                    doc['localLink'] = local_path.replace('\\', '/')

        df = pd.DataFrame(documents)
        columns_map = {
            "stt": "STT", "name": "Tên tài liệu", "format": "Định dạng",
            "dateReceived": "Ngày nhận", "revision": "Phiên bản", "localLink": "Đường dẫn Local"
        }
        
        cols_to_export = [key for key in columns_map if key in df.columns]
        df_export = df[cols_to_export].rename(columns=columns_map)

        writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
        df_export.to_excel(writer, sheet_name='Sheet1', index=False)
        
        workbook  = writer.book
        worksheet = writer.sheets['Sheet1']
        url_format = workbook.add_format({'font_color': 'blue', 'underline': 1})
        
        try:
            link_col_idx = df_export.columns.get_loc("Đường dẫn Local")
            for index, row in df_export.iterrows():
                link_path = row["Đường dẫn Local"]
                if link_path:
                    worksheet.write_url(index + 1, link_col_idx, link_path, string='Mở File', cell_format=url_format)
        except KeyError:
            pass

        writer.close()
        
        print(json.dumps({"success": True, "path": output_path}), flush=True)
        
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}), flush=True)

def get_document_stats():
    conn = db_connect()
    cursor = conn.cursor()
    
    # Total documents
    cursor.execute('SELECT COUNT(*) FROM documents')
    total_docs = cursor.fetchone()[0]
    
    # By discipline
    cursor.execute('''
        SELECT discipline, COUNT(*)
        FROM documents
        GROUP BY discipline
        ORDER BY COUNT(*) DESC
    ''')
    docs_by_discipline_raw = cursor.fetchall()
    docs_by_discipline = {item[0] if item[0] else "N/A": item[1] for item in docs_by_discipline_raw}
    
    # By Scope
    cursor.execute('''
        SELECT scope, COUNT(*)
        FROM documents
        WHERE scope IS NOT NULL
        GROUP BY scope
    ''')
    docs_by_scope_raw = cursor.fetchall()
    docs_by_scope = {item[0]: item[1] for item in docs_by_scope_raw}
    
    # By IPI Status
    cursor.execute('''
        SELECT ipi_status, COUNT(*)
        FROM documents
        WHERE ipi_status IS NOT NULL
        GROUP BY ipi_status
    ''')
    docs_by_ipi_raw = cursor.fetchall()
    docs_by_ipi = {item[0]: item[1] for item in docs_by_ipi_raw}
    
    # By Document Status
    cursor.execute('''
        SELECT doc_status, COUNT(*)
        FROM documents
        WHERE doc_status IS NOT NULL
        GROUP BY doc_status
        ORDER BY COUNT(*) DESC
    ''')
    docs_by_status_raw = cursor.fetchall()
    docs_by_status = {item[0]: item[1] for item in docs_by_status_raw}
    
    # TRN Statistics
    cursor.execute('''
        SELECT COUNT(*)
        FROM documents
        WHERE trn_out_date IS NOT NULL
    ''')
    total_trn_out = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*)
        FROM documents
        WHERE trn_out_date IS NOT NULL AND trn_in_date IS NULL
    ''')
    trn_pending = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*)
        FROM documents
        WHERE trn_in_date IS NOT NULL
    ''')
    trn_received = cursor.fetchone()[0]
    
    # Review Code Statistics
    cursor.execute('''
        SELECT review_code, COUNT(*)
        FROM documents
        WHERE review_code IS NOT NULL
        GROUP BY review_code
        ORDER BY COUNT(*) DESC
    ''')
    docs_by_review_code_raw = cursor.fetchall()
    docs_by_review_code = {item[0]: item[1] for item in docs_by_review_code_raw}
    
    # Legacy feedback
    cursor.execute('''
        SELECT COUNT(*)
        FROM documents
        WHERE feedbackStatus IS NULL OR feedbackStatus = ''
    ''')
    docs_needing_feedback = cursor.fetchone()[0]
    
    # Status Detail Distribution (matching Excel Summary sheet categories)
    # Count by Table for each status category
    status_categories = [
        'Input Plan', 'Ongoing 1st Issue', 'Ongoing Resubmit', 
        'Overdue 1st issue', 'Overdue Cmt', 'Overdue Re-submit',
        'Waiting Issue Final', 'Waiting Cmt'
    ]
    
    status_detail_distribution = {}
    
    for status_cat in status_categories:
        cursor.execute('''
            SELECT "table", COUNT(*)
            FROM documents
            WHERE doc_status LIKE ?
            GROUP BY "table"
        ''', (f'%{status_cat}%',))
        table_data_raw = cursor.fetchall()
        table_data = {item[0] if item[0] else "N/A": item[1] for item in table_data_raw}
        
        # Get total for this category
        cursor.execute('''
            SELECT COUNT(*)
            FROM documents
            WHERE doc_status LIKE ?
        ''', (f'%{status_cat}%',))
        total_count = cursor.fetchone()[0]
        
        status_detail_distribution[status_cat] = {
            "by_table": table_data,
            "total": total_count
        }
    
    # Status by Table (for Overdue tracking)
    cursor.execute('''
        SELECT "table", doc_status, COUNT(*)
        FROM documents
        WHERE "table" IS NOT NULL AND doc_status IS NOT NULL
        GROUP BY "table", doc_status
        ORDER BY "table", COUNT(*) DESC
    ''')
    status_by_table_raw = cursor.fetchall()
    
    # Organize by table
    status_by_table = {}
    for table_name, status, count in status_by_table_raw:
        if table_name not in status_by_table:
            status_by_table[table_name] = {}
        status_by_table[table_name][status] = count
    
    # Get Overdue counts by Table
    cursor.execute('''
        SELECT "table", COUNT(*)
        FROM documents
        WHERE doc_status LIKE '%Overdue%'
        GROUP BY "table"
        ORDER BY "table"
    ''')
    overdue_by_table_raw = cursor.fetchall()
    overdue_by_table = {item[0]: item[1] for item in overdue_by_table_raw if item[0]}
    
    conn.close()
    
    return {
        "total_documents": total_docs,
        "docs_by_discipline": docs_by_discipline,
        "docs_by_scope": docs_by_scope,
        "docs_by_ipi": docs_by_ipi,
        "docs_by_status": docs_by_status,
        "docs_by_review_code": docs_by_review_code,
        "trn_stats": {
            "total_trn_out": total_trn_out,
            "trn_pending": trn_pending,
            "trn_received": trn_received
        },
        "docs_needing_feedback": docs_needing_feedback,
        "status_detail_distribution": status_detail_distribution,
        "status_by_table": status_by_table,
        "overdue_by_table": overdue_by_table
    }

def import_from_excel_mdi(excel_path):
    """Import MDI data from Excel"""
    try:
        import subprocess
        script_path = os.path.join(get_script_dir(), 'excel_importer.py')
        result = subprocess.run(
            [sys.executable, script_path, DB_NAME, excel_path],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            # Parse the JSON output from the importer
            output_lines = result.stdout.strip().split('\n')
            last_line = output_lines[-1] if output_lines else '{}'
            import_result = json.loads(last_line)
            
            if import_result.get('success'):
                # Reload documents after import
                load_all_docs()
            else:
                print(json.dumps(import_result), file=sys.stderr)
        else:
            print(json.dumps({
                "success": False,
                "error": result.stderr
            }), file=sys.stderr)
    except Exception as e:
        import traceback
        print(json.dumps({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), file=sys.stderr)

if __name__ == "__main__":
    # Arguments are now: script_name.py, db_path, command, [other_args...]
    command = sys.argv[2]
    
    if command == "init":
        init_db()
    elif command == "load_docs":
        load_all_docs()
    elif command == "load_generic":
        load_all_generic_files()
    elif command == "scan":
        scan_documents(sys.argv[3])
    elif command == "upload":
        json_data = sys.stdin.read()
        sp_path = sys.argv[3]
        upload_to_sharepoint(json_data, sp_path)
    elif command == "feedback":
        json_data = sys.stdin.read()
        feedback_path = sys.argv[3]
        subcon_path = sys.argv[4]
        process_feedback(json_data, feedback_path, subcon_path)
    elif command == "export":
        json_data = sys.stdin.read()
        output_path = sys.argv[3]
        export_to_excel(json_data, output_path)
    elif command == "scan_generic":
        scan_generic_files(sys.argv[3])
    elif command == "export_generic":
        json_data = sys.stdin.read()
        output_path = sys.argv[3]
        export_generic_to_excel(json_data, output_path)
    elif command == "get_stats":
        stats = get_document_stats()
        print(json.dumps(stats))
    elif command == "import_excel":
        excel_path = sys.argv[3]
        import_from_excel_mdi(excel_path)