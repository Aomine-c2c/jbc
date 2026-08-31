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
  Boxes,
  Truck,
  Wrench,
  Cpu,
  Building,
  Factory,
  Search,
  Plus,
  RefreshCw,
  MapPin,
  Building2,
  UserCheck,
  AlertTriangle,
  CheckCircle2,
  SlidersHorizontal,
  FileText,
  Activity,
  History,
  Archive,
  ArrowUpRight,
  Shield,
  Eye,
  X,
} from 'lucide-react';

interface AssetRow {
  id: string;
  asset_tag: string;
  name: string;
  asset_type: string;
  category?: string;
  manufacturer?: string;
  model_number?: string;
  serial_number?: string;
  department_id: string;
  department_name?: string;
  location_breadcrumb?: string;
  custodian_name?: string;
  status: string;
  criticality: string;
  is_archived: boolean;
  machine_id?: string;
  created_at?: string;
}

interface AssetDetail extends AssetRow {
  purchase_cost?: number;
  current_value?: number;
  commissioned_date?: string;
  retired_date?: string;
  notes?: string;
  specifications?: Record<string, any>;
  open_work_items_count: number;
  activity_logs: Array<{
    id: string;
    activity_type: string;
    previous_value?: string;
    new_value?: string;
    notes?: string;
    created_at: string;
    user_name?: string;
  }>;
  maintenance_records: Array<{
    id: string;
    maintenance_type: string;
    summary: string;
    service_date: string;
    performed_by?: string;
    meter_reading?: number;
    cost: number;
  }>;
}

interface DepartmentOption {
  id: string;
  name: string;
}

const ASSET_TYPE_TABS = [
  { id: 'ALL', label: 'All Assets', icon: Boxes },
  { id: 'MACHINE', label: 'Machines', icon: Truck },
  { id: 'EQUIPMENT', label: 'Equipment', icon: Wrench },
  { id: 'VEHICLE', label: 'Vehicles', icon: Truck },
  { id: 'TOOL', label: 'Tools', icon: Wrench },
  { id: 'PRODUCTION_EQUIPMENT', label: 'Production', icon: Factory },
  { id: 'INFRASTRUCTURE', label: 'Infrastructure', icon: Building },
  { id: 'IT_EQUIPMENT', label: 'IT & Systems', icon: Cpu },
];

export default function AssetManagementPage() {
  const [assets, setAssets] = useState<AssetRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [includeArchived, setIncludeArchived] = useState(false);
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);

  // Detail drawer
  const [selectedAsset, setSelectedAsset] = useState<AssetDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Create Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newTag, setNewTag] = useState('');
  const [newType, setNewType] = useState('EQUIPMENT');
  const [newCategory, setNewCategory] = useState('');
  const [newManufacturer, setNewManufacturer] = useState('');
  const [newModel, setNewModel] = useState('');
  const [newSerial, setNewSerial] = useState('');
  const [newDeptId, setNewDeptId] = useState('');
  const [newLocationId, setNewLocationId] = useState<string | null>(null);
  const [newCriticality, setNewCriticality] = useState('MEDIUM');
  const [newCost, setNewCost] = useState('');
  const [newNotes, setNewNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadAssets = useCallback(async () => {
    setLoading(true);
    try {
      let url = `/api/v1/assets?limit=100&include_archived=${includeArchived}`;
      if (selectedType !== 'ALL') {
        url += `&asset_type=${selectedType}`;
      }
      if (statusFilter !== 'ALL') {
        url += `&status=${statusFilter}`;
      }
      if (searchQuery.trim()) {
        url += `&search=${encodeURIComponent(searchQuery.trim())}`;
      }
      const data = await apiFetch<AssetRow[]>(url);
      setAssets(data || []);

      const deptData = await apiFetch<DepartmentOption[]>('/api/v1/departments');
      if (deptData) setDepartments(deptData);
    } catch (err) {
      console.error('Failed to load assets', err);
    } finally {
      setLoading(false);
    }
  }, [selectedType, statusFilter, searchQuery, includeArchived]);

  useEffect(() => {
    loadAssets();
  }, [loadAssets]);

  const viewAssetDetail = async (id: string) => {
    setDetailLoading(true);
    try {
      const data = await apiFetch<AssetDetail>(`/api/v1/assets/${id}`);
      setSelectedAsset(data);
    } catch (err) {
      console.error('Failed to load asset details', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim() || !newDeptId) return;
    setSubmitting(true);
    try {
      await apiFetch('/api/v1/assets', {
        method: 'POST',
        body: JSON.stringify({
          name: newName.trim(),
          asset_tag: newTag.trim() || undefined,
          asset_type: newType,
          category: newCategory.trim() || undefined,
          manufacturer: newManufacturer.trim() || undefined,
          model_number: newModel.trim() || undefined,
          serial_number: newSerial.trim() || undefined,
          department_id: newDeptId,
          location_id: newLocationId || undefined,
          criticality: newCriticality,
          purchase_cost: newCost ? parseFloat(newCost) : 0.0,
          notes: newNotes.trim() || undefined,
        }),
      });
      setIsCreateOpen(false);
      setNewName('');
      setNewTag('');
      setNewCategory('');
      setNewManufacturer('');
      setNewModel('');
      setNewSerial('');
      setNewLocationId(null);
      setNewNotes('');
      loadAssets();
    } catch (err) {
      console.error('Failed to create asset', err);
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (st: string) => {
    switch (st) {
      case 'AVAILABLE':
        return <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-[10px]">AVAILABLE</Badge>;
      case 'IN_USE':
        return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30 text-[10px]">IN USE</Badge>;
      case 'UNDER_MAINTENANCE':
        return <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 text-[10px]">UNDER MAINTENANCE</Badge>;
      case 'OUT_OF_SERVICE':
        return <Badge className="bg-red-500/20 text-red-400 border-red-500/30 text-[10px]">OUT OF SERVICE</Badge>;
      case 'RETIRED':
        return <Badge variant="secondary" className="text-[10px]">RETIRED</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px]">{st}</Badge>;
    }
  };

  const getCriticalityBadge = (crit: string) => {
    switch (crit) {
      case 'CRITICAL':
        return <span className="inline-flex items-center gap-1 text-[10px] font-mono text-red-400 font-bold"><AlertTriangle className="size-3" /> CRITICAL</span>;
      case 'HIGH':
        return <span className="inline-flex items-center gap-1 text-[10px] font-mono text-amber-400 font-bold"><AlertTriangle className="size-3" /> HIGH</span>;
      case 'MEDIUM':
        return <span className="inline-flex items-center gap-1 text-[10px] font-mono text-blue-400">MEDIUM</span>;
      default:
        return <span className="inline-flex items-center gap-1 text-[10px] font-mono text-muted-foreground">LOW</span>;
    }
  };

  // Metrics
  const totalCount = assets.length;
  const inUseCount = assets.filter((a) => a.status === 'IN_USE').length;
  const maintCount = assets.filter((a) => ['UNDER_MAINTENANCE', 'OUT_OF_SERVICE'].includes(a.status)).length;
  const criticalCount = assets.filter((a) => a.criticality === 'CRITICAL' || a.criticality === 'HIGH').length;

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-primary/10 text-primary">
            <Boxes className="size-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              Asset & Equipment Registry
            </h1>
            <p className="text-xs text-muted-foreground">
              Centralized physical asset registry, lifecycle management, custody, and maintenance histories.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={loadAssets} disabled={loading} className="text-xs gap-1.5">
            <RefreshCw className={`size-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button size="sm" onClick={() => setIsCreateOpen(true)} className="text-xs gap-1.5 bg-primary text-primary-foreground">
            <Plus className="size-3.5" />
            Register Asset
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Total Registered</p>
              <p className="text-2xl font-mono font-bold text-foreground mt-1">{totalCount}</p>
            </div>
            <div className="p-2.5 rounded-md bg-muted text-muted-foreground">
              <Boxes className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Operational / In Use</p>
              <p className="text-2xl font-mono font-bold text-blue-400 mt-1">{inUseCount}</p>
            </div>
            <div className="p-2.5 rounded-md bg-blue-500/10 text-blue-400">
              <CheckCircle2 className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">Maintenance / Down</p>
              <p className="text-2xl font-mono font-bold text-amber-400 mt-1">{maintCount}</p>
            </div>
            <div className="p-2.5 rounded-md bg-amber-500/10 text-amber-400">
              <Wrench className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-mono text-muted-foreground uppercase">High / Critical Rating</p>
              <p className="text-2xl font-mono font-bold text-red-400 mt-1">{criticalCount}</p>
            </div>
            <div className="p-2.5 rounded-md bg-red-500/10 text-red-400">
              <Shield className="size-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Asset Type Segmented Tabs */}
      <div className="flex items-center gap-1.5 p-1 bg-muted/40 rounded-lg border border-border overflow-x-auto">
        {ASSET_TYPE_TABS.map((t) => {
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

      {/* Search & Filter Controls */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            placeholder="Search by tag, name, serial number, manufacturer, or location..."
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
          <option value="AVAILABLE">AVAILABLE</option>
          <option value="IN_USE">IN USE</option>
          <option value="RESERVED">RESERVED</option>
          <option value="UNDER_MAINTENANCE">UNDER MAINTENANCE</option>
          <option value="OUT_OF_SERVICE">OUT OF SERVICE</option>
          <option value="INACTIVE">INACTIVE</option>
          <option value="RETIRED">RETIRED</option>
        </select>
        <label className="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer select-none shrink-0 pl-1">
          <input
            type="checkbox"
            checked={includeArchived}
            onChange={(e) => setIncludeArchived(e.target.checked)}
            className="rounded border-input text-primary focus:ring-primary size-3.5"
          />
          <span>Include Archived</span>
        </label>
      </div>

      {/* Main Asset Table */}
      <Card className="bg-card border-border">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-12 text-center text-xs text-muted-foreground">Loading asset inventory...</div>
          ) : assets.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted-foreground border border-dashed rounded-lg m-4">
              No assets found matching the selected parameters.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-border bg-muted/20 text-muted-foreground font-mono text-[11px]">
                    <th className="p-3 pl-4">ASSET TAG</th>
                    <th className="p-3">NAME & SPECS</th>
                    <th className="p-3">TYPE & CATEGORY</th>
                    <th className="p-3">LOCATION</th>
                    <th className="p-3">STATUS</th>
                    <th className="p-3">CRITICALITY</th>
                    <th className="p-3">CUSTODIAN</th>
                    <th className="p-3 pr-4 text-right">ACTION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {assets.map((asset) => (
                    <tr key={asset.id} className="hover:bg-muted/30 transition-colors">
                      <td className="p-3 pl-4 font-mono font-bold text-foreground">
                        {asset.asset_tag}
                      </td>
                      <td className="p-3 max-w-xs">
                        <div className="font-semibold text-foreground truncate">{asset.name}</div>
                        {(asset.manufacturer || asset.model_number) && (
                          <div className="text-[11px] text-muted-foreground truncate mt-0.5">
                            {[asset.manufacturer, asset.model_number].filter(Boolean).join(' - ')}
                          </div>
                        )}
                        {asset.serial_number && (
                          <div className="text-[10px] font-mono text-muted-foreground">
                            SN: {asset.serial_number}
                          </div>
                        )}
                      </td>
                      <td className="p-3">
                        <Badge variant="outline" className="font-mono text-[10px]">
                          {asset.asset_type}
                        </Badge>
                        {asset.category && (
                          <div className="text-[11px] text-muted-foreground mt-0.5">{asset.category}</div>
                        )}
                      </td>
                      <td className="p-3 max-w-xs">
                        {asset.location_breadcrumb ? (
                          <div className="flex items-center gap-1 text-[11px] text-muted-foreground truncate">
                            <MapPin className="size-3 shrink-0 text-emerald-400" />
                            <span className="truncate">{asset.location_breadcrumb}</span>
                          </div>
                        ) : (
                          <span className="text-[11px] text-muted-foreground italic">Unassigned</span>
                        )}
                        <div className="text-[10px] text-muted-foreground/70 mt-0.5">
                          {asset.department_name || 'General Operations'}
                        </div>
                      </td>
                      <td className="p-3">
                        {getStatusBadge(asset.status)}
                      </td>
                      <td className="p-3">
                        {getCriticalityBadge(asset.criticality)}
                      </td>
                      <td className="p-3 text-[11px] text-muted-foreground">
                        {asset.custodian_name || 'Department Custody'}
                      </td>
                      <td className="p-3 pr-4 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => viewAssetDetail(asset.id)}
                          className="h-7 text-xs gap-1"
                        >
                          <Eye className="size-3" />
                          <span>Inspect</span>
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

      {/* Asset Detail Drawer */}
      {selectedAsset && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-2xl bg-card border-l border-border h-full flex flex-col shadow-2xl overflow-hidden">
            {/* Drawer Header */}
            <div className="p-4 border-b border-border flex items-center justify-between bg-muted/20">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded bg-primary/10 text-primary">
                  <Boxes className="size-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-foreground">{selectedAsset.name}</h2>
                    <span className="font-mono text-xs text-primary font-bold">{selectedAsset.asset_tag}</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    {[selectedAsset.manufacturer, selectedAsset.model_number].filter(Boolean).join(' • ') || selectedAsset.asset_type}
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setSelectedAsset(null)} className="size-8 p-0">
                <X className="size-4" />
              </Button>
            </div>

            {/* Drawer Content */}
            <div className="flex-1 overflow-y-auto p-5 space-y-5 text-xs">
              {/* Status & Quick Stats */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded-lg border border-border bg-card/60">
                  <div className="text-[10px] font-mono text-muted-foreground uppercase">Current Status</div>
                  <div className="mt-1">{getStatusBadge(selectedAsset.status)}</div>
                </div>
                <div className="p-3 rounded-lg border border-border bg-card/60">
                  <div className="text-[10px] font-mono text-muted-foreground uppercase">Criticality</div>
                  <div className="mt-1">{getCriticalityBadge(selectedAsset.criticality)}</div>
                </div>
                <div className="p-3 rounded-lg border border-border bg-card/60">
                  <div className="text-[10px] font-mono text-muted-foreground uppercase">Open Work Units</div>
                  <div className="mt-1 font-mono font-bold text-sm text-foreground">{selectedAsset.open_work_items_count}</div>
                </div>
              </div>

              {/* Location & Ownership */}
              <div className="p-3.5 rounded-lg border border-border bg-card/60 space-y-2">
                <div className="font-semibold text-foreground text-xs flex items-center gap-1.5">
                  <MapPin className="size-3.5 text-emerald-400" />
                  <span>Physical Placement & Ownership</span>
                </div>
                <div className="grid grid-cols-2 gap-2 pt-1 border-t border-border/50 text-[11px]">
                  <div>
                    <span className="text-muted-foreground">Location: </span>
                    <span className="text-foreground font-medium">{selectedAsset.location_breadcrumb || 'Not Assigned'}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Department: </span>
                    <span className="text-foreground font-medium">{selectedAsset.department_name || 'Operations'}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Custodian: </span>
                    <span className="text-foreground font-medium">{selectedAsset.custodian_name || 'Unassigned'}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Serial Number: </span>
                    <span className="font-mono text-foreground">{selectedAsset.serial_number || 'N/A'}</span>
                  </div>
                </div>
              </div>

              {/* Maintenance History */}
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-foreground text-xs flex items-center gap-1.5">
                    <Wrench className="size-3.5 text-amber-400" />
                    <span>Maintenance & Overhaul Log</span>
                  </span>
                  <Badge variant="outline" className="text-[10px]">
                    {selectedAsset.maintenance_records.length} records
                  </Badge>
                </div>
                {selectedAsset.maintenance_records.length === 0 ? (
                  <div className="p-4 border border-dashed rounded-lg text-center text-muted-foreground text-[11px]">
                    No recorded maintenance events.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {selectedAsset.maintenance_records.map((rec) => (
                      <div key={rec.id} className="p-3 rounded-lg border border-border bg-card/60 space-y-1">
                        <div className="flex items-center justify-between">
                          <Badge variant="outline" className="text-[10px] font-mono uppercase">{rec.maintenance_type}</Badge>
                          <span className="text-[10px] font-mono text-muted-foreground">{new Date(rec.service_date).toLocaleDateString()}</span>
                        </div>
                        <p className="text-[11px] text-foreground">{rec.summary}</p>
                        <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1 border-t border-border/40">
                          <span>By: {rec.performed_by || 'Technician'}</span>
                          {rec.cost > 0 && <span className="font-mono font-semibold">${rec.cost.toFixed(2)}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Activity & Custody Timeline */}
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-foreground text-xs flex items-center gap-1.5">
                    <History className="size-3.5 text-primary" />
                    <span>Custody & Movement History</span>
                  </span>
                  <Badge variant="outline" className="text-[10px]">
                    {selectedAsset.activity_logs.length} events
                  </Badge>
                </div>
                <div className="space-y-2">
                  {selectedAsset.activity_logs.map((log) => (
                    <div key={log.id} className="p-2.5 rounded border border-border bg-card/40 space-y-1 text-[11px]">
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-foreground text-[10px] uppercase">{log.activity_type}</span>
                        <span className="text-[10px] font-mono text-muted-foreground">{new Date(log.created_at).toLocaleString()}</span>
                      </div>
                      {log.notes && <p className="text-muted-foreground">{log.notes}</p>}
                      {log.previous_value && log.new_value && (
                        <div className="text-[10px] font-mono text-muted-foreground">
                          <span>{log.previous_value}</span> → <span className="text-foreground font-bold">{log.new_value}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Asset Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <Card className="w-full max-w-xl bg-card border-border shadow-xl">
            <CardHeader className="border-b border-border pb-3">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Boxes className="size-5 text-primary" />
                <span>Register Physical Asset</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Register a new operational machine, equipment, vehicle, tool or production asset into the registry.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleCreateSubmit}>
              <CardContent className="p-4 space-y-3.5 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Asset Name *</label>
                    <Input
                      required
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                      placeholder="e.g. Atlas Copco GA 90 VSD Compressor"
                      className="h-8 text-xs"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Asset Tag (Optional)</label>
                    <Input
                      value={newTag}
                      onChange={(e) => setNewTag(e.target.value)}
                      placeholder="Auto-generated if blank (e.g. AST-2026-0001)"
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Asset Type</label>
                    <select
                      value={newType}
                      onChange={(e) => setNewType(e.target.value)}
                      className="w-full h-8 rounded border border-input bg-card px-2 text-xs"
                    >
                      <option value="MACHINE">MACHINE</option>
                      <option value="EQUIPMENT">EQUIPMENT</option>
                      <option value="VEHICLE">VEHICLE</option>
                      <option value="TOOL">TOOL</option>
                      <option value="PRODUCTION_EQUIPMENT">PRODUCTION_EQUIPMENT</option>
                      <option value="INFRASTRUCTURE">INFRASTRUCTURE</option>
                      <option value="IT_EQUIPMENT">IT_EQUIPMENT</option>
                      <option value="OTHER">OTHER</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Category</label>
                    <Input
                      value={newCategory}
                      onChange={(e) => setNewCategory(e.target.value)}
                      placeholder="e.g. Pneumatics / Haulage"
                      className="h-8 text-xs"
                    />
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

                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Manufacturer</label>
                    <Input
                      value={newManufacturer}
                      onChange={(e) => setNewManufacturer(e.target.value)}
                      placeholder="e.g. Caterpillar, ABB"
                      className="h-8 text-xs"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Model Number</label>
                    <Input
                      value={newModel}
                      onChange={(e) => setNewModel(e.target.value)}
                      placeholder="e.g. 349D2 L"
                      className="h-8 text-xs"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Serial Number</label>
                    <Input
                      value={newSerial}
                      onChange={(e) => setNewSerial(e.target.value)}
                      placeholder="e.g. CAT0349DXA0091"
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-foreground">Physical Location</label>
                  <LocationSelector
                    value={newLocationId}
                    onChange={(id) => setNewLocationId(id)}
                    placeholder="Search plant, facility, area, or section..."
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Criticality Rating</label>
                    <select
                      value={newCriticality}
                      onChange={(e) => setNewCriticality(e.target.value)}
                      className="w-full h-8 rounded border border-input bg-card px-2 text-xs"
                    >
                      <option value="LOW">LOW</option>
                      <option value="MEDIUM">MEDIUM</option>
                      <option value="HIGH">HIGH</option>
                      <option value="CRITICAL">CRITICAL</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Purchase Cost ($)</label>
                    <Input
                      type="number"
                      value={newCost}
                      onChange={(e) => setNewCost(e.target.value)}
                      placeholder="0.00"
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-foreground">Notes & Technical Specifications</label>
                  <textarea
                    value={newNotes}
                    onChange={(e) => setNewNotes(e.target.value)}
                    rows={2}
                    placeholder="Operating parameters, vendor contact, or warranty details..."
                    className="w-full rounded border border-input bg-card p-2 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
                  />
                </div>
              </CardContent>

              <div className="p-4 border-t border-border flex justify-end gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsCreateOpen(false)} className="text-xs">
                  Cancel
                </Button>
                <Button type="submit" size="sm" disabled={submitting} className="text-xs">
                  {submitting ? 'Registering...' : 'Register Asset'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}
