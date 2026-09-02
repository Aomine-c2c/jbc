'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { apiFetch } from '@/lib/api';
import { Protect } from '@/components/auth/Protect';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Settings,
  ShieldCheck,
  Layers,
  GitFork,
  RefreshCw,
  Plus,
  ChevronRight,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Eye,
  Zap,
  ArrowRight,
  Lock,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

// ── Approval Chain Types ──────────────────────────────────────────────────────

interface WorkflowStep {
  step_number: number;
  authority_role: string;
  required_permission: string;
}

interface ApprovalWorkflow {
  id: string;
  name: string;
  description: string;
  workflow_type?: string;
  resource_type?: string;
  min_cost?: number;
  priority: number;
  risk_level?: string;
  is_active: boolean;
  steps: WorkflowStep[];
}

// ── State Machine Workflow Types ──────────────────────────────────────────────

interface WFState {
  name: string;
  label?: string;
  is_initial: boolean;
  is_terminal: boolean;
  requires_approval?: boolean;
  sla_minutes?: number;
}

interface WFTransition {
  from_state: string;
  to_state: string;
  action: string;
  label?: string;
  required_role?: string;
  required_permission?: string;
}

interface WFTemplate {
  id: string;
  name: string;
  description?: string;
  entity_type: string;
  version: number;
  is_active: boolean;
  is_default: boolean;
  states_count: number;
  transitions_count: number;
  department_name?: string;
  created_at?: string;
}

interface WFTemplateDetail {
  id: string;
  name: string;
  description?: string;
  entity_type: string;
  version: number;
  is_active: boolean;
  states: WFState[];
  transitions: WFTransition[];
  created_at?: string;
}

interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export default function WorkflowsAdminPage() {
  const [activeTab, setActiveTab] = useState<'APPROVAL_CHAINS' | 'STATE_MACHINES'>('APPROVAL_CHAINS');

  // Approval Chain state
  const [approvalWorkflows, setApprovalWorkflows] = useState<ApprovalWorkflow[]>([]);
  const [appLoading, setAppLoading] = useState(true);

  // State Machine state
  const [templates, setTemplates] = useState<WFTemplate[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState<WFTemplateDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Create Template form
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newEntityType, setNewEntityType] = useState('REQUEST');
  const [selectedPreset, setSelectedPreset] = useState<'MACHINE_REQUEST' | 'WORK_ITEM' | 'RESOURCE_ALLOCATION' | 'CUSTOM'>('MACHINE_REQUEST');

  const PRESETS = {
    MACHINE_REQUEST: {
      name: 'Machine Request Full Lifecycle',
      description: 'Standard Machine Request with Supervisor Review, Conditional Safety Approval, and Resource Allocation',
      entity_type: 'REQUEST',
      states: [
        { name: 'DRAFT', label: 'Draft', is_initial: true, is_terminal: false, requires_approval: false },
        { name: 'SUBMITTED', label: 'Submitted', is_initial: false, is_terminal: false, requires_approval: false },
        { name: 'SUPERVISOR_REVIEW', label: 'Supervisor Review', is_initial: false, is_terminal: false, requires_approval: true, approval_role: 'Supervisor' },
        { name: 'SAFETY_REVIEW', label: 'Safety Approval', is_initial: false, is_terminal: false, requires_approval: true, approval_role: 'Safety_Officer' },
        { name: 'RESOURCE_COORDINATION', label: 'Resource Coordinator', is_initial: false, is_terminal: false, requires_approval: false },
        { name: 'ALLOCATED', label: 'Allocated', is_initial: false, is_terminal: false, requires_approval: false },
        { name: 'COMPLETED', label: 'Completed', is_initial: false, is_terminal: true, requires_approval: false },
        { name: 'REJECTED', label: 'Rejected', is_initial: false, is_terminal: true, requires_approval: false },
      ],
      transitions: [
        { from_state: 'DRAFT', to_state: 'SUBMITTED', action: 'submit', label: 'Submit Request', required_role: 'Requester' },
        { from_state: 'SUBMITTED', to_state: 'SUPERVISOR_REVIEW', action: 'begin_review', label: 'Begin Supervisor Review', required_role: 'Supervisor' },
        { from_state: 'SUPERVISOR_REVIEW', to_state: 'SAFETY_REVIEW', action: 'supervisor_approve_high_risk', label: 'Approve & Route to Safety', required_role: 'Supervisor', conditions: { risk_level: 'HIGH' } },
        { from_state: 'SUPERVISOR_REVIEW', to_state: 'RESOURCE_COORDINATION', action: 'supervisor_approve_standard', label: 'Approve (Standard Risk)', required_role: 'Supervisor', conditions: { risk_level: ['LOW', 'MEDIUM'] } },
        { from_state: 'SUPERVISOR_REVIEW', to_state: 'REJECTED', action: 'reject', label: 'Reject', required_role: 'Supervisor' },
        { from_state: 'SAFETY_REVIEW', to_state: 'RESOURCE_COORDINATION', action: 'safety_approve', label: 'Safety Signoff', required_role: 'Safety_Officer' },
        { from_state: 'SAFETY_REVIEW', to_state: 'REJECTED', action: 'safety_reject', label: 'Safety Reject', required_role: 'Safety_Officer' },
        { from_state: 'RESOURCE_COORDINATION', to_state: 'ALLOCATED', action: 'allocate', label: 'Allocate Machinery', required_role: 'Resource_Coordinator' },
        { from_state: 'ALLOCATED', to_state: 'COMPLETED', action: 'complete', label: 'Mark Completed', required_role: 'Resource_Coordinator' },
      ],
    },
    WORK_ITEM: {
      name: 'Work Item Standard Lifecycle',
      description: 'Standard Job Card and Work Item execution lifecycle',
      entity_type: 'WORK_ITEM',
      states: [
        { name: 'DRAFT', label: 'Draft', is_initial: true, is_terminal: false, requires_approval: false },
        { name: 'SUBMITTED', label: 'Submitted', is_initial: false, is_terminal: false, requires_approval: false },
        { name: 'APPROVED', label: 'Approved', is_initial: false, is_terminal: false, requires_approval: true, approval_role: 'Supervisor' },
        { name: 'IN_PROGRESS', label: 'In Progress', is_initial: false, is_terminal: false, requires_approval: false },
        { name: 'COMPLETED', label: 'Completed', is_initial: false, is_terminal: false, requires_approval: false },
        { name: 'VERIFIED', label: 'Verified & Closed', is_initial: false, is_terminal: true, requires_approval: false },
        { name: 'CANCELLED', label: 'Cancelled', is_initial: false, is_terminal: true, requires_approval: false },
      ],
      transitions: [
        { from_state: 'DRAFT', to_state: 'SUBMITTED', action: 'submit', label: 'Submit for Review', required_role: 'Operator' },
        { from_state: 'SUBMITTED', to_state: 'APPROVED', action: 'approve', label: 'Supervisor Approve', required_role: 'Supervisor' },
        { from_state: 'SUBMITTED', to_state: 'DRAFT', action: 'return', label: 'Return for Correction', required_role: 'Supervisor' },
        { from_state: 'APPROVED', to_state: 'IN_PROGRESS', action: 'start', label: 'Start Work', required_role: 'Technician' },
        { from_state: 'IN_PROGRESS', to_state: 'COMPLETED', action: 'complete', label: 'Complete Work', required_role: 'Technician' },
        { from_state: 'COMPLETED', to_state: 'VERIFIED', action: 'verify', label: 'Verify & Close', required_role: 'Supervisor' },
        { from_state: 'DRAFT', to_state: 'CANCELLED', action: 'cancel', label: 'Cancel', required_role: 'Supervisor' },
      ],
    },
    RESOURCE_ALLOCATION: {
      name: 'Resource Allocation Lifecycle',
      description: 'Fleet, machinery, and tool allocation workflow',
      entity_type: 'RESOURCE_ALLOCATION',
      states: [
        { name: 'PENDING_ALLOCATION', label: 'Pending Allocation', is_initial: true, is_terminal: false },
        { name: 'RESERVED', label: 'Reserved', is_initial: false, is_terminal: false },
        { name: 'DISPATCHED', label: 'Dispatched / In Use', is_initial: false, is_terminal: false },
        { name: 'RETURNED', label: 'Returned', is_initial: false, is_terminal: true },
        { name: 'REJECTED', label: 'Rejected', is_initial: false, is_terminal: true },
      ],
      transitions: [
        { from_state: 'PENDING_ALLOCATION', to_state: 'RESERVED', action: 'reserve', label: 'Reserve Asset', required_role: 'Resource_Coordinator' },
        { from_state: 'PENDING_ALLOCATION', to_state: 'REJECTED', action: 'reject', label: 'Reject Requisition', required_role: 'Resource_Coordinator' },
        { from_state: 'RESERVED', to_state: 'DISPATCHED', action: 'dispatch', label: 'Dispatch to Site', required_role: 'Resource_Coordinator' },
        { from_state: 'DISPATCHED', to_state: 'RETURNED', action: 'return', label: 'Return & Inspect', required_role: 'Resource_Coordinator' },
      ],
    },
  };

  const applyPreset = (key: 'MACHINE_REQUEST' | 'WORK_ITEM' | 'RESOURCE_ALLOCATION') => {
    const p = PRESETS[key];
    setSelectedPreset(key);
    setNewName(p.name);
    setNewDesc(p.description);
    setNewEntityType(p.entity_type);
    setNewStatesJson(JSON.stringify(p.states, null, 2));
    setNewTransitionsJson(JSON.stringify(p.transitions, null, 2));
  };

  const [newStatesJson, setNewStatesJson] = useState(JSON.stringify(PRESETS.MACHINE_REQUEST.states, null, 2));
  const [newTransitionsJson, setNewTransitionsJson] = useState(JSON.stringify(PRESETS.MACHINE_REQUEST.transitions, null, 2));
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [validating, setValidating] = useState(false);
  const [creating, setCreating] = useState(false);
  const [jsonError, setJsonError] = useState<string | null>(null);

  const loadApprovalWorkflows = useCallback(async () => {
    setAppLoading(true);
    try {
      const data = await apiFetch<ApprovalWorkflow[]>('/api/v1/approvals/admin/workflows');
      setApprovalWorkflows(data || []);
    } catch {
      setApprovalWorkflows([]);
    } finally {
      setAppLoading(false);
    }
  }, []);

  const loadTemplates = useCallback(async () => {
    setTemplatesLoading(true);
    try {
      const data = await apiFetch<WFTemplate[]>('/api/v1/workflows/templates');
      setTemplates(data || []);
    } catch {
      setTemplates([]);
    } finally {
      setTemplatesLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'APPROVAL_CHAINS') loadApprovalWorkflows();
    else loadTemplates();
  }, [activeTab, loadApprovalWorkflows, loadTemplates]);

  const viewTemplateDetail = async (id: string) => {
    setDetailLoading(true);
    try {
      const data = await apiFetch<WFTemplateDetail>(`/api/v1/workflows/templates/${id}`);
      setSelectedTemplate(data);
    } catch {
    } finally {
      setDetailLoading(false);
    }
  };

  const activateTemplate = async (id: string) => {
    try {
      await apiFetch(`/api/v1/workflows/templates/${id}/activate`, { method: 'PUT' });
      loadTemplates();
      if (selectedTemplate?.id === id) viewTemplateDetail(id);
    } catch (e) {
      console.error('Activate failed', e);
    }
  };

  const parseJsonFields = () => {
    try {
      const states = JSON.parse(newStatesJson);
      const transitions = JSON.parse(newTransitionsJson);
      setJsonError(null);
      return { states, transitions };
    } catch (e: any) {
      setJsonError(`JSON parse error: ${e.message}`);
      return null;
    }
  };

  const runValidation = async () => {
    const parsed = parseJsonFields();
    if (!parsed) return;
    setValidating(true);
    try {
      const result = await apiFetch<ValidationResult>('/api/v1/workflows/templates/validate', {
        method: 'POST',
        body: JSON.stringify({
          name: newName || 'Validation Draft',
          entity_type: newEntityType,
          states: parsed.states,
          transitions: parsed.transitions,
        }),
      });
      setValidation(result);
    } catch (e) {
      console.error('Validation failed', e);
    } finally {
      setValidating(false);
    }
  };

  const handleCreateSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const parsed = parseJsonFields();
    if (!parsed) return;
    setCreating(true);
    try {
      await apiFetch('/api/v1/workflows/templates', {
        method: 'POST',
        body: JSON.stringify({
          name: newName.trim(),
          description: newDesc.trim() || undefined,
          entity_type: newEntityType,
          states: parsed.states,
          transitions: parsed.transitions,
        }),
      });
      setIsCreateOpen(false);
      setNewName('');
      setNewDesc('');
      setValidation(null);
      loadTemplates();
    } catch (e: any) {
      console.error('Create template failed', e);
    } finally {
      setCreating(false);
    }
  };

  return (
    <Protect capability="workflows:manage" isPageGuard moduleName="Workflow Configuration">
      <div className="p-6 space-y-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Settings className="size-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-foreground">
                Workflow Configuration
              </h1>
              <p className="text-xs text-muted-foreground">
                Manage approval chains and configurable state machine workflows.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {activeTab === 'STATE_MACHINES' && (
              <Button size="sm" onClick={() => setIsCreateOpen(true)} className="text-xs gap-1.5">
                <Plus className="size-3.5" />
                New Template
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => activeTab === 'APPROVAL_CHAINS' ? loadApprovalWorkflows() : loadTemplates()}
              className="text-xs gap-1.5"
            >
              <RefreshCw className="size-3.5" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 p-1 bg-muted/40 rounded-lg border border-border w-fit">
          <button
            onClick={() => setActiveTab('APPROVAL_CHAINS')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              activeTab === 'APPROVAL_CHAINS'
                ? 'bg-card text-foreground shadow-xs border border-border'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <ShieldCheck className="size-3.5" />
            Approval Chains
          </button>
          <button
            onClick={() => setActiveTab('STATE_MACHINES')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              activeTab === 'STATE_MACHINES'
                ? 'bg-card text-foreground shadow-xs border border-border'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <GitFork className="size-3.5" />
            State Machine Workflows
          </button>
        </div>

        {/* ── APPROVAL CHAINS TAB ───────────────────────────────────────────── */}
        {activeTab === 'APPROVAL_CHAINS' && (
          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold">Active Approval Chain Configurations</CardTitle>
              <CardDescription className="text-xs">
                Configured multi-step authorization tiers matching resources by type, cost, priority, and risk.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              {appLoading ? (
                <div className="p-12 text-center text-xs text-muted-foreground">Loading approval workflows...</div>
              ) : approvalWorkflows.length === 0 ? (
                <div className="p-12 text-center text-xs text-muted-foreground border border-dashed rounded-lg">
                  No custom approval chains registered. Standard multi-tier policies apply.
                </div>
              ) : (
                <div className="space-y-3">
                  {approvalWorkflows.map((wf) => (
                    <div key={wf.id} className="p-4 rounded-lg border border-border bg-card/60 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-xs text-foreground">{wf.name}</span>
                          <Badge variant="outline" className="text-[10px] uppercase font-mono">
                            {wf.resource_type || 'JOB_CARD'}
                          </Badge>
                          {wf.risk_level && (
                            <Badge className="text-[10px] bg-amber-500/20 text-amber-400 border-amber-500/30">
                              {wf.risk_level} RISK
                            </Badge>
                          )}
                        </div>
                        <Badge variant={wf.is_active ? 'default' : 'secondary'} className="text-[10px]">
                          {wf.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                      {wf.description && (
                        <p className="text-xs text-muted-foreground">{wf.description}</p>
                      )}
                      {wf.steps && wf.steps.length > 0 && (
                        <div className="flex items-center gap-2 flex-wrap pt-2 border-t border-border/50">
                          <span className="text-[10px] font-mono text-muted-foreground uppercase">Approval Steps:</span>
                          {wf.steps.map((st, idx) => (
                            <div key={idx} className="flex items-center gap-1 text-[11px] font-mono bg-muted/60 px-2 py-1 rounded">
                              <span className="text-primary font-bold">Step {st.step_number}:</span>
                              <span>{st.authority_role}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* ── STATE MACHINE WORKFLOWS TAB ───────────────────────────────────── */}
        {activeTab === 'STATE_MACHINES' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Template List */}
            <div className="lg:col-span-2 space-y-3">
              <Card className="bg-card border-border">
                <CardHeader className="pb-2 border-b border-border">
                  <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    <GitFork className="size-4 text-primary" />
                    Workflow Templates
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Versioned state machine definitions. Activate a version to use it for new workflow instances.
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                  {templatesLoading ? (
                    <div className="p-10 text-center text-xs text-muted-foreground">Loading templates...</div>
                  ) : templates.length === 0 ? (
                    <div className="p-10 text-center text-xs text-muted-foreground border border-dashed rounded-lg m-4">
                      No workflow templates defined. Click "New Template" to create one.
                    </div>
                  ) : (
                    <div className="divide-y divide-border/60">
                      {templates.map((t) => (
                        <div key={t.id} className="p-3.5 flex items-center justify-between gap-3 hover:bg-muted/20 transition-colors">
                          <div className="flex items-center gap-3 flex-1 min-w-0">
                            <div className={`p-1.5 rounded ${t.is_active ? 'bg-emerald-500/15 text-emerald-400' : 'bg-muted text-muted-foreground'}`}>
                              <GitFork className="size-4" />
                            </div>
                            <div className="min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-xs font-semibold text-foreground">{t.name}</span>
                                <Badge variant="outline" className="text-[10px] font-mono shrink-0">v{t.version}</Badge>
                                <Badge variant="outline" className="text-[10px] shrink-0">{t.entity_type}</Badge>
                                {t.is_active && (
                                  <Badge className="text-[10px] bg-emerald-500/20 text-emerald-400 border-emerald-500/30 shrink-0">ACTIVE</Badge>
                                )}
                                {t.is_default && (
                                  <Badge className="text-[10px] bg-blue-500/20 text-blue-400 border-blue-500/30 shrink-0">DEFAULT</Badge>
                                )}
                              </div>
                              <div className="text-[10px] text-muted-foreground font-mono mt-0.5">
                                {t.states_count} states · {t.transitions_count} transitions
                                {t.department_name && ` · ${t.department_name}`}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-1 shrink-0">
                            {!t.is_active && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => activateTemplate(t.id)}
                                className="text-[11px] h-7 gap-1 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10"
                              >
                                <Zap className="size-3" />
                                Activate
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => viewTemplateDetail(t.id)}
                              className="text-[11px] h-7 gap-1"
                            >
                              <Eye className="size-3" />
                              View
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Template Detail Panel */}
            <div className="space-y-4">
              {detailLoading ? (
                <Card className="bg-card border-border">
                  <CardContent className="p-8 text-center text-xs text-muted-foreground">Loading...</CardContent>
                </Card>
              ) : selectedTemplate ? (
                <Card className="bg-card border-border">
                  <CardHeader className="pb-2 border-b border-border">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-sm font-bold">{selectedTemplate.name}</CardTitle>
                        <p className="text-[10px] text-muted-foreground font-mono mt-0.5">
                          {selectedTemplate.entity_type} · v{selectedTemplate.version}
                          {selectedTemplate.is_active && ' · ACTIVE'}
                        </p>
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => setSelectedTemplate(null)} className="h-7 w-7 p-0">
                        <X className="size-3.5" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="p-4 space-y-4 text-xs">
                    {/* States */}
                    <div>
                      <div className="text-[10px] font-mono text-muted-foreground uppercase mb-2">States ({selectedTemplate.states.length})</div>
                      <div className="space-y-1.5">
                        {selectedTemplate.states.map((s) => (
                          <div key={s.name} className="flex items-center gap-2 p-2 rounded border border-border bg-muted/20 text-[11px]">
                            <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                              s.is_initial ? 'bg-blue-400' : s.is_terminal ? 'bg-emerald-400' : 'bg-muted-foreground'
                            }`} />
                            <span className="font-mono font-bold text-foreground">{s.name}</span>
                            {s.label && <span className="text-muted-foreground">{s.label}</span>}
                            <div className="ml-auto flex gap-1">
                              {s.is_initial && <Badge className="text-[9px] bg-blue-500/20 text-blue-400 border-blue-500/30 px-1">INITIAL</Badge>}
                              {s.is_terminal && <Badge className="text-[9px] bg-emerald-500/20 text-emerald-400 border-emerald-500/30 px-1">TERMINAL</Badge>}
                              {s.requires_approval && <Badge className="text-[9px] bg-amber-500/20 text-amber-400 border-amber-500/30 px-1">APPROVAL</Badge>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Transitions */}
                    <div>
                      <div className="text-[10px] font-mono text-muted-foreground uppercase mb-2">Transitions ({selectedTemplate.transitions.length})</div>
                      <div className="space-y-1.5">
                        {selectedTemplate.transitions.map((t, i) => (
                          <div key={i} className="p-2 rounded border border-border bg-muted/20 space-y-1 text-[11px]">
                            <div className="flex items-center gap-1.5 font-mono">
                              <span className="text-muted-foreground">{t.from_state}</span>
                              <ArrowRight className="size-3 text-muted-foreground shrink-0" />
                              <span className="text-foreground font-bold">{t.to_state}</span>
                              <Badge variant="outline" className="text-[9px] ml-auto">{t.action}</Badge>
                            </div>
                            <div className="flex items-center gap-1.5 text-muted-foreground">
                              <Lock className="size-3 shrink-0" />
                              <span>{t.required_role || t.required_permission || 'Superuser'}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card className="bg-card border-border border-dashed">
                  <CardContent className="p-8 text-center text-xs text-muted-foreground">
                    <GitFork className="size-8 mx-auto mb-2 opacity-30" />
                    Select a template to inspect its states and transitions.
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}

        {/* ── CREATE TEMPLATE MODAL ─────────────────────────────────────────── */}
        {isCreateOpen && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-start justify-end">
            <div className="w-full max-w-2xl bg-card border-l border-border h-full flex flex-col shadow-2xl overflow-hidden">
              <div className="p-4 border-b border-border flex items-center justify-between bg-muted/20">
                <div className="flex items-center gap-2">
                  <GitFork className="size-5 text-primary" />
                  <div>
                    <h2 className="text-sm font-bold text-foreground">Create Workflow Template</h2>
                    <p className="text-[10px] text-muted-foreground">Define states and transitions using JSON. Validate before saving.</p>
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={() => { setIsCreateOpen(false); setValidation(null); }} className="h-8 w-8 p-0">
                  <X className="size-4" />
                </Button>
              </div>

              <form id="workflow-template-form" onSubmit={handleCreateSubmit} className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
                {/* Presets */}
                <div className="space-y-1.5 p-3 rounded-lg border border-border bg-muted/20">
                  <div className="text-[11px] font-semibold text-foreground flex items-center justify-between">
                    <span>Workflow Templates & Presets:</span>
                    <span className="text-[10px] text-muted-foreground">Click to populate schema</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    <Button
                      type="button"
                      variant={selectedPreset === 'MACHINE_REQUEST' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => applyPreset('MACHINE_REQUEST')}
                      className="text-[11px] h-7"
                    >
                      Machine Request
                    </Button>
                    <Button
                      type="button"
                      variant={selectedPreset === 'WORK_ITEM' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => applyPreset('WORK_ITEM')}
                      className="text-[11px] h-7"
                    >
                      Work Item / Job Card
                    </Button>
                    <Button
                      type="button"
                      variant={selectedPreset === 'RESOURCE_ALLOCATION' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => applyPreset('RESOURCE_ALLOCATION')}
                      className="text-[11px] h-7"
                    >
                      Resource Allocation
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Template Name *</label>
                    <Input
                      required
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                      placeholder="e.g. Machine Request Standard"
                      className="h-8 text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Entity Type</label>
                    <select
                      value={newEntityType}
                      onChange={(e) => setNewEntityType(e.target.value)}
                      className="w-full h-8 rounded border border-input bg-card px-2 text-xs"
                    >
                      <option value="REQUEST">REQUEST</option>
                      <option value="WORK_ITEM">WORK_ITEM</option>
                      <option value="RESOURCE_ALLOCATION">RESOURCE_ALLOCATION</option>
                      <option value="APPROVAL">APPROVAL</option>
                      <option value="JOB_CARD">JOB_CARD</option>
                      <option value="ASSET">ASSET</option>
                      <option value="ANY">ANY</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-foreground">Description</label>
                  <Input
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                    placeholder="Optional description of this workflow's purpose"
                    className="h-8 text-xs"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-foreground flex items-center justify-between">
                    <span>States (JSON array)</span>
                    <span className="text-[10px] text-muted-foreground">is_initial, is_terminal, requires_approval</span>
                  </label>
                  <textarea
                    value={newStatesJson}
                    onChange={(e) => setNewStatesJson(e.target.value)}
                    rows={10}
                    className="w-full rounded-md border border-input bg-muted/30 px-3 py-2 text-xs font-mono resize-y focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-foreground flex items-center justify-between">
                    <span>Transitions (JSON array)</span>
                    <span className="text-[10px] text-muted-foreground">from_state, to_state, action, required_role</span>
                  </label>
                  <textarea
                    value={newTransitionsJson}
                    onChange={(e) => setNewTransitionsJson(e.target.value)}
                    rows={10}
                    className="w-full rounded-md border border-input bg-muted/30 px-3 py-2 text-xs font-mono resize-y focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>

                {jsonError && (
                  <div className="p-3 rounded border border-rose-500/40 bg-rose-500/10 text-rose-400 text-[11px] flex items-start gap-2">
                    <XCircle className="size-4 shrink-0 mt-0.5" />
                    <span>{jsonError}</span>
                  </div>
                )}

                {/* Validation Result */}
                {validation && (
                  <div className={`p-3 rounded border text-[11px] space-y-2 ${
                    validation.valid
                      ? 'border-emerald-500/40 bg-emerald-500/10'
                      : 'border-rose-500/40 bg-rose-500/10'
                  }`}>
                    <div className={`flex items-center gap-1.5 font-semibold ${validation.valid ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {validation.valid ? <CheckCircle2 className="size-4" /> : <XCircle className="size-4" />}
                      {validation.valid ? 'Validation Passed — Ready to save.' : `Validation Failed — ${validation.errors.length} error(s)`}
                    </div>
                    {validation.errors.map((e, i) => (
                      <div key={i} className="flex items-start gap-1.5 text-rose-400">
                        <XCircle className="size-3 shrink-0 mt-0.5" />
                        <span>{e}</span>
                      </div>
                    ))}
                    {validation.warnings.map((w, i) => (
                      <div key={i} className="flex items-start gap-1.5 text-amber-400">
                        <AlertCircle className="size-3 shrink-0 mt-0.5" />
                        <span>{w}</span>
                      </div>
                    ))}
                  </div>
                )}
              </form>

              <div className="p-4 border-t border-border flex justify-end gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => { setIsCreateOpen(false); setValidation(null); }} className="text-xs">
                  Cancel
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={runValidation}
                  disabled={validating || !newName.trim()}
                  className="text-xs border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
                >
                  {validating ? 'Validating...' : 'Validate'}
                </Button>
                <Button
                  type="submit"
                  form="workflow-template-form"
                  size="sm"
                  disabled={creating || !newName.trim() || validation === null || !validation.valid}
                  className="text-xs"
                >
                  {creating ? 'Saving...' : 'Save Template'}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Protect>
  );
}
