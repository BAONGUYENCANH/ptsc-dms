import { MDIDocument, KPIStats } from '../types/mdi';

// Helper to safely parse date string to ISO format if needed, or keep as is
const parseDate = (dateStr: any): string | undefined => {
  if (!dateStr || dateStr === 'N/A') return undefined;
  return String(dateStr);
};

/**
 * Helper to get column value with multiple possible names
 * Supports different Excel column name formats
 */
const getColumnValue = (raw: any, possibleNames: string[]): any => {
  for (const name of possibleNames) {
    const value = raw[name];
    // Skip undefined, null, empty string, and 'N/A'
    if (value !== undefined && value !== null && value !== '' && value !== 'N/A') {
      return value;
    }
  }
  return undefined;
};

/**
 * Check if document is overdue based on dates
 * Logic: Plan Date < Today AND Actual Date is empty
 */
const checkIsOverdue = (raw: any): boolean => {
  const today = new Date();
  today.setHours(0, 0, 0, 0); // Reset time to compare dates only
  
  // Check IFI milestone - support multiple column name formats
  const ifiPlan = getColumnValue(raw, [
    'ifi_plan_date',
    'IFI\nPlan Date',
    'IFI Plan Date',
    'IFIPlan Date',
    'IFI_Plan_Date'
  ]);
  const ifiActual = getColumnValue(raw, [
    'ifi_actual_date',
    'IFI\nActual Date',
    'IFI Actual Date',
    'IFIActual Date',
    'IFI_Actual_Date'
  ]);
  
  if (ifiPlan && !ifiActual) {
    try {
      const planDate = new Date(ifiPlan);
      planDate.setHours(0, 0, 0, 0);
      if (planDate < today) return true;
    } catch (e) {
      // Invalid date, skip
    }
  }
  
  // Check IFR milestone
  const ifrPlan = getColumnValue(raw, [
    'ifr_plan_date',
    'IFR\nPlan Date',
    'IFR Plan Date',
    'IFRPlan Date',
    'IFR_Plan_Date'
  ]);
  const ifrActual = getColumnValue(raw, [
    'ifr_actual_date',
    'IFR\nActual Date',
    'IFR Actual Date',
    'IFRActual Date',
    'IFR_Actual_Date'
  ]);
  
  if (ifrPlan && !ifrActual) {
    try {
      const planDate = new Date(ifrPlan);
      planDate.setHours(0, 0, 0, 0);
      if (planDate < today) return true;
    } catch (e) {
      // Invalid date, skip
    }
  }
  
  // Check IFA milestone
  const ifaPlan = getColumnValue(raw, [
    'ifa_plan_date',
    'IFA\nPlan Date',
    'IFA Plan Date',
    'IFAPlan Date',
    'IFA_Plan_Date'
  ]);
  const ifaActual = getColumnValue(raw, [
    'ifa_actual_date',
    'IFA\nActual Date',
    'IFA Actual Date',
    'IFAActual Date',
    'IFA_Actual_Date'
  ]);
  
  if (ifaPlan && !ifaActual) {
    try {
      const planDate = new Date(ifaPlan);
      planDate.setHours(0, 0, 0, 0);
      if (planDate < today) return true;
    } catch (e) {
      // Invalid date, skip
    }
  }
  
  return false;
};

export const parseMDIDocument = (raw: any): MDIDocument => {
  // Determine overdue status based on dates (not status string)
  const isOverdue = checkIsOverdue(raw);
  const isCritical = isOverdue || raw.doc_status?.toLowerCase().includes('waiting');

  return {
    id: raw.localPath || raw.id || `doc-${Math.random()}`,
    stt: Number(raw.stt) || 0,
    documentNo: raw.companyDocNo || raw['CompanyDoc.No.'] || '',
    title: raw.name || raw.DocumentName || '',
    revision: raw.revision || raw.Rev || '',
    
    discipline: raw.discipline || raw.Org || 'General',
    scope: raw.scope || raw.Scope || 'PTSC',
    docClass: raw.doc_class || raw.Class || '',
    table: raw.table || raw.Table || '',
    item: raw.item || raw.Item || '',
    
    status: raw.doc_status || raw.Status || 'Not yet issued',
    ipiStatus: raw.ipi_status || raw.IPI || '',
    reviewCode: raw.review_code || raw.Code || '',
    
    // Dates Mapping - support multiple column name formats
    planDates: {
      ifi: parseDate(getColumnValue(raw, ['ifi_plan_date', 'IFI\nPlan Date', 'IFI Plan Date', 'IFIPlan Date'])),
      ifr: parseDate(getColumnValue(raw, ['ifr_plan_date', 'IFR\nPlan Date', 'IFR Plan Date', 'IFRPlan Date'])),
      ifa: parseDate(getColumnValue(raw, ['ifa_plan_date', 'IFA\nPlan Date', 'IFA Plan Date', 'IFAPlan Date'])),
      ifc: parseDate(getColumnValue(raw, ['ifc_plan_date', 'IFC\nPlan Date', 'IFC Plan Date', 'IFCPlan Date'])),
      iff: parseDate(getColumnValue(raw, ['iff_plan_date', 'IFF/ASB\nPlan Date', 'IFF/ASB Plan Date', 'IFF Plan Date'])),
    },
    actualDates: {
      ifi: parseDate(getColumnValue(raw, ['ifi_actual_date', 'IFI\nActual Date', 'IFI Actual Date', 'IFIActual Date'])),
      ifr: parseDate(getColumnValue(raw, ['ifr_actual_date', 'IFR\nActual Date', 'IFR Actual Date', 'IFRActual Date'])),
      ifa: parseDate(getColumnValue(raw, ['ifa_actual_date', 'IFA\nActual Date', 'IFA Actual Date', 'IFAActual Date'])),
      ifc: parseDate(getColumnValue(raw, ['ifc_actual_date', 'IFC\nActual Date', 'IFC Actual Date', 'IFCActual Date'])),
      iff: parseDate(getColumnValue(raw, ['iff_actual_date', 'IFF/ASB\nActual Date', 'IFF/ASB Actual Date', 'IFF Actual Date'])),
    },
    targetMitigationDate: parseDate(getColumnValue(raw, ['target_mitigation_date', 'Target Mitigation Date', 'TargetMitigation Date'])),
    
    // Transmittals
    transNo: raw.transNo || raw.transNo || '',
    dateReceived: parseDate(raw.dateReceived),
    trnOutDate: parseDate(raw.trn_out_date || raw.DateTRNOut),
    trnOutNo: raw.trn_out_no || raw['TRNOutNo.'],
    trnInDate: parseDate(raw.trn_in_date || raw.DateTRNIn),
    trnInNo: raw.trn_in_no || raw['TRNInNo.'],
    
    picPtsc: getColumnValue(raw, ['pic_ptsc', 'PIC PTSC', 'PICPTSC', 'PIC_PTSC']) || '',
    picLsp: getColumnValue(raw, ['pic_lsp', 'PIC LSP', 'PICLSP', 'PIC_LSP']) || '',
    
    localPath: raw.localPath,
    sharepointPath: raw.sharepointPath,
    
    isOverdue,
    isCritical
  };
};

export const parseMDIList = (rawData: any[]): MDIDocument[] => {
  return rawData.map(parseMDIDocument);
};

export const calculateKPIs = (docs: MDIDocument[]): KPIStats => {
  const totalDocuments = docs.length;
  const overdueCount = docs.filter(d => d.isOverdue).length;
  const waitingCommentCount = docs.filter(d => d.status.toLowerCase().includes('waiting')).length;
  
  // Mock calculation for weight factor if not present
  const totalWeightFactor = 100; 
  const overallProgress = 45; // Placeholder until weight factor logic is confirmed

  return {
    totalDocuments,
    totalWeightFactor,
    overallProgress,
    criticalIssues: overdueCount + waitingCommentCount,
    overdueCount,
    waitingCommentCount
  };
};
