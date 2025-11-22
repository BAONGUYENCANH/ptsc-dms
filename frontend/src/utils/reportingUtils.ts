import { MDIDocument } from '../types/mdi';
import dayjs from 'dayjs';
import isBetween from 'dayjs/plugin/isBetween';
import isoWeek from 'dayjs/plugin/isoWeek';

dayjs.extend(isBetween);
dayjs.extend(isoWeek);

/**
 * Returns items where Actual Date is missing AND Plan Date < Today
 * Focusing mainly on 'IFI' or 'IFR' as primary milestones for now.
 */
export const getOverdueItems = (documents: MDIDocument[]): MDIDocument[] => {
  const today = dayjs();
  
  return documents.filter(doc => {
    // Check IFI Overdue
    if (doc.planDates.ifi && !doc.actualDates.ifi) {
        if (dayjs(doc.planDates.ifi).isBefore(today, 'day')) return true;
    }
    // Check IFR Overdue (if IFI is done)
    if (doc.planDates.ifr && !doc.actualDates.ifr) {
        if (dayjs(doc.planDates.ifr).isBefore(today, 'day')) return true;
    }
    return false;
  });
};

/**
 * Returns items where Plan or Actual submission falls within the current week (Mon-Sun).
 */
export const getWeeklySubmissionItems = (documents: MDIDocument[]): MDIDocument[] => {
  const startOfWeek = dayjs().startOf('isoWeek');
  const endOfWeek = dayjs().endOf('isoWeek');

  return documents.filter(doc => {
    const datesToCheck = [
        doc.planDates.ifi, doc.actualDates.ifi,
        doc.planDates.ifr, doc.actualDates.ifr,
        doc.planDates.ifa, doc.actualDates.ifa,
        doc.planDates.ifc, doc.actualDates.ifc
    ];

    return datesToCheck.some(dateStr => {
        if (!dateStr) return false;
        const d = dayjs(dateStr);
        return d.isBetween(startOfWeek, endOfWeek, 'day', '[]');
    });
  });
};

/**
 * Helper to get documents pending feedback (status = Waiting cmt)
 */
export const getPendingFeedbackItems = (documents: MDIDocument[]): MDIDocument[] => {
    return documents.filter(doc => doc.status.toLowerCase().includes('waiting'));
};
