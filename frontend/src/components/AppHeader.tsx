import { Calendar } from 'lucide-react';
import { ExcelImporter } from './ExcelImporter';
import { MDIDocument } from '../types/mdi';

interface AppHeaderProps {
  onDataLoaded: (docs: MDIDocument[]) => void;
  documentCount: number;
  dbStats?: { total: number; lastImport?: string } | null;
}

export const AppHeader: React.FC<AppHeaderProps> = ({ 
  onDataLoaded, 
  documentCount,
  dbStats 
}) => {
  // Get current date
  const currentDate = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  return (
    <div className="bg-gradient-to-r text-white shadow-lg" style={{ background: 'linear-gradient(to right, #0078C9, #233A7A)' }}>
      <div className="container mx-auto px-6 py-4">
        {/* Top Row: Logo + Title + Actions */}
        <div className="flex items-center justify-between">
          {/* Left: PTSC Logo + Title */}
          <div className="flex items-center gap-4">
            <div className="bg-white/10 backdrop-blur-sm p-2 rounded-lg">
              <img 
                src="/ptsc_logo.ico" 
                alt="PTSC Logo" 
                className="h-10 w-10"
                onError={(e) => {
                  // Fallback to icon if image not found
                  e.currentTarget.style.display = 'none';
                  const parent = e.currentTarget.parentElement;
                  if (parent) {
                    const icon = document.createElement('div');
                    icon.innerHTML = '<svg class="h-10 w-10 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M9 2L7.17 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2h-3.17L15 2H9zm3 15c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z"/></svg>';
                    parent.appendChild(icon);
                  }
                }}
              />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">
                PTSC Document Control
              </h1>
              <p className="text-blue-100 text-sm flex items-center gap-2 mt-1">
                <Calendar className="h-3 w-3" />
                {currentDate}
              </p>
            </div>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-3">
            {/* Import Button - Header Variant */}
            <ExcelImporter onDataLoaded={onDataLoaded} variant="header" />
            
            {/* Stats Badge */}
            {documentCount > 0 && (
              <div className="bg-white/10 backdrop-blur-sm px-4 py-2 rounded-lg border border-white/20">
                <div className="text-xs text-blue-100">Total Documents</div>
                <div className="text-2xl font-bold">{documentCount.toLocaleString()}</div>
              </div>
            )}
          </div>
        </div>

        {/* Bottom Row: Stats (if available) */}
        {dbStats && dbStats.total > 0 && (
          <div className="mt-3 pt-3 border-t border-white/20">
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-blue-100">Database Active</span>
              </div>
              <div className="text-blue-100">
                <span className="font-medium">{dbStats.total}</span> documents stored
              </div>
              {dbStats.lastImport && (
                <div className="text-blue-100">
                  Last import: <span className="font-medium">{new Date(dbStats.lastImport).toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
