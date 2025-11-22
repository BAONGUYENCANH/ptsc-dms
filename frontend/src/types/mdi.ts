export interface MDIPlanDates {
  ifi?: string;
  ifr?: string;
  ifa?: string;
  ifc?: string;
  iff?: string; // IFF/ASB
}

export interface MDIActualDates {
  ifi?: string;
  ifr?: string;
  ifa?: string;
  ifc?: string;
  iff?: string;
}

export interface MDIDocument {
  // Key Identifiers
  id: string; // Unique ID (could be localPath or generated)
  stt: number; // Sequence number
  documentNo: string; // Company Doc No
  title: string; // Document Name
  revision: string;
  
  // Classification
  discipline: string; // E.g., EE, PL, CV
  scope: 'PTSC' | 'TCC' | string;
  docClass: string; // Class 1, 2, 3
  table: string; // Table 01, Table 02...
  item: string; // A19, C10...
  
  // Status & Progress
  status: string; // Not yet issued, Waiting cmt, Approved...
  ipiStatus: string; // IFI, IFR, IFA, IFC...
  reviewCode?: string; // A1, R1...
  weightFactor?: number; // If available
  
  // Dates
  planDates: MDIPlanDates;
  actualDates: MDIActualDates;
  targetMitigationDate?: string;
  
  // Transmittals
  transNo?: string;
  dateReceived?: string;
  trnOutDate?: string;
  trnOutNo?: string;
  trnInDate?: string;
  trnInNo?: string;
  
  // People
  picPtsc?: string;
  picLsp?: string;
  
  // System Paths
  localPath?: string;
  sharepointPath?: string;
  
  // Computed/Frontend-only
  isOverdue?: boolean;
  isCritical?: boolean;
}

export interface KPIStats {
  totalDocuments: number;
  totalWeightFactor: number;
  overallProgress: number;
  criticalIssues: number;
  overdueCount: number;
  waitingCommentCount: number;
}
