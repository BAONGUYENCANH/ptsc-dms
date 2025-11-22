/**
 * Export SQLite database to JSON for GitHub Pages
 * Run this script from Electron app or Node.js environment
 */

const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');

const DB_PATH = path.join(__dirname, '..', 'project_data.db');
const OUTPUT_PATH = path.join(__dirname, '..', 'public', 'data.json');

try {
  // Open database
  const db = new Database(DB_PATH, { readonly: true });

  // Get all documents
  const documents = db.prepare(`
    SELECT * FROM mdi_documents ORDER BY stt ASC
  `).all();

  // Get metadata
  const stats = db.prepare(`
    SELECT
      COUNT(*) as total,
      MAX(updated_at) as lastUpdate
    FROM mdi_documents
  `).get();

  // Prepare export data
  const exportData = {
    metadata: {
      exportDate: new Date().toISOString(),
      totalDocuments: stats.total,
      lastUpdate: stats.lastUpdate,
      version: '1.0.0'
    },
    documents: documents.map(doc => ({
      id: doc.id,
      stt: doc.stt,
      documentNo: doc.document_no,
      status: doc.status,
      planDates: JSON.parse(doc.plan_dates || '{}'),
      actualDates: JSON.parse(doc.actual_dates || '{}'),
      discipline: doc.discipline,
      scope: doc.scope,
      docClass: doc.doc_class,
      table: doc.table_name,
      item: doc.item,
      title: doc.title,
      revision: doc.revision,
      ipiStatus: doc.ipi_status,
      isOverdue: doc.is_overdue === 1
    }))
  };

  // Write to JSON file
  fs.writeFileSync(
    OUTPUT_PATH,
    JSON.stringify(exportData, null, 2),
    'utf8'
  );

  console.log(`✅ Exported ${stats.total} documents to ${OUTPUT_PATH}`);
  console.log(`📊 Last update: ${stats.lastUpdate}`);

  db.close();

} catch (error) {
  console.error('❌ Export failed:', error.message);
  process.exit(1);
}
