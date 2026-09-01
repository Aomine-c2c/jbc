'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { apiFetch } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Briefcase,
  Users,
  HardHat,
  ShieldCheck,
  Search,
  Plus,
  RefreshCw,
  Clock,
  Star,
  CheckCircle2,
  AlertTriangle,
  X,
  Eye,
  Building2,
  Calendar,
  DollarSign,
  FileCheck,
  Wrench,
} from 'lucide-react';

interface CompanyRow {
  id: string;
  company_code: string;
  name: string;
  primary_contact_name?: string;
  contact_phone?: string;
  service_categories: string[];
  status: string;
  safety_induction_valid_until?: string;
  worker_count: number;
  is_archived: boolean;
  created_at?: string;
}

interface WorkerRow {
  id: string;
  worker_code: string;
  full_name: string;
  skill_or_role: string;
  company_name?: string;
  status: string;
  certification_expiry?: string;
  phone_number?: string;
  badge_number?: string;
  created_at?: string;
}

interface AssignmentRow {
  id: string;
  assignment_number: string;
  company_name: string;
  work_scope: string;
  verification_status: string;
  supervisor_name?: string;
  performance_rating?: number;
  assignment_date: string;
  start_date?: string;
  completion_date?: string;
  work_item_reference?: string;
}

interface AssignmentDetail extends AssignmentRow {
  contractor_company_id: string;
  cost_agreed: number;
  actual_cost: number;
  performance_notes?: string;
  verified_by_name?: string;
  verified_at?: string;
  assigned_workers: WorkerRow[];
}

export default function ContractorsManagementPage() {
  const [activeTab, setActiveTab] = useState<'COMPANIES' | 'WORKERS' | 'ASSIGNMENTS'>('COMPANIES');
  const [companies, setCompanies] = useState<CompanyRow[]>([]);
  const [workers, setWorkers] = useState<WorkerRow[]>([]);
  const [assignments, setAssignments] = useState<AssignmentRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Detail & Verification Drawer
  const [selectedAssignment, setSelectedAssignment] = useState<AssignmentDetail | null>(null);
  const [verifyRating, setVerifyRating] = useState<number>(5);
  const [verifyNotes, setVerifyNotes] = useState('');
  const [verifyCost, setVerifyCost] = useState('');
  const [verifying, setVerifying] = useState(false);

  // Modals
  const [isCreateCompanyOpen, setIsCreateCompanyOpen] = useState(false);
  const [newCompanyName, setNewCompanyName] = useState('');
  const [newRegNum, setNewRegNum] = useState('');
  const [newContactName, setNewContactName] = useState('');
  const [newContactPhone, setNewContactPhone] = useState('');
  const [newContactEmail, setNewContactEmail] = useState('');
  const [newCategories, setNewCategories] = useState('');

  const [isCreateWorkerOpen, setIsCreateWorkerOpen] = useState(false);
  const [newWorkerCompanyId, setNewWorkerCompanyId] = useState('');
  const [newWorkerName, setNewWorkerName] = useState('');
  const [newWorkerRole, setNewWorkerRole] = useState('');
  const [newWorkerPhone, setNewWorkerPhone] = useState('');
  const [newWorkerBadge, setNewWorkerBadge] = useState('');

  const [isCreateAssignOpen, setIsCreateAssignOpen] = useState(false);
  const [newAssignCompanyId, setNewAssignCompanyId] = useState('');
  const [newAssignScope, setNewAssignScope] = useState('');
  const [newAssignCost, setNewAssignCost] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      if (activeTab === 'COMPANIES') {
        let url = `/api/v1/contractors/companies?limit=100`;
        if (statusFilter !== 'ALL') url += `&status=${statusFilter}`;
        if (searchQuery.trim()) url += `&search=${encodeURIComponent(searchQuery.trim())}`;
        const data = await apiFetch<CompanyRow[]>(url);
        setCompanies(data || []);
      } else if (activeTab === 'WORKERS') {
        let url = `/api/v1/contractors/workers?limit=100`;
        if (searchQuery.trim()) url += `&search=${encodeURIComponent(searchQuery.trim())}`;
        const data = await apiFetch<WorkerRow[]>(url);
        setWorkers(data || []);
      } else {
        let url = `/api/v1/contractors/assignments?limit=100`;
        if (searchQuery.trim()) url += `&search=${encodeURIComponent(searchQuery.trim())}`;
        const data = await apiFetch<AssignmentRow[]>(url);
        setAssignments(data || []);
      }

      // Always load companies for dropdowns
      const allCos = await apiFetch<CompanyRow[]>('/api/v1/contractors/companies?limit=200');
      if (allCos) setCompanies(allCos);
    } catch (err) {
      console.error('Failed to load contractor data', err);
    } finally {
      setLoading(false);
    }
  }, [activeTab, statusFilter, searchQuery]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const viewAssignmentDetail = async (id: string) => {
    try {
      const data = await apiFetch<AssignmentDetail>(`/api/v1/contractors/assignments/${id}`);
      setSelectedAssignment(data);
      if (data.performance_rating) setVerifyRating(data.performance_rating);
      if (data.performance_notes) setVerifyNotes(data.performance_notes);
      if (data.actual_cost) setVerifyCost(data.actual_cost.toString());
    } catch (err) {
      console.error('Failed to load assignment detail', err);
    }
  };

  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssignment) return;
    setVerifying(true);
    try {
      const updated = await apiFetch<AssignmentDetail>(`/api/v1/contractors/assignments/${selectedAssignment.id}/verify`, {
        method: 'POST',
        body: JSON.stringify({
          verification_status: 'VERIFIED_ACCEPTED',
          performance_rating: verifyRating,
          performance_notes: verifyNotes.trim() || undefined,
          actual_cost: verifyCost ? parseFloat(verifyCost) : selectedAssignment.cost_agreed,
        }),
      });
      setSelectedAssignment(updated);
      loadData();
    } catch (err) {
      console.error('Failed to verify assignment', err);
    } finally {
      setVerifying(false);
    }
  };

  const handleCreateCompanySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCompanyName.trim()) return;
    try {
      const cats = newCategories.split(',').map((c) => c.trim()).filter(Boolean);
      await apiFetch('/api/v1/contractors/companies', {
        method: 'POST',
        body: JSON.stringify({
          name: newCompanyName.trim(),
          registration_number: newRegNum.trim() || undefined,
          primary_contact_name: newContactName.trim() || undefined,
          contact_phone: newContactPhone.trim() || undefined,
          contact_email: newContactEmail.trim() || undefined,
          service_categories: cats,
        }),
      });
      setIsCreateCompanyOpen(false);
      setNewCompanyName('');
      setNewRegNum('');
      setNewCategories('');
      loadData();
    } catch (err) {
      console.error('Failed to create contractor company', err);
    }
  };

  const handleCreateWorkerSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWorkerCompanyId || !newWorkerName.trim() || !newWorkerRole.trim()) return;
    try {
      await apiFetch('/api/v1/contractors/workers', {
        method: 'POST',
        body: JSON.stringify({
          contractor_company_id: newWorkerCompanyId,
          full_name: newWorkerName.trim(),
          skill_or_role: newWorkerRole.trim(),
          phone_number: newWorkerPhone.trim() || undefined,
          badge_number: newWorkerBadge.trim() || undefined,
        }),
      });
      setIsCreateWorkerOpen(false);
      setNewWorkerName('');
      setNewWorkerRole('');
      setNewWorkerPhone('');
      loadData();
    } catch (err) {
      console.error('Failed to onboard contractor worker', err);
    }
  };

  const handleCreateAssignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAssignCompanyId || !newAssignScope.trim()) return;
    try {
      await apiFetch('/api/v1/contractors/assignments', {
        method: 'POST',
        body: JSON.stringify({
          contractor_company_id: newAssignCompanyId,
          work_scope: newAssignScope.trim(),
          cost_agreed: newAssignCost ? parseFloat(newAssignCost) : 0.0,
        }),
      });
      setIsCreateAssignOpen(false);
      setNewAssignScope('');
      setNewAssignCost('');
      loadData();
    } catch (err) {
      console.error('Failed to create assignment', err);
    }
  };

  const getStatusBadge = (st: string) => {
    switch (st) {
      case 'ACTIVE':
        return <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-[10px]">ACTIVE</Badge>;
      case 'SUSPENDED':
        return <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 text-[10px]">SUSPENDED</Badge>;
      case 'INACTIVE':
        return <Badge variant="secondary" className="text-[10px]">INACTIVE</Badge>;
      case 'PENDING':
        return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30 text-[10px]">PENDING</Badge>;
      case 'IN_PROGRESS':
        return <Badge className="bg-indigo-500/20 text-indigo-400 border-indigo-500/30 text-[10px]">IN PROGRESS</Badge>;
      case 'VERIFIED_ACCEPTED':
        return <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-[10px]">VERIFIED & ACCEPTED</Badge>;
      case 'REWORK_REQUIRED':
        return <Badge className="bg-rose-500/20 text-rose-400 border-rose-500/30 text-[10px]">REWORK REQUIRED</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px]">{st}</Badge>;
    }
  };

  // Metrics
  const totalCompanies = companies.length;
  const activeWorkers = workers.length;
  const totalAssignments = assignments.length;
  const pendingSignoffs = assignments.filter((a) => a.verification_status === 'PENDING').length;

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-primary/10 text-primary">
            <Briefcase className="size-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              Contractors & External Workforce
            </h1>
            <p className="text-xs text-muted-foreground">
              Manage contractor firms, external specialist technicians, trade qualifications, and quality verification sign-offs.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={loadData} disabled={loading} className="text-xs gap-1.5">
            <RefreshCw className={`size-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {activeTab === 'COMPANIES' && (
            <Button size="sm" onClick={() => setIsCreateCompanyOpen(true)} className="text-xs gap-1.5 bg-primary text-primary-foreground">
              <Plus className="size-3.5" />
              Register Contractor
            </Button>
          )}
          {activeTab === 'WORKERS' && (
            <Button size="sm" onClick={() => setIsCreateWorkerOpen(true)} className="text-xs gap-1.5 bg-primary text-primary-foreground">
              <Plus className="size-3.5" />
              Onboard Worker
            </Button>
          )}
          {activeTab === 'ASSIGNMENTS' && (
            <Button size="sm" onClick={() => setIsCreateAssignOpen(true)} className="text-xs gap-1.5 bg-primary text-primary-foreground">
              <Plus className="size-3.5" />
              New Assignment
            </Button>
          )}
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Registered Vendors</p>
              <p className="text-2xl font-mono font-bold text-foreground mt-1">{totalCompanies}</p>
            </div>
            <div className="p-2.5 rounded-md bg-muted text-muted-foreground">
              <Building2 className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Contractor Workers</p>
              <p className="text-2xl font-mono font-bold text-cyan-400 mt-1">{activeWorkers}</p>
            </div>
            <div className="p-2.5 rounded-md bg-cyan-500/10 text-cyan-400">
              <HardHat className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Work Engagements</p>
              <p className="text-2xl font-mono font-bold text-foreground mt-1">{totalAssignments}</p>
            </div>
            <div className="p-2.5 rounded-md bg-muted text-muted-foreground">
              <Briefcase className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Awaiting Sign-off</p>
              <p className="text-2xl font-mono font-bold text-amber-400 mt-1">{pendingSignoffs}</p>
            </div>
            <div className="p-2.5 rounded-md bg-amber-500/10 text-amber-400">
              <Clock className="size-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Segmented View Tabs */}
      <div className="flex items-center gap-1.5 p-1 bg-muted/40 rounded-lg border border-border w-fit">
        <button
          onClick={() => setActiveTab('COMPANIES')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            activeTab === 'COMPANIES'
              ? 'bg-card text-foreground shadow-xs border border-border'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
          }`}
        >
          <Building2 className="size-3.5" />
          <span>Contractor Companies</span>
        </button>
        <button
          onClick={() => setActiveTab('WORKERS')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            activeTab === 'WORKERS'
              ? 'bg-card text-foreground shadow-xs border border-border'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
          }`}
        >
          <HardHat className="size-3.5" />
          <span>External Workers</span>
        </button>
        <button
          onClick={() => setActiveTab('ASSIGNMENTS')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            activeTab === 'ASSIGNMENTS'
              ? 'bg-card text-foreground shadow-xs border border-border'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
          }`}
        >
          <FileCheck className="size-3.5" />
          <span>Assignments & Sign-offs</span>
        </button>
      </div>

      {/* Filters */}
      <div className="relative w-full max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
        <Input
          placeholder={
            activeTab === 'COMPANIES'
              ? 'Search contractor firms, services, contacts...'
              : activeTab === 'WORKERS'
              ? 'Search workers, skills, roles, badges...'
              : 'Search assignments, scopes, numbers...'
          }
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9 text-xs h-9"
        />
      </div>

      {/* Main Table */}
      <Card className="bg-card border-border">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-12 text-center text-xs text-muted-foreground">Loading contractor directory...</div>
          ) : activeTab === 'COMPANIES' ? (
            companies.length === 0 ? (
              <div className="p-12 text-center text-xs text-muted-foreground border border-dashed rounded-lg m-4">
                No contractor companies found.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-border bg-muted/20 text-muted-foreground font-mono text-[11px]">
                      <th className="p-3 pl-4">CODE</th>
                      <th className="p-3">COMPANY NAME</th>
                      <th className="p-3">SERVICE CATEGORIES</th>
                      <th className="p-3">PRIMARY CONTACT</th>
                      <th className="p-3">WORKERS</th>
                      <th className="p-3">STATUS</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    {companies.map((co) => (
                      <tr key={co.id} className="hover:bg-muted/30 transition-colors">
                        <td className="p-3 pl-4 font-mono font-bold text-foreground">{co.company_code}</td>
                        <td className="p-3 font-semibold text-foreground">{co.name}</td>
                        <td className="p-3 max-w-xs">
                          <div className="flex flex-wrap gap-1">
                            {co.service_categories.map((c, i) => (
                              <Badge key={i} variant="outline" className="text-[10px] py-0">{c}</Badge>
                            ))}
                          </div>
                        </td>
                        <td className="p-3 text-muted-foreground">
                          <div>{co.primary_contact_name || '—'}</div>
                          {co.contact_phone && <div className="text-[10px] font-mono">{co.contact_phone}</div>}
                        </td>
                        <td className="p-3 font-mono font-bold text-cyan-400">{co.worker_count} active</td>
                        <td className="p-3">{getStatusBadge(co.status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          ) : activeTab === 'WORKERS' ? (
            workers.length === 0 ? (
              <div className="p-12 text-center text-xs text-muted-foreground border border-dashed rounded-lg m-4">
                No external contractor workers registered.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-border bg-muted/20 text-muted-foreground font-mono text-[11px]">
                      <th className="p-3 pl-4">CODE</th>
                      <th className="p-3">WORKER NAME</th>
                      <th className="p-3">TRADE SKILL / ROLE</th>
                      <th className="p-3">CONTRACTOR FIRM</th>
                      <th className="p-3">BADGE #</th>
                      <th className="p-3">STATUS</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    {workers.map((w) => (
                      <tr key={w.id} className="hover:bg-muted/30 transition-colors">
                        <td className="p-3 pl-4 font-mono font-bold text-foreground">{w.worker_code}</td>
                        <td className="p-3 font-semibold text-foreground">{w.full_name}</td>
                        <td className="p-3 text-cyan-400 font-medium">{w.skill_or_role}</td>
                        <td className="p-3 text-muted-foreground">{w.company_name}</td>
                        <td className="p-3 font-mono text-[11px] text-muted-foreground">{w.badge_number || '—'}</td>
                        <td className="p-3">{getStatusBadge(w.status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          ) : (
            /* Assignments Table */
            assignments.length === 0 ? (
              <div className="p-12 text-center text-xs text-muted-foreground border border-dashed rounded-lg m-4">
                No contractor assignments found.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-border bg-muted/20 text-muted-foreground font-mono text-[11px]">
                      <th className="p-3 pl-4">ASSIGNMENT #</th>
                      <th className="p-3">CONTRACTOR FIRM</th>
                      <th className="p-3">WORK SCOPE</th>
                      <th className="p-3">SUPERVISOR</th>
                      <th className="p-3">VERIFICATION</th>
                      <th className="p-3">RATING</th>
                      <th className="p-3 pr-4 text-right">ACTION</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    {assignments.map((a) => (
                      <tr key={a.id} className="hover:bg-muted/30 transition-colors">
                        <td className="p-3 pl-4 font-mono font-bold text-foreground">{a.assignment_number}</td>
                        <td className="p-3 font-semibold text-foreground">{a.company_name}</td>
                        <td className="p-3 max-w-sm">
                          <div className="truncate text-foreground">{a.work_scope}</div>
                          {a.work_item_reference && (
                            <div className="text-[10px] font-mono text-primary">WI: {a.work_item_reference}</div>
                          )}
                        </td>
                        <td className="p-3 text-muted-foreground">{a.supervisor_name || '—'}</td>
                        <td className="p-3">{getStatusBadge(a.verification_status)}</td>
                        <td className="p-3 font-mono">
                          {a.performance_rating ? (
                            <div className="flex items-center gap-1 text-amber-400 font-bold">
                              <Star className="size-3 fill-amber-400" />
                              <span>{a.performance_rating}/5</span>
                            </div>
                          ) : (
                            <span className="text-muted-foreground text-[10px]">Unrated</span>
                          )}
                        </td>
                        <td className="p-3 pr-4 text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => viewAssignmentDetail(a.id)}
                            className="h-7 text-xs gap-1"
                          >
                            <Eye className="size-3" />
                            <span>Sign-off</span>
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          )}
        </CardContent>
      </Card>

      {/* Assignment Sign-off Drawer */}
      {selectedAssignment && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-lg bg-card border-l border-border h-full flex flex-col shadow-2xl overflow-hidden">
            <div className="p-4 border-b border-border flex items-center justify-between bg-muted/20">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded bg-primary/10 text-primary">
                  <Briefcase className="size-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-foreground">{selectedAssignment.assignment_number}</h2>
                    {getStatusBadge(selectedAssignment.verification_status)}
                  </div>
                  <p className="text-[11px] text-muted-foreground">{selectedAssignment.company_name}</p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setSelectedAssignment(null)} className="size-8 p-0">
                <X className="size-4" />
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
              <div className="p-3.5 rounded-lg border border-border bg-card/60 space-y-2 text-[11px]">
                <div className="font-semibold text-foreground text-xs">Work Scope</div>
                <p className="text-foreground">{selectedAssignment.work_scope}</p>
                {selectedAssignment.work_item_reference && (
                  <div><span className="text-muted-foreground">Work Item: </span><span className="font-mono text-primary font-bold">{selectedAssignment.work_item_reference}</span></div>
                )}
                <div><span className="text-muted-foreground">Supervisor: </span><span className="text-foreground">{selectedAssignment.supervisor_name}</span></div>
                <div><span className="text-muted-foreground">Agreed Cost: </span><span className="font-mono text-emerald-400 font-bold">${selectedAssignment.cost_agreed.toFixed(2)}</span></div>
              </div>

              {/* Assigned Workers */}
              <div className="space-y-2">
                <div className="font-semibold text-foreground text-xs flex items-center gap-1.5">
                  <HardHat className="size-3.5 text-primary" />
                  <span>Assigned External Technicians</span>
                </div>
                {selectedAssignment.assigned_workers.length === 0 ? (
                  <div className="p-3 border border-dashed rounded-lg text-center text-muted-foreground text-[11px]">
                    No specific individual technicians logged (general contractor crew).
                  </div>
                ) : (
                  <div className="space-y-1.5">
                    {selectedAssignment.assigned_workers.map((w) => (
                      <div key={w.id} className="p-2.5 rounded border border-border bg-card/40 flex items-center justify-between text-[11px]">
                        <div>
                          <span className="font-semibold text-foreground">{w.full_name}</span>
                          <span className="text-muted-foreground ml-2">({w.skill_or_role})</span>
                        </div>
                        <span className="font-mono text-[10px] text-muted-foreground">{w.worker_code}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Quality Sign-off & Verification Form */}
              <form onSubmit={handleVerifySubmit} className="p-4 rounded-lg border border-border bg-card/60 space-y-3">
                <div className="font-semibold text-foreground text-xs flex items-center gap-1.5">
                  <ShieldCheck className="size-4 text-emerald-400" />
                  <span>Quality Sign-off & Performance Rating</span>
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-foreground text-[11px]">Performance Rating (1 to 5 Stars)</label>
                  <div className="flex items-center gap-2 pt-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        type="button"
                        key={star}
                        onClick={() => setVerifyRating(star)}
                        className="p-1 text-muted-foreground hover:text-amber-400 transition-colors"
                      >
                        <Star
                          className={`size-5 ${
                            star <= verifyRating ? 'text-amber-400 fill-amber-400' : 'text-muted-foreground'
                          }`}
                        />
                      </button>
                    ))}
                    <span className="font-mono font-bold text-amber-400 text-xs ml-2">{verifyRating} / 5</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-foreground text-[11px]">Actual Invoiced Cost ($)</label>
                  <Input
                    type="number"
                    value={verifyCost}
                    onChange={(e) => setVerifyCost(e.target.value)}
                    placeholder={selectedAssignment.cost_agreed.toString()}
                    className="h-8 text-xs font-mono"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-foreground text-[11px]">Verification Sign-off Notes</label>
                  <Input
                    value={verifyNotes}
                    onChange={(e) => setVerifyNotes(e.target.value)}
                    placeholder="Work inspected and verified to standard..."
                    className="h-8 text-xs"
                  />
                </div>

                <Button
                  type="submit"
                  disabled={verifying}
                  className="w-full text-xs bg-emerald-600 hover:bg-emerald-700 text-white gap-1.5"
                >
                  <CheckCircle2 className="size-3.5" />
                  Sign-off & Complete Verification
                </Button>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Create Company Modal */}
      {isCreateCompanyOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <Card className="w-full max-w-lg bg-card border-border shadow-xl">
            <CardHeader className="border-b border-border pb-3">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Building2 className="size-5 text-primary" />
                <span>Register Contractor Firm</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Onboard an external vendor, specialist service contractor, or equipment repairer.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleCreateCompanySubmit}>
              <CardContent className="p-4 space-y-3 text-xs">
                <div className="space-y-1">
                  <label className="font-medium text-foreground">Company Name *</label>
                  <Input
                    required
                    value={newCompanyName}
                    onChange={(e) => setNewCompanyName(e.target.value)}
                    placeholder="e.g. ABB High Voltage Services"
                    className="h-8 text-xs"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Registration / VAT #</label>
                    <Input
                      value={newRegNum}
                      onChange={(e) => setNewRegNum(e.target.value)}
                      placeholder="e.g. VAT-881902"
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Primary Contact Person</label>
                    <Input
                      value={newContactName}
                      onChange={(e) => setNewContactName(e.target.value)}
                      placeholder="e.g. Mark Zondo"
                      className="h-8 text-xs"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Contact Phone</label>
                    <Input
                      value={newContactPhone}
                      onChange={(e) => setNewContactPhone(e.target.value)}
                      placeholder="+263 77..."
                      className="h-8 text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Contact Email</label>
                    <Input
                      type="email"
                      value={newContactEmail}
                      onChange={(e) => setNewContactEmail(e.target.value)}
                      placeholder="contact@contractor.com"
                      className="h-8 text-xs"
                    />
                  </div>
                </div>
                <div className="space-y-1">
                  <label className="font-medium text-foreground">Service Categories (comma separated)</label>
                  <Input
                    value={newCategories}
                    onChange={(e) => setNewCategories(e.target.value)}
                    placeholder="High Voltage, Transformer Overhaul, Rigging"
                    className="h-8 text-xs"
                  />
                </div>
              </CardContent>
              <div className="p-4 border-t border-border flex justify-end gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsCreateCompanyOpen(false)} className="text-xs">
                  Cancel
                </Button>
                <Button type="submit" size="sm" className="text-xs">
                  Register Company
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Onboard Worker Modal */}
      {isCreateWorkerOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <Card className="w-full max-w-md bg-card border-border shadow-xl">
            <CardHeader className="border-b border-border pb-3">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <HardHat className="size-5 text-primary" />
                <span>Onboard Contractor Worker</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Register an external contractor technician with trade qualifications.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleCreateWorkerSubmit}>
              <CardContent className="p-4 space-y-3 text-xs">
                <div className="space-y-1">
                  <label className="font-medium text-foreground">Contractor Firm *</label>
                  <select
                    required
                    value={newWorkerCompanyId}
                    onChange={(e) => setNewWorkerCompanyId(e.target.value)}
                    className="w-full h-8 rounded border border-input bg-card px-2 text-xs"
                  >
                    <option value="">Select Contractor Company...</option>
                    {companies.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="font-medium text-foreground">Full Name *</label>
                  <Input
                    required
                    value={newWorkerName}
                    onChange={(e) => setNewWorkerName(e.target.value)}
                    placeholder="e.g. Tendai Chiweshe"
                    className="h-8 text-xs"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-medium text-foreground">Skill / Trade Role *</label>
                  <Input
                    required
                    value={newWorkerRole}
                    onChange={(e) => setNewWorkerRole(e.target.value)}
                    placeholder="e.g. 33kV Certified High Voltage Specialist"
                    className="h-8 text-xs"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Phone Number</label>
                    <Input
                      value={newWorkerPhone}
                      onChange={(e) => setNewWorkerPhone(e.target.value)}
                      placeholder="+263..."
                      className="h-8 text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Site Badge #</label>
                    <Input
                      value={newWorkerBadge}
                      onChange={(e) => setNewWorkerBadge(e.target.value)}
                      placeholder="EXT-001"
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                </div>
              </CardContent>
              <div className="p-4 border-t border-border flex justify-end gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsCreateWorkerOpen(false)} className="text-xs">
                  Cancel
                </Button>
                <Button type="submit" size="sm" className="text-xs">
                  Onboard Worker
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Create Assignment Modal */}
      {isCreateAssignOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <Card className="w-full max-w-lg bg-card border-border shadow-xl">
            <CardHeader className="border-b border-border pb-3">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Briefcase className="size-5 text-primary" />
                <span>Create Contractor Assignment</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Dispatch an external contractor firm to execute operational maintenance or specialized project work.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleCreateAssignSubmit}>
              <CardContent className="p-4 space-y-3 text-xs">
                <div className="space-y-1">
                  <label className="font-medium text-foreground">Contractor Firm *</label>
                  <select
                    required
                    value={newAssignCompanyId}
                    onChange={(e) => setNewAssignCompanyId(e.target.value)}
                    className="w-full h-8 rounded border border-input bg-card px-2 text-xs"
                  >
                    <option value="">Select Contractor Company...</option>
                    {companies.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="font-medium text-foreground">Work Scope & Specifications *</label>
                  <textarea
                    required
                    rows={3}
                    value={newAssignScope}
                    onChange={(e) => setNewAssignScope(e.target.value)}
                    placeholder="Describe specific tasks, equipment tags, safety rules, and deliverable expectations..."
                    className="w-full rounded border border-input bg-card p-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-medium text-foreground">Agreed Cost ($)</label>
                  <Input
                    type="number"
                    value={newAssignCost}
                    onChange={(e) => setNewAssignCost(e.target.value)}
                    placeholder="0.00"
                    className="h-8 text-xs font-mono"
                  />
                </div>
              </CardContent>
              <div className="p-4 border-t border-border flex justify-end gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsCreateAssignOpen(false)} className="text-xs">
                  Cancel
                </Button>
                <Button type="submit" size="sm" className="text-xs">
                  Create Assignment
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}
