"""
PTSC Document Management System - Backend API
Flask server for handling Excel import, database operations
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
from datetime import datetime
import sqlite3
from werkzeug.utils import secure_filename
import sys

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from export_db_to_json_v2 import export_database_to_json
from excel_importer import process_excel_file

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
UPLOAD_FOLDER = 'uploads'
DATABASE_PATH = 'project_data.db'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================
# API Routes
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': os.path.exists(DATABASE_PATH)
    })

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Get all documents from database"""
    try:
        # Export database to JSON format
        data = export_database_to_json(DATABASE_PATH, return_dict=True)
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload and process Excel file"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Only .xlsx and .xls allowed'
            }), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Process Excel file and import to database
        result = process_excel_file(filepath, DATABASE_PATH)
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': f'Imported {result["count"]} documents',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/export', methods=['GET'])
def export_json():
    """Export database to JSON file"""
    try:
        output_path = 'export.json'
        export_database_to_json(DATABASE_PATH, output_path)
        
        return send_file(
            output_path,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'ptsc_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Total documents
        cursor.execute("SELECT COUNT(*) FROM documents")
        total = cursor.fetchone()[0]
        
        # Overdue count
        cursor.execute("SELECT COUNT(*) FROM documents WHERE is_overdue = 1")
        overdue = cursor.fetchone()[0]
        
        # By discipline
        cursor.execute("""
            SELECT discipline, COUNT(*) as count 
            FROM documents 
            GROUP BY discipline 
            ORDER BY count DESC 
            LIMIT 5
        """)
        disciplines = [{'discipline': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # By status
        cursor.execute("""
            SELECT doc_status, COUNT(*) as count 
            FROM documents 
            GROUP BY doc_status 
            ORDER BY count DESC 
            LIMIT 5
        """)
        statuses = [{'status': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'overdue': overdue,
                'disciplines': disciplines,
                'statuses': statuses
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# Main
# ============================================

if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development'
    )
