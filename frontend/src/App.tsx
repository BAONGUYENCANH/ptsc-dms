import { useState, useEffect } from 'react';
import { DashboardView } from './components/DashboardView';
import { DocumentTable } from './components/DocumentTable';
import { AppHeader } from './components/AppHeader';
import { QuickReports } from './components/QuickReports';
import { MDIDocument } from './types/mdi';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAppStore } from './store/useAppStore';
import { Toaster } from 'sonner';
import { loadDocumentsFromJSON, getExportMetadata } from './utils/dataLoader';

const App = () => {
  const [documents, setDocuments] = useState<MDIDocument[]>([]);
  const [view, setView] = useState<'dashboard' | 'list'>('dashboard');
  const [loading, setLoading] = useState(true);
  const [dbStats, setDbStats] = useState<{ total: number; lastImport?: string } | null>(null);
  
  // Subscribe to store to auto-switch views if a filter is applied from Dashboard
  const filters = useAppStore((state) => state.filters);
  
  // Auto-load documents from database on app startup
  useEffect(() => {
    loadDocumentsFromDB();
  }, []);
  
  useEffect(() => {
      // If a filter is applied (e.g. clicking a chart bar), switch to list view automatically
      if (filters.discipline || filters.status || filters.isOverdue) {
          setView('list');
      }
  }, [filters]);

  /**
   * Load documents from database or static JSON
   */
  const loadDocumentsFromDB = async () => {
    try {
      setLoading(true);
      
      // Check if running in Electron
      if (typeof window !== 'undefined' && window.electronAPI) {
        console.log('[App] Running in Electron mode - loading from database...');
        
        const response = await window.electronAPI.getDocuments();
        
        if (response.success && response.documents) {
          setDocuments(response.documents);
          console.log(`[App] ✅ Loaded ${response.documents.length} documents from DB`);
          
          // Get database stats
          const stats = await window.electronAPI.getDatabaseStats();
          setDbStats(stats);
        } else {
          console.log('[App] No documents in database');
          setDocuments([]);
        }
      } else {
        // Browser mode - load from static JSON
        console.log('[App] Running in browser mode - loading from static JSON...');
        
        const docs = await loadDocumentsFromJSON();
        setDocuments(docs);
        
        if (docs.length > 0) {
          console.log(`[App] ✅ Loaded ${docs.length} documents from JSON`);
          
          // Get metadata for stats
          const metadata = await getExportMetadata();
          if (metadata) {
            setDbStats({
              total: metadata.totalDocuments,
              lastImport: metadata.lastUpdate
            });
          }
        } else {
          console.log('[App] No data found in JSON file');
        }
      }
    } catch (error) {
      console.error('[App] Error loading documents:', error);
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle Excel import and save to database
   */
  const handleDataLoaded = async (newDocuments: MDIDocument[]) => {
    try {
      // Update UI immediately
      setDocuments(newDocuments);
      
      // Save to database if running in Electron
      if (typeof window !== 'undefined' && window.electronAPI) {
        console.log(`[App] Saving ${newDocuments.length} documents to database...`);
        
        const response = await window.electronAPI.saveDocuments(newDocuments);
        
        if (response.success) {
          console.log(`[App] ✅ Saved ${response.count} documents to DB`);
          
          // Update stats
          const stats = await window.electronAPI.getDatabaseStats();
          setDbStats(stats);
        } else {
          console.error('[App] Failed to save documents:', response.error);
        }
      }
    } catch (error) {
      console.error('[App] Error saving documents to DB:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* New Professional Header */}
      <AppHeader 
        onDataLoaded={handleDataLoaded}
        documentCount={documents.length}
        dbStats={dbStats}
      />

      <div className="p-6">
        <div className="grid grid-cols-12 gap-6">
        {/* Sidebar / Quick Actions */}
        <aside className="col-span-12 md:col-span-3 lg:col-span-2 space-y-6">
            <QuickReports documents={documents} />
            
            {/* Copyright Section */}
            <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
                <div className="text-xs text-gray-500 leading-relaxed space-y-2">
                    <p className="font-semibold text-gray-700">© Copyright by</p>
                    <p className="italic">Nguyễn Thị Thanh Hương</p>
                    <p className="text-gray-600">PTSC Industrial Division</p>
                    <div className="pt-2 border-t border-gray-200">
                        <p className="font-medium text-gray-700">Hotline:</p>
                        <p className="text-blue-600 font-semibold">0934 914 173</p>
                    </div>
                </div>
            </div>
        </aside>

        {/* Main Content Area */}
        <main className="col-span-12 md:col-span-9 lg:col-span-10">
             <Tabs value={view} onValueChange={(v) => setView(v as any)} className="space-y-4">
                <TabsList>
                    <TabsTrigger value="dashboard">Dashboard Overview</TabsTrigger>
                    <TabsTrigger value="list">Document Master List</TabsTrigger>
                </TabsList>

                <TabsContent value="dashboard" className="space-y-4">
                    {loading ? (
                         <div className="flex h-[400px] items-center justify-center rounded-lg border border-dashed bg-white">
                            <div className="text-center">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                                <h3 className="mt-2 text-lg font-semibold">Loading Data...</h3>
                                <p className="text-gray-500">Please wait while we load documents from database</p>
                            </div>
                        </div>
                    ) : documents.length > 0 ? (
                        <DashboardView documents={documents} />
                    ) : (
                         <div className="flex h-[400px] items-center justify-center rounded-lg border border-dashed bg-white">
                            <div className="text-center">
                                <h3 className="mt-2 text-lg font-semibold">No Data Loaded</h3>
                                <p className="text-gray-500">Upload an Excel file to view the dashboard.</p>
                            </div>
                        </div>
                    )}
                </TabsContent>

                <TabsContent value="list" className="space-y-4">
                     <DocumentTable documents={documents} />
                </TabsContent>
            </Tabs>
        </main>
        </div>
      </div>
      
      {/* Toast Notifications */}
      <Toaster position="top-right" richColors />
    </div>
  );
};

export default App;
