import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { MDIDocument } from '../types/mdi';
import { getOverdueItems, getWeeklySubmissionItems, getPendingFeedbackItems } from '../utils/reportingUtils';
import { useAppStore } from '../store/useAppStore';
import { ClipboardList, CalendarClock, MessageSquareWarning } from 'lucide-react';

interface QuickReportsProps {
  documents: MDIDocument[];
}

export const QuickReports: React.FC<QuickReportsProps> = ({ documents }) => {
  const setFilter = useAppStore((state) => state.setFilter);
  const resetFilters = useAppStore((state) => state.resetFilters);

  // Calculate counts for badges
  const overdueCount = getOverdueItems(documents).length;
  const weeklyCount = getWeeklySubmissionItems(documents).length;
  const pendingCount = getPendingFeedbackItems(documents).length;

  const applyReport = (type: 'overdue' | 'weekly' | 'feedback') => {
      resetFilters();
      // Note: Real implementation might set specific complex filter objects 
      // or separate view states. For now, we map to existing store filters where possible, 
      // or we could assume the parent component switches to a specific 'Report View' based on store.
      
      // Since the current store is simple, let's use the 'isOverdue' flag for one,
      // but for 'Weekly' we might need a new store property or just filtered interaction.
      // For this task, let's simulate the action by setting a specific filter combination 
      // or assuming the store handles "reportMode".
      
      if (type === 'overdue') {
          setFilter('isOverdue', true);
      } else if (type === 'feedback') {
          setFilter('status', 'Waiting');
      } else if (type === 'weekly') {
           // Since we don't have a "date range" filter in the store yet, 
           // we would typically add it. For now, I'll console log implementation note.
           console.log("Weekly filter would apply date range logic here.");
           alert("Weekly Submission View: This would filter the table for current week's items.");
      }
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Quick Reports</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-2">
        <Button 
            variant="outline" 
            className="justify-start" 
            onClick={() => applyReport('overdue')}
        >
            <ClipboardList className="mr-2 h-4 w-4 text-red-500" />
            Overdue Items
            <span className="ml-auto bg-red-100 text-red-800 text-xs px-2 py-0.5 rounded-full">
                {overdueCount}
            </span>
        </Button>
        
        <Button 
            variant="outline" 
            className="justify-start" 
            onClick={() => applyReport('weekly')}
        >
            <CalendarClock className="mr-2 h-4 w-4 text-blue-500" />
            Due This Week
            <span className="ml-auto bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded-full">
                {weeklyCount}
            </span>
        </Button>
        
        <Button 
            variant="outline" 
            className="justify-start"
            onClick={() => applyReport('feedback')}
        >
            <MessageSquareWarning className="mr-2 h-4 w-4 text-yellow-500" />
            Waiting Feedback
            <span className="ml-auto bg-yellow-100 text-yellow-800 text-xs px-2 py-0.5 rounded-full">
                {pendingCount}
            </span>
        </Button>
      </CardContent>
    </Card>
  );
};
