'use client';

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { Protect } from "@/components/auth/Protect";
import { Car, CheckCircle, Wrench, Activity, ArrowRight, BarChart3, AlertOctagon, Filter } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";

interface Requisition {
  id: string;
  status: string;
  machine_type_id?: string;
  start_time: string;
  end_time: string;
  department_id?: string;
  requisition_number?: string;
  machine_type?: { name: string };
  purpose?: string;
  department?: { name: string };
  requester?: { first_name: string; last_name: string };
}

interface Machine {
  id: string;
  machine_type_id: string;
  identifier: string;
  serial_number?: string | null;
  status: string;
  location?: string | null;
  capacity_rating?: string | null;
  current_hour_meter?: number;
  last_maintenance_date: string | null;
  machine_type?: {
    name: string;
    category?: string;
    hourly_rate?: number;
  };
}

export default function FleetDashboard() {
  const router = useRouter();
  const [requisitions, setRequisitions] = useState<Requisition[]>([]);
  const [machines, setMachines] = useState<Machine[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const handleStatusChange = async (machineId: string, newStatus: string) => {
    setUpdatingId(machineId);
    // Optimistic UI update
    setMachines((prev) =>
      prev.map((m) => (m.id === machineId ? { ...m, status: newStatus } : m))
    );
    try {
      const res = await apiFetch(`/api/v1/fleet/machines/${machineId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      if (res) {
        const updatedMachinesRes = await apiFetch<Machine[]>("/api/v1/fleet/machines");
        if (Array.isArray(updatedMachinesRes) && updatedMachinesRes.length > 0) {
          setMachines(updatedMachinesRes);
        }
      }
    } catch (e) {
      console.error("Failed to update status", e);
      // Revert if error
      const updatedMachinesRes = await apiFetch<Machine[]>("/api/v1/fleet/machines").catch(() => null);
      if (Array.isArray(updatedMachinesRes)) setMachines(updatedMachinesRes);
    } finally {
      setUpdatingId(null);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [reqsData, machData] = await Promise.all([
          apiFetch("/api/v1/fleet/requisitions"),
          apiFetch("/api/v1/fleet/machines")
        ]);
        if (Array.isArray(reqsData)) {
          setRequisitions(reqsData);
        } else {
          setRequisitions([]);
        }

        if (Array.isArray(machData)) {
          setMachines(machData);
        } else {
          setMachines([]);
        }
      } catch {
        setRequisitions([]);
        setMachines([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const totalMachines = machines.length;
  const availableMachines = machines.filter(m => m.status === 'AVAILABLE').length;
  const inUseMachines = machines.filter(m => m.status === 'IN_USE').length;
  const maintenanceMachines = machines.filter(m => m.status === 'UNDER_MAINTENANCE').length;
  const outOfServiceMachines = machines.filter(m => m.status === 'OUT_OF_SERVICE').length;
  const availabilityRate = totalMachines > 0 ? Math.round((availableMachines / totalMachines) * 100) : 0;

  const filteredMachines = statusFilter === 'ALL'
    ? machines
    : machines.filter(m => m.status === statusFilter);

  return (
    <Protect capability="fleet:view" isPageGuard moduleName="Fleet & Heavy Equipment">
      <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-4 md:space-y-5">
        
        {/* ── HEADER ──────────────────────────────────────────────────────── */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-3">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-foreground tracking-tight">Fleet & Equipment</h1>
            <p className="text-xs text-muted-foreground font-mono mt-0.5">
              Heavy mining machinery register, real-time telemetry, pre-starts & dispatch allocations
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <Link href="/fleet/calendar">
              <Button variant="outline" size="sm" className="text-xs">
                Calendar
              </Button>
            </Link>
            <Link href="/fleet/requisitions">
              <Button variant="outline" size="sm" className="text-xs">
                Requisitions
              </Button>
            </Link>
            <Protect capability="requisition:create">
              <Link href="/fleet/requisitions/new">
                <Button size="sm" className="text-xs">
                  New Requisition
                </Button>
              </Link>
            </Protect>
          </div>
        </div>

        {/* ── COMPACT TOP 4 KPI CARDS ─────────────────────────────────────── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Card className="p-3.5 bg-card border border-border">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-primary/10 text-primary rounded-xl shrink-0">
                <Car className="size-5" />
              </div>
              <div className="min-w-0">
                <p className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">Total Fleet</p>
                <p className="text-xl md:text-2xl font-bold font-mono text-foreground">{totalMachines}</p>
              </div>
            </div>
          </Card>

          <Card className="p-3.5 bg-card border border-border">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-emerald-500/10 text-emerald-500 rounded-xl shrink-0">
                <CheckCircle className="size-5" />
              </div>
              <div className="min-w-0">
                <p className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">Available</p>
                <p className="text-xl md:text-2xl font-bold font-mono text-emerald-500">{availableMachines}</p>
              </div>
            </div>
          </Card>

          <Card className="p-3.5 bg-card border border-border">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-blue-500/10 text-blue-500 rounded-xl shrink-0">
                <Activity className="size-5" />
              </div>
              <div className="min-w-0">
                <p className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">In Use</p>
                <p className="text-xl md:text-2xl font-bold font-mono text-blue-500">{inUseMachines}</p>
              </div>
            </div>
          </Card>

          <Card className="p-3.5 bg-card border border-border">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-amber-500/10 text-amber-500 rounded-xl shrink-0">
                <Wrench className="size-5" />
              </div>
              <div className="min-w-0">
                <p className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">Maintenance</p>
                <p className="text-xl md:text-2xl font-bold font-mono text-amber-500">{maintenanceMachines}</p>
              </div>
            </div>
          </Card>
        </div>

        {/* ── 2-COLUMN SPLIT: COMPACT CHART & QUICK FILTER PANEL ──────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5">
          <Card className="lg:col-span-7 flex flex-col justify-between">
            <CardHeader className="pb-1 pt-3.5 px-4">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-bold flex items-center gap-1.5">
                  <BarChart3 className="size-4 text-primary" />
                  Fleet Status Overview
                </CardTitle>
                <span className="text-[11px] font-mono text-muted-foreground">Live Telemetry Distribution</span>
              </div>
            </CardHeader>
            <CardContent className="px-2 pb-2 h-44">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={[
                    { name: 'Available', count: availableMachines, fill: '#10b981' }, 
                    { name: 'In Use', count: inUseMachines, fill: '#3b82f6' },
                    { name: 'Maintenance', count: maintenanceMachines, fill: '#f59e0b' },
                    { name: 'Grounded', count: outOfServiceMachines, fill: '#ef4444' },
                  ]}
                  margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                >
                  <XAxis dataKey="name" stroke="var(--color-muted-foreground)" fontSize={11} />
                  <YAxis stroke="var(--color-muted-foreground)" allowDecimals={false} fontSize={11} />
                  <Tooltip 
                    cursor={{fill: 'var(--color-muted)'}} 
                    contentStyle={{backgroundColor: 'var(--color-popover)', borderColor: 'var(--color-border)', borderRadius: '8px', color: 'var(--color-popover-foreground)', fontSize: '11px'}} 
                    itemStyle={{color: 'var(--color-popover-foreground)'}}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="lg:col-span-5 flex flex-col justify-between">
            <CardHeader className="pb-1 pt-3.5 px-4">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-bold flex items-center gap-1.5">
                  <Filter className="size-4 text-emerald-500" />
                  Fleet Readiness & Quick Filters
                </CardTitle>
                <Badge variant="outline" className="text-[10px] font-mono font-bold text-emerald-500 border-emerald-500/30">
                  {availabilityRate}% Ready
                </Badge>
              </div>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                Click any status chip below to filter the inventory grid:
              </p>
            </CardHeader>
            <CardContent className="px-4 pb-3.5 space-y-2">
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <button
                  type="button"
                  onClick={() => setStatusFilter('ALL')}
                  className={`p-2 rounded-lg border text-left flex items-center justify-between transition ${
                    statusFilter === 'ALL'
                      ? 'bg-primary/10 border-primary text-primary font-bold shadow-xs'
                      : 'bg-muted/30 border-border hover:bg-muted/60 text-muted-foreground'
                  }`}
                >
                  <span>All Fleet</span>
                  <span className="font-bold">{totalMachines}</span>
                </button>

                <button
                  type="button"
                  onClick={() => setStatusFilter('AVAILABLE')}
                  className={`p-2 rounded-lg border text-left flex items-center justify-between transition ${
                    statusFilter === 'AVAILABLE'
                      ? 'bg-emerald-500/15 border-emerald-500 text-emerald-500 font-bold shadow-xs'
                      : 'bg-muted/30 border-border hover:bg-muted/60 text-muted-foreground'
                  }`}
                >
                  <span className="flex items-center gap-1.5">
                    <span className="size-2 rounded-full bg-emerald-500" />
                    Available
                  </span>
                  <span className="font-bold text-emerald-500">{availableMachines}</span>
                </button>

                <button
                  type="button"
                  onClick={() => setStatusFilter('IN_USE')}
                  className={`p-2 rounded-lg border text-left flex items-center justify-between transition ${
                    statusFilter === 'IN_USE'
                      ? 'bg-blue-500/15 border-blue-500 text-blue-500 font-bold shadow-xs'
                      : 'bg-muted/30 border-border hover:bg-muted/60 text-muted-foreground'
                  }`}
                >
                  <span className="flex items-center gap-1.5">
                    <span className="size-2 rounded-full bg-blue-500" />
                    In Use
                  </span>
                  <span className="font-bold text-blue-500">{inUseMachines}</span>
                </button>

                <button
                  type="button"
                  onClick={() => setStatusFilter('UNDER_MAINTENANCE')}
                  className={`p-2 rounded-lg border text-left flex items-center justify-between transition ${
                    statusFilter === 'UNDER_MAINTENANCE'
                      ? 'bg-amber-500/15 border-amber-500 text-amber-500 font-bold shadow-xs'
                      : 'bg-muted/30 border-border hover:bg-muted/60 text-muted-foreground'
                  }`}
                >
                  <span className="flex items-center gap-1.5">
                    <span className="size-2 rounded-full bg-amber-500" />
                    Maintenance
                  </span>
                  <span className="font-bold text-amber-500">{maintenanceMachines}</span>
                </button>
              </div>

              {outOfServiceMachines > 0 && (
                <button
                  type="button"
                  onClick={() => setStatusFilter('OUT_OF_SERVICE')}
                  className={`w-full p-2 rounded-lg border text-left flex items-center justify-between text-xs font-mono transition ${
                    statusFilter === 'OUT_OF_SERVICE'
                      ? 'bg-red-500/15 border-red-500 text-red-500 font-bold shadow-xs'
                      : 'bg-red-500/5 border-red-500/20 hover:bg-red-500/10 text-red-400'
                  }`}
                >
                  <span className="flex items-center gap-1.5">
                    <span className="size-2 rounded-full bg-red-500 animate-pulse" />
                    Red-Tag Grounded
                  </span>
                  <span className="font-bold text-red-500">{outOfServiceMachines}</span>
                </button>
              )}
            </CardContent>
          </Card>
        </div>

        {/* ── MACHINE INVENTORY GRID ──────────────────────────────────────── */}
        <div className="space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold tracking-tight text-foreground">Machine Inventory</h2>
              <Badge variant="outline" className="text-xs font-mono">
                Showing {filteredMachines.length} of {totalMachines}
              </Badge>
              {statusFilter !== 'ALL' && (
                <button
                  type="button"
                  onClick={() => setStatusFilter('ALL')}
                  className="text-xs text-primary hover:underline font-medium ml-1"
                >
                  Clear Filter
                </button>
              )}
            </div>
          </div>

          {loading ? (
            <p className="text-xs text-muted-foreground font-mono py-6 text-center">Loading machinery inventory...</p>
          ) : filteredMachines.length === 0 ? (
            <div className="p-8 border border-dashed rounded-xl text-center space-y-2">
              <p className="text-sm font-medium text-muted-foreground">No machines match status &quot;{statusFilter}&quot;.</p>
              <Button size="sm" variant="outline" onClick={() => setStatusFilter('ALL')} className="text-xs">
                Reset Filter
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {filteredMachines.map(machine => {
                const statusVariant = 
                  machine.status === 'AVAILABLE' ? 'default' : 
                  machine.status === 'IN_USE' ? 'secondary' : 'destructive';
                
                // Find location (department) if in use
                const activeReq = requisitions.find(r => r.machine_type_id === machine.machine_type_id && (r.status === 'DISPATCHED' || r.status === 'IN_USE'));
                const derivedLocation = machine.status === 'IN_USE' && activeReq
                  ? (activeReq.department?.name || activeReq.department_id || "Mining Pit")
                  : (machine.location || "Central Yard");

                return (
                  <Card 
                    key={machine.id} 
                    onClick={() => router.push(`/fleet/machines/${machine.id}`)}
                    className="p-3 flex flex-col justify-between hover:border-primary hover:shadow-md transition-all cursor-pointer group bg-card border border-border"
                  >
                    <div className="space-y-1.5">
                      <div className="flex justify-between items-start">
                        <div className="font-mono font-bold text-base text-foreground group-hover:text-primary transition-colors">
                          {machine.identifier}
                        </div>
                        <Badge variant={statusVariant as "default" | "secondary" | "destructive" | "outline"} className="text-[10px] font-mono py-0 px-1.5">
                          {machine.status.replace("_", " ")}
                        </Badge>
                      </div>

                      <div className="space-y-1 text-xs">
                        <div className="text-muted-foreground truncate" title={machine.machine_type?.name || machine.machine_type_id}>
                          <span className="font-medium text-foreground/85">{machine.machine_type?.name || "Heavy Equipment"}</span>
                        </div>
                        <div className="flex items-center justify-between text-[11px] text-muted-foreground font-mono">
                          <span className="truncate max-w-28" title={derivedLocation}>{derivedLocation}</span>
                          <span className="font-bold text-foreground">
                            {machine.current_hour_meter != null ? `${machine.current_hour_meter.toLocaleString()}h` : '0h'}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="pt-2 mt-2 border-t border-border/50 flex items-center justify-between gap-2" onClick={(e) => e.stopPropagation()}>
                      <span className="text-[11px] text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-0.5">
                        Profile <ArrowRight className="size-3" />
                      </span>

                      <Protect capability="fleet:allocate">
                        <div className="ml-auto">
                          {machine.status === 'AVAILABLE' && (
                             <Button 
                               size="sm"
                               variant="outline"
                               className="h-6 px-2 text-[10px]"
                               onClick={(e) => {
                                 e.stopPropagation();
                                 handleStatusChange(machine.id, 'UNDER_MAINTENANCE');
                               }}
                               disabled={updatingId === machine.id}
                             >
                               {updatingId === machine.id ? '...' : 'Maintenance'}
                             </Button>
                          )}
                          {machine.status === 'UNDER_MAINTENANCE' && (
                             <Button 
                               size="sm"
                               variant="default"
                               className="h-6 px-2 text-[10px]"
                               onClick={(e) => {
                                 e.stopPropagation();
                                 handleStatusChange(machine.id, 'AVAILABLE');
                               }}
                               disabled={updatingId === machine.id}
                             >
                               {updatingId === machine.id ? '...' : 'Make Available'}
                             </Button>
                          )}
                          {machine.status === 'IN_USE' && (
                            <Badge variant="secondary" className="text-[9px] font-mono py-0">
                              Dispatched
                            </Badge>
                          )}
                          {machine.status === 'OUT_OF_SERVICE' && (
                            <Button 
                              size="sm"
                              variant="destructive" 
                              className="h-6 px-2 text-[10px]"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleStatusChange(machine.id, 'UNDER_MAINTENANCE');
                              }}
                              disabled={updatingId === machine.id}
                            >
                              {updatingId === machine.id ? '...' : 'Repair'}
                            </Button>
                          )}
                        </div>
                      </Protect>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>

        {/* ── COMPACT ACTIVE REQUISITIONS TABLE ───────────────────────────── */}
        <Card>
          <CardHeader className="py-2.5 px-4 flex flex-row items-center justify-between border-b border-border/50">
            <CardTitle className="text-sm font-bold">Active Requisitions</CardTitle>
            <Link href="/fleet/requisitions" className="text-xs font-semibold text-primary hover:underline">
              View All ({requisitions.length}) &rarr;
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader className="bg-muted/40">
                <TableRow>
                  <TableHead className="py-2 text-xs">Requisition #</TableHead>
                  <TableHead className="py-2 text-xs">Machine Type / Purpose</TableHead>
                  <TableHead className="py-2 text-xs">Department</TableHead>
                  <TableHead className="py-2 text-xs">Start Time</TableHead>
                  <TableHead className="py-2 text-xs">End Time</TableHead>
                  <TableHead className="py-2 text-xs">Status</TableHead>
                  <TableHead className="py-2 text-xs">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-muted-foreground h-16 text-xs">Loading requisitions...</TableCell>
                  </TableRow>
                ) : requisitions.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-muted-foreground h-16 text-xs">No active requisitions.</TableCell>
                  </TableRow>
                ) : (
                  requisitions.slice(0, 8).map((req) => (
                    <TableRow key={req.id}>
                      <TableCell className="py-2 font-mono text-xs font-semibold">
                        {req.requisition_number || req.id.substring(0, 8)}
                      </TableCell>
                      <TableCell className="py-2">
                        <div className="text-xs font-medium text-foreground">
                          {req.machine_type?.name || "Heavy Equipment"}
                        </div>
                        {req.purpose && (
                          <div className="text-[11px] text-muted-foreground truncate max-w-xs" title={req.purpose}>
                            {req.purpose}
                          </div>
                        )}
                      </TableCell>
                      <TableCell className="py-2 text-xs text-muted-foreground">
                        {req.department?.name || req.department_id || "Mining Ops"}
                      </TableCell>
                      <TableCell className="py-2 text-xs">{new Date(req.start_time).toLocaleString()}</TableCell>
                      <TableCell className="py-2 text-xs">{new Date(req.end_time).toLocaleString()}</TableCell>
                      <TableCell className="py-2">
                        <Badge variant="outline" className="text-[10px] font-mono py-0">{req.status.replace("_", " ")}</Badge>
                      </TableCell>
                      <TableCell className="py-2">
                        <Link href={`/fleet/requisitions/${req.id}`} className="text-primary hover:underline text-xs font-semibold">
                          View Details
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

      </div>
    </Protect>
  );
}
