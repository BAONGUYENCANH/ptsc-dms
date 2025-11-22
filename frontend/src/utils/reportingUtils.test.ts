import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest';
import { getOverdueItems, getWeeklySubmissionItems } from './reportingUtils';
import { MDIDocument } from '../types/mdi';

describe('Reporting Utils', () => {
  // Mock today as 2025-11-20
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2025-11-20')); 
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  const mockDocs: MDIDocument[] = [
    {
      id: '1',
      stt: 1,
      documentNo: 'DOC-OK',
      status: 'Approved',
      planDates: { ifi: '2025-11-25' },
      actualDates: {},
      discipline: 'EE',
      scope: 'PTSC',
      docClass: '1',
      table: '1',
      item: '1',
      title: 'Doc 1',
      revision: '0',
      ipiStatus: '',
      isOverdue: false
    },
    {
      id: '2',
      stt: 2,
      documentNo: 'DOC-OVERDUE',
      status: 'Not yet issued',
      planDates: { ifi: '2025-11-10' },
      actualDates: {},
      discipline: 'EE',
      scope: 'PTSC',
      docClass: '1',
      table: '1',
      item: '1',
      title: 'Doc 2',
      revision: '0',
      ipiStatus: '',
      isOverdue: false
    },
    {
        id: '3',
        stt: 3,
        documentNo: 'DOC-DONE-LATE',
        status: 'Approved',
        planDates: { ifi: '2025-11-10' },
        actualDates: { ifi: '2025-11-12' },
        discipline: 'EE',
        scope: 'PTSC',
        docClass: '1',
        table: '1',
        item: '1',
        title: 'Doc 3',
        revision: '0',
        ipiStatus: '',
        isOverdue: false
    }
  ];

  it('getOverdueItems should return items with past plan date and no actual date', () => {
    const result = getOverdueItems(mockDocs);
    expect(result).toHaveLength(1);
    expect(result[0].documentNo).toBe('DOC-OVERDUE');
  });

  it('getWeeklySubmissionItems should return items planned or actualized this week', () => {
     // Current week of Nov 20, 2025 is Nov 17 - Nov 23
     const weeklyDocs: MDIDocument[] = [
         { ...mockDocs[0], planDates: { ifi: '2025-11-21' } }, // Friday (In week)
         { ...mockDocs[0], planDates: { ifi: '2025-11-25' } }, // Next week (Out)
     ];
     
     const result = getWeeklySubmissionItems(weeklyDocs);
     expect(result).toHaveLength(1);
     expect(result[0].planDates.ifi).toBe('2025-11-21');
  });
});
