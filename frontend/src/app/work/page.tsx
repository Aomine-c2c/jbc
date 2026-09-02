'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { apiFetch } from '@/lib/api';
import { Protect } from '@/components/auth/Protect';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { LocationSelector } from '@/components/locations/LocationSelector';
import {
  Briefcase,
  Wrench,
  Search,
  Plus,
  Filter,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Layers,
  ArrowUpRight,
  RefreshCw,
  GitFork,
  FileCheck,
  Building2,
  MapPin,
  Truck,
  Eye,
  SlidersHorizontal,
} from 'lucide-react';
import Link from 'next/link';

interface WorkItemRow {
  id: string;
  reference_number: string;
  work_type: string;
  title: string;
  status: string;
  priority: number;
  department_id: string;
  department_name?: string;
  location_breadcrumb?: string;
  machine_identifier?: string;
  supervisor_name?: string;
  assigned_personnel?: string;
  due_date?: string;
  sla_status: string;
  job_card_id?: string;
  created_at: string;
}

interface DepartmentOption {
  id: string;
  name: string;
  code?: string;
}

const WORK_TYPES = [
  { id: 'ALL', label: 'All Work Units', icon: Layers },
  { id: 'JOB_CARD', label: 'Job Cards', icon: Wrench },
  { id: 'MAINTENANCE', label: 'Maintenance', icon: Briefcase },
  { id: 'INSPECTION', label: 'Inspections', icon: FileCheck },
  { id: 'FOLLOW_UP', label: 'Follow-ups', icon: GitFork },
];

export default function WorkManagementHubPage() {
  const [items, setItems] = useState<WorkItemRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);
  
  // Modal state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newWorkType, setNewWorkType] = useState('MAINTENANCE');
  const [newDeptId, setNewDeptId] = useState('');
  const [newLocationId, setNewLocationId] = useState<string | null>(null);
  const [newPriority, setNewPriority] = useState(2);
  const [newAssigned, setNewAssigned] = useState('');
  const [newDueDate, setNewDueDate] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      let url = '/api/v1/work-items?limit=100';
      if (selectedType !== 'ALL') {
        url += `&work_type=${selectedType}`;
      }
      if (statusFilter !== 'ALL') {
        url += `&status=${statusFilter}`;
      }
      if (searchQuery.trim()) {
        url += `&search=${encodeURIComponent(searchQuery.trim())}`;
      }
      const data = await apiFetch<WorkItemRow[]>(url);
      if (Array.isArray(data) && data.length > 0) {
        setItems(data);
      } else {
        const { MOCK_JOB_CARDS } = await import('@/lib/mockData');
        const fallbackItems: WorkItemRow[] = MOCK_JOB_CARDS.map((jc) => ({
          id: jc.id,
          reference_number: jc.job_number,
          work_type: jc.job_type || 'JOB_CARD',
          title: jc.title,
          status: jc.status,
          priority: jc.priority,
          department_id: jc.department_id,
          department_name: jc.department_name,
          location_breadcrumb: jc.location,
          machine_identifier: jc.machine_identifier,
          supervisor_name: jc.supervisor_name,
          assigned_personnel: jc.assigned_personnel,
          due_date: jc.required_date,
          sla_status: 'ON_TRACK',
          job_card_id: jc.id,
          created_at: jc.created_at,
        }));
        setItems(fallbackItems);
      }

      const deptData = await apiFetch<DepartmentOption[]>('/api/v1/iam/departments');
      if (deptData && deptData.length > 0) {
        setDepartments(deptData);
      } else {
        const { MOCK_DEPARTMENTS } = await import('@/lib/mockData');
        setDepartments(MOCK_DEPARTMENTS);
      }
    } catch (err) {
      console.warn('Failed to load work items from central server, using synthetic fallback', err);
      const { MOCK_JOB_CARDS, MOCK_DEPARTMENTS } = await import('@/lib/mockData');
      const fallbackItems: WorkItemRow[] = MOCK_JOB_CARDS.map((jc) => ({
        id: jc.id,
        reference_number: jc.job_number,
        work_type: jc.job_type || 'JOB_CARD',
        title: jc.title,
        status: jc.status,
        priority: jc.priority,
        department_id: jc.department_id,
        department_name: jc.department_name,
        location_breadcrumb: jc.location,
        machine_identifier: jc.machine_identifier,
        supervisor_name: jc.supervisor_name,
        assigned_personnel: jc.assigned_personnel,
        due_date: jc.required_date,
        sla_status: 'ON_TRACK',
        job_card_id: jc.id,
        created_at: jc.created_at,
      }));
      setItems(fallbackItems);
      setDepartments(MOCK_DEPARTMENTS);
    } finally {
      setLoading(false);
    }
  }, [selectedType, statusFilter, searchQuery]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newDeptId) return;
    setSubmitting(true);
    try {
      await apiFetch('/api/v1/work-items', {
        method: 'POST',
        body: JSON.stringify({
          title: newTitle.trim(),
          description: newDesc.trim() || undefined,
          work_type: newWorkType,
          department_id: newDeptId,
          location_id: newLocationId || undefined,
          priority: newPriority,
          assigned_personnel: newAssigned.trim() || undefined,
          due_date: newDueDate ? new Date(newDueDate).toISOString() : undefined,
        }),
      });
      setIsCreateOpen(false);
      setNewTitle('');
      setNewDesc('');
      setNewLocationId(null);
      loadData();
    } catch (err) {
      console.error('Failed to create work item', err);
    } finally {
      setSubmitting(false);
    }
  };

  const getPriorityBadge = (p: number) => {
    switch (p) {
      case 4:
        return <Badge className="bg-red-600/20 text-red-400 border-red-500/30 text-[10px]">CRITICAL</Badge>;
      case 3:
        return <Badge className="bg-amber-600/20 text-amber-400 border-amber-500/30 text-[10px]">URGENT</Badge>;
      case 2:
        return <Badge className="bg-yellow-600/20 text-yellow-400 border-yellow-500/30 text-[10px]">HIGH</Badge>;
      case 1:
        return <Badge className="bg-blue-600/20 text-blue-400 border-blue-500/30 text-[10px]">MEDIUM</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px]">LOW</Badge>;
    }
  };

  const getTypeBadge = (wt: string) => {
    switch (wt) {
      case 'JOB_CARD':
        return <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/30 text-[10px]">JOB CARD</Badge>;
      case 'MAINTENANCE':
        return <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/30 text-[10px]">MAINTENANCE</Badge>;
      case 'INSPECTION':
        return <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30 text-[10px]">INSPECTION</Badge>;
      case 'FOLLOW_UP':
        return <Badge variant="outline" className="bg-orange-500/10 text-orange-400 border-orange-500/30 text-[10px]">FOLLOW-UP</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px]">{wt}</Badge>;
    }
  };

  const getSlaBadge = (sla: string) => {
    switch (sla) {
      case 'BREACHED':
        return <span className="inline-flex items-center gap-1 text-[10px] font-mono text-red-400 font-bold"><AlertTriangle className="size-3" /> SLA BREACHED</span>;
      case 'AT_RISK':
        return <span className="inline-flex items-center gap-1 text-[10px] font-mono text-amber-400 font-bold"><Clock className="size-3 animate-pulse" /> AT RISK</span>;
      case 'MET':
        return <span className="inline-flex items-center gap-1 text-[10px] font-mono text-emerald-400"><CheckCircle2 className="size-3" /> MET</span>;
      default:
        return <span className="inline-flex items-center gap-1 text-[10px] font-mono text-muted-foreground"><Clock className="size-3" /> ON SCHEDULE</span>;
    }
  };

  // Metrics
  const totalCount = items.length;
  const inProgressCount = items.filter((i) => i.status === 'IN_PROGRESS').length;
  const atRiskCount = items.filter((i) => i.sla_status === 'AT_RISK' || i.sla_status === 'BREACHED').length;
  const completedCount = items.filter((i) => ['COMPLETED', 'VERIFIED', 'CLOSED'].includes(i.status)).length;

  return (
    <Protect capability="work_hub:view" isPageGuard moduleName="Work Hub Kanban">
      <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-primary/10 text-primary">
            <Layers className="size-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              Work Management Hub
            </h1>
            <p className="text-xs text-muted-foreground">
              Unified operational execution engine for Job Cards, Maintenance, Inspections & Follow-ups.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={loadData} disabled={loading} className="text-xs gap-1.5">
            <RefreshCw className={`size-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button size="sm" onClick={() => setIsCreateOpen(true)} className="text-xs gap-1.5 bg-primary text-primary-foreground">
            <Plus className="size-3.5" />
            New Work Item
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Active Work Units</p>
              <p className="text-2xl font-mono font-bold text-foreground mt-1">{totalCount}</p>
            </div>
            <div className="p-2.5 rounded-md bg-muted text-muted-foreground">
              <Layers className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">In Progress</p>
              <p className="text-2xl font-mono font-bold text-blue-400 mt-1">{inProgressCount}</p>
            </div>
            <div className="p-2.5 rounded-md bg-blue-500/10 text-blue-400">
              <Wrench className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">SLA At Risk / Breached</p>
              <p className="text-2xl font-mono font-bold text-amber-400 mt-1">{atRiskCount}</p>
            </div>
            <div className="p-2.5 rounded-md bg-amber-500/10 text-amber-400">
              <AlertTriangle className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Completed & Verified</p>
              <p className="text-2xl font-mono font-bold text-emerald-400 mt-1">{completedCount}</p>
            </div>
            <div className="p-2.5 rounded-md bg-emerald-500/10 text-emerald-400">
              <CheckCircle2 className="size-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Work Type Segmented Tabs */}
      <div className="flex items-center gap-1.5 p-1 bg-muted/40 rounded-lg border border-border overflow-x-auto">
        {WORK_TYPES.map((t) => {
          const Icon = t.icon;
          const isActive = selectedType === t.id;
          return (
            <button
              key={t.id}
              onClick={() => setSelectedType(t.id)}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-medium transition-colors shrink-0 ${
                isActive
                  ? 'bg-card text-foreground shadow-xs border border-border'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
              }`}
            >
              <Icon className="size-3.5" />
              <span>{t.label}</span>
            </button>
          );
        })}
      </div>

      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            placeholder="Search by reference, title, technician, or location..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 text-xs h-9"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="h-9 rounded-md border border-input bg-card px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring shrink-0"
        >
          <option value="ALL">All Statuses</option>
          <option value="DRAFT">DRAFT</option>
          <option value="SUBMITTED">SUBMITTED</option>
          <option value="APPROVED">APPROVED</option>
          <option value="ASSIGNED">ASSIGNED</option>
          <option value="IN_PROGRESS">IN PROGRESS</option>
          <option value="ON_HOLD">ON HOLD</option>
          <option value="COMPLETED">COMPLETED</option>
          <option value="VERIFIED">VERIFIED</option>
          <option value="CLOSED">CLOSED</option>
        </select>
      </div>

      {/* Main Table */}
      <Card className="bg-card border-border">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-12 text-center text-xs text-muted-foreground">Loading work units...</div>
          ) : items.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted-foreground border border-dashed rounded-lg m-4">
              No work items match the selected filters.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-border bg-muted/20 text-muted-foreground font-mono text-[11px]">
                    <th className="p-3 pl-4">REFERENCE</th>
                    <th className="p-3">TYPE</th>
                    <th className="p-3">TITLE & DEPARTMENT</th>
                    <th className="p-3">LOCATION & ASSET</th>
                    <th className="p-3">STATUS</th>
                    <th className="p-3">SLA</th>
                    <th className="p-3">ASSIGNED</th>
                    <th className="p-3 pr-4 text-right">ACTION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {items.map((item) => (
                    <tr key={item.id} className="hover:bg-muted/30 transition-colors">
                      <td className="p-3 pl-4 font-mono font-bold text-foreground">
                        {item.reference_number}
                      </td>
                      <td className="p-3">
                        {getTypeBadge(item.work_type)}
                      </td>
                      <td className="p-3 max-w-xs">
                        <div className="font-medium text-foreground truncate">{item.title}</div>
                        <div className="flex items-center gap-1 text-[11px] text-muted-foreground mt-0.5">
                          <Building2 className="size-3" />
                          <span>{item.department_name || 'General Operations'}</span>
                          {getPriorityBadge(item.priority)}
                        </div>
                      </td>
                      <td className="p-3 max-w-xs">
                        {item.location_breadcrumb && (
                          <div className="flex items-center gap-1 text-[11px] text-muted-foreground truncate">
                            <MapPin className="size-3 shrink-0 text-emerald-400" />
                            <span className="truncate">{item.location_breadcrumb}</span>
                          </div>
                        )}
                        {item.machine_identifier && (
                          <div className="flex items-center gap-1 text-[11px] text-blue-400 font-mono mt-0.5">
                            <Truck className="size-3 shrink-0" />
                            <span>{item.machine_identifier}</span>
                          </div>
                        )}
                      </td>
                      <td className="p-3">
                        <Badge variant="outline" className="font-mono text-[10px]">
                          {item.status}
                        </Badge>
                      </td>
                      <td className="p-3">
                        {getSlaBadge(item.sla_status)}
                      </td>
                      <td className="p-3 text-[11px] text-muted-foreground">
                        {item.assigned_personnel || item.supervisor_name || 'Unassigned'}
                      </td>
                      <td className="p-3 pr-4 text-right">
                        {item.job_card_id ? (
                          <Link href={`/jobs/${item.job_card_id}`}>
                            <Button variant="ghost" size="sm" className="h-7 text-xs gap-1">
                              <span>Open Job</span>
                              <ArrowUpRight className="size-3" />
                            </Button>
                          </Link>
                        ) : (
                          <Button variant="ghost" size="sm" className="h-7 text-xs gap-1">
                            <Eye className="size-3" />
                            <span>Inspect</span>
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Work Item Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <Card className="w-full max-w-xl bg-card border-border shadow-xl">
            <CardHeader className="border-b border-border pb-3">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Layers className="size-5 text-primary" />
                <span>Create New Work Item</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Initialize an operational trackable work unit with spatial hierarchy and SLA monitoring.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleCreateSubmit}>
              <CardContent className="p-4 space-y-3.5 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Work Type</label>
                    <select
                      value={newWorkType}
                      onChange={(e) => setNewWorkType(e.target.value)}
                      className="w-full h-8 rounded border border-input bg-card px-2 text-xs"
                    >
                      <option value="MAINTENANCE">MAINTENANCE</option>
                      <option value="INSPECTION">INSPECTION</option>
                      <option value="FOLLOW_UP">FOLLOW_UP</option>
                      <option value="JOB_CARD">JOB_CARD</option>
                      <option value="OTHER">OTHER</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Department *</label>
                    <select
                      value={newDeptId}
                      onChange={(e) => setNewDeptId(e.target.value)}
                      required
                      className="w-full h-8 rounded border border-input bg-card px-2 text-xs"
                    >
                      <option value="">Select Department...</option>
                      {departments.map((d) => (
                        <option key={d.id} value={d.id}>{d.name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-foreground">Work Title *</label>
                  <Input
                    required
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="e.g. 250hr Scheduled Lubrication on Conveyor C-01"
                    className="h-8 text-xs"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-foreground">Physical Location</label>
                  <LocationSelector
                    value={newLocationId}
                    onChange={(id) => setNewLocationId(id)}
                    placeholder="Search plant, facility, area or section..."
                  />
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Priority</label>
                    <select
                      value={newPriority}
                      onChange={(e) => setNewPriority(Number(e.target.value))}
                      className="w-full h-8 rounded border border-input bg-card px-2 text-xs"
                    >
                      <option value={0}>0 - Low (48h SLA)</option>
                      <option value={1}>1 - Medium (24h SLA)</option>
                      <option value={2}>2 - High (12h SLA)</option>
                      <option value={3}>3 - Urgent (6h SLA)</option>
                      <option value={4}>4 - Critical (2.4h SLA)</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Assigned Personnel</label>
                    <Input
                      value={newAssigned}
                      onChange={(e) => setNewAssigned(e.target.value)}
                      placeholder="Tech name / Team"
                      className="h-8 text-xs"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Due Date</label>
                    <Input
                      type="date"
                      value={newDueDate}
                      onChange={(e) => setNewDueDate(e.target.value)}
                      className="h-8 text-xs"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-foreground">Detailed Description / Instructions</label>
                  <textarea
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                    rows={3}
                    placeholder="Outline scope of work, safety requirements, and required parts..."
                    className="w-full rounded border border-input bg-card p-2 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
                  />
                </div>
              </CardContent>

              <div className="p-4 border-t border-border flex justify-end gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsCreateOpen(false)} className="text-xs">
                  Cancel
                </Button>
                <Button type="submit" size="sm" disabled={submitting} className="text-xs">
                  {submitting ? 'Creating...' : 'Create Work Unit'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
      </div>
    </Protect>
  );
}
