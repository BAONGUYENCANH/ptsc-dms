import React, { useRef, useState } from 'react';
import * as XLSX from 'xlsx';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Upload, FileSpreadsheet, AlertCircle, Check, Loader2 } from 'lucide-react';
import { parseMDIList } from '../utils/mdi-parser';
import { MDIDocument } from '../types/mdi';
import { toast } from 'sonner';

interface ExcelImporterProps {
  onDataLoaded: (documents: MDIDocument[]) => void;
  variant?: 'default' | 'header'; // For different styles
}

export const ExcelImporter: React.FC<ExcelImporterProps> = ({ onDataLoaded, variant = 'default' }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    setLoading(true);
    setError(null);

    // Show loading toast
    const loadingToast = toast.loading('Parsing Excel file...', {
      description: `Processing ${file.name}`
    });

    try {
      const data = await file.arrayBuffer();
      const workbook = XLSX.read(data, { type: 'array' });

      // 1. Validate Sheets
      const mdiSheetName = workbook.SheetNames.find(name => name.includes('MDI_DetailStatus'));
      
      if (!mdiSheetName) {
        throw new Error('Sheet "MDI_DetailStatus" not found in the Excel file. Please use the CLEAN file.');
      }

      // 2. Parse MDI Detail Status
      const worksheet = workbook.Sheets[mdiSheetName];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);
      
      if (jsonData.length === 0) {
        throw new Error('The MDI sheet appears to be empty.');
      }

      // 3. Transform Data
      const parsedDocuments = parseMDIList(jsonData);
      
      // Debug: Check overdue detection
      const overdueCount = parsedDocuments.filter(d => d.isOverdue).length;
      const docsWithPIC = parsedDocuments.filter(d => d.picPtsc).length;
      console.log(`✅ Successfully parsed ${parsedDocuments.length} documents`);
      console.log(`   - Overdue documents: ${overdueCount}`);
      console.log(`   - Documents with PIC: ${docsWithPIC}`);
      
      // Sample overdue document for debugging
      const sampleOverdue = parsedDocuments.find(d => d.isOverdue);
      if (sampleOverdue) {
        console.log('   Sample overdue doc:', {
          documentNo: sampleOverdue.documentNo,
          picPtsc: sampleOverdue.picPtsc,
          planDates: sampleOverdue.planDates,
          actualDates: sampleOverdue.actualDates
        });
      }
      
      // Call parent callback
      onDataLoaded(parsedDocuments);

      // Dismiss loading toast and show success
      toast.success(`Successfully imported ${parsedDocuments.length} documents`, {
        id: loadingToast,
        description: `File: ${file.name}`,
        duration: 5000,
      });

    } catch (err: any) {
      console.error("Import Error:", err);
      const errorMessage = err.message || 'Failed to parse Excel file.';
      setError(errorMessage);
      setFileName(null);

      // Dismiss loading toast and show error
      toast.error('Import failed', {
        id: loadingToast,
        description: errorMessage,
        duration: 7000,
      });
      
    } finally {
      setLoading(false);
      // Reset input so same file can be selected again if needed
      if (fileInputRef.current) {
          fileInputRef.current.value = '';
      }
    }
  };

  const triggerUpload = () => {
    fileInputRef.current?.click();
  };

  // Header variant - compact button style
  if (variant === 'header') {
    return (
      <>
        <input 
          type="file" 
          accept=".xlsx, .xls, .csv" 
          ref={fileInputRef} 
          className="hidden" 
          onChange={handleFileChange}
        />
        <Button 
          onClick={triggerUpload} 
          disabled={loading}
          className="bg-white/10 backdrop-blur-sm border border-white/20 text-white hover:bg-white/20 transition-all"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Parsing...
            </>
          ) : (
            <>
              <Upload className="mr-2 h-4 w-4" />
              Import Excel
            </>
          )}
        </Button>
      </>
    );
  }

  // Default variant - card style
  return (
    <Card className="w-full border-dashed border-2 hover:bg-gray-50 transition-colors">
      <CardContent className="flex flex-col items-center justify-center p-6 text-center">
        <input 
            type="file" 
            accept=".xlsx, .xls, .csv" 
            ref={fileInputRef} 
            className="hidden" 
            onChange={handleFileChange}
        />
        
        <div className="bg-blue-100 p-3 rounded-full mb-4">
            {fileName ? <FileSpreadsheet className="h-6 w-6 text-blue-600" /> : <Upload className="h-6 w-6 text-blue-600" />}
        </div>

        <h3 className="text-lg font-semibold mb-1">
            {fileName ? 'File Loaded' : 'Import MDI Report'}
        </h3>
        
        <p className="text-sm text-muted-foreground mb-4 max-w-xs">
            {fileName 
                ? <span className="flex items-center justify-center text-green-600"><Check className="h-4 w-4 mr-1"/> {fileName}</span> 
                : 'Upload the "LSPET_MDI_Status_Report.xlsx" file to update the dashboard.'}
        </p>

        {error && (
            <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-md mb-4 flex items-center">
                <AlertCircle className="h-4 w-4 mr-2" />
                {error}
            </div>
        )}

        <Button onClick={triggerUpload} disabled={loading}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {loading ? 'Parsing...' : (fileName ? 'Upload Different File' : 'Select Excel File')}
        </Button>
      </CardContent>
    </Card>
  );
};
