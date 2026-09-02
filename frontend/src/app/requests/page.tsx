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
  FileText,
  Truck,
  Wrench,
  Package,
  Users,
  Briefcase,
  Search,
  Plus,
  RefreshCw,
  MapPin,
  Building2,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Send,
  Check,
  X,
  Eye,
  SlidersHorizontal,
  Layers,
  Archive,
  ArrowRight,
} from 'lucide-react';

interface RequestRow {
  id: string;
  request_number: string;
  request_type: string;
  title: string;
  purpose: string;
  priority: number;
  status: string;
  fulfillment_status: string;
  requester_name?: string;
  department_id: string;
  department_name?: string;
  collaborating_department_name?: string;
  location_breadcrumb?: string;
  required_from?: string;
  required_to?: string;
  work_item_id?: string;
  created_at?: string;
}

interface RequestDetail extends RequestRow {
  description?: string;
  estimated_duration_hours?: number;
  cost_centre?: string;
  estimated_cost?: number;
  actual_cost?: number;
  work_item_reference?: string;
  approver_name?: string;
  approved_at?: string;
  fulfillment_user_name?: string;
  fulfilled_at?: string;
  rejection_reason?: string;
  type_specific_data?: Record<string, any>;
  material_items: Array<{
    id: string;
    material_name: string;
    part_number?: string;
    quantity_requested: number;
    unit: string;
    store_location?: string;
    quantity_issued: number;
    quantity_returned: number;
    unit_cost: number;
  }>;
  action_logs: Array<{
    id: string;
    action: string;
    from_status?: string;
    to_status?: string;
    notes?: string;
    created_at: string;
    user_name?: string;
  }>;
  comments: Array<{
    id: string;
    comment: string;
    created_at: string;
    user_name?: string;
  }>;
}

interface DepartmentOption {
  id: string;
  name: string;
}

const REQUEST_TYPE_TABS = [
  { id: 'ALL', label: 'All Requests', icon: FileText },
  { id: 'MACHINE_REQUEST', label: 'Machinery', icon: Truck },
  { id: 'EQUIPMENT_REQUEST', label: 'Equipment', icon: Wrench },
  { id: 'VEHICLE_REQUEST', label: 'Vehicles', icon: Truck },
  { id: 'MATERIAL_REQUEST', label: 'Materials & Spares', icon: Package },
  { id: 'PERSONNEL_REQUEST', label: 'Personnel', icon: Users },
  { id: 'CONTRACTOR_REQUEST', label: 'Contractors', icon: Briefcase },
];

export default function UniversalRequestsPage() {
  const [requests, setRequests] = useState<RequestRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [fulfillmentFilter, setFulfillmentFilter] = useState('ALL');
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);

  // Detail Drawer
  const [selectedRequest, setSelectedRequest] = useState<RequestDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [actionNotes, setActionNotes] = useState('');
  const [actionSubmitting, setActionSubmitting] = useState(false);

  // Create Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newType, setNewType] = useState('MACHINE_REQUEST');
  const [newTitle, setNewTitle] = useState('');
  const [newPurpose, setNewPurpose] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newPriority, setNewPriority] = useState(1);
  const [newDeptId, setNewDeptId] = useState('');
  const [newCollabDeptId, setNewCollabDeptId] = useState('');
  const [newLocationId, setNewLocationId] = useState<string | null>(null);
  const [newRequiredFrom, setNewRequiredFrom] = useState('');
  const [newRequiredTo, setNewRequiredTo] = useState('');
  const [newDuration, setNewDuration] = useState('');
  const [newCost, setNewCost] = useState('');
  
  // Dynamic material items
  const [materials, setMaterials] = useState<Array<{ name: string; part: string; qty: number; unit: string }>>([
    { name: '', part: '', qty: 1, unit: 'units' },
  ]);

  // Dynamic contractor / personnel specs
  const [requiredSkill, setRequiredSkill] = useState('');
  const [workScope, setWorkScope] = useState('');
  const [contractorName, setContractorName] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadRequests = useCallback(async () => {
    setLoading(true);
    try {
      let url = `/api/v1/requests?limit=100`;
      if (selectedType !== 'ALL') {
        url += `&request_type=${selectedType}`;
      }
      if (statusFilter !== 'ALL') {
        url += `&status=${statusFilter}`;
      }
      if (fulfillmentFilter !== 'ALL') {
        url += `&fulfillment_status=${fulfillmentFilter}`;
      }
      if (searchQuery.trim()) {
        url += `&search=${encodeURIComponent(searchQuery.trim())}`;
      }
      const data = await apiFetch<RequestRow[]>(url);
      setRequests(data || []);

      const deptData = await apiFetch<DepartmentOption[]>('/api/v1/iam/departments');
      if (deptData) setDepartments(deptData);
    } catch (err) {
      console.error('Failed to load requests', err);
    } finally {
      setLoading(false);
    }
  }, [selectedType, statusFilter, fulfillmentFilter, searchQuery]);

  useEffect(() => {
    loadRequests();
  }, [loadRequests]);

  const viewRequestDetail = async (id: string) => {
    setDetailLoading(true);
    try {
      const data = await apiFetch<RequestDetail>(`/api/v1/requests/${id}`);
      setSelectedRequest(data);
    } catch (err) {
      console.error('Failed to load request details', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleTransition = async (action: string) => {
    if (!selectedRequest) return;
    setActionSubmitting(true);
    try {
      const updated = await apiFetch<RequestDetail>(`/api/v1/requests/${selectedRequest.id}/transition`, {
        method: 'POST',
        body: JSON.stringify({
          action,
          notes: actionNotes.trim() || undefined,
        }),
      });
      setSelectedRequest(updated);
      setActionNotes('');
      loadRequests();
    } catch (err) {
      console.error(`Failed to ${action} request`, err);
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleFulfill = async (fulfillment_status: string) => {
    if (!selectedRequest) return;
    setActionSubmitting(true);
    try {
      const updated = await apiFetch<RequestDetail>(`/api/v1/requests/${selectedRequest.id}/fulfill`, {
        method: 'POST',
        body: JSON.stringify({
          fulfillment_status,
          notes: actionNotes.trim() || undefined,
        }),
      });
      setSelectedRequest(updated);
      setActionNotes('');
      loadRequests();
    } catch (err) {
      console.error('Failed to fulfill request', err);
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRequest || !newComment.trim()) return;
    try {
      await apiFetch(`/api/v1/requests/${selectedRequest.id}/comments`, {
        method: 'POST',
        body: JSON.stringify({ comment: newComment.trim() }),
      });
      setNewComment('');
      viewRequestDetail(selectedRequest.id);
    } catch (err) {
      console.error('Failed to post comment', err);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newPurpose.trim() || !newDeptId) return;
    setSubmitting(true);
    try {
      const materialItemsPayload =
        newType === 'MATERIAL_REQUEST'
          ? materials
              .filter((m) => m.name.trim())
              .map((m) => ({
                material_name: m.name.trim(),
                part_number: m.part.trim() || undefined,
                quantity_requested: m.qty,
                unit: m.unit,
              }))
          : undefined;

      const typeSpecificPayload: Record<string, any> = {};
      if (requiredSkill) typeSpecificPayload.required_skill = requiredSkill.trim();
      if (workScope) typeSpecificPayload.work_scope = workScope.trim();
      if (contractorName) typeSpecificPayload.contractor_name = contractorName.trim();

      await apiFetch('/api/v1/requests', {
        method: 'POST',
        body: JSON.stringify({
          request_type: newType,
          title: newTitle.trim(),
          purpose: newPurpose.trim(),
          description: newDescription.trim() || undefined,
          priority: newPriority,
          department_id: newDeptId,
          collaborating_department_id: newCollabDeptId || undefined,
          location_id: newLocationId || undefined,
          required_from: newRequiredFrom ? new Date(newRequiredFrom).toISOString() : undefined,
          required_to: newRequiredTo ? new Date(newRequiredTo).toISOString() : undefined,
          estimated_duration_hours: newDuration ? parseFloat(newDuration) : 0.0,
          estimated_cost: newCost ? parseFloat(newCost) : 0.0,
          material_items: materialItemsPayload,
          type_specific_data: Object.keys(typeSpecificPayload).length > 0 ? typeSpecificPayload : undefined,
        }),
      });

      setIsCreateOpen(false);
      setNewTitle('');
      setNewPurpose('');
      setNewDescription('');
      setNewLocationId(null);
      setMaterials([{ name: '', part: '', qty: 1, unit: 'units' }]);
      setRequiredSkill('');
      setWorkScope('');
      setContractorName('');
      loadRequests();
    } catch (err) {
      console.error('Failed to create request', err);
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (st: string) => {
    switch (st) {
      case 'DRAFT':
        return <Badge variant="secondary" className="text-[10px]">DRAFT</Badge>;
      case 'SUBMITTED':
        return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30 text-[10px]">SUBMITTED</Badge>;
      case 'UNDER_REVIEW':
        return <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 text-[10px]">UNDER REVIEW</Badge>;
      case 'APPROVED':
        return <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-[10px]">APPROVED</Badge>;
      case 'FULFILLED':
      case 'CLOSED':
        return <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30 text-[10px]">{st}</Badge>;
      case 'REJECTED':
      case 'CANCELLED':
        return <Badge variant="destructive" className="text-[10px]">{st}</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px]">{st}</Badge>;
    }
  };

  const getFulfillmentBadge = (fst: string) => {
    switch (fst) {
      case 'UNALLOCATED':
        return <span className="text-[10px] font-mono text-muted-foreground">UNALLOCATED</span>;
      case 'AWAITING_FULFILLMENT':
        return <span className="text-[10px] font-mono text-amber-400 font-bold">AWAITING FULFILLMENT</span>;
      case 'PARTIALLY_FULFILLED':
        return <span className="text-[10px] font-mono text-blue-400 font-bold">PARTIAL</span>;
      case 'FULFILLED':
        return <span className="text-[10px] font-mono text-emerald-400 font-bold">FULFILLED</span>;
      case 'CLOSED':
        return <span className="text-[10px] font-mono text-purple-400 font-bold">CLOSED</span>;
      default:
        return <span className="text-[10px] font-mono text-muted-foreground">{fst}</span>;
    }
  };

  // Metrics
  const totalCount = requests.length;
  const pendingApproval = requests.filter((r) => ['SUBMITTED', 'UNDER_REVIEW'].includes(r.status)).length;
  const awaitingFulfillment = requests.filter((r) => r.fulfillment_status === 'AWAITING_FULFILLMENT' || r.fulfillment_status === 'PARTIALLY_FULFILLED').length;
  const completedCount = requests.filter((r) => ['FULFILLED', 'CLOSED'].includes(r.status)).length;

  return (
    <Protect capability="requisition:create" isPageGuard moduleName="Requests & Requisitions Hub">
      <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-primary/10 text-primary">
            <FileText className="size-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              Universal Requests & Requisitions Hub
            </h1>
            <p className="text-xs text-muted-foreground">
              Cross-departmental requisitions for machinery, equipment, fleet vehicles, store materials, personnel, and contractors.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={loadRequests} disabled={loading} className="text-xs gap-1.5">
            <RefreshCw className={`size-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button size="sm" onClick={() => setIsCreateOpen(true)} className="text-xs gap-1.5 bg-primary text-primary-foreground">
            <Plus className="size-3.5" />
            New Requisition
          </Button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Total Active</p>
              <p className="text-2xl font-mono font-bold text-foreground mt-1">{totalCount}</p>
            </div>
            <div className="p-2.5 rounded-md bg-muted text-muted-foreground">
              <FileText className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Pending Approval</p>
              <p className="text-2xl font-mono font-bold text-amber-400 mt-1">{pendingApproval}</p>
            </div>
            <div className="p-2.5 rounded-md bg-amber-500/10 text-amber-400">
              <Clock className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Awaiting Fulfillment</p>
              <p className="text-2xl font-mono font-bold text-blue-400 mt-1">{awaitingFulfillment}</p>
            </div>
            <div className="p-2.5 rounded-md bg-blue-500/10 text-blue-400">
              <Truck className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Fulfilled & Closed</p>
              <p className="text-2xl font-mono font-bold text-purple-400 mt-1">{completedCount}</p>
            </div>
            <div className="p-2.5 rounded-md bg-purple-500/10 text-purple-400">
              <CheckCircle2 className="size-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Segmented Type Filter Tabs */}
      <div className="flex items-center gap-1.5 p-1 bg-muted/40 rounded-lg border border-border overflow-x-auto">
        {REQUEST_TYPE_TABS.map((t) => {
          const Icon = t.icon;
          const isActive = selectedType === t.id;
          return (
            <button
              key={t.id}
              onClick={() => setSelectedType(t.id)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors shrink-0 ${
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

      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            placeholder="Search by request #, title, purpose, or location..."
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
          <option value="ALL">All Approval States</option>
          <option value="DRAFT">DRAFT</option>
          <option value="SUBMITTED">SUBMITTED</option>
          <option value="UNDER_REVIEW">UNDER REVIEW</option>
          <option value="APPROVED">APPROVED</option>
          <option value="REJECTED">REJECTED</option>
          <option value="CANCELLED">CANCELLED</option>
        </select>
        <select
          value={fulfillmentFilter}
          onChange={(e) => setFulfillmentFilter(e.target.value)}
          className="h-9 rounded-md border border-input bg-card px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring shrink-0"
        >
          <option value="ALL">All Fulfillment States</option>
          <option value="UNALLOCATED">UNALLOCATED</option>
          <option value="AWAITING_FULFILLMENT">AWAITING FULFILLMENT</option>
          <option value="PARTIALLY_FULFILLED">PARTIALLY FULFILLED</option>
          <option value="FULFILLED">FULFILLED</option>
          <option value="CLOSED">CLOSED</option>
        </select>
      </div>

      {/* Requests Table */}
      <Card className="bg-card border-border">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-12 text-center text-xs text-muted-foreground">Loading requisitions...</div>
          ) : requests.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted-foreground border border-dashed rounded-lg m-4">
              No requisitions found matching the query.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-border bg-muted/20 text-muted-foreground font-mono text-[11px]">
                    <th className="p-3 pl-4">REQ #</th>
                    <th className="p-3">TITLE & PURPOSE</th>
                    <th className="p-3">TYPE</th>
                    <th className="p-3">DEPARTMENT & LOCATION</th>
                    <th className="p-3">REQUESTER</th>
                    <th className="p-3">APPROVAL</th>
                    <th className="p-3">FULFILLMENT</th>
                    <th className="p-3 pr-4 text-right">ACTION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {requests.map((req) => (
                    <tr key={req.id} className="hover:bg-muted/30 transition-colors">
                      <td className="p-3 pl-4 font-mono font-bold text-foreground">
                        {req.request_number}
                      </td>
                      <td className="p-3 max-w-xs">
                        <div className="font-semibold text-foreground truncate">{req.title}</div>
                        <div className="text-[11px] text-muted-foreground truncate mt-0.5">{req.purpose}</div>
                      </td>
                      <td className="p-3">
                        <Badge variant="outline" className="font-mono text-[10px]">
                          {req.request_type.replace('_REQUEST', '')}
                        </Badge>
                      </td>
                      <td className="p-3 max-w-xs">
                        <div className="font-medium text-foreground">{req.department_name}</div>
                        {req.location_breadcrumb && (
                          <div className="flex items-center gap-1 text-[10px] text-muted-foreground truncate mt-0.5">
                            <MapPin className="size-3 shrink-0 text-emerald-400" />
                            <span className="truncate">{req.location_breadcrumb}</span>
                          </div>
                        )}
                      </td>
                      <td className="p-3 text-[11px] text-muted-foreground">
                        {req.requester_name}
                      </td>
                      <td className="p-3">
                        {getStatusBadge(req.status)}
                      </td>
                      <td className="p-3">
                        {getFulfillmentBadge(req.fulfillment_status)}
                      </td>
                      <td className="p-3 pr-4 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => viewRequestDetail(req.id)}
                          className="h-7 text-xs gap-1"
                        >
                          <Eye className="size-3" />
                          <span>Manage</span>
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Request Detail & Management Drawer */}
      {selectedRequest && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-2xl bg-card border-l border-border h-full flex flex-col shadow-2xl overflow-hidden">
            {/* Drawer Header */}
            <div className="p-4 border-b border-border flex items-center justify-between bg-muted/20">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded bg-primary/10 text-primary">
                  <FileText className="size-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-foreground">{selectedRequest.title}</h2>
                    <span className="font-mono text-xs text-primary font-bold">{selectedRequest.request_number}</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    {selectedRequest.request_type} • By {selectedRequest.requester_name}
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setSelectedRequest(null)} className="size-8 p-0">
                <X className="size-4" />
              </Button>
            </div>

            {/* Drawer Content */}
            <div className="flex-1 overflow-y-auto p-5 space-y-5 text-xs">
              {/* Lifecycle States */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg border border-border bg-card/60">
                  <div className="text-[10px] font-mono text-muted-foreground uppercase">Approval State</div>
                  <div className="mt-1 flex items-center gap-2">
                    {getStatusBadge(selectedRequest.status)}
                    {selectedRequest.approver_name && (
                      <span className="text-[10px] text-muted-foreground">by {selectedRequest.approver_name}</span>
                    )}
                  </div>
                </div>
                <div className="p-3 rounded-lg border border-border bg-card/60">
                  <div className="text-[10px] font-mono text-muted-foreground uppercase">Fulfillment State</div>
                  <div className="mt-1 flex items-center gap-2">
                    {getFulfillmentBadge(selectedRequest.fulfillment_status)}
                    {selectedRequest.fulfillment_user_name && (
                      <span className="text-[10px] text-muted-foreground">by {selectedRequest.fulfillment_user_name}</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Purpose & Description */}
              <div className="p-3.5 rounded-lg border border-border bg-card/60 space-y-2">
                <div className="font-semibold text-foreground text-xs">Purpose & Operational Scope</div>
                <p className="text-foreground">{selectedRequest.purpose}</p>
                {selectedRequest.description && (
                  <p className="text-muted-foreground pt-1 border-t border-border/40">{selectedRequest.description}</p>
                )}
                {selectedRequest.work_item_reference && (
                  <div className="pt-2 border-t border-border/40 flex items-center gap-1.5 text-primary font-mono font-bold">
                    <Layers className="size-3.5" />
                    <span>Linked Work Item: {selectedRequest.work_item_reference}</span>
                  </div>
                )}
              </div>

              {/* Material Line Items if MATERIAL_REQUEST */}
              {selectedRequest.material_items.length > 0 && (
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-foreground text-xs flex items-center gap-1.5">
                      <Package className="size-3.5 text-primary" />
                      <span>Requisitioned Materials & Spares</span>
                    </span>
                    <Badge variant="outline" className="text-[10px]">
                      {selectedRequest.material_items.length} items
                    </Badge>
                  </div>
                  <div className="border border-border rounded-lg overflow-hidden">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-muted/30 border-b border-border text-[10px] font-mono text-muted-foreground">
                        <tr>
                          <th className="p-2 pl-3">MATERIAL</th>
                          <th className="p-2">REQUESTED</th>
                          <th className="p-2">ISSUED</th>
                          <th className="p-2 pr-3">RETURNED</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/40 text-[11px]">
                        {selectedRequest.material_items.map((item) => (
                          <tr key={item.id}>
                            <td className="p-2 pl-3">
                              <div className="font-medium text-foreground">{item.material_name}</div>
                              {item.part_number && <div className="text-[10px] font-mono text-muted-foreground">PN: {item.part_number}</div>}
                            </td>
                            <td className="p-2 font-mono">{item.quantity_requested} {item.unit}</td>
                            <td className="p-2 font-mono text-emerald-400 font-bold">{item.quantity_issued} {item.unit}</td>
                            <td className="p-2 pr-3 font-mono text-muted-foreground">{item.quantity_returned} {item.unit}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Operational Actions */}
              <div className="p-3.5 rounded-lg border border-border bg-card/60 space-y-3">
                <div className="font-semibold text-foreground text-xs">Workflow & Fulfillment Actions</div>
                <Input
                  placeholder="Optional action notes / dispatch reference..."
                  value={actionNotes}
                  onChange={(e) => setActionNotes(e.target.value)}
                  className="h-8 text-xs"
                />
                <div className="flex flex-wrap items-center gap-2">
                  {selectedRequest.status === 'DRAFT' && (
                    <Button size="sm" onClick={() => handleTransition('SUBMIT')} disabled={actionSubmitting} className="text-xs gap-1">
                      <Send className="size-3" /> Submit for Approval
                    </Button>
                  )}
                  {selectedRequest.status === 'SUBMITTED' && (
                    <>
                      <Button size="sm" variant="outline" onClick={() => handleTransition('REVIEW')} disabled={actionSubmitting} className="text-xs">
                        Mark Under Review
                      </Button>
                      <Button size="sm" onClick={() => handleTransition('APPROVE')} disabled={actionSubmitting} className="text-xs bg-emerald-600 hover:bg-emerald-700 text-white gap-1">
                        <Check className="size-3" /> Approve Requisition
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => handleTransition('REJECT')} disabled={actionSubmitting} className="text-xs gap-1">
                        <X className="size-3" /> Reject
                      </Button>
                    </>
                  )}
                  {selectedRequest.status === 'UNDER_REVIEW' && (
                    <>
                      <Button size="sm" onClick={() => handleTransition('APPROVE')} disabled={actionSubmitting} className="text-xs bg-emerald-600 hover:bg-emerald-700 text-white gap-1">
                        <Check className="size-3" /> Approve Requisition
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => handleTransition('REJECT')} disabled={actionSubmitting} className="text-xs gap-1">
                        <X className="size-3" /> Reject
                      </Button>
                    </>
                  )}
                  {selectedRequest.status === 'APPROVED' && selectedRequest.fulfillment_status !== 'FULFILLED' && selectedRequest.fulfillment_status !== 'CLOSED' && (
                    <Button size="sm" onClick={() => handleFulfill('FULFILLED')} disabled={actionSubmitting} className="text-xs bg-purple-600 hover:bg-purple-700 text-white gap-1">
                      <Truck className="size-3" /> Dispatch / Complete Fulfillment
                    </Button>
                  )}
                </div>
              </div>

              {/* Action History & Comments */}
              <div className="space-y-3">
                <div className="font-semibold text-foreground text-xs">Action Audit Trail</div>
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {selectedRequest.action_logs.map((log) => (
                    <div key={log.id} className="p-2 rounded border border-border bg-card/40 text-[11px] flex items-center justify-between">
                      <div>
                        <span className="font-mono font-bold text-foreground uppercase">{log.action}</span>
                        {log.notes && <span className="text-muted-foreground ml-2">{log.notes}</span>}
                      </div>
                      <span className="font-mono text-[10px] text-muted-foreground">{new Date(log.created_at).toLocaleTimeString()}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Add Comment */}
              <form onSubmit={handleAddComment} className="flex gap-2">
                <Input
                  placeholder="Write a comment or query..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  className="h-8 text-xs"
                />
                <Button type="submit" size="sm" className="text-xs shrink-0">
                  Comment
                </Button>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Create Requisition Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <Card className="w-full max-w-xl bg-card border-border shadow-xl max-h-[90vh] flex flex-col">
            <CardHeader className="border-b border-border pb-3 shrink-0">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <FileText className="size-5 text-primary" />
                <span>Create Operational Requisition</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Submit a new request for machinery, specialized equipment, materials, personnel, or contractor services.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleCreateSubmit} className="flex-1 overflow-y-auto">
              <CardContent className="p-4 space-y-3.5 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Request Type *</label>
                    <select
                      value={newType}
                      onChange={(e) => setNewType(e.target.value)}
                      className="w-full h-8 rounded border border-input bg-card px-2 text-xs"
                    >
                      <option value="MACHINE_REQUEST">MACHINE REQUEST</option>
                      <option value="EQUIPMENT_REQUEST">EQUIPMENT REQUEST</option>
                      <option value="VEHICLE_REQUEST">VEHICLE REQUEST</option>
                      <option value="MATERIAL_REQUEST">MATERIAL REQUEST</option>
                      <option value="PERSONNEL_REQUEST">PERSONNEL REQUEST</option>
                      <option value="CONTRACTOR_REQUEST">CONTRACTOR REQUEST</option>
                      <option value="OTHER">OTHER</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Priority</label>
                    <select
                      value={newPriority}
                      onChange={(e) => setNewPriority(parseInt(e.target.value))}
                      className="w-full h-8 rounded border border-input bg-card px-2 text-xs"
                    >
                      <option value={0}>LOW</option>
                      <option value={1}>MEDIUM</option>
                      <option value={2}>HIGH</option>
                      <option value={3}>URGENT</option>
                      <option value={4}>CRITICAL</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-foreground">Title *</label>
                  <Input
                    required
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="e.g. 50T Mobile Crane for Slurry Pump Overhaul"
                    className="h-8 text-xs"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-foreground">Purpose & Justification *</label>
                  <Input
                    required
                    value={newPurpose}
                    onChange={(e) => setNewPurpose(e.target.value)}
                    placeholder="Reason why this resource/material is needed"
                    className="h-8 text-xs"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Requesting Department *</label>
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

                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Fulfilling / Target Dept</label>
                    <select
                      value={newCollabDeptId}
                      onChange={(e) => setNewCollabDeptId(e.target.value)}
                      className="w-full h-8 rounded border border-input bg-card px-2 text-xs"
                    >
                      <option value="">Auto / Internal</option>
                      {departments.map((d) => (
                        <option key={d.id} value={d.id}>{d.name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-foreground">Operational Location</label>
                  <LocationSelector
                    value={newLocationId}
                    onChange={(id) => setNewLocationId(id)}
                    placeholder="Search plant, facility, area, or section..."
                  />
                </div>

                {/* Conditional Material Line Items */}
                {newType === 'MATERIAL_REQUEST' && (
                  <div className="space-y-2 p-3 rounded-lg border border-border bg-muted/20">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-foreground text-xs">Material Line Items</span>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setMaterials([...materials, { name: '', part: '', qty: 1, unit: 'units' }])}
                        className="h-6 text-[10px]"
                      >
                        + Add Item
                      </Button>
                    </div>
                    {materials.map((m, idx) => (
                      <div key={idx} className="grid grid-cols-4 gap-2 items-center">
                        <Input
                          placeholder="Material Name *"
                          value={m.name}
                          onChange={(e) => {
                            const copy = [...materials];
                            copy[idx].name = e.target.value;
                            setMaterials(copy);
                          }}
                          className="h-7 text-xs col-span-2"
                        />
                        <Input
                          placeholder="Part #"
                          value={m.part}
                          onChange={(e) => {
                            const copy = [...materials];
                            copy[idx].part = e.target.value;
                            setMaterials(copy);
                          }}
                          className="h-7 text-xs font-mono"
                        />
                        <Input
                          type="number"
                          placeholder="Qty"
                          value={m.qty}
                          onChange={(e) => {
                            const copy = [...materials];
                            copy[idx].qty = parseFloat(e.target.value) || 1;
                            setMaterials(copy);
                          }}
                          className="h-7 text-xs font-mono"
                        />
                      </div>
                    ))}
                  </div>
                )}

                {/* Conditional Contractor / Personnel Fields */}
                {(newType === 'CONTRACTOR_REQUEST' || newType === 'PERSONNEL_REQUEST') && (
                  <div className="space-y-2 p-3 rounded-lg border border-border bg-muted/20">
                    <div className="space-y-1">
                      <label className="font-medium text-foreground">Required Skill / Trade</label>
                      <Input
                        value={requiredSkill}
                        onChange={(e) => setRequiredSkill(e.target.value)}
                        placeholder="e.g. High Voltage Certified Lineman / Rigger Class 1"
                        className="h-8 text-xs"
                      />
                    </div>
                    {newType === 'CONTRACTOR_REQUEST' && (
                      <div className="space-y-1">
                        <label className="font-medium text-foreground">Preferred Contractor / Company</label>
                        <Input
                          value={contractorName}
                          onChange={(e) => setContractorName(e.target.value)}
                          placeholder="e.g. ZESA Transmission Services"
                          className="h-8 text-xs"
                        />
                      </div>
                    )}
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Est. Duration (Hours)</label>
                    <Input
                      type="number"
                      value={newDuration}
                      onChange={(e) => setNewDuration(e.target.value)}
                      placeholder="e.g. 8.0"
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Est. Budget / Cost ($)</label>
                    <Input
                      type="number"
                      value={newCost}
                      onChange={(e) => setNewCost(e.target.value)}
                      placeholder="0.00"
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                </div>
              </CardContent>

              <div className="p-4 border-t border-border flex justify-end gap-2 shrink-0">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsCreateOpen(false)} className="text-xs">
                  Cancel
                </Button>
                <Button type="submit" size="sm" disabled={submitting} className="text-xs">
                  {submitting ? 'Creating...' : 'Submit Requisition'}
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
