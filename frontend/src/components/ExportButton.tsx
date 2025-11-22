/**
 * ExportButton Component
 * Exports filtered/displayed documents to Excel file
 */

import React, { useState } from 'react';
import * as XLSX from 'xlsx';
import { Button } from '@/components/ui/button';
import { Download, Loader2 } from 'lucide-react';
import { MDIDocument } from '../types/mdi';
import { toast } from 'sonner';

interface ExportButtonProps {
  documents: MDIDocument[];
  fileName?: string;
  disabled?: boolean;
}

export const ExportButton: React.FC<ExportButtonProps> = ({ 
  documents, 
  fileName = 'MDI_Export',
  disabled = false 
}) => {
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    if (documents.length === 0) {
      toast.warning('No data to export', {
        description: 'Please import documents first or adjust your filters.'
      });
      return;
    }

    setExporting(true);

    const exportingToast = toast.loading('Exporting to Excel...', {
      description: `Preparing ${documents.length} documents`
    });

    try {
      // Transform MDIDocument data to flat structure for Excel
      const exportData = documents.map((doc, index) => ({
        'STT': index + 1,
        'Document No': doc.documentNo,
        'Title': doc.title,
        'Revision': doc.revision,
        'Discipline': doc.discipline,
        'Scope': doc.scope,
        'Class': doc.docClass,
        'Table': doc.table,
        'Item': doc.item,
        'Status': doc.status,
        'IPI Status': doc.ipiStatus || '',
        'Review Code': doc.reviewCode || '',
        
        // Plan Dates
        'IFI Plan Date': doc.planDates?.ifi || '',
        'IFR Plan Date': doc.planDates?.ifr || '',
        'IFA Plan Date': doc.planDates?.ifa || '',
        'IFC Plan Date': doc.planDates?.ifc || '',
        'IFF Plan Date': doc.planDates?.iff || '',
        
        // Actual Dates
        'IFI Actual Date': doc.actualDates?.ifi || '',
        'IFR Actual Date': doc.actualDates?.ifr || '',
        'IFA Actual Date': doc.actualDates?.ifa || '',
        'IFC Actual Date': doc.actualDates?.ifc || '',
        'IFF Actual Date': doc.actualDates?.iff || '',
        
        'Target Mitigation Date': doc.targetMitigationDate || '',
        'Trans No': doc.transNo,
        'Date Received': doc.dateReceived || '',
        'TRN Out Date': doc.trnOutDate || '',
        'TRN Out No': doc.trnOutNo || '',
        'TRN In Date': doc.trnInDate || '',
        'TRN In No': doc.trnInNo || '',
        'PIC PTSC': doc.picPtsc || '',
        'PIC LSP': doc.picLsp || '',
        'Local Path': doc.localPath || '',
        'SharePoint Path': doc.sharepointPath || '',
        'Is Overdue': doc.isOverdue ? 'Yes' : 'No',
        'Is Critical': doc.isCritical ? 'Yes' : 'No',
      }));

      // Create workbook
      const worksheet = XLSX.utils.json_to_sheet(exportData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Documents');

      // Auto-size columns
      const maxWidth = 50;
      const columnWidths = Object.keys(exportData[0] || {}).map(key => ({
        wch: Math.min(
          maxWidth,
          Math.max(
            key.length,
            ...exportData.map(row => String(row[key as keyof typeof row] || '').length)
          )
        )
      }));
      worksheet['!cols'] = columnWidths;

      // Generate file name with timestamp
      const timestamp = new Date().toISOString().split('T')[0];
      const fullFileName = `${fileName}_${timestamp}.xlsx`;

      // Write file
      XLSX.writeFile(workbook, fullFileName);

      // Success toast
      toast.success(`Successfully exported ${documents.length} documents`, {
        id: exportingToast,
        description: `File saved: ${fullFileName}`,
        duration: 5000,
      });

    } catch (error: any) {
      console.error('Export error:', error);
      
      toast.error('Export failed', {
        id: exportingToast,
        description: error.message || 'Failed to export documents to Excel',
        duration: 7000,
      });
    } finally {
      setExporting(false);
    }
  };

  return (
    <Button 
      onClick={handleExport} 
      disabled={disabled || exporting || documents.length === 0}
      variant="outline"
      size="sm"
    >
      {exporting ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Exporting...
        </>
      ) : (
        <>
          <Download className="mr-2 h-4 w-4" />
          Export to Excel ({documents.length})
        </>
      )}
    </Button>
  );
};
