'use client';

import React, { useState, useEffect } from 'react';
import { FilterPanel, DashboardFilters } from '@/components/dashboard/FilterPanel';
import { MetricsCards, FleetMetricsCards, ChartsSection } from '@/components/dashboard/Metrics';
import api from '@/lib/api';
import { Download } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [departments, setDepartments] = useState<{id: string, name: string}[]>([]);
  const [filters, setFilters] = useState<DashboardFilters>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch departments for filter dropdown
    const fetchDepartments = async () => {
      try {
        const res = await api.get('/api/v1/iam/departments');
        setDepartments(res.data || []);
      } catch (err) {
        console.error("Failed to fetch departments", err);
      }
    };
    fetchDepartments();
  }, []);

  const fetchDashboardData = useCallback(async (currentFilters: DashboardFilters) => {
    try {
      setLoading(true);
      setError(null);
      // Construct payload, dropping empty/all values
      const payload: Record<string, unknown> = {};
      Object.entries(currentFilters).forEach(([k, v]) => {
        if (v !== undefined && v !== '' && v !== 'all') {
          payload[k] = v;
        }
      });
      
      const res = await api.post('/api/v1/dashboard/metrics', payload);
      setData(res.data);
    } catch (err: unknown) {
      console.error("Failed to load dashboard data", err);
      const message = err instanceof Error ? err.message : undefined;
      setError(message || "Failed to load dashboard data. Check your permissions.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData(filters);
  }, [fetchDashboardData, filters]);

  const handleExport = () => {
    // Simple CSV export of timeseries data for demonstration
    if (!data?.timeseries_data) return;
    
    const headers = ["Date", "Jobs Created", "Jobs Completed"];
    const rows = data.timeseries_data.map((d: any) => [d.date, d.jobs_created, d.jobs_completed]);
    const csvContent = [headers, ...rows].map(e => e.join(",")).join("\n");
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `dashboard_export_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Operational Dashboard</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">Key performance metrics and workloads</p>
        </div>
        <Button onClick={handleExport} variant="outline" className="flex items-center gap-2">
          <Download className="h-4 w-4" /> Export Report
        </Button>
      </div>

      <FilterPanel onFilter={setFilters} departments={departments} />

      {error ? (
        <div className="p-4 bg-red-50 text-red-600 rounded-lg border border-red-200">
          {error}
        </div>
      ) : loading && !data ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : data ? (
        <>
          <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-4">Job Execution Metrics</h3>
          <MetricsCards data={data} />
          
          <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-4 mt-8">Fleet & Requisition Metrics</h3>
          <FleetMetricsCards data={data} />
          
          <ChartsSection data={data} />
        </>
      ) : null}
    </div>
  );
}
