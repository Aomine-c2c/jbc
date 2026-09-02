'use client';

import React, { useState, useEffect, useCallback } from 'react';
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
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-zinc-200">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-900 uppercase font-mono">Operations Dashboard</h1>
          <p className="text-xs text-zinc-500">Live operational throughput, equipment telemetry & department workloads</p>
        </div>
        <Button onClick={handleExport} variant="outline" className="flex items-center gap-2 text-xs h-8 border-zinc-200 text-zinc-800 hover:bg-zinc-100">
          <Download className="h-3.5 w-3.5" /> Export Report (CSV)
        </Button>
      </div>

      <FilterPanel onFilter={setFilters} departments={departments} />

      {error ? (
        <div className="p-4 bg-rose-50 text-rose-700 rounded-md border border-rose-200 text-xs">
          {error}
        </div>
      ) : loading && !data ? (
        <div className="flex justify-center py-24">
          <div className="animate-spin rounded-full h-7 w-7 border-2 border-zinc-900 border-t-transparent"></div>
        </div>
      ) : data ? (
        <>
          <div className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 font-mono">Job Execution Metrics</h3>
            <MetricsCards data={data} />
          </div>
          
          <div className="space-y-3 pt-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 font-mono">Fleet & Materials Metrics</h3>
            <FleetMetricsCards data={data} />
          </div>
          
          <div className="pt-2">
            <ChartsSection data={data} />
          </div>
        </>
      ) : null}
    </div>
  );
}
