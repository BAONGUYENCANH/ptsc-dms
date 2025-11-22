import { describe, it, expect } from 'vitest';
import { parseMDIDocument } from './mdi-parser';

describe('parseMDIDocument', () => {
  it('should correctly parse a standard MDI row', () => {
    const rawRow = {
      'CompanyDoc.No.': 'DOC-001',
      'DocumentName': 'Test Document',
      'Rev': 'A',
      'Org': 'EE',
      'Status': 'Approved',
      'IFI\nPlan Date': '2025-10-01',
      'IFI\nActual Date': '2025-10-05',
    };

    const result = parseMDIDocument(rawRow);

    expect(result.documentNo).toBe('DOC-001');
    expect(result.title).toBe('Test Document');
    expect(result.discipline).toBe('EE');
    expect(result.planDates.ifi).toBe('2025-10-01');
    expect(result.actualDates.ifi).toBe('2025-10-05');
  });

  it('should handle missing or N/A dates gracefully', () => {
    const rawRow = {
      'CompanyDoc.No.': 'DOC-002',
      'IFI\nPlan Date': 'N/A',
      'IFR\nActual Date': null,
    };

    const result = parseMDIDocument(rawRow);

    expect(result.planDates.ifi).toBeUndefined();
    expect(result.actualDates.ifr).toBeUndefined();
  });

  it('should detect overdue status based on doc_status text', () => {
    const rawRow = {
      'CompanyDoc.No.': 'DOC-003',
      'doc_status': 'Overdue 1st Issue',
    };

    const result = parseMDIDocument(rawRow);
    expect(result.isOverdue).toBe(true);
  });
});
