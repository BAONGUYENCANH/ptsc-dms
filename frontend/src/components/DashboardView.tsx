import React, { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { MDIDocument, KPIStats } from '../types/mdi';
import { calculateKPIs } from '../utils/mdi-parser';
import { FileText, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';

interface DashboardViewProps {
  documents: MDIDocument[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

export const DashboardView: React.FC<DashboardViewProps> = ({ documents }) => {
  const stats: KPIStats = useMemo(() => calculateKPIs(documents), [documents]);
  const setFilter = useAppStore((state) => state.setFilter);

  // Prepare Bar Chart Data: Plan vs Actual by Discipline
  const barData = useMemo(() => {
    const grouped: Record<string, { name: string; Plan: number; Actual: number }> = {};
    
    documents.forEach(doc => {
      const disc = doc.discipline || 'Other';
      if (!grouped[disc]) {
        grouped[disc] = { name: disc, Plan: 0, Actual: 0 };
      }
      // Logic: Plan = Has any plan date; Actual = Has any actual date
      const hasPlan = Object.values(doc.planDates).some(d => !!d);
      const hasActual = Object.values(doc.actualDates).some(d => !!d);
      
      if (hasPlan) grouped[disc].Plan++;
      if (hasActual) grouped[disc].Actual++;
    });
    
    return Object.values(grouped);
  }, [documents]);

  // Prepare Pie Chart Data: Status Distribution
  const pieData = useMemo(() => {
    const grouped: Record<string, number> = {};
    documents.forEach(doc => {
      const status = doc.status || 'Unknown';
      grouped[status] = (grouped[status] || 0) + 1;
    });
    
    return Object.entries(grouped).map(([name, value]) => ({ name, value }));
  }, [documents]);

  // NEW: Top 5 Overdue by PIC
  const topOverdueByPIC = useMemo(() => {
    // Filter overdue documents only
    const overdueDocuments = documents.filter(doc => doc.isOverdue);
    
    // Group by PIC (use picPtsc as primary)
    const grouped: Record<string, number> = {};
    overdueDocuments.forEach(doc => {
      const pic = doc.picPtsc || 'Unknown';
      grouped[pic] = (grouped[pic] || 0) + 1;
    });
    
    // Convert to array and sort by count (descending)
    const sorted = Object.entries(grouped)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count);
    
    // Return top 5
    return sorted.slice(0, 5);
  }, [documents]);

  // Handlers for Drill-down
  const handleBarClick = (data: any) => {
      if (data && data.activeLabel) {
          setFilter('discipline', data.activeLabel);
      }
  };

  const handlePieClick = (data: any) => {
      if (data && data.name) {
          setFilter('status', data.name);
      }
  };

  const handleCardClick = (type: 'total' | 'overdue' | 'waiting') => {
      if (type === 'overdue') {
          setFilter('isOverdue', true);
      } else if (type === 'waiting') {
          setFilter('status', 'Waiting'); // Simple string match filter logic
      } else {
          // Total - reset or show all
          setFilter('discipline', null);
          setFilter('status', null);
          setFilter('isOverdue', null);
      }
  };

  // NEW: Handle clicking on PIC bar in Top Overdue chart
  const handlePICBarClick = (data: any) => {
      if (data && data.activePayload && data.activePayload[0]) {
          const picName = data.activePayload[0].payload.name;
          // Filter by PIC and show only overdue
          setFilter('isOverdue', true);
          // Note: Need to add PIC filter to store
          console.log('Clicked PIC:', picName);
          // TODO: Add picFilter to store for full functionality
      }
  };

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      <h2 className="text-3xl font-bold tracking-tight">Dashboard Overview</h2>
      
      {/* KPI Cards - Enhanced with Colorful Icons */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Total Documents - Blue */}
        <Card onClick={() => handleCardClick('total')} className="cursor-pointer hover:shadow-lg transition-all border-l-4 border-blue-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-3 rounded-lg shadow-lg">
              <FileText className="h-6 w-6 text-white" strokeWidth={2.5} />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats.totalDocuments}</div>
            <p className="text-xs text-muted-foreground">tracked in system</p>
          </CardContent>
        </Card>

        {/* Overall Progress - Green */}
        <Card className="hover:shadow-lg transition-all border-l-4 border-green-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overall Progress</CardTitle>
            <div className="bg-gradient-to-br from-green-500 to-green-600 p-3 rounded-lg shadow-lg">
              <CheckCircle className="h-6 w-6 text-white" strokeWidth={2.5} />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.overallProgress}%</div>
            <p className="text-xs text-muted-foreground">weighted completion</p>
          </CardContent>
        </Card>

        {/* Critical Issues - Red */}
        <Card onClick={() => handleCardClick('overdue')} className="cursor-pointer hover:shadow-lg transition-all border-l-4 border-red-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical Issues</CardTitle>
            <div className="bg-gradient-to-br from-red-500 to-red-600 p-3 rounded-lg shadow-lg">
              <AlertTriangle className="h-6 w-6 text-white" strokeWidth={2.5} />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.criticalIssues}</div>
            <p className="text-xs text-muted-foreground">overdue or blocked</p>
          </CardContent>
        </Card>

        {/* Pending Review - Orange */}
        <Card onClick={() => handleCardClick('waiting')} className="cursor-pointer hover:shadow-lg transition-all border-l-4 border-orange-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Review</CardTitle>
            <div className="bg-gradient-to-br from-orange-500 to-orange-600 p-3 rounded-lg shadow-lg">
              <Clock className="h-6 w-6 text-white" strokeWidth={2.5} />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{stats.waitingCommentCount}</div>
            <p className="text-xs text-muted-foreground">waiting for comment</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* Bar Chart */}
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Submission Progress by Discipline</CardTitle>
          </CardHeader>
          <CardContent className="pl-2">
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData} onClick={handleBarClick}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
                  <Tooltip cursor={{ fill: 'transparent' }} />
                  <Legend />
                  <Bar dataKey="Plan" fill="#adfa1d" radius={[4, 4, 0, 0]} name="Planned Docs" cursor="pointer" />
                  <Bar dataKey="Actual" fill="#0ea5e9" radius={[4, 4, 0, 0]} name="Submitted Docs" cursor="pointer" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Donut Chart - Status Distribution */}
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Document Status Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="35%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={2}
                    dataKey="value"
                    onClick={handlePieClick}
                    cursor="pointer"
                    label={false}
                  >
                    {pieData.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend 
                    layout="vertical" 
                    align="right" 
                    verticalAlign="middle"
                    iconSize={10}
                    wrapperStyle={{ paddingLeft: '20px', fontSize: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* NEW: Top 5 Overdue by PIC Chart */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            Top 5 Overdue by Person In Charge (PIC)
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Click a bar to filter documents by PIC
          </p>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            {topOverdueByPIC.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={topOverdueByPIC}
                  layout="vertical"
                  onClick={handlePICBarClick}
                  margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={90} />
                  <Tooltip 
                    cursor={{ fill: 'rgba(239, 68, 68, 0.1)' }}
                    contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
                  />
                  <Bar 
                    dataKey="count" 
                    fill="#ef4444" 
                    radius={[0, 4, 4, 0]}
                    name="Overdue Documents"
                    cursor="pointer"
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                <p>No overdue documents found</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
