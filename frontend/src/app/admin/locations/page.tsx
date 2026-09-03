'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '@/lib/api';
import { Protect } from '@/components/auth/Protect';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  MapPin,
  FolderTree,
  ChevronRight,
  ChevronDown,
  Plus,
  Search,
  RefreshCw,
  Archive,
  RotateCcw,
  Trash2,
  CheckCircle2,
  Compass,
  Sparkles,
} from 'lucide-react';

interface LocationTreeNode {
  id: string;
  code: string;
  name: string;
  location_type: string;
  breadcrumb?: string;
  hierarchy_level: number;
  is_active: boolean;
  is_archived: boolean;
  gps_coordinates?: string;
  barcode_or_nfc?: string;
  criticality_rating?: string;
  children: LocationTreeNode[];
  reference_count: number;
}

interface SiteItem {
  id: string;
  code: string;
  name: string;
  site_type: string;
}

interface MigrationSummary {
  scanned_job_cards: number;
  scanned_machines: number;
  scanned_requisitions: number;
  created_locations: number;
  matched_locations: number;
  details: string[];
}

export default function LocationsAdminPage() {
  const [treeData, setTreeData] = useState<LocationTreeNode[]>([]);
  const [sites, setSites] = useState<SiteItem[]>([]);
  const [selectedSiteId, setSelectedSiteId] = useState<string>('');
  const [includeArchived, setIncludeArchived] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});

  // Dialog State
  const [showModal, setShowModal] = useState<boolean>(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [selectedNode, setSelectedNode] = useState<LocationTreeNode | null>(null);
  const [parentForNew, setParentForNew] = useState<LocationTreeNode | null>(null);

  // Form State
  const [formCode, setFormCode] = useState('');
  const [formName, setFormName] = useState('');
  const [formType, setFormType] = useState('AREA');
  const [formDesc, setFormDesc] = useState('');
  const [formGps, setFormGps] = useState('');
  const [formBarcode, setFormBarcode] = useState('');
  const [formCriticality, setFormCriticality] = useState('MEDIUM');
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Migration State
  const [migrationRunning, setMigrationRunning] = useState(false);
  const [migrationSummary, setMigrationSummary] = useState<MigrationSummary | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      // 1. Fetch sites
      const sitesRes = await apiFetch<SiteItem[]>('/api/v1/org/sites');
      setSites(sitesRes || []);

      // 2. Fetch hierarchy tree
      const params = new URLSearchParams();
      if (selectedSiteId) params.append('site_id', selectedSiteId);
      if (includeArchived) params.append('include_archived', 'true');

      const treeRes = await apiFetch<LocationTreeNode[]>(`/api/v1/locations/tree?${params.toString()}`);
      setTreeData(treeRes || []);

      // Auto-expand top level nodes
      const initialExpanded: Record<string, boolean> = {};
      (treeRes || []).forEach((node: LocationTreeNode) => {
        initialExpanded[node.id] = true;
      });
      setExpandedNodes((prev) => ({ ...initialExpanded, ...prev }));
    } catch (err: unknown) {
      setErrorMsg((err as { message?: string })?.message || 'Failed to load location hierarchy.');
    } finally {
      setLoading(false);
    }
  }, [selectedSiteId, includeArchived]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const toggleExpand = (id: string) => {
    setExpandedNodes((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const openCreateModal = (parent: LocationTreeNode | null = null) => {
    setModalMode('create');
    setParentForNew(parent);
    setSelectedNode(null);
    setFormCode('');
    setFormName('');
    setFormType(parent ? 'SECTION' : 'FACILITY');
    setFormDesc('');
    setFormGps('');
    setFormBarcode('');
    setFormCriticality('MEDIUM');
    setErrorMsg('');
    setShowModal(true);
  };

  const openEditModal = (node: LocationTreeNode) => {
    setModalMode('edit');
    setSelectedNode(node);
    setParentForNew(null);
    setFormCode(node.code);
    setFormName(node.name);
    setFormType(node.location_type);
    setFormDesc('');
    setFormGps(node.gps_coordinates || '');
    setFormBarcode(node.barcode_or_nfc || '');
    setFormCriticality(node.criticality_rating || 'MEDIUM');
    setErrorMsg('');
    setShowModal(true);
  };

  const handleSaveLocation = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMsg('');

    try {
      if (modalMode === 'create') {
        await apiFetch('/api/v1/locations', {
          method: 'POST',
          body: JSON.stringify({
            code: formCode.trim(),
            name: formName.trim(),
            location_type: formType,
            description: formDesc.trim() || undefined,
            gps_coordinates: formGps.trim() || undefined,
            barcode_or_nfc: formBarcode.trim() || undefined,
            criticality_rating: formCriticality,
            parent_id: parentForNew ? parentForNew.id : undefined,
            site_id: selectedSiteId || (sites.length > 0 ? sites[0].id : undefined),
          }),
        });
      } else if (selectedNode) {
        await apiFetch(`/api/v1/locations/${selectedNode.id}`, {
          method: 'PATCH',
          body: JSON.stringify({
            code: formCode.trim(),
            name: formName.trim(),
            location_type: formType,
            description: formDesc.trim() || undefined,
            gps_coordinates: formGps.trim() || undefined,
            barcode_or_nfc: formBarcode.trim() || undefined,
            criticality_rating: formCriticality,
          }),
        });
      }
      setShowModal(false);
      await loadData();
    } catch (err: unknown) {
      setErrorMsg((err as { message?: string })?.message || 'Failed to save location.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleArchive = async (node: LocationTreeNode) => {
    if (!confirm(`Are you sure you want to archive "${node.name}" (${node.code})? It will be deactivated from active selection.`)) return;
    try {
      await apiFetch(`/api/v1/locations/${node.id}/archive`, {
        method: 'POST',
        body: JSON.stringify({ reason: 'Decommissioned / archived via Administration' }),
      });
      await loadData();
    } catch (err: unknown) {
      alert((err as { message?: string })?.message || 'Failed to archive location.');
    }
  };

  const handleRestore = async (node: LocationTreeNode) => {
    try {
      await apiFetch(`/api/v1/locations/${node.id}/restore`, { method: 'POST' });
      await loadData();
    } catch (err: unknown) {
      alert((err as { message?: string })?.message || 'Failed to restore location.');
    }
  };

  const handleDelete = async (node: LocationTreeNode) => {
    if (!confirm(`Permanently delete location "${node.name}" (${node.code})?`)) return;
    try {
      await apiFetch(`/api/v1/locations/${node.id}`, { method: 'DELETE' });
      await loadData();
    } catch (err: unknown) {
      alert((err as { message?: string })?.message || 'Cannot delete location.');
    }
  };

  const handleMigrate = async () => {
    if (!confirm('Scan historical Job Cards, Machines, and Requisitions to link or auto-provision matching location hierarchy records?')) return;
    setMigrationRunning(true);
    setMigrationSummary(null);
    try {
      const res = await apiFetch<MigrationSummary>('/api/v1/locations/migrate', { method: 'POST' });
      setMigrationSummary(res);
      await loadData();
    } catch (err: unknown) {
      alert((err as { message?: string })?.message || 'Migration failed.');
    } finally {
      setMigrationRunning(false);
    }
  };

  const getTypeColor = (type: string) => {
    switch (type?.toUpperCase()) {
      case 'SITE':
        return 'bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/30';
      case 'FACILITY':
      case 'PLANT':
        return 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30';
      case 'AREA':
        return 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30';
      case 'SECTION':
        return 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30';
      case 'WORK_CENTER':
      case 'ROOM':
      case 'SPECIFIC_LOCATION':
        return 'bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 border-indigo-500/30';
      default:
        return 'bg-muted text-muted-foreground border-border';
    }
  };

  const filterTree = (nodes: LocationTreeNode[], query: string): LocationTreeNode[] => {
    if (!query.trim()) return nodes;
    const lower = query.toLowerCase();

    return nodes.reduce<LocationTreeNode[]>((acc, node) => {
      const matchSelf =
        node.name.toLowerCase().includes(lower) ||
        node.code.toLowerCase().includes(lower) ||
        (node.breadcrumb && node.breadcrumb.toLowerCase().includes(lower)) ||
        (node.barcode_or_nfc && node.barcode_or_nfc.toLowerCase().includes(lower));

      const filteredChildren = filterTree(node.children || [], query);

      if (matchSelf || filteredChildren.length > 0) {
        acc.push({
          ...node,
          children: filteredChildren,
        });
      }
      return acc;
    }, []);
  };

  const filteredTree = filterTree(treeData, searchQuery);

  const renderNode = (node: LocationTreeNode, depth: number = 0) => {
    const hasChildren = node.children && node.children.length > 0;
    const isExpanded = expandedNodes[node.id] ?? false;

    return (
      <div key={node.id} className="select-none">
        <div
          className={`flex items-center justify-between p-2 rounded-lg transition-colors group mb-1 ${
            node.is_archived
              ? 'bg-muted/30 opacity-60 border border-dashed border-border'
              : 'hover:bg-muted/50 border border-transparent hover:border-border'
          }`}
          style={{ marginLeft: `${depth * 20}px` }}
        >
          <div className="flex items-center gap-2 min-w-0">
            {hasChildren ? (
              <button
                type="button"
                onClick={() => toggleExpand(node.id)}
                className="p-1 rounded hover:bg-muted text-muted-foreground shrink-0"
              >
                {isExpanded ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
              </button>
            ) : (
              <span className="size-6 shrink-0 flex items-center justify-center text-muted-foreground/40">
                •
              </span>
            )}

            <div className="p-1 rounded bg-primary/10 text-primary shrink-0">
              <MapPin className="size-3.5" />
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-xs text-foreground truncate">
                  {node.name}
                </span>
                <span className="text-[10px] font-mono px-1 rounded bg-muted text-muted-foreground">
                  {node.code}
                </span>
                <Badge variant="outline" className={`text-[9px] px-1 py-0 uppercase font-mono ${getTypeColor(node.location_type)}`}>
                  {node.location_type}
                </Badge>
                {node.is_archived && (
                  <Badge variant="secondary" className="text-[9px] px-1 py-0 text-amber-500 font-mono">
                    Archived
                  </Badge>
                )}
              </div>
              {node.breadcrumb && (
                <p className="text-[10px] font-mono text-muted-foreground truncate mt-0.5">
                  {node.breadcrumb}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-1.5 shrink-0 opacity-80 group-hover:opacity-100 transition-opacity">
            {node.barcode_or_nfc && (
              <span className="text-[10px] font-mono text-muted-foreground px-1.5 py-0.5 rounded bg-muted">
                🏷️ {node.barcode_or_nfc}
              </span>
            )}

            {node.reference_count > 0 && (
              <Badge variant="outline" className="text-[10px] font-mono bg-blue-500/10 text-blue-600 border-blue-500/20">
                {node.reference_count} refs
              </Badge>
            )}

            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs gap-1 text-primary hover:text-primary"
              onClick={() => openCreateModal(node)}
            >
              <Plus className="size-3" />
              Sub-location
            </Button>

            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs"
              onClick={() => openEditModal(node)}
            >
              Edit
            </Button>

            {node.is_archived ? (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs text-emerald-600 hover:text-emerald-500"
                onClick={() => handleRestore(node)}
              >
                <RotateCcw className="size-3 mr-1" />
                Restore
              </Button>
            ) : (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs text-amber-600 hover:text-amber-500"
                onClick={() => handleArchive(node)}
              >
                <Archive className="size-3 mr-1" />
                Archive
              </Button>
            )}

            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs text-destructive hover:text-destructive"
              onClick={() => handleDelete(node)}
            >
              <Trash2 className="size-3" />
            </Button>
          </div>
        </div>

        {hasChildren && isExpanded && (
          <div>
            {node.children.map((child) => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <Protect capability="locations:manage" isPageGuard moduleName="Physical & Spatial Hierarchy">
      <div className="p-6 space-y-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-primary/10 text-primary">
                <Compass className="size-6" />
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight text-foreground">
                  Physical & Spatial Hierarchy
                </h1>
                <p className="text-xs text-muted-foreground">
                  Configurable enterprise locations: Site → Plant/Facility → Area → Section → Specific Location
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleMigrate}
              disabled={migrationRunning}
              className="text-xs gap-1.5"
            >
              <Sparkles className={`size-3.5 ${migrationRunning ? 'animate-spin' : ''}`} />
              {migrationRunning ? 'Migrating...' : 'Migrate Legacy Text'}
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={loadData}
              disabled={loading}
              className="text-xs gap-1.5"
            >
              <RefreshCw className={`size-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>

            <Button
              size="sm"
              onClick={() => openCreateModal(null)}
              className="text-xs gap-1.5"
            >
              <Plus className="size-3.5" />
              New Top-Level Location
            </Button>
          </div>
        </div>

        {/* Migration Summary Banner */}
        {migrationSummary && (
          <Card className="bg-emerald-500/10 border-emerald-500/30 animate-in fade-in-0">
            <CardContent className="p-4 flex items-start gap-3">
              <CheckCircle2 className="size-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
              <div className="space-y-1 text-xs">
                <p className="font-semibold text-emerald-800 dark:text-emerald-300">
                  Migration Complete: {migrationSummary.created_locations} new location nodes provisioned, {migrationSummary.matched_locations} records linked.
                </p>
                <p className="text-muted-foreground text-[11px]">
                  Scanned: {migrationSummary.scanned_job_cards} Job Cards, {migrationSummary.scanned_machines} Machines, {migrationSummary.scanned_requisitions} Requisitions.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Filters & Search */}
        <Card className="bg-card border-border">
          <CardContent className="p-4 flex flex-col sm:flex-row gap-3 items-center justify-between">
            <div className="relative w-full sm:w-80">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search hierarchy (name, code, barcode)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 text-xs"
              />
            </div>

            <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
              {sites.length > 0 && (
                <select
                  value={selectedSiteId}
                  onChange={(e) => setSelectedSiteId(e.target.value)}
                  className="h-9 px-3 text-xs rounded-md border border-input bg-background text-foreground"
                >
                  <option value="">All Operational Sites</option>
                  {sites.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.code})
                    </option>
                  ))}
                </select>
              )}

              <label className="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={includeArchived}
                  onChange={(e) => setIncludeArchived(e.target.checked)}
                  className="rounded border-input text-primary focus:ring-primary size-3.5"
                />
                Include Archived
              </label>
            </div>
          </CardContent>
        </Card>

        {/* Hierarchy Tree Card */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FolderTree className="size-4 text-primary" />
                <CardTitle className="text-sm font-semibold">Hierarchy Tree</CardTitle>
              </div>
              <span className="text-xs text-muted-foreground font-mono">
                {filteredTree.length} Top-level Root(s)
              </span>
            </div>
            <CardDescription className="text-xs">
              Flexible multi-level hierarchy supporting arbitrary depths without hardcoded structure limits.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            {loading ? (
              <div className="p-12 text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
                <span className="size-4 rounded-full border-2 border-primary border-t-transparent animate-spin" />
                Loading physical hierarchy...
              </div>
            ) : filteredTree.length === 0 ? (
              <div className="p-12 text-center text-xs text-muted-foreground border border-dashed rounded-lg">
                No location nodes found. Create a top-level location or run the migration tool.
              </div>
            ) : (
              <div className="space-y-1">
                {filteredTree.map((node) => renderNode(node, 0))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Create / Edit Modal */}
        {showModal && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in-0 zoom-in-95 duration-150">
              <div className="px-5 py-4 border-b border-border flex items-center justify-between">
                <h2 className="text-sm font-bold text-foreground">
                  {modalMode === 'create'
                    ? parentForNew
                      ? `Add Sub-location under "${parentForNew.name}"`
                      : 'Add Top-Level Location'
                    : `Edit Location: ${selectedNode?.name}`}
                </h2>
                <Button
                  variant="ghost"
                  size="sm"
                  className="size-7 p-0"
                  onClick={() => setShowModal(false)}
                >
                  ✕
                </Button>
              </div>

              <form onSubmit={handleSaveLocation} className="p-5 space-y-4 text-xs">
                {errorMsg && (
                  <div className="p-2.5 rounded bg-destructive/10 text-destructive text-xs border border-destructive/20">
                    {errorMsg}
                  </div>
                )}

                {parentForNew && (
                  <div className="p-2.5 rounded bg-muted/40 border border-border">
                    <span className="text-muted-foreground font-mono text-[10px] uppercase">Parent Node:</span>
                    <p className="font-semibold text-xs mt-0.5">{parentForNew.name} ({parentForNew.code})</p>
                    <p className="text-[10px] text-muted-foreground font-mono">{parentForNew.breadcrumb}</p>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-medium text-muted-foreground mb-1">
                      Location Code *
                    </label>
                    <Input
                      required
                      type="text"
                      placeholder="e.g. CRUSH-01"
                      value={formCode}
                      onChange={(e) => setFormCode(e.target.value)}
                      className="text-xs uppercase font-mono"
                    />
                  </div>

                  <div>
                    <label className="block font-medium text-muted-foreground mb-1">
                      Hierarchy Level Type *
                    </label>
                    <select
                      value={formType}
                      onChange={(e) => setFormType(e.target.value)}
                      className="w-full h-9 px-3 rounded-md border border-input bg-background text-xs"
                    >
                      <option value="SITE">SITE (Operational Site)</option>
                      <option value="FACILITY">FACILITY (Plant / Building)</option>
                      <option value="PLANT">PLANT (Processing Plant)</option>
                      <option value="AREA">AREA (Operational Zone)</option>
                      <option value="SECTION">SECTION (Work Section)</option>
                      <option value="WORK_CENTER">WORK_CENTER (Workshop / Bay)</option>
                      <option value="ROOM">ROOM (Electrical / Server Room)</option>
                      <option value="SPECIFIC_LOCATION">SPECIFIC_LOCATION (Equipment Point)</option>
                      <option value="OTHER">OTHER (Custom Unit)</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block font-medium text-muted-foreground mb-1">
                    Location Name *
                  </label>
                  <Input
                    required
                    type="text"
                    placeholder="e.g. Primary Crushing Circuit"
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    className="text-xs"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-medium text-muted-foreground mb-1">
                      Barcode / NFC Tag
                    </label>
                    <Input
                      type="text"
                      placeholder="e.g. TAG-CRUSH-099"
                      value={formBarcode}
                      onChange={(e) => setFormBarcode(e.target.value)}
                      className="text-xs font-mono"
                    />
                  </div>

                  <div>
                    <label className="block font-medium text-muted-foreground mb-1">
                      Criticality Rating
                    </label>
                    <select
                      value={formCriticality}
                      onChange={(e) => setFormCriticality(e.target.value)}
                      className="w-full h-9 px-3 rounded-md border border-input bg-background text-xs"
                    >
                      <option value="LOW">LOW</option>
                      <option value="MEDIUM">MEDIUM</option>
                      <option value="HIGH">HIGH</option>
                      <option value="CRITICAL">CRITICAL</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block font-medium text-muted-foreground mb-1">
                    GPS Coordinates (Optional)
                  </label>
                  <Input
                    type="text"
                    placeholder="e.g. -20.0712, 31.6214"
                    value={formGps}
                    onChange={(e) => setFormGps(e.target.value)}
                    className="text-xs font-mono"
                  />
                </div>

                <div>
                  <label className="block font-medium text-muted-foreground mb-1">
                    Description
                  </label>
                  <textarea
                    rows={2}
                    placeholder="Operational notes, safety considerations..."
                    value={formDesc}
                    onChange={(e) => setFormDesc(e.target.value)}
                    className="w-full p-2.5 rounded-md border border-input bg-background text-xs resize-none"
                  />
                </div>

                <div className="pt-3 border-t border-border flex items-center justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setShowModal(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    size="sm"
                    disabled={submitting}
                  >
                    {submitting ? 'Saving...' : modalMode === 'create' ? 'Create Location' : 'Save Changes'}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </Protect>
  );
}
