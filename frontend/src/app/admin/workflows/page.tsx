'use client';

import React, { useEffect, useState } from 'react';
import { apiFetch } from '@/lib/api';
import { Protect } from '@/components/auth/Protect';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Settings, ShieldCheck, Layers, GitFork, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface WorkflowStep {
  step_number: number;
  authority_role: string;
  required_permission: string;
}

interface WorkflowDefinition {
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

export default function WorkflowsAdminPage() {
  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([]);
  const [loading, setLoading] = useState(true);

  const loadWorkflows = async () => {
    setLoading(true);
    try {
      const data = await apiFetch<WorkflowDefinition[]>('/api/v1/approvals/admin/workflows');
      setWorkflows(data || []);
    } catch (err) {
      console.error('Failed to load workflows', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorkflows();
  }, []);

  return (
    <Protect capability="settings:manage">
      <div className="p-6 space-y-6 max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Settings className="size-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-foreground">
                Workflow Rules & Approvals
              </h1>
              <p className="text-xs text-muted-foreground">
                Authoritative approval chains, threshold levels, and separation of duties policies.
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={loadWorkflows} disabled={loading} className="text-xs gap-1.5">
            <RefreshCw className={`size-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        <Card className="bg-card border-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">Active Workflow Configurations</CardTitle>
            <CardDescription className="text-xs">
              Configured authorization tiers and verification steps across operational resources.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            {loading ? (
              <div className="p-12 text-center text-xs text-muted-foreground">Loading workflows...</div>
            ) : workflows.length === 0 ? (
              <div className="p-12 text-center text-xs text-muted-foreground border border-dashed rounded-lg">
                No active workflow definitions registered. Standard multi-tier policies apply.
              </div>
            ) : (
              <div className="space-y-3">
                {workflows.map((wf) => (
                  <div key={wf.id} className="p-4 rounded-lg border border-border bg-card/60 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-xs text-foreground">{wf.name}</span>
                        <Badge variant="outline" className="text-[10px] uppercase font-mono">
                          {wf.resource_type || 'JOB_CARD'}
                        </Badge>
                      </div>
                      <Badge variant={wf.is_active ? 'default' : 'secondary'} className="text-[10px]">
                        {wf.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">{wf.description}</p>
                    {wf.steps && wf.steps.length > 0 && (
                      <div className="flex items-center gap-2 flex-wrap pt-2 border-t border-border/50">
                        <span className="text-[10px] font-mono text-muted-foreground uppercase">Steps:</span>
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
      </div>
    </Protect>
  );
}
