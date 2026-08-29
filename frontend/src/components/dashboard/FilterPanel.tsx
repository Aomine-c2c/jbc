import React, { useState } from 'react';
import { Filter, Search, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface DashboardFilters {
  department_id?: string;
  date_from?: string;
  date_to?: string;
  status?: string;
  priority?: number;
  job_type?: string;
  location?: string;
  cost_centre?: string;
}

interface FilterPanelProps {
  onFilter: (filters: DashboardFilters) => void;
  departments: { id: string, name: string }[];
}

export function FilterPanel({ onFilter, departments }: FilterPanelProps) {
  const [filters, setFilters] = useState<DashboardFilters>({});
  const [isExpanded, setIsExpanded] = useState(false);

  const handleApply = () => {
    onFilter(filters);
  };

  const handleClear = () => {
    setFilters({});
    onFilter({});
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-4 mb-6 shadow-sm">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
          <Filter className="h-4 w-4" /> Operational Filters
        </h3>
        <Button 
          variant="outline" 
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? 'Hide Advanced' : 'Show Advanced'}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Department</label>
          <select 
            className="w-full text-sm border-slate-300 dark:border-slate-700 rounded-md bg-transparent dark:bg-slate-800 focus:ring-blue-500 focus:border-blue-500"
            value={filters.department_id || ''}
            onChange={(e) => setFilters({...filters, department_id: e.target.value || undefined})}
          >
            <option value="">All Departments</option>
            {departments.map(d => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Status</label>
          <select 
            className="w-full text-sm border-slate-300 dark:border-slate-700 rounded-md bg-transparent dark:bg-slate-800 focus:ring-blue-500 focus:border-blue-500"
            value={filters.status || ''}
            onChange={(e) => setFilters({...filters, status: e.target.value || undefined})}
          >
            <option value="">All Statuses</option>
            <option value="SUBMITTED">Submitted</option>
            <option value="PENDING_APPROVAL">Pending Approval</option>
            <option value="APPROVED">Approved</option>
            <option value="ASSIGNED">Assigned</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="ON_HOLD">On Hold</option>
            <option value="COMPLETED">Completed</option>
            <option value="VERIFIED">Verified</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Date From</label>
          <input 
            type="date"
            className="w-full text-sm border-slate-300 dark:border-slate-700 rounded-md bg-transparent dark:bg-slate-800 focus:ring-blue-500 focus:border-blue-500"
            value={filters.date_from || ''}
            onChange={(e) => setFilters({...filters, date_from: e.target.value || undefined})}
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Date To</label>
          <input 
            type="date"
            className="w-full text-sm border-slate-300 dark:border-slate-700 rounded-md bg-transparent dark:bg-slate-800 focus:ring-blue-500 focus:border-blue-500"
            value={filters.date_to || ''}
            onChange={(e) => setFilters({...filters, date_to: e.target.value || undefined})}
          />
        </div>

        {isExpanded && (
          <>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Priority</label>
              <select 
                className="w-full text-sm border-slate-300 dark:border-slate-700 rounded-md bg-transparent dark:bg-slate-800 focus:ring-blue-500 focus:border-blue-500"
                value={filters.priority !== undefined ? filters.priority : ''}
                onChange={(e) => setFilters({...filters, priority: e.target.value ? parseInt(e.target.value) : undefined})}
              >
                <option value="">Any</option>
                <option value="0">Low (0)</option>
                <option value="1">Medium (1)</option>
                <option value="2">High (2)</option>
                <option value="3">Critical (3)</option>
              </select>
            </div>
            
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Location</label>
              <input 
                type="text"
                placeholder="Search location..."
                className="w-full text-sm border-slate-300 dark:border-slate-700 rounded-md bg-transparent dark:bg-slate-800 focus:ring-blue-500 focus:border-blue-500"
                value={filters.location || ''}
                onChange={(e) => setFilters({...filters, location: e.target.value || undefined})}
              />
            </div>
          </>
        )}
      </div>

      <div className="mt-4 flex justify-end gap-2">
        <Button variant="ghost" size="sm" onClick={handleClear} className="flex gap-1 items-center">
          <X className="h-4 w-4" /> Clear
        </Button>
        <Button onClick={handleApply} size="sm" className="flex gap-1 items-center">
          <Search className="h-4 w-4" /> Apply Filters
        </Button>
      </div>
    </div>
  );
}
