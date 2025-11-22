/**
 * Data Loader Utility
 * Load documents from static JSON file for web deployment
 */

import { MDIDocument } from '@/types/mdi';

export interface DataExport {
  metadata: {
    exportDate: string;
    totalDocuments: number;
    lastUpdate: string;
    version: string;
    statistics: {
      total: number;
      approved: number;
      overdue: number;
      disciplines: number;
    };
  };
  documents: MDIDocument[];
}

/**
 * Load documents from static JSON file
 * Used for static web deployment (GitHub Pages)
 */
export async function loadDocumentsFromJSON(): Promise<MDIDocument[]> {
  try {
    console.log('[DataLoader] Loading documents from static JSON...');
    
    const response = await fetch('/data.json');
    
    if (!response.ok) {
      throw new Error(`Failed to fetch data.json: ${response.status}`);
    }
    
    const data: DataExport = await response.json();
    
    console.log('[DataLoader] ✅ Loaded data:');
    console.log(`  - Total: ${data.metadata.totalDocuments} documents`);
    console.log(`  - Export Date: ${data.metadata.exportDate}`);
    console.log(`  - Approved: ${data.metadata.statistics.approved}`);
    console.log(`  - Overdue: ${data.metadata.statistics.overdue}`);
    
    return data.documents;
    
  } catch (error) {
    console.error('[DataLoader] ❌ Failed to load JSON:', error);
    
    // Return empty array on error
    return [];
  }
}

/**
 * Get metadata from JSON export
 */
export async function getExportMetadata(): Promise<DataExport['metadata'] | null> {
  try {
    const response = await fetch('/data.json');
    if (!response.ok) return null;
    
    const data: DataExport = await response.json();
    return data.metadata;
    
  } catch (error) {
    console.error('[DataLoader] Failed to get metadata:', error);
    return null;
  }
}

/**
 * Check if running in static mode (web) or Electron
 */
export function isStaticMode(): boolean {
  return typeof window !== 'undefined' && !window.electronAPI;
}

/**
 * Check if data.json is available
 */
export async function isDataAvailable(): Promise<boolean> {
  try {
    const response = await fetch('/data.json', { method: 'HEAD' });
    return response.ok;
  } catch {
    return false;
  }
}
