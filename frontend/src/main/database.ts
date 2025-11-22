/**
 * Database Service - SQLite Integration
 * Handles all database operations for MDI documents persistence
 */

import Database from 'better-sqlite3';
import { app } from 'electron';
import * as path from 'path';
import * as fs from 'fs';

// Type definition matching MDIDocument interface
interface MDIDocument {
  id: string;
  stt: number;
  documentNo: string;
  title: string;
  revision: string;
  discipline: string;
  scope: string;
  docClass: string;
  table: string;
  item: string;
  status: string;
  ipiStatus: string;
  reviewCode: string;
  planDates: {
    ifi?: string;
    ifr?: string;
    ifa?: string;
    ifc?: string;
    iff?: string;
  };
  actualDates: {
    ifi?: string;
    ifr?: string;
    ifa?: string;
    ifc?: string;
    iff?: string;
  };
  targetMitigationDate?: string;
  transNo: string;
  dateReceived?: string;
  trnOutDate?: string;
  trnOutNo?: string;
  trnInDate?: string;
  trnInNo?: string;
  picPtsc?: string;
  picLsp?: string;
  localPath?: string;
  sharepointPath?: string;
  isOverdue: boolean;
  isCritical: boolean;
}

export class DatabaseService {
  private db: Database.Database | null = null;
  private dbPath: string;

  constructor() {
    // Store database in userData directory (persists across updates)
    const userDataPath = app.getPath('userData');
    this.dbPath = path.join(userDataPath, 'mdi_data.db');
    
    console.log('[Database] DB Path:', this.dbPath);
  }

  /**
   * Initialize database connection and create tables if not exists
   */
  initialize(): void {
    try {
      // Ensure userData directory exists
      const userDataPath = app.getPath('userData');
      if (!fs.existsSync(userDataPath)) {
        fs.mkdirSync(userDataPath, { recursive: true });
      }

      // Open database
      this.db = new Database(this.dbPath);
      
      // Enable WAL mode for better concurrency
      this.db.pragma('journal_mode = WAL');
      
      // Create documents table
      this.createTables();
      
      console.log('[Database] Initialized successfully');
    } catch (error) {
      console.error('[Database] Initialization error:', error);
      throw error;
    }
  }

  /**
   * Create database tables
   */
  private createTables(): void {
    if (!this.db) throw new Error('Database not initialized');

    const createTableSQL = `
      CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        stt INTEGER,
        documentNo TEXT NOT NULL,
        title TEXT,
        revision TEXT,
        discipline TEXT,
        scope TEXT,
        docClass TEXT,
        table_name TEXT,
        item TEXT,
        status TEXT,
        ipiStatus TEXT,
        reviewCode TEXT,
        
        -- Plan Dates (JSON stored as TEXT)
        ifi_plan_date TEXT,
        ifr_plan_date TEXT,
        ifa_plan_date TEXT,
        ifc_plan_date TEXT,
        iff_plan_date TEXT,
        
        -- Actual Dates
        ifi_actual_date TEXT,
        ifr_actual_date TEXT,
        ifa_actual_date TEXT,
        ifc_actual_date TEXT,
        iff_actual_date TEXT,
        
        targetMitigationDate TEXT,
        transNo TEXT,
        dateReceived TEXT,
        trnOutDate TEXT,
        trnOutNo TEXT,
        trnInDate TEXT,
        trnInNo TEXT,
        picPtsc TEXT,
        picLsp TEXT,
        localPath TEXT,
        sharepointPath TEXT,
        isOverdue INTEGER DEFAULT 0,
        isCritical INTEGER DEFAULT 0,
        
        -- Metadata
        import_date TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
      );
    `;

    this.db.exec(createTableSQL);

    // Create indexes for performance
    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_documentNo ON documents(documentNo);
      CREATE INDEX IF NOT EXISTS idx_discipline ON documents(discipline);
      CREATE INDEX IF NOT EXISTS idx_status ON documents(status);
      CREATE INDEX IF NOT EXISTS idx_isOverdue ON documents(isOverdue);
    `);

    console.log('[Database] Tables created successfully');
  }

  /**
   * Save documents to database (REPLACE existing)
   * Uses transaction for performance
   */
  saveDocuments(documents: MDIDocument[]): { success: boolean; count: number; error?: string } {
    if (!this.db) {
      return { success: false, count: 0, error: 'Database not initialized' };
    }

    try {
      console.log(`[Database] Saving ${documents.length} documents...`);

      const insertSQL = this.db.prepare(`
        INSERT OR REPLACE INTO documents (
          id, stt, documentNo, title, revision, discipline, scope, docClass,
          table_name, item, status, ipiStatus, reviewCode,
          ifi_plan_date, ifr_plan_date, ifa_plan_date, ifc_plan_date, iff_plan_date,
          ifi_actual_date, ifr_actual_date, ifa_actual_date, ifc_actual_date, iff_actual_date,
          targetMitigationDate, transNo, dateReceived, trnOutDate, trnOutNo,
          trnInDate, trnInNo, picPtsc, picLsp, localPath, sharepointPath,
          isOverdue, isCritical, updated_at
        ) VALUES (
          @id, @stt, @documentNo, @title, @revision, @discipline, @scope, @docClass,
          @table, @item, @status, @ipiStatus, @reviewCode,
          @ifi_plan, @ifr_plan, @ifa_plan, @ifc_plan, @iff_plan,
          @ifi_actual, @ifr_actual, @ifa_actual, @ifc_actual, @iff_actual,
          @targetMitigationDate, @transNo, @dateReceived, @trnOutDate, @trnOutNo,
          @trnInDate, @trnInNo, @picPtsc, @picLsp, @localPath, @sharepointPath,
          @isOverdue, @isCritical, datetime('now')
        )
      `);

      // Use transaction for bulk insert (much faster)
      const insertMany = this.db.transaction((docs: MDIDocument[]) => {
        for (const doc of docs) {
          insertSQL.run({
            id: doc.id,
            stt: doc.stt,
            documentNo: doc.documentNo,
            title: doc.title,
            revision: doc.revision,
            discipline: doc.discipline,
            scope: doc.scope,
            docClass: doc.docClass,
            table: doc.table,
            item: doc.item,
            status: doc.status,
            ipiStatus: doc.ipiStatus,
            reviewCode: doc.reviewCode,
            ifi_plan: doc.planDates?.ifi || null,
            ifr_plan: doc.planDates?.ifr || null,
            ifa_plan: doc.planDates?.ifa || null,
            ifc_plan: doc.planDates?.ifc || null,
            iff_plan: doc.planDates?.iff || null,
            ifi_actual: doc.actualDates?.ifi || null,
            ifr_actual: doc.actualDates?.ifr || null,
            ifa_actual: doc.actualDates?.ifa || null,
            ifc_actual: doc.actualDates?.ifc || null,
            iff_actual: doc.actualDates?.iff || null,
            targetMitigationDate: doc.targetMitigationDate || null,
            transNo: doc.transNo,
            dateReceived: doc.dateReceived || null,
            trnOutDate: doc.trnOutDate || null,
            trnOutNo: doc.trnOutNo || null,
            trnInDate: doc.trnInDate || null,
            trnInNo: doc.trnInNo || null,
            picPtsc: doc.picPtsc || null,
            picLsp: doc.picLsp || null,
            localPath: doc.localPath || null,
            sharepointPath: doc.sharepointPath || null,
            isOverdue: doc.isOverdue ? 1 : 0,
            isCritical: doc.isCritical ? 1 : 0
          });
        }
      });

      insertMany(documents);

      console.log(`[Database] ✅ Saved ${documents.length} documents successfully`);
      return { success: true, count: documents.length };

    } catch (error: any) {
      console.error('[Database] Error saving documents:', error);
      return { success: false, count: 0, error: error.message };
    }
  }

  /**
   * Get all documents from database
   */
  getDocuments(): MDIDocument[] {
    if (!this.db) {
      console.error('[Database] Not initialized');
      return [];
    }

    try {
      const selectSQL = this.db.prepare('SELECT * FROM documents ORDER BY stt ASC');
      const rows = selectSQL.all() as any[];

      console.log(`[Database] Retrieved ${rows.length} documents`);

      // Transform database rows back to MDIDocument format
      const documents: MDIDocument[] = rows.map((row) => ({
        id: row.id,
        stt: row.stt,
        documentNo: row.documentNo,
        title: row.title,
        revision: row.revision,
        discipline: row.discipline,
        scope: row.scope,
        docClass: row.docClass,
        table: row.table_name,
        item: row.item,
        status: row.status,
        ipiStatus: row.ipiStatus,
        reviewCode: row.reviewCode,
        planDates: {
          ifi: row.ifi_plan_date,
          ifr: row.ifr_plan_date,
          ifa: row.ifa_plan_date,
          ifc: row.ifc_plan_date,
          iff: row.iff_plan_date
        },
        actualDates: {
          ifi: row.ifi_actual_date,
          ifr: row.ifr_actual_date,
          ifa: row.ifa_actual_date,
          ifc: row.ifc_actual_date,
          iff: row.iff_actual_date
        },
        targetMitigationDate: row.targetMitigationDate,
        transNo: row.transNo,
        dateReceived: row.dateReceived,
        trnOutDate: row.trnOutDate,
        trnOutNo: row.trnOutNo,
        trnInDate: row.trnInDate,
        trnInNo: row.trnInNo,
        picPtsc: row.picPtsc,
        picLsp: row.picLsp,
        localPath: row.localPath,
        sharepointPath: row.sharepointPath,
        isOverdue: row.isOverdue === 1,
        isCritical: row.isCritical === 1
      }));

      return documents;
    } catch (error) {
      console.error('[Database] Error getting documents:', error);
      return [];
    }
  }

  /**
   * Get database statistics
   */
  getStats(): { total: number; lastImport?: string } {
    if (!this.db) return { total: 0 };

    try {
      const countResult = this.db.prepare('SELECT COUNT(*) as total FROM documents').get() as { total: number };
      const lastImportResult = this.db.prepare('SELECT MAX(import_date) as lastImport FROM documents').get() as { lastImport: string };

      return {
        total: countResult.total,
        lastImport: lastImportResult.lastImport
      };
    } catch (error) {
      console.error('[Database] Error getting stats:', error);
      return { total: 0 };
    }
  }

  /**
   * Clear all documents from database
   */
  clearDocuments(): { success: boolean; error?: string } {
    if (!this.db) {
      return { success: false, error: 'Database not initialized' };
    }

    try {
      this.db.prepare('DELETE FROM documents').run();
      console.log('[Database] Cleared all documents');
      return { success: true };
    } catch (error: any) {
      console.error('[Database] Error clearing documents:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Close database connection
   */
  close(): void {
    if (this.db) {
      this.db.close();
      this.db = null;
      console.log('[Database] Connection closed');
    }
  }
}

// Export singleton instance
export const databaseService = new DatabaseService();
