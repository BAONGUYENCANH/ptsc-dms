# doc_processor.py

import os
import sys
import json
import re
from datetime import datetime
import shutil
import pandas as pd
import sqlite3
import html

# --- CONFIGURATION AND DATABASE SETUP ---

def get_script_dir():
    """
    Returns the directory of the script or the executable's resources.
    This function handles both development and packaged environments.
    """
    if getattr(sys, 'frozen', False):
        # The app is running from a packaged executable
        return os.path.join(os.path.dirname(sys.executable), 'resources')
    else:
        # The app is running in a development environment
        return os.path.dirname(os.path.abspath(__file__))

def load_config():
    """Loads configuration from config.json."""
    try:
        config_path = os.path.join(get_script_dir(), 'config.json')
        if not os.path.exists(config_path):
            # Tạo file config.json rỗng nếu không tìm thấy
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            print(f"Warning: config.json not found, an empty file was created at {config_path}", file=sys.stderr)
            return {}

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config.json: {e}", file=sys.stderr)
        return {}

CONFIG = load_config()
DB_NAME = os.path.join(get_script_dir(), CONFIG.get("database_name", "database.db"))
DISCIPLINE_MAP = CONFIG.get("discipline_map", {})

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            localPath TEXT PRIMARY KEY,
            stt INTEGER, name TEXT, "table" TEXT, description TEXT,
            discipline TEXT, transNo TEXT, dateReceived TEXT, revision TEXT,
            doc_class TEXT, sharepointPath TEXT, feedbackStatus TEXT
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS generic_files (
            localPath TEXT PRIMARY KEY,
            stt INTEGER, name TEXT, format TEXT,
            dateReceived TEXT, revision TEXT
        )''')
        
        conn.commit()
        conn.close()
        print(json.dumps({"success": True, "message": "Database initialized successfully."}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}), file=sys.stderr)

def db_connect():
    return sqlite3.connect(DB_NAME)

# --- MDI MAPPING ---
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


# --- CORE LOGIC ---

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
    # --- BẮT ĐẦU THAY ĐỔI ---
    # 1. Xác định các định dạng file được phép quét
    allowed_extensions = ('.pdf', '.doc', '.docx', '.xls', '.xlsx')
    # --- KẾT THÚC THAY ĐỔI ---

    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute('SELECT localPath, sharepointPath, feedbackStatus FROM documents')
    existing_data = {row[0]: {'sp': row[1], 'fb': row[2]} for row in cursor.fetchall()}
    project_trans_no = "N/A"
    root_folder_name = os.path.basename(root_folder)
    trans_match = re.search(r'(LSPET-TCPT-T-\w{2}-\d{4})', root_folder_name)
    if trans_match:
        project_trans_no = trans_match.group(1).replace(' ', '')
    documents_to_upsert = []
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            # --- BẮT ĐẦU THAY ĐỔI ---
            # 2. Bỏ qua file nếu không có định dạng hợp lệ
            if not filename.lower().endswith(allowed_extensions):
                continue
            # --- KẾT THÚC THAY ĐỔI ---

            base_name, _ = os.path.splitext(filename)
            file_path = os.path.join(dirpath, filename)
            table, desc, disc, rev, doc_class = "N/A", "N/A", "N/A", "N/A", "N/A"
            if base_name.startswith("LSPET-TCPT-T-") or base_name.startswith("TCPT-LSPET-T-"):
                rev = parse_revision_from_name(base_name)
            else:
                table, desc, disc, rev = parse_filename(base_name)
                found_key = next((key for key in SORTED_MDI_KEYS if base_name.startswith(key)), None)
                if found_key:
                    class_value = MDI_MAPPING.get(found_key, "N/A")
                    if class_value and class_value != "N/A":
                        doc_class = class_value[0]
            creation_date = datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
            existing_info = existing_data.get(file_path, {})
            sharepoint_path = existing_info.get('sp')
            feedback_status = existing_info.get('fb')
            documents_to_upsert.append((
                file_path, base_name, table, desc, disc, project_trans_no,
                creation_date, rev, doc_class, sharepoint_path, feedback_status
            ))
    if documents_to_upsert:
        cursor.executemany('''
        REPLACE INTO documents (localPath, name, "table", description, discipline, transNo, dateReceived, revision, doc_class, sharepointPath, feedbackStatus)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

        # --- BẮT ĐẦU ĐOẠN CODE LÀM SẠCH DỮ LIỆU ---
        sanitized_documents = []
        for doc in documents:
            sanitized_doc = {}
            for key, value in doc.items():
                if isinstance(value, str):
                    # Sửa các ký tự surrogate không hợp lệ
                    sanitized_doc[key] = value.encode('utf-8', 'surrogateescape').decode('utf-8', 'replace')
                else:
                    sanitized_doc[key] = value
            sanitized_documents.append(sanitized_doc)
        # --- KẾT THÚC ĐOẠN CODE LÀM SẠCH DỮ LIỆU ---

        # Sử dụng dữ liệu đã được làm sạch để tạo DataFrame
        df = pd.DataFrame(sanitized_documents)
        
        columns_map = {
            "stt": "STT", "name": "Tên tài liệu", "transNo": "Trans No", "table": "Table", 
            "description": "Description", "discipline": "Bộ môn", "doc_class": "Class", 
            "dateReceived": "Ngày nhận", "revision": "Phiên bản", 
            "sharepointPath": "Đường dẫn (SharePoint)", "feedbackStatus": "Trạng thái Phản hồi"
        }
        
        cols_to_export = [key for key in columns_map if key in df.columns]
        df_export = df[cols_to_export].rename(columns=columns_map)

        writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
        df_export.to_excel(writer, sheet_name='Sheet1', index=False)
        
        workbook  = writer.book
        worksheet = writer.sheets['Sheet1']
        url_format = workbook.add_format({'font_color': 'blue', 'underline': 1})
        
        link_col_idx = len(df_export.columns)
        
        worksheet.write(0, link_col_idx, 'Đường dẫn Local') 
        # Sử dụng sanitized_documents để lấy đường dẫn
        for index, doc in enumerate(sanitized_documents):
            local_path = doc.get("localPath")
            if local_path:
                url = 'file:///' + local_path.replace('\\', '/')
                worksheet.write_url(index + 1, link_col_idx, url, string='Mở File', cell_format=url_format)

        writer.close()
        
        print(json.dumps({"success": True, "path": output_path}), flush=True)

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}), flush=True)

def export_generic_to_excel(documents_json, output_path):
    try:
        documents = json.loads(documents_json)
        if not documents:
            return print(json.dumps({"success": False, "error": "Không có dữ liệu để xuất."}))

        # --- BẮT ĐẦU ĐOẠN CODE LÀM SẠCH DỮ LIỆU ---
        sanitized_documents = []
        for doc in documents:
            sanitized_doc = {}
            for key, value in doc.items():
                if isinstance(value, str):
                    # Sửa các ký tự surrogate không hợp lệ
                    sanitized_doc[key] = value.encode('utf-8', 'surrogateescape').decode('utf-8', 'replace')
                else:
                    sanitized_doc[key] = value
            sanitized_documents.append(sanitized_doc)
        # --- KẾT THÚC ĐOẠN CODE LÀM SẠCH DỮ LIỆU ---

        # Sử dụng dữ liệu đã được làm sạch để tạo DataFrame
        df = pd.DataFrame(sanitized_documents)
        columns_map = {
            "stt": "STT", "name": "Tên tài liệu", "format": "Định dạng",
            "dateReceived": "Ngày nhận", "revision": "Phiên bản"
        }
        
        cols_to_export = [key for key in columns_map if key in df.columns]
        df_export = df[cols_to_export].rename(columns=columns_map)

        writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
        df_export.to_excel(writer, sheet_name='Sheet1', index=False)
        
        workbook  = writer.book
        worksheet = writer.sheets['Sheet1']
        url_format = workbook.add_format({'font_color': 'blue', 'underline': 1})
        
        link_col_idx = len(df_export.columns)
        
        worksheet.write(0, link_col_idx, 'Đường dẫn Local')
        # Sử dụng sanitized_documents để lấy đường dẫn
        for index, doc in enumerate(sanitized_documents):
            local_path = doc.get("localPath")
            if local_path:
                url = 'file:///' + local_path.replace('\\', '/')
                worksheet.write_url(index + 1, link_col_idx, url, string='Mở File', cell_format=url_format)
                
        writer.close()
        
        print(json.dumps({"success": True, "path": output_path}), flush=True)
        
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}), flush=True)


def get_document_stats():
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM documents')
    total_docs = cursor.fetchone()[0]
    cursor.execute('''
        SELECT discipline, COUNT(*)
        FROM documents
        GROUP BY discipline
        ORDER BY COUNT(*) DESC
    ''')
    docs_by_discipline_raw = cursor.fetchall()
    docs_by_discipline = {item[0] if item[0] else "N/A": item[1] for item in docs_by_discipline_raw}
    cursor.execute('''
        SELECT COUNT(*)
        FROM documents
        WHERE feedbackStatus IS NULL OR feedbackStatus = ''
    ''')
    docs_needing_feedback = cursor.fetchone()[0]
    conn.close()
    return {
        "total_documents": total_docs,
        "docs_by_discipline": docs_by_discipline,
        "docs_needing_feedback": docs_needing_feedback
    }

if __name__ == "__main__":
    command = sys.argv[1]
    
    if command == "init":
        init_db()
    elif command == "load_docs":
        load_all_docs()
    elif command == "load_generic":
        load_all_generic_files()
    elif command == "scan":
        scan_documents(sys.argv[2])
    elif command == "upload":
        json_data = sys.stdin.read()
        sp_path = sys.argv[2]
        upload_to_sharepoint(json_data, sp_path)
    elif command == "feedback":
        json_data = sys.stdin.read()
        feedback_path = sys.argv[2]
        subcon_path = sys.argv[3]
        process_feedback(json_data, feedback_path, subcon_path)
    elif command == "export":
        json_data = sys.stdin.read()
        output_path = sys.argv[2]
        export_to_excel(json_data, output_path)
    elif command == "scan_generic":
        scan_generic_files(sys.argv[2])
    elif command == "export_generic":
        json_data = sys.stdin.read()
        output_path = sys.argv[2]
        export_generic_to_excel(json_data, output_path)
    elif command == "get_stats":
        stats = get_document_stats()
        print(json.dumps(stats))