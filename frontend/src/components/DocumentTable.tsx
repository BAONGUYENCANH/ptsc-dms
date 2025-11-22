import React, { useMemo, useState, useEffect } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  ColumnDef,
  flexRender,
  SortingState,
} from '@tanstack/react-table';
import { MDIDocument } from '../types/mdi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight, AlertCircle, X, FileQuestion } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { ExportButton } from './ExportButton';
import { DataTableFacetedFilter } from '@/components/ui/data-table-faceted-filter';

interface DocumentTableProps {
  documents: MDIDocument[];
}

// Status Badge Component (Inline for simplicity)
const StatusBadge = ({ status }: { status: string }) => {
  let colorClass = 'bg-gray-100 text-gray-800';
  const s = status.toLowerCase();
  
  if (s.includes('approved') || s.includes('issue')) colorClass = 'bg-green-100 text-green-800';
  else if (s.includes('waiting') || s.includes('comment')) colorClass = 'bg-yellow-100 text-yellow-800';
  else if (s.includes('rejected') || s.includes('revise')) colorClass = 'bg-red-100 text-red-800';
  else if (s.includes('overdue')) colorClass = 'bg-red-200 text-red-900 font-bold';

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colorClass}`}>
      {status}
    </span>
  );
};

export const DocumentTable: React.FC<DocumentTableProps> = ({ documents }) => {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState('');
  
  // Store Integration
  const filters = useAppStore((state) => state.filters);
  const resetFilters = useAppStore((state) => state.resetFilters);
  const setPicFilter = useAppStore((state) => state.setPicFilter);

  // Get unique PICs with counts
  const picOptions = useMemo(() => {
    const picCounts = new Map<string, number>();
    documents.forEach((doc) => {
      const pic = doc.picPtsc || 'Unknown';
      picCounts.set(pic, (picCounts.get(pic) || 0) + 1);
    });

    return Array.from(picCounts.entries())
      .map(([pic, count]) => ({
        label: pic,
        value: pic,
        count,
      }))
      .sort((a, b) => a.label.localeCompare(b.label));
  }, [documents]);

  // Filtered Data Calculation
  const filteredData = useMemo(() => {
    return documents.filter((doc) => {
      // Discipline Filter
      if (filters.discipline && doc.discipline !== filters.discipline) return false;
      
      // Status Filter
      if (filters.status) {
          if (filters.status === 'Waiting') {
               if (!doc.status.toLowerCase().includes('waiting')) return false;
          } else if (doc.status !== filters.status) return false;
      }
      
      // Overdue Filter
      if (filters.isOverdue === true && !doc.isOverdue) return false;

      // PIC Filter (NEW - Multiple selection)
      if (filters.picPtsc.size > 0) {
        const docPic = doc.picPtsc || 'Unknown';
        if (!filters.picPtsc.has(docPic)) return false;
      }

      return true;
    });
  }, [documents, filters]);

  // Sync global filter with store if needed (optional, but good for "Quick Search" anywhere)
  useEffect(() => {
      if (filters.searchQuery) setGlobalFilter(filters.searchQuery);
  }, [filters.searchQuery]);

  const columns = useMemo<ColumnDef<MDIDocument>[]>(
    () => [
      {
        accessorKey: 'documentNo',
        header: 'Doc No',
        cell: (info) => <span className="font-medium text-blue-600">{info.getValue() as string}</span>,
        size: 180,
        enablePinning: true, 
      },
      {
        accessorKey: 'title',
        header: 'Document Title',
        cell: (info) => <div className="truncate max-w-[300px]" title={info.getValue() as string}>{info.getValue() as string}</div>,
        size: 300,
      },
      {
        accessorKey: 'revision',
        header: 'Rev',
        size: 60,
      },
      {
        accessorKey: 'discipline',
        header: 'Disc',
        size: 80,
      },
      {
        accessorKey: 'picPtsc',
        header: 'PIC',
        cell: (info) => {
          const pic = info.getValue() as string;
          return (
            <span className="text-sm font-medium text-gray-700">
              {pic || '-'}
            </span>
          );
        },
        size: 120,
        enableSorting: true,
      },
      {
        accessorKey: 'status',
        header: 'Status',
        cell: (info) => <StatusBadge status={info.getValue() as string} />,
        size: 150,
      },
      {
        header: 'IFI Plan',
        accessorFn: (row) => row.planDates.ifi,
        cell: (info) => {
            const val = info.getValue() as string;
            const isOverdue = info.row.original.isOverdue;
            return (
                <div className={`flex items-center ${isOverdue ? 'text-red-600 font-bold' : ''}`}>
                    {val || '-'}
                    {isOverdue && <AlertCircle className="ml-1 h-3 w-3" />}
                </div>
            )
        }
      },
      {
        header: 'IFI Actual',
        accessorFn: (row) => row.actualDates.ifi,
        cell: (info) => <span className="text-gray-600">{info.getValue() as string || '-'}</span>,
      },
      {
        header: 'IFR Plan',
        accessorFn: (row) => row.planDates.ifr,
        cell: (info) => info.getValue() as string || '-',
      },
       {
        header: 'IFR Actual',
        accessorFn: (row) => row.actualDates.ifr,
        cell: (info) => info.getValue() as string || '-',
      },
    ],
    []
  );

  const table = useReactTable({
    data: filteredData,
    columns,
    state: {
      sorting,
      globalFilter,
    },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  const hasActiveFilters = filters.discipline || filters.status || filters.isOverdue || filters.picPtsc.size > 0;

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
                <CardTitle>Document Master List</CardTitle>
                {hasActiveFilters && (
                    <div className="flex items-center gap-2 ml-4">
                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-md">
                            Filters Active
                        </span>
                        <Button variant="ghost" size="sm" onClick={resetFilters} className="h-6 px-2 text-red-500">
                            <X className="h-3 w-3 mr-1" /> Clear
                        </Button>
                    </div>
                )}
            </div>
            <div className="flex items-center gap-2">
                <Input 
                    placeholder="Search documents..." 
                    value={globalFilter ?? ''}
                    onChange={(e) => setGlobalFilter(e.target.value)}
                    className="max-w-sm"
                />
                <ExportButton documents={filteredData} fileName="MDI_Filtered_Export" />
            </div>
        </div>
        {/* Toolbar with Faceted Filters */}
        <div className="flex items-center gap-2 mt-2">
          <DataTableFacetedFilter
            title="Filter by PIC"
            options={picOptions}
            selectedValues={filters.picPtsc}
            onSelectionChange={setPicFilter}
          />
          <span className="text-xs text-muted-foreground ml-2">
            {filteredData.length} of {documents.length} documents
          </span>
        </div>
        {hasActiveFilters && (
             <div className="flex gap-2 text-sm text-muted-foreground mt-2">
                {filters.discipline && <span>Discipline: <b>{filters.discipline}</b></span>}
                {filters.status && <span>Status: <b>{filters.status}</b></span>}
                {filters.isOverdue && <span className="text-red-500 font-bold">Overdue Only</span>}
                {filters.picPtsc.size > 0 && <span>PIC: <b>{filters.picPtsc.size} selected</b></span>}
             </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="rounded-md border overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-gray-100 text-gray-700 border-b">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => {
                    // Sticky Column Logic for First Column
                    const isSticky = header.index === 0;
                    const stickyStyle: React.CSSProperties = isSticky ? {
                        position: 'sticky',
                        left: 0,
                        zIndex: 20,
                        backgroundColor: '#f3f4f6', // match header bg
                        boxShadow: '2px 0 5px -2px rgba(0,0,0,0.1)'
                    } : {};

                    return (
                        <th
                        key={header.id}
                        className="h-10 px-4 align-middle font-medium"
                        style={{ ...stickyStyle, minWidth: header.column.columnDef.size }}
                        onClick={header.column.getToggleSortingHandler()}
                        >
                        {header.isPlaceholder
                            ? null
                            : flexRender(header.column.columnDef.header, header.getContext())}
                        {{
                            asc: ' 🔼',
                            desc: ' 🔽',
                        }[header.column.getIsSorted() as string] ?? null}
                        </th>
                    );
                  })}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.length ? (
                table.getRowModel().rows.map((row) => (
                  <tr
                    key={row.id}
                    className="border-b transition-colors hover:bg-gray-50 data-[state=selected]:bg-muted"
                  >
                    {row.getVisibleCells().map((cell) => {
                         // Sticky Column Logic for First Column Cells
                         const isSticky = cell.column.id === 'documentNo';
                         const stickyStyle: React.CSSProperties = isSticky ? {
                             position: 'sticky',
                             left: 0,
                             zIndex: 10,
                             backgroundColor: 'white', // match row bg
                             boxShadow: '2px 0 5px -2px rgba(0,0,0,0.1)'
                         } : {};

                        return (
                            <td key={cell.id} className="p-4 align-middle" style={stickyStyle}>
                                {flexRender(cell.column.columnDef.cell, cell.getContext())}
                            </td>
                        )
                    })}
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={columns.length} className="h-64 text-center">
                    <div className="flex flex-col items-center justify-center space-y-3 py-8">
                      <FileQuestion className="h-16 w-16 text-gray-300" />
                      <div className="space-y-1">
                        <h3 className="text-lg font-semibold text-gray-700">No Documents Found</h3>
                        <p className="text-sm text-gray-500">
                          {filteredData.length === 0 && documents.length > 0
                            ? 'No documents match your current filters. Try adjusting your search criteria.'
                            : 'No documents available. Import an Excel file to get started.'}
                        </p>
                      </div>
                      {filteredData.length === 0 && documents.length > 0 && (
                        <Button variant="outline" size="sm" onClick={resetFilters}>
                          <X className="h-4 w-4 mr-2" />
                          Clear All Filters
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination Controls */}
        <div className="flex items-center justify-end space-x-2 py-4">
            <div className="text-sm text-muted-foreground mr-4">
                Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()} ({filteredData.length} items)
            </div>
            <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            >
            <ChevronLeft className="h-4 w-4" />
            Previous
            </Button>
            <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            >
            Next
            <ChevronRight className="h-4 w-4" />
            </Button>
        </div>
      </CardContent>
    </Card>
  );
};
