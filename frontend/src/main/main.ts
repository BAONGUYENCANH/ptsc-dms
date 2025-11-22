/**
 * Main Process - Electron Entry Point
 * Handles window creation, IPC handlers, and database initialization
 */

import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
// Temporarily disabled due to better-sqlite3 build issues
// import { databaseService } from './database';

let mainWindow: BrowserWindow | null = null;

/**
 * Create the main application window
 */
function createWindow(): void {
  // Use simple path without Vietnamese characters to avoid encoding issues
  const iconPath = 'C:\\Temp\\ptsc_logo.ico';
  const iconExists = require('fs').existsSync(iconPath);
  
  console.log('[Main] Icon path:', iconPath);
  console.log('[Main] Icon exists:', iconExists);
  
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    icon: iconExists ? iconPath : undefined, // Only set icon if file exists
    title: 'PTSC Document Control',
    show: false, // Don't show until ready
    backgroundColor: '#ffffff', // White background instead of black
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      devTools: true, // Force enable DevTools
      preload: path.join(__dirname, 'preload.js') // Note: TypeScript compiled to preload.js
    }
  });
  
  // Show window when ready to avoid white flash
  mainWindow.once('ready-to-show', () => {
    console.log('[Main] Window ready to show');
    mainWindow?.maximize();
    mainWindow?.show();
  });
  
  // Set icon explicitly for Windows taskbar
  if (process.platform === 'win32' && iconExists) {
    mainWindow.setIcon(iconPath);
    console.log('[Main] Icon set for Windows taskbar');
  }

  // Load the React app
  if (process.env.NODE_ENV === 'development') {
    // Development: Load from Vite dev server
    console.log('[Main] Loading URL: http://localhost:5173');
    
    mainWindow.loadURL('http://localhost:5173').catch(err => {
      console.error('[Main] Failed to load URL:', err);
    });
    
    // Open DevTools
    mainWindow.webContents.openDevTools();
    
    // Add error handlers
    mainWindow.webContents.on('did-fail-load', (_event, errorCode, errorDescription, validatedURL) => {
      console.error('[Main] ❌ Failed to load:', {
        errorCode,
        errorDescription,
        validatedURL
      });
    });
    
    mainWindow.webContents.on('did-finish-load', () => {
      console.log('[Main] ✅ Page loaded successfully');
    });
    
    mainWindow.webContents.on('render-process-gone', (_event, details) => {
      console.error('[Main] ❌ Renderer process gone:', details);
    });
    
  } else {
    // Production: Load from dist folder
    mainWindow.loadFile(path.join(__dirname, '../../dist/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  console.log('[Main] Window created');
}

/**
 * Initialize database and IPC handlers
 */
function initializeApp(): void {
  try {
    // Initialize database - TEMPORARILY DISABLED
    // databaseService.initialize();
    console.log('[Main] Database temporarily disabled - using localStorage in renderer');

    // Register IPC handlers
    registerIPCHandlers();
    console.log('[Main] IPC handlers registered');

  } catch (error) {
    console.error('[Main] Initialization error:', error);
  }
}

/**
 * Register IPC handlers for communication with Renderer
 */
function registerIPCHandlers(): void {
  
  // ========== DATABASE HANDLERS ==========

  /**
   * Save documents to database
   */
  ipcMain.handle('db:save-documents', async (_event, documents) => {
    try {
      console.log(`[IPC] Received request to save ${documents.length} documents (DB disabled, using localStorage)`);
      // Temporarily return success - app will use localStorage
      return { success: true, count: documents.length };
    } catch (error: any) {
      console.error('[IPC] Error in save-documents:', error);
      return { success: false, count: 0, error: error.message };
    }
  });

  /**
   * Get all documents from database
   */
  ipcMain.handle('db:get-documents', async (_event) => {
    try {
      console.log('[IPC] Received request to get documents (DB disabled, returning empty)');
      // Temporarily return empty - app will use localStorage
      return { success: true, documents: [] };
    } catch (error: any) {
      console.error('[IPC] Error in get-documents:', error);
      return { success: false, documents: [], error: error.message };
    }
  });

  /**
   * Get database statistics
   */
  ipcMain.handle('db:get-stats', async (_event) => {
    try {
      console.log('[IPC] get-stats (DB disabled)');
      return { total: 0 };
    } catch (error: any) {
      console.error('[IPC] Error in get-stats:', error);
      return { total: 0 };
    }
  });

  /**
   * Clear all documents from database
   */
  ipcMain.handle('db:clear-documents', async (_event) => {
    try {
      console.log('[IPC] Received request to clear documents (DB disabled)');
      return { success: true };
    } catch (error: any) {
      console.error('[IPC] Error in clear-documents:', error);
      return { success: false, error: error.message };
    }
  });

  console.log('[Main] Database IPC handlers registered');
}

/**
 * App lifecycle events
 */
app.whenReady().then(() => {
  // Set app user model ID for Windows (required for proper taskbar icon)
  if (process.platform === 'win32') {
    app.setAppUserModelId('com.ptsc.document-control');
  }
  
  initializeApp();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    // databaseService.close(); // Disabled
    app.quit();
  }
});

app.on('before-quit', () => {
  // databaseService.close(); // Disabled
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('[Main] Uncaught exception:', error);
});

process.on('unhandledRejection', (reason) => {
  console.error('[Main] Unhandled rejection:', reason);
});

console.log('[Main] Application started');
console.log('[Main] Environment:', process.env.NODE_ENV || 'production');
console.log('[Main] App path:', app.getPath('userData'));
