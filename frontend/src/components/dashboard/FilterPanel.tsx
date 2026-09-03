import React, { useState } from 'react';
import { Filter, Search, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface DashboardFilters {
  department_id?: string;
  departmentId?: string;
  date_from?: string;
  date_to?: string;
  startDate?: string;
  endDate?: string;
  status?: string;
  priority?: number;
  job_type?: string;
  location?: string;
  cost_centre?: string;
}

interface FilterPanelProps {
  onFilter?: (filters: DashboardFilters) => void;
  onFilterChange?: (filters: DashboardFilters) => void;
  departments: { id: string, name: string }[];
  loading?: boolean;
}

export function FilterPanel({ onFilter, onFilterChange, departments, loading }: FilterPanelProps) {
  const [filters, setFilters] = useState<DashboardFilters>({});
  const [isExpanded, setIsExpanded] = useState(false);

  const applyFilters = (newFilters: DashboardFilters) => {
    if (onFilterChange) onFilterChange(newFilters);
    if (onFilter) onFilter(newFilters);
  };

  const handleApply = () => {
    applyFilters(filters);
  };

  const handleClear = () => {
    setFilters({});
    applyFilters({});
  };

  return (
    <div className="bg-white border border-zinc-200 rounded-lg p-4 mb-6 shadow-2xs">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-xs uppercase tracking-wider text-zinc-900 flex items-center gap-2">
          <Filter className="h-3.5 w-3.5 text-zinc-500" /> Operational Filters
        </h3>
        <Button 
          variant="outline" 
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-xs h-7 border-zinc-200 text-zinc-700 hover:bg-zinc-100"
        >
          {isExpanded ? 'Hide Advanced' : 'Show Advanced'}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <div>
          <label className="block text-[11px] font-medium text-zinc-600 mb-1">Department</label>
          <select 
            className="w-full text-xs h-8 border border-zinc-200 rounded-md bg-white text-zinc-900 px-2 focus:ring-1 focus:ring-zinc-400 focus:border-zinc-400 outline-none"
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
          <label className="block text-[11px] font-medium text-zinc-600 mb-1">Status</label>
          <select 
            className="w-full text-xs h-8 border border-zinc-200 rounded-md bg-white text-zinc-900 px-2 focus:ring-1 focus:ring-zinc-400 focus:border-zinc-400 outline-none"
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
          <label className="block text-[11px] font-medium text-zinc-600 mb-1">Date From</label>
          <input 
            type="date"
            className="w-full text-xs h-8 border border-zinc-200 rounded-md bg-white text-zinc-900 px-2 focus:ring-1 focus:ring-zinc-400 focus:border-zinc-400 outline-none"
            value={filters.date_from || ''}
            onChange={(e) => setFilters({...filters, date_from: e.target.value || undefined})}
          />
        </div>

        <div>
          <label className="block text-[11px] font-medium text-zinc-600 mb-1">Date To</label>
          <input 
            type="date"
            className="w-full text-xs h-8 border border-zinc-200 rounded-md bg-white text-zinc-900 px-2 focus:ring-1 focus:ring-zinc-400 focus:border-zinc-400 outline-none"
            value={filters.date_to || ''}
            onChange={(e) => setFilters({...filters, date_to: e.target.value || undefined})}
          />
        </div>

        {isExpanded && (
          <>
            <div>
              <label className="block text-[11px] font-medium text-zinc-600 mb-1">Priority</label>
              <select
                className="w-full text-xs h-8 border border-zinc-200 rounded-md bg-white text-zinc-900 px-2 focus:ring-1 focus:ring-zinc-400 focus:border-zinc-400 outline-none"
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
              <label className="block text-[11px] font-medium text-zinc-600 mb-1">Location</label>
              <input
                type="text"
                placeholder="Search location..."
                className="w-full text-xs h-8 border border-zinc-200 rounded-md bg-white text-zinc-900 px-2 focus:ring-1 focus:ring-zinc-400 focus:border-zinc-400 outline-none"
                value={filters.location || ''}
                onChange={(e) => setFilters({...filters, location: e.target.value || undefined})}
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-zinc-600 mb-1">Job Type</label>
              <select
                className="w-full text-xs h-8 border border-zinc-200 rounded-md bg-white text-zinc-900 px-2 focus:ring-1 focus:ring-zinc-400 focus:border-zinc-400 outline-none"
                value={filters.job_type || ''}
                onChange={(e) => setFilters({...filters, job_type: e.target.value || undefined})}
              >
                <option value="">Any</option>
                <option value="CORRECTIVE">Corrective</option>
                <option value="PREVENTIVE">Preventive</option>
                <option value="EMERGENCY">Emergency</option>
                <option value="INSPECTION">Inspection</option>
                <option value="INSTALLATION">Installation</option>
                <option value="CALIBRATION">Calibration</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-zinc-600 mb-1">Cost Centre</label>
              <input
                type="text"
                placeholder="e.g. CC-1042"
                className="w-full text-xs h-8 border border-zinc-200 rounded-md bg-white text-zinc-900 px-2 focus:ring-1 focus:ring-zinc-400 focus:border-zinc-400 outline-none"
                value={filters.cost_centre || ''}
                onChange={(e) => setFilters({...filters, cost_centre: e.target.value || undefined})}
              />
            </div>
          </>
        )}
      </div>

      <div className="mt-4 flex justify-end gap-2">
        <Button variant="ghost" size="sm" onClick={handleClear} className="flex gap-1 items-center text-xs h-8 text-zinc-600 hover:text-zinc-900">
          <X className="h-3.5 w-3.5" /> Clear
        </Button>
        <Button onClick={handleApply} size="sm" className="flex gap-1 items-center text-xs h-8 bg-zinc-900 text-white hover:bg-black">
          <Search className="h-3.5 w-3.5" /> Apply Filters
        </Button>
      </div>
    </div>
  );
}
