'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { apiFetch } from '@/lib/api';
import { Protect } from '@/components/auth/Protect';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Package,
  Layers,
  Search,
  Plus,
  RefreshCw,
  CheckCircle2,
  Clock,
  Check,
  X,
  Eye,
  Truck,
  RotateCcw,
  Boxes,
  Database,
} from 'lucide-react';

interface MaterialReqRow {
  id: string;
  requirement_number: string;
  material_name: string;
  part_number?: string;
  category?: string;
  unit: string;
  unit_cost: number;
  quantity_required: number;
  quantity_approved: number;
  quantity_issued: number;
  quantity_used: number;
  quantity_returned: number;
  status: string;
  store_location?: string;
  department_name?: string;
  requester_name?: string;
  work_item_id?: string;
  created_at?: string;
}

interface MaterialReqDetail extends MaterialReqRow {
  purpose?: string;
  notes?: string;
  approver_name?: string;
  approved_at?: string;
  work_item_reference?: string;
  asset_name?: string;
  transactions: Array<{
    id: string;
    transaction_type: string;
    quantity: number;
    unit: string;
    unit_cost: number;
    total_cost: number;
    store_location?: string;
    batch_or_serial?: string;
    issued_by_name?: string;
    received_by_name?: string;
    notes?: string;
    external_reference?: string;
    created_at: string;
  }>;
}

interface CatalogItem {
  id: string;
  part_number: string;
  name: string;
  description?: string;
  category?: string;
  unit_of_measure: string;
  default_unit_cost: number;
  primary_store?: string;
}

interface DepartmentOption {
  id: string;
  name: string;
}

import { MOCK_DEPARTMENTS, MOCK_MATERIAL_REQUIREMENTS, MOCK_MATERIALS_CATALOG } from '@/lib/mockData';

export default function MaterialsManagementPage() {
  const [activeTab, setActiveTab] = useState<'REQUIREMENTS' | 'CATALOG'>('REQUIREMENTS');
  const [requirements, setRequirements] = useState<MaterialReqRow[]>(MOCK_MATERIAL_REQUIREMENTS);
  const [catalog, setCatalog] = useState<CatalogItem[]>(MOCK_MATERIALS_CATALOG);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [departments, setDepartments] = useState<DepartmentOption[]>(MOCK_DEPARTMENTS);

  // Detail & Action Drawer
  const [selectedReq, setSelectedReq] = useState<MaterialReqDetail | null>(null);
  const [actionNotes, setActionNotes] = useState('');
  const [actionQty, setActionQty] = useState('');
  const [actionSubmitting, setActionSubmitting] = useState(false);

  // Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newMatName, setNewMatName] = useState('');
  const [newPartNum, setNewPartNum] = useState('');
  const [newUnit, setNewUnit] = useState('units');
  const [newUnitCost, setNewUnitCost] = useState('');
  const [newQtyRequired, setNewQtyRequired] = useState('1');
  const [newStore, setNewStore] = useState('');
  const [newPurpose, setNewPurpose] = useState('');
  const [newDeptId, setNewDeptId] = useState('');
  const [selectedCatalogId, setSelectedCatalogId] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const reqUrl = `/api/v1/materials/requirements?limit=100${statusFilter !== 'ALL' ? `&status=${statusFilter}` : ''}${searchQuery.trim() ? `&search=${encodeURIComponent(searchQuery.trim())}` : ''}`;
      const catUrl = `/api/v1/materials/catalog?limit=100${searchQuery.trim() ? `&search=${encodeURIComponent(searchQuery.trim())}` : ''}`;

      const [reqsRes, catRes, deptsRes] = await Promise.allSettled([
        apiFetch<MaterialReqRow[]>(reqUrl),
        apiFetch<CatalogItem[]>(catUrl),
        apiFetch<DepartmentOption[]>('/api/v1/iam/departments')
      ]);

      if (reqsRes.status === 'fulfilled' && Array.isArray(reqsRes.value) && reqsRes.value.length > 0) {
        setRequirements(reqsRes.value);
      } else {
        setRequirements(MOCK_MATERIAL_REQUIREMENTS);
      }

      if (catRes.status === 'fulfilled' && Array.isArray(catRes.value) && catRes.value.length > 0) {
        setCatalog(catRes.value);
      } else {
        setCatalog(MOCK_MATERIALS_CATALOG);
      }

      if (deptsRes.status === 'fulfilled' && Array.isArray(deptsRes.value) && deptsRes.value.length > 0) {
        setDepartments(deptsRes.value);
      } else {
        setDepartments(MOCK_DEPARTMENTS);
      }
    } catch (err) {
      console.warn('Failed to load materials from server, using synthetic fallback:', err);
      setRequirements(MOCK_MATERIAL_REQUIREMENTS);
      setCatalog(MOCK_MATERIALS_CATALOG);
      setDepartments(MOCK_DEPARTMENTS);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, searchQuery]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const viewDetail = async (id: string) => {
    try {
      const data = await apiFetch<MaterialReqDetail>(`/api/v1/materials/requirements/${id}`);
      setSelectedReq(data);
    } catch (err) {
      console.error('Failed to load detail', err);
    }
  };

  const handleApprove = async () => {
    if (!selectedReq) return;
    setActionSubmitting(true);
    try {
      const updated = await apiFetch<MaterialReqDetail>(`/api/v1/materials/requirements/${selectedReq.id}/approve`, {
        method: 'POST',
        body: JSON.stringify({
          quantity_approved: selectedReq.quantity_required,
          notes: actionNotes.trim() || undefined,
        }),
      });
      setSelectedReq(updated);
      setActionNotes('');
      loadData();
    } catch (err) {
      console.error('Failed to approve', err);
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleIssue = async () => {
    if (!selectedReq || !actionQty) return;
    setActionSubmitting(true);
    try {
      await apiFetch(`/api/v1/materials/requirements/${selectedReq.id}/issue`, {
        method: 'POST',
        body: JSON.stringify({
          quantity: parseFloat(actionQty),
          notes: actionNotes.trim() || undefined,
        }),
      });
      viewDetail(selectedReq.id);
      setActionNotes('');
      setActionQty('');
      loadData();
    } catch (err) {
      console.error('Failed to issue', err);
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleUsage = async () => {
    if (!selectedReq || !actionQty) return;
    setActionSubmitting(true);
    try {
      await apiFetch(`/api/v1/materials/requirements/${selectedReq.id}/usage`, {
        method: 'POST',
        body: JSON.stringify({
          quantity: parseFloat(actionQty),
          notes: actionNotes.trim() || undefined,
        }),
      });
      viewDetail(selectedReq.id);
      setActionNotes('');
      setActionQty('');
      loadData();
    } catch (err) {
      console.error('Failed to record usage', err);
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleReturn = async () => {
    if (!selectedReq || !actionQty) return;
    setActionSubmitting(true);
    try {
      await apiFetch(`/api/v1/materials/requirements/${selectedReq.id}/return`, {
        method: 'POST',
        body: JSON.stringify({
          quantity: parseFloat(actionQty),
          notes: actionNotes.trim() || undefined,
        }),
      });
      viewDetail(selectedReq.id);
      setActionNotes('');
      setActionQty('');
      loadData();
    } catch (err) {
      console.error('Failed to return', err);
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMatName.trim() || !newDeptId) return;
    try {
      await apiFetch('/api/v1/materials/requirements', {
        method: 'POST',
        body: JSON.stringify({
          catalog_item_id: selectedCatalogId || undefined,
          material_name: newMatName.trim(),
          part_number: newPartNum.trim() || undefined,
          unit: newUnit,
          unit_cost: newUnitCost ? parseFloat(newUnitCost) : 0.0,
          quantity_required: parseFloat(newQtyRequired) || 1.0,
          store_location: newStore.trim() || undefined,
          purpose: newPurpose.trim() || undefined,
          department_id: newDeptId,
        }),
      });
      setIsCreateOpen(false);
      setNewMatName('');
      setNewPartNum('');
      setNewPurpose('');
      setSelectedCatalogId('');
      loadData();
    } catch (err) {
      console.error('Failed to create material requirement', err);
    }
  };

  const getStatusBadge = (st: string) => {
    switch (st) {
      case 'REQUESTED':
        return <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 text-[10px]">REQUESTED</Badge>;
      case 'APPROVED':
        return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30 text-[10px]">APPROVED</Badge>;
      case 'PARTIALLY_ISSUED':
        return <Badge className="bg-indigo-500/20 text-indigo-400 border-indigo-500/30 text-[10px]">PARTIAL ISSUE</Badge>;
      case 'ISSUED':
        return <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-[10px]">ISSUED</Badge>;
      case 'IN_USE':
        return <Badge className="bg-cyan-500/20 text-cyan-400 border-cyan-500/30 text-[10px]">IN USE ON SITE</Badge>;
      case 'CONSUMED':
        return <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30 text-[10px]">CONSUMED</Badge>;
      case 'RETURNED':
        return <Badge variant="secondary" className="text-[10px]">RETURNED</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px]">{st}</Badge>;
    }
  };

  // Metrics
  const totalCount = requirements.length;
  const pendingIssue = requirements.filter((r) => ['APPROVED', 'PARTIALLY_ISSUED'].includes(r.status)).length;
  const inUseCount = requirements.filter((r) => ['ISSUED', 'IN_USE'].includes(r.status)).length;
  const totalValue = requirements.reduce((acc, r) => acc + (r.quantity_issued * r.unit_cost), 0);

  return (
    <Protect capability="materials:view" isPageGuard moduleName="Materials & Stores Management">
      <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-primary/10 text-primary">
            <Package className="size-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              Materials & Stores Management
            </h1>
            <p className="text-xs text-muted-foreground">
              Track material requirements, warehouse store issues, on-site consumption, and unused returns with ERP decoupling.
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
            Request Material
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Total Requirements</p>
              <p className="text-2xl font-mono font-bold text-foreground mt-1">{totalCount}</p>
            </div>
            <div className="p-2.5 rounded-md bg-muted text-muted-foreground">
              <Package className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Awaiting Store Issue</p>
              <p className="text-2xl font-mono font-bold text-amber-400 mt-1">{pendingIssue}</p>
            </div>
            <div className="p-2.5 rounded-md bg-amber-500/10 text-amber-400">
              <Clock className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">In Use on Site</p>
              <p className="text-2xl font-mono font-bold text-cyan-400 mt-1">{inUseCount}</p>
            </div>
            <div className="p-2.5 rounded-md bg-cyan-500/10 text-cyan-400">
              <Layers className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Issued Material Cost</p>
              <p className="text-2xl font-mono font-bold text-emerald-400 mt-1">${totalValue.toFixed(2)}</p>
            </div>
            <div className="p-2.5 rounded-md bg-emerald-500/10 text-emerald-400">
              <Boxes className="size-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Segmented View Tabs */}
      <div className="flex items-center gap-1.5 p-1 bg-muted/40 rounded-lg border border-border w-fit">
        <button
          onClick={() => setActiveTab('REQUIREMENTS')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            activeTab === 'REQUIREMENTS'
              ? 'bg-card text-foreground shadow-xs border border-border'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
          }`}
        >
          <Package className="size-3.5" />
          <span>Material Requirements</span>
        </button>
        <button
          onClick={() => setActiveTab('CATALOG')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            activeTab === 'CATALOG'
              ? 'bg-card text-foreground shadow-xs border border-border'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
          }`}
        >
          <Database className="size-3.5" />
          <span>Spare Parts Catalog</span>
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            placeholder="Search by part number, material name, requirement #, or store..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 text-xs h-9"
          />
        </div>
        {activeTab === 'REQUIREMENTS' && (
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-9 rounded-md border border-input bg-card px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring shrink-0"
          >
            <option value="ALL">All Statuses</option>
            <option value="REQUESTED">REQUESTED</option>
            <option value="APPROVED">APPROVED</option>
            <option value="PARTIALLY_ISSUED">PARTIAL ISSUE</option>
            <option value="ISSUED">ISSUED</option>
            <option value="IN_USE">IN USE</option>
            <option value="CONSUMED">CONSUMED</option>
            <option value="RETURNED">RETURNED</option>
          </select>
        )}
      </div>

      {/* Main Table */}
      <Card className="bg-card border-border">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-12 text-center text-xs text-muted-foreground">Loading materials ledger...</div>
          ) : activeTab === 'REQUIREMENTS' ? (
            requirements.length === 0 ? (
              <div className="p-12 text-center text-xs text-muted-foreground border border-dashed rounded-lg m-4">
                No material requirements found.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-border bg-muted/20 text-muted-foreground font-mono text-[11px]">
                      <th className="p-3 pl-4">REQ #</th>
                      <th className="p-3">MATERIAL & PART #</th>
                      <th className="p-3">STORE</th>
                      <th className="p-3">QUANTITIES (REQ / ISSUED / USED / RET)</th>
                      <th className="p-3">UNIT COST</th>
                      <th className="p-3">STATUS</th>
                      <th className="p-3">DEPARTMENT</th>
                      <th className="p-3 pr-4 text-right">ACTION</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    {requirements.map((req) => (
                      <tr key={req.id} className="hover:bg-muted/30 transition-colors">
                        <td className="p-3 pl-4 font-mono font-bold text-foreground">
                          {req.requirement_number}
                        </td>
                        <td className="p-3 max-w-xs">
                          <div className="font-semibold text-foreground truncate">{req.material_name}</div>
                          {req.part_number && (
                            <div className="text-[10px] font-mono text-muted-foreground">PN: {req.part_number}</div>
                          )}
                        </td>
                        <td className="p-3 text-muted-foreground">
                          {req.store_location || 'Central Stores'}
                        </td>
                        <td className="p-3 font-mono text-[11px]">
                          <span>{req.quantity_required} req</span> •{' '}
                          <span className="text-emerald-400 font-bold">{req.quantity_issued} iss</span> •{' '}
                          <span className="text-cyan-400 font-bold">{req.quantity_used} use</span> •{' '}
                          <span className="text-muted-foreground">{req.quantity_returned} ret</span>
                        </td>
                        <td className="p-3 font-mono font-semibold text-foreground">
                          ${req.unit_cost.toFixed(2)}
                        </td>
                        <td className="p-3">
                          {getStatusBadge(req.status)}
                        </td>
                        <td className="p-3 text-[11px] text-muted-foreground">
                          {req.department_name}
                        </td>
                        <td className="p-3 pr-4 text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => viewDetail(req.id)}
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
            )
          ) : (
            /* Catalog Table */
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-border bg-muted/20 text-muted-foreground font-mono text-[11px]">
                    <th className="p-3 pl-4">PART NUMBER</th>
                    <th className="p-3">ITEM NAME & DESCRIPTION</th>
                    <th className="p-3">CATEGORY</th>
                    <th className="p-3">UNIT</th>
                    <th className="p-3">DEFAULT COST</th>
                    <th className="p-3 pr-4">PRIMARY STORE</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {catalog.map((item) => (
                    <tr key={item.id} className="hover:bg-muted/30 transition-colors">
                      <td className="p-3 pl-4 font-mono font-bold text-foreground">
                        {item.part_number}
                      </td>
                      <td className="p-3 max-w-sm">
                        <div className="font-semibold text-foreground">{item.name}</div>
                        {item.description && (
                          <div className="text-[11px] text-muted-foreground truncate">{item.description}</div>
                        )}
                      </td>
                      <td className="p-3">
                        <Badge variant="outline" className="text-[10px]">{item.category || 'General'}</Badge>
                      </td>
                      <td className="p-3 font-mono text-muted-foreground">{item.unit_of_measure}</td>
                      <td className="p-3 font-mono font-bold text-emerald-400">${item.default_unit_cost.toFixed(2)}</td>
                      <td className="p-3 pr-4 text-muted-foreground">{item.primary_store || 'Central Warehouse'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Material Detail & Store Action Drawer */}
      {selectedReq && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-2xl bg-card border-l border-border h-full flex flex-col shadow-2xl overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-border flex items-center justify-between bg-muted/20">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded bg-primary/10 text-primary">
                  <Package className="size-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-foreground">{selectedReq.material_name}</h2>
                    <span className="font-mono text-xs text-primary font-bold">{selectedReq.requirement_number}</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    {selectedReq.part_number ? `PN: ${selectedReq.part_number} • ` : ''}Requested by {selectedReq.requester_name}
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setSelectedReq(null)} className="size-8 p-0">
                <X className="size-4" />
              </Button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-5 space-y-5 text-xs">
              {/* Quantities Status Card */}
              <div className="p-4 rounded-lg border border-border bg-card/60 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-foreground text-xs">Quantities & Fulfillment Flow</span>
                  {getStatusBadge(selectedReq.status)}
                </div>
                <div className="grid grid-cols-5 gap-2 text-center">
                  <div className="p-2 rounded bg-muted/30 border border-border/50">
                    <div className="text-[10px] text-muted-foreground uppercase">Required</div>
                    <div className="font-mono font-bold text-foreground mt-0.5">{selectedReq.quantity_required}</div>
                  </div>
                  <div className="p-2 rounded bg-muted/30 border border-border/50">
                    <div className="text-[10px] text-muted-foreground uppercase">Approved</div>
                    <div className="font-mono font-bold text-blue-400 mt-0.5">{selectedReq.quantity_approved}</div>
                  </div>
                  <div className="p-2 rounded bg-muted/30 border border-border/50">
                    <div className="text-[10px] text-muted-foreground uppercase">Issued</div>
                    <div className="font-mono font-bold text-emerald-400 mt-0.5">{selectedReq.quantity_issued}</div>
                  </div>
                  <div className="p-2 rounded bg-muted/30 border border-border/50">
                    <div className="text-[10px] text-muted-foreground uppercase">Used</div>
                    <div className="font-mono font-bold text-cyan-400 mt-0.5">{selectedReq.quantity_used}</div>
                  </div>
                  <div className="p-2 rounded bg-muted/30 border border-border/50">
                    <div className="text-[10px] text-muted-foreground uppercase">Returned</div>
                    <div className="font-mono font-bold text-purple-400 mt-0.5">{selectedReq.quantity_returned}</div>
                  </div>
                </div>
              </div>

              {/* Operational Context */}
              <div className="p-3.5 rounded-lg border border-border bg-card/60 space-y-2 text-[11px]">
                <div className="font-semibold text-foreground text-xs">Requirement Details</div>
                <div><span className="text-muted-foreground">Purpose: </span><span className="text-foreground">{selectedReq.purpose || 'General Maintenance'}</span></div>
                <div><span className="text-muted-foreground">Store Source: </span><span className="text-foreground">{selectedReq.store_location || 'Central Stores'}</span></div>
                {selectedReq.work_item_reference && (
                  <div><span className="text-muted-foreground">Work Item: </span><span className="font-mono text-primary font-bold">{selectedReq.work_item_reference}</span></div>
                )}
                {selectedReq.asset_name && (
                  <div><span className="text-muted-foreground">Linked Asset: </span><span className="text-foreground font-medium">{selectedReq.asset_name}</span></div>
                )}
              </div>

              {/* Store & Fulfillment Operations */}
              <div className="p-4 rounded-lg border border-border bg-card/60 space-y-3">
                <div className="font-semibold text-foreground text-xs">Store & Operational Actions</div>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    type="number"
                    placeholder="Quantity to action..."
                    value={actionQty}
                    onChange={(e) => setActionQty(e.target.value)}
                    className="h-8 text-xs font-mono"
                  />
                  <Input
                    placeholder="Action notes / reason..."
                    value={actionNotes}
                    onChange={(e) => setActionNotes(e.target.value)}
                    className="h-8 text-xs"
                  />
                </div>
                <div className="flex flex-wrap gap-2 pt-1">
                  {selectedReq.status === 'REQUESTED' && (
                    <Button size="sm" onClick={handleApprove} disabled={actionSubmitting} className="text-xs bg-blue-600 hover:bg-blue-700 text-white gap-1">
                      <Check className="size-3" /> Approve Requirement
                    </Button>
                  )}
                  {['APPROVED', 'PARTIALLY_ISSUED'].includes(selectedReq.status) && (
                    <Button size="sm" onClick={handleIssue} disabled={actionSubmitting || !actionQty} className="text-xs bg-emerald-600 hover:bg-emerald-700 text-white gap-1">
                      <Truck className="size-3" /> Issue from Stores (Goods Issue)
                    </Button>
                  )}
                  {['ISSUED', 'IN_USE'].includes(selectedReq.status) && (
                    <>
                      <Button size="sm" onClick={handleUsage} disabled={actionSubmitting || !actionQty} className="text-xs bg-cyan-600 hover:bg-cyan-700 text-white gap-1">
                        <CheckCircle2 className="size-3" /> Record Consumption / Usage
                      </Button>
                      <Button size="sm" onClick={handleReturn} disabled={actionSubmitting || !actionQty} className="text-xs bg-purple-600 hover:bg-purple-700 text-white gap-1">
                        <RotateCcw className="size-3" /> Return to Stores (Goods Return)
                      </Button>
                    </>
                  )}
                </div>
              </div>

              {/* Transactions Ledger */}
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-foreground text-xs flex items-center gap-1.5">
                    <Boxes className="size-3.5 text-primary" />
                    <span>Material Transactions & ERP Audit Ledger</span>
                  </span>
                  <Badge variant="outline" className="text-[10px]">
                    {selectedReq.transactions.length} movements
                  </Badge>
                </div>
                {selectedReq.transactions.length === 0 ? (
                  <div className="p-4 border border-dashed rounded-lg text-center text-muted-foreground text-[11px]">
                    No transactions recorded yet.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {selectedReq.transactions.map((tx) => (
                      <div key={tx.id} className="p-3 rounded-lg border border-border bg-card/40 space-y-1 text-[11px]">
                        <div className="flex items-center justify-between">
                          <Badge variant="outline" className="text-[10px] font-mono uppercase">{tx.transaction_type}</Badge>
                          <span className="font-mono text-[10px] text-muted-foreground">{new Date(tx.created_at).toLocaleString()}</span>
                        </div>
                        <div className="flex items-center justify-between pt-1">
                          <span className="font-mono font-bold text-foreground">{tx.quantity} {tx.unit} (${tx.total_cost.toFixed(2)})</span>
                          {tx.external_reference && (
                            <span className="font-mono text-[10px] text-emerald-400">ERP Ref: {tx.external_reference}</span>
                          )}
                        </div>
                        {tx.notes && <p className="text-muted-foreground text-[10px]">{tx.notes}</p>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Requirement Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <Card className="w-full max-w-lg bg-card border-border shadow-xl">
            <CardHeader className="border-b border-border pb-3">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Package className="size-5 text-primary" />
                <span>Submit Material Requirement</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Request spare parts or materials required for operational work or overhaul tasks.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleCreateSubmit}>
              <CardContent className="p-4 space-y-3.5 text-xs">
                <div className="space-y-1">
                  <label className="font-medium text-foreground">Select From Spare Parts Catalog (Optional)</label>
                  <select
                    value={selectedCatalogId}
                    onChange={(e) => {
                      const id = e.target.value;
                      setSelectedCatalogId(id);
                      const item = catalog.find((c) => c.id === id);
                      if (item) {
                        setNewMatName(item.name);
                        setNewPartNum(item.part_number);
                        setNewUnit(item.unit_of_measure);
                        setNewUnitCost(item.default_unit_cost.toString());
                        setNewStore(item.primary_store || '');
                      }
                    }}
                    className="w-full h-8 rounded border border-input bg-card px-2 text-xs font-mono"
                  >
                    <option value="">-- Ad-hoc or Custom Item --</option>
                    {catalog.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.part_number} — {c.name} (${c.default_unit_cost})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Material Name *</label>
                    <Input
                      required
                      value={newMatName}
                      onChange={(e) => setNewMatName(e.target.value)}
                      placeholder="e.g. Warman Impeller 8/6"
                      className="h-8 text-xs"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Part Number</label>
                    <Input
                      value={newPartNum}
                      onChange={(e) => setNewPartNum(e.target.value)}
                      placeholder="e.g. W86-IMP-5"
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Quantity Required *</label>
                    <Input
                      type="number"
                      required
                      value={newQtyRequired}
                      onChange={(e) => setNewQtyRequired(e.target.value)}
                      className="h-8 text-xs font-mono"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Unit</label>
                    <Input
                      value={newUnit}
                      onChange={(e) => setNewUnit(e.target.value)}
                      className="h-8 text-xs"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Unit Cost ($)</label>
                    <Input
                      type="number"
                      value={newUnitCost}
                      onChange={(e) => setNewUnitCost(e.target.value)}
                      placeholder="0.00"
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
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

                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Store Location</label>
                    <Input
                      value={newStore}
                      onChange={(e) => setNewStore(e.target.value)}
                      placeholder="e.g. Warehouse Bay 4B"
                      className="h-8 text-xs"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-foreground">Purpose & Usage Scope</label>
                  <Input
                    value={newPurpose}
                    onChange={(e) => setNewPurpose(e.target.value)}
                    placeholder="e.g. Slurry pump overhaul on Ball Mill 1"
                    className="h-8 text-xs"
                  />
                </div>
              </CardContent>

              <div className="p-4 border-t border-border flex justify-end gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsCreateOpen(false)} className="text-xs">
                  Cancel
                </Button>
                <Button type="submit" size="sm" className="text-xs">
                  Submit Requirement
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
