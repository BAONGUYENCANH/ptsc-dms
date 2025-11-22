/**
 * Preload Script - IPC Bridge between Main and Renderer
 * Exposes secure APIs to the Renderer process
 */

import { contextBridge, ipcRenderer, IpcRendererEvent } from 'electron';

// Type definitions for MDIDocument
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
  reviewCode?: string;
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
  transNo?: string;
  dateReceived?: string;
  trnOutDate?: string;
  trnOutNo?: string;
  trnInDate?: string;
  trnInNo?: string;
  picPtsc?: string;
  picLsp?: string;
  localPath?: string;
  sharepointPath?: string;
  isOverdue?: boolean;
  isCritical?: boolean;
}

// Type definitions for API responses
interface SaveDocumentsResponse {
  success: boolean;
  count: number;
  error?: string;
}

interface GetDocumentsResponse {
  success: boolean;
  documents: MDIDocument[];
  error?: string;
}

interface DatabaseStats {
  total: number;
  lastImport?: string;
}

// Expose secure APIs to Renderer
contextBridge.exposeInMainWorld('electronAPI', {
  // ========== DATABASE APIs ==========
  
  /**
   * Save documents to SQLite database
   */
  saveDocuments: (documents: MDIDocument[]): Promise<SaveDocumentsResponse> => {
    return ipcRenderer.invoke('db:save-documents', documents);
  },

  /**
   * Get all documents from database
   */
  getDocuments: (): Promise<GetDocumentsResponse> => {
    return ipcRenderer.invoke('db:get-documents');
  },

  /**
   * Get database statistics
   */
  getDatabaseStats: (): Promise<DatabaseStats> => {
    return ipcRenderer.invoke('db:get-stats');
  },

  /**
   * Clear all documents from database
   */
  clearDocuments: (): Promise<{ success: boolean; error?: string }> => {
    return ipcRenderer.invoke('db:clear-documents');
  },

  // ========== LEGACY APIs (từ main.js cũ) ==========
  
  /**
   * Open file path in default application
   */
  openFilePath: (filePath: string): void => {
    ipcRenderer.send('open-file-path', filePath);
  },

  /**
   * Python-based APIs (legacy, có thể migrate sau)
   */
  initDatabase: () => ipcRenderer.invoke('init-database'),
  loadDocuments: () => ipcRenderer.invoke('load-documents'),
  loadGenericFiles: () => ipcRenderer.invoke('load-generic-files'),
  scanDocuments: () => ipcRenderer.invoke('scan-documents'),
  scanGenericFiles: () => ipcRenderer.invoke('scan-generic-files'),
  uploadSharepoint: (docs: any) => ipcRenderer.invoke('upload-sharepoint', docs),
  processFeedback: (docs: any) => ipcRenderer.invoke('process-feedback', docs),
  exportToExcel: (docs: any) => ipcRenderer.invoke('export-to-excel', docs),
  exportGenericToExcel: (docs: any) => ipcRenderer.invoke('export-generic-to-excel', docs),
  importFromExcel: () => ipcRenderer.invoke('import-from-excel'),
  getStats: () => ipcRenderer.invoke('get-stats'),

  /**
   * Event listeners
   */
  on: (channel: string, callback: (...args: any[]) => void): void => {
    const validChannels = ['scan-started', 'open-file-error', 'progress-update'];
    if (validChannels.includes(channel)) {
      const subscription = (_event: IpcRendererEvent, ...args: any[]) => callback(...args);
      ipcRenderer.on(channel, subscription);
    }
  },

  /**
   * Remove event listeners
   */
  removeAllListeners: (channel: string): void => {
    const validChannels = ['scan-started', 'open-file-error', 'progress-update'];
    if (validChannels.includes(channel)) {
      ipcRenderer.removeAllListeners(channel);
    }
  }
});

// Type augmentation for window object
declare global {
  interface Window {
    electronAPI: {
      // Database APIs
      saveDocuments: (documents: MDIDocument[]) => Promise<SaveDocumentsResponse>;
      getDocuments: () => Promise<GetDocumentsResponse>;
      getDatabaseStats: () => Promise<DatabaseStats>;
      clearDocuments: () => Promise<{ success: boolean; error?: string }>;
      
      // File APIs
      openFilePath: (filePath: string) => void;
      
      // Legacy Python APIs
      initDatabase: () => Promise<any>;
      loadDocuments: () => Promise<any>;
      loadGenericFiles: () => Promise<any>;
      scanDocuments: () => Promise<any>;
      scanGenericFiles: () => Promise<any>;
      uploadSharepoint: (docs: any) => Promise<any>;
      processFeedback: (docs: any) => Promise<any>;
      exportToExcel: (docs: any) => Promise<any>;
      exportGenericToExcel: (docs: any) => Promise<any>;
      importFromExcel: () => Promise<any>;
      getStats: () => Promise<any>;
      
      // Event APIs
      on: (channel: string, callback: (...args: any[]) => void) => void;
      removeAllListeners: (channel: string) => void;
    };
  }
}

console.log('[Preload] Script loaded successfully');
