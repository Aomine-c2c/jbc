'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '@/lib/api';
import { Protect } from '@/components/auth/Protect';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Building2,
  MapPin,
  FolderTree,
  Users,
  Briefcase,
  GitFork,
  ChevronRight,
  ChevronDown,
  ShieldCheck,
  RefreshCw,
  Plus,
  ArrowUpRight,
  Layers,
} from 'lucide-react';

interface MemberNode {
  id: string;
  name: string;
  email: string;
  position_title?: string;
  roles: string[];
  shift_pattern?: string;
  supervisor_id?: string;
}

interface TeamNode {
  id: string;
  code: string;
  name: string;
  shift_pattern: string;
  members: MemberNode[];
}

interface SectionNode {
  id: string;
  code: string;
  name: string;
  teams: TeamNode[];
  unassigned_members: MemberNode[];
}

interface DepartmentNode {
  id: string;
  code?: string;
  name: string;
  sla_hours_default: number;
  sections: SectionNode[];
  unassigned_members: MemberNode[];
}

interface SiteNode {
  id: string;
  code: string;
  name: string;
  site_type: string;
  departments: DepartmentNode[];
}

interface OrgTree {
  id: string;
  code: string;
  name: string;
  industry_type: string;
  country: string;
  sites: SiteNode[];
}

interface PositionItem {
  id: string;
  code: string;
  title: string;
  skill_level: string;
  description?: string;
}

interface ChainStep {
  level: number;
  user_id: string;
  name: string;
  email: string;
  position_title?: string;
  department_name?: string;
  role: string;
}

export default function OrgAdminPage() {
  const [activeTab, setActiveTab] = useState<'tree' | 'positions' | 'chain'>('tree');
  const [treeData, setTreeData] = useState<OrgTree | null>(null);
  const [positions, setPositions] = useState<PositionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});

  // Chain of command inspection
  const [selectedUserId, setSelectedUserId] = useState<string>('');
  const [chainSteps, setChainSteps] = useState<ChainStep[]>([]);
  const [chainLoading, setChainLoading] = useState(false);

  const toggleNode = (nodeId: string) => {
    setExpandedNodes(prev => ({ ...prev, [nodeId]: !prev[nodeId] }));
  };

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const tree = await apiFetch('/api/v1/org/hierarchy') as OrgTree;
      setTreeData(tree);

      const posList = await apiFetch('/api/v1/org/positions') as PositionItem[];
      setPositions(posList);

      // Auto-expand top sites and departments
      const initialExpanded: Record<string, boolean> = {};
      if (tree?.sites) {
        tree.sites.forEach(s => {
          initialExpanded[s.id] = true;
          s.departments.forEach(d => {
            initialExpanded[d.id] = true;
          });
        });
      }
      setExpandedNodes(initialExpanded);
    } catch (err) {
      console.error('Failed to load org hierarchy:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const inspectChain = async (userId: string) => {
    if (!userId) return;
    try {
      setChainLoading(true);
      setSelectedUserId(userId);
      const res = await apiFetch(`/api/v1/org/users/${userId}/chain-of-command`) as { chain: ChainStep[] };
      setChainSteps(res.chain || []);
    } catch (err) {
      console.error('Failed to inspect chain of command:', err);
      setChainSteps([]);
    } finally {
      setChainLoading(false);
    }
  };

  return (
    <Protect capability="users:manage">
      <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-6">
        {/* HEADER */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-border pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Building2 className="size-6 text-primary" />
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                Industrial Operations Core & Governance
              </h1>
            </div>
            <p className="text-xs text-muted-foreground font-mono mt-0.5">
              Multi-Tier Enterprise Hierarchy • Sites, Sections, Crews & Supervisory Escalation Chains
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={loadData} disabled={loading}>
              <RefreshCw className={`size-3.5 mr-1 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* TOP TABS */}
        <div className="flex border-b border-border space-x-4">
          <button
            onClick={() => setActiveTab('tree')}
            className={`pb-2.5 text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 transition-colors border-b-2 ${
              activeTab === 'tree'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <FolderTree className="size-4" />
            Organizational Tree
          </button>
          <button
            onClick={() => setActiveTab('positions')}
            className={`pb-2.5 text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 transition-colors border-b-2 ${
              activeTab === 'positions'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Briefcase className="size-4" />
            Positions vs RBAC Roles
          </button>
          <button
            onClick={() => setActiveTab('chain')}
            className={`pb-2.5 text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 transition-colors border-b-2 ${
              activeTab === 'chain'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <GitFork className="size-4" />
            Supervisory Escalation Paths
          </button>
        </div>

        {/* TAB 1: ORGANIZATIONAL TREE */}
        {activeTab === 'tree' && (
          <Card>
            <CardHeader className="pb-3">
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Building2 className="size-4 text-primary" />
                    {treeData?.name || 'Enterprise Structure'}
                  </CardTitle>
                  <CardDescription className="text-xs">
                    {treeData?.code} • {treeData?.industry_type} • {treeData?.country}
                  </CardDescription>
                </div>
                <Badge variant="outline" className="font-mono text-xs">
                  {treeData?.sites?.length || 0} Operating Site(s)
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {loading ? (
                <div className="py-12 text-center text-muted-foreground text-xs font-mono">
                  Loading multi-tier hierarchy...
                </div>
              ) : (
                <div className="space-y-3 font-sans text-xs">
                  {treeData?.sites?.map(site => (
                    <div key={site.id} className="border border-border rounded-lg p-3 bg-card/60">
                      {/* SITE NODE */}
                      <div
                        onClick={() => toggleNode(site.id)}
                        className="flex items-center justify-between cursor-pointer select-none font-semibold text-foreground"
                      >
                        <div className="flex items-center gap-2">
                          {expandedNodes[site.id] ? (
                            <ChevronDown className="size-4 text-primary" />
                          ) : (
                            <ChevronRight className="size-4 text-muted-foreground" />
                          )}
                          <MapPin className="size-4 text-emerald-500" />
                          <span>{site.name}</span>
                          <span className="text-[10px] font-mono text-muted-foreground">({site.code})</span>
                        </div>
                        <Badge variant="secondary" className="text-[10px]">
                          {site.site_type}
                        </Badge>
                      </div>

                      {/* DEPARTMENTS UNDER SITE */}
                      {expandedNodes[site.id] && (
                        <div className="pl-6 pt-3 space-y-3 border-l-2 border-primary/20 ml-2 mt-2">
                          {site.departments.map(dept => (
                            <div key={dept.id} className="border border-border/80 rounded p-2.5 bg-muted/20">
                              <div
                                onClick={() => toggleNode(dept.id)}
                                className="flex items-center justify-between cursor-pointer select-none font-medium"
                              >
                                <div className="flex items-center gap-2">
                                  {expandedNodes[dept.id] ? (
                                    <ChevronDown className="size-3.5 text-primary" />
                                  ) : (
                                    <ChevronRight className="size-3.5 text-muted-foreground" />
                                  )}
                                  <Layers className="size-3.5 text-blue-500" />
                                  <span className="font-semibold">{dept.name}</span>
                                  {dept.code && (
                                    <span className="text-[10px] font-mono text-muted-foreground">[{dept.code}]</span>
                                  )}
                                </div>
                                <span className="text-[10px] font-mono text-muted-foreground">
                                  Default SLA: {dept.sla_hours_default}h
                                </span>
                              </div>

                              {/* SECTIONS UNDER DEPARTMENT */}
                              {expandedNodes[dept.id] && (
                                <div className="pl-5 pt-2 space-y-2 border-l border-border ml-1 mt-1.5">
                                  {dept.sections.map(sec => (
                                    <div key={sec.id} className="border border-border/60 rounded p-2 bg-background/50">
                                      <div
                                        onClick={() => toggleNode(sec.id)}
                                        className="flex items-center justify-between cursor-pointer select-none"
                                      >
                                        <div className="flex items-center gap-1.5 font-medium">
                                          {expandedNodes[sec.id] ? (
                                            <ChevronDown className="size-3 text-primary" />
                                          ) : (
                                            <ChevronRight className="size-3 text-muted-foreground" />
                                          )}
                                          <Users className="size-3.5 text-purple-500" />
                                          <span>{sec.name}</span>
                                        </div>
                                        <span className="text-[10px] font-mono text-muted-foreground">
                                          {sec.teams.length} Crew(s)
                                        </span>
                                      </div>

                                      {/* TEAMS UNDER SECTION */}
                                      {expandedNodes[sec.id] && (
                                        <div className="pl-4 pt-1.5 space-y-1.5 border-l border-border ml-1 mt-1">
                                          {sec.teams.map(team => (
                                            <div
                                              key={team.id}
                                              className="p-2 rounded bg-muted/40 text-[11px] flex justify-between items-center"
                                            >
                                              <div className="flex items-center gap-2">
                                                <span className="font-semibold">{team.name}</span>
                                                <Badge variant="outline" className="text-[9px] font-mono">
                                                  {team.shift_pattern}
                                                </Badge>
                                              </div>
                                              <span className="text-[10px] text-muted-foreground">
                                                {team.members.length} Member(s)
                                              </span>
                                            </div>
                                          ))}
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              )}
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

        {/* TAB 2: POSITIONS VS RBAC ROLES */}
        {activeTab === 'positions' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Briefcase className="size-4 text-primary" />
                  Operational Positions (Job Titles)
                </CardTitle>
                <CardDescription className="text-xs">
                  Operational trade titles, technical specialties, and trade skill levels.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="border border-border rounded overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-muted/50 border-b border-border text-[10px] font-mono uppercase text-muted-foreground">
                      <tr>
                        <th className="p-2.5">Code</th>
                        <th className="p-2.5">Job Title</th>
                        <th className="p-2.5">Skill Level</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {positions.length === 0 ? (
                        <tr>
                          <td colSpan={3} className="p-4 text-center text-muted-foreground">
                            No positions registered yet.
                          </td>
                        </tr>
                      ) : (
                        positions.map(p => (
                          <tr key={p.id} className="hover:bg-muted/20">
                            <td className="p-2.5 font-mono font-semibold text-primary">{p.code}</td>
                            <td className="p-2.5 font-medium text-foreground">{p.title}</td>
                            <td className="p-2.5">
                              <Badge variant="secondary" className="text-[9px]">
                                {p.skill_level}
                              </Badge>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <ShieldCheck className="size-4 text-primary" />
                  System RBAC Roles (Software Authorization)
                </CardTitle>
                <CardDescription className="text-xs">
                  Software capability matrix. Job title does not grant raw privileges.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                <div className="p-3 border border-border rounded bg-muted/20 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-foreground">ADMIN</span>
                    <Badge variant="default" className="text-[9px]">Platform Governance</Badge>
                  </div>
                  <p className="text-muted-foreground text-[11px]">
                    Full system administration, platform health, user placement, and security overrides.
                  </p>
                </div>

                <div className="p-3 border border-border rounded bg-muted/20 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-foreground">HOD (Head of Department)</span>
                    <Badge variant="secondary" className="text-[9px]">Department Authority</Badge>
                  </div>
                  <p className="text-muted-foreground text-[11px]">
                    Authorizes departmental requisitions, high-cost Job Cards, and oversees section supervisors.
                  </p>
                </div>

                <div className="p-3 border border-border rounded bg-muted/20 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-foreground">SUPERVISOR</span>
                    <Badge variant="secondary" className="text-[9px]">Section Lead</Badge>
                  </div>
                  <p className="text-muted-foreground text-[11px]">
                    Reviews, approves, and assigns work orders within their section. Signs off completed jobs.
                  </p>
                </div>

                <div className="p-3 border border-border rounded bg-muted/20 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-foreground">TECHNICIAN</span>
                    <Badge variant="secondary" className="text-[9px]">Field Execution</Badge>
                  </div>
                  <p className="text-muted-foreground text-[11px]">
                    Executes assigned Job Cards, records parts & labor, and submits work permits.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* TAB 3: SUPERVISORY ESCALATION PATHS */}
        {activeTab === 'chain' && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <GitFork className="size-4 text-primary" />
                Chain of Command & Escalation Path Inspector
              </CardTitle>
              <CardDescription className="text-xs">
                Inspect reporting relationships and automatic approval escalation routes for any employee.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2 max-w-md">
                <input
                  type="text"
                  placeholder="Enter User UUID..."
                  value={selectedUserId}
                  onChange={e => setSelectedUserId(e.target.value)}
                  className="flex-1 px-3 py-1.5 text-xs bg-background border border-border rounded focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <Button size="sm" onClick={() => inspectChain(selectedUserId)} disabled={chainLoading || !selectedUserId}>
                  {chainLoading ? 'Tracing...' : 'Trace Path'}
                </Button>
              </div>

              {chainSteps.length > 0 ? (
                <div className="border border-border rounded p-4 bg-muted/10 space-y-3">
                  <h4 className="font-semibold text-xs text-foreground uppercase tracking-wider font-mono">
                    Supervisory Hierarchy
                  </h4>
                  <div className="space-y-2">
                    {chainSteps.map(step => (
                      <div
                        key={step.user_id}
                        className="flex items-center gap-3 p-2.5 rounded border border-border bg-card text-xs"
                      >
                        <div className="size-6 rounded-full bg-primary/20 text-primary font-bold flex items-center justify-center text-[10px]">
                          L{step.level}
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold text-foreground">{step.name}</div>
                          <div className="text-[10px] text-muted-foreground font-mono">
                            {step.position_title || 'No Position'} • {step.department_name || 'No Dept'} • Role: {step.role}
                          </div>
                        </div>
                        <ArrowUpRight className="size-4 text-muted-foreground" />
                      </div>
                    ))}
                  </div>
                </div>
              ) : selectedUserId && !chainLoading ? (
                <div className="p-4 border border-dashed border-border rounded text-center text-xs text-muted-foreground">
                  No supervisor assigned for this employee (Top-level or independent).
                </div>
              ) : null}
            </CardContent>
          </Card>
        )}
      </div>
    </Protect>
  );
}
