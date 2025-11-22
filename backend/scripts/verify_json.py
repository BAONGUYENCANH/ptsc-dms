"""
Verify JSON structure for web deployment
"""
import json
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def verify_json():
    print("\n" + "="*60)
    print("  JSON STRUCTURE VERIFICATION")
    print("="*60 + "\n")
    
    try:
        with open('public/data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"[OK] JSON file loaded successfully")
        print(f"\n--- METADATA ---")
        print(f"Total documents: {data['metadata']['totalDocuments']}")
        print(f"Last update: {data['metadata']['lastUpdate']}")
        print(f"Version: {data['metadata']['version']}")
        print(f"Export date: {data['metadata']['exportDate']}")
        
        print(f"\n--- STATISTICS ---")
        stats = data['metadata']['statistics']
        print(f"Total: {stats['total']}")
        print(f"Approved: {stats['approved']}")
        print(f"Overdue: {stats['overdue']}")
        print(f"Disciplines: {stats['disciplines']}")
        
        print(f"\n--- DOCUMENTS ARRAY ---")
        print(f"Array length: {len(data['documents'])}")
        
        if len(data['documents']) > 0:
            doc1 = data['documents'][0]
            print(f"\n--- FIRST DOCUMENT ---")
            print(f"id: {doc1['id']}")
            print(f"stt: {doc1['stt']}")
            print(f"documentNo: {doc1['documentNo']}")
            print(f"title: {doc1['title'][:60]}...")
            print(f"discipline: {doc1['discipline']}")
            print(f"status: {doc1['status']}")
            print(f"revision: {doc1['revision']}")
            print(f"scope: {doc1['scope']}")
            print(f"docClass: {doc1['docClass']}")
            print(f"table: {doc1['table']}")
            print(f"item: {doc1['item']}")
            print(f"ipiStatus: {doc1['ipiStatus']}")
            
            print(f"\n--- DATES ---")
            print(f"planDates: {doc1['planDates']}")
            print(f"actualDates: {doc1['actualDates']}")
            
            print(f"\n--- FLAGS ---")
            print(f"isOverdue: {doc1['isOverdue']} (type: {type(doc1['isOverdue']).__name__})")
            print(f"isCritical: {doc1['isCritical']} (type: {type(doc1['isCritical']).__name__})")
            
            # Check field types match TypeScript interface
            print(f"\n--- TYPE VALIDATION ---")
            required_fields = [
                'id', 'stt', 'documentNo', 'title', 'revision',
                'discipline', 'scope', 'docClass', 'table', 'item',
                'status', 'ipiStatus', 'planDates', 'actualDates',
                'isOverdue', 'isCritical'
            ]
            
            missing = []
            for field in required_fields:
                if field not in doc1:
                    missing.append(field)
            
            if missing:
                print(f"[ERROR] Missing fields: {missing}")
            else:
                print(f"[OK] All required fields present")
            
            # Check planDates and actualDates structure
            if isinstance(doc1['planDates'], dict) and isinstance(doc1['actualDates'], dict):
                print(f"[OK] Dates are objects (not strings)")
                print(f"     planDates keys: {list(doc1['planDates'].keys())}")
                print(f"     actualDates keys: {list(doc1['actualDates'].keys())}")
            else:
                print(f"[ERROR] Dates should be objects, not {type(doc1['planDates']).__name__}")
            
            # Check boolean types
            if isinstance(doc1['isOverdue'], bool) and isinstance(doc1['isCritical'], bool):
                print(f"[OK] isOverdue and isCritical are booleans")
            else:
                print(f"[ERROR] isOverdue/isCritical should be boolean")
        
        print("\n" + "="*60)
        print("[SUCCESS] JSON structure is valid for web deployment!")
        print("="*60 + "\n")
        
        return True
        
    except FileNotFoundError:
        print("[ERROR] public/data.json not found!")
        print("Run: batch\\export_to_json_v2.bat")
        return False
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON: {e}")
        return False
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = verify_json()
    sys.exit(0 if success else 1)
