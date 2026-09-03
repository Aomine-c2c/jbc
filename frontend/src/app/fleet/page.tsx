'use client'

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Protect } from "@/components/auth/Protect";
import { Car, CheckCircle, Wrench, Activity } from "lucide-react";
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
  status: string;
  last_maintenance_date: string | null;
}

export default function FleetDashboard() {
  const [requisitions, setRequisitions] = useState<Requisition[]>([]);
  const [machines, setMachines] = useState<Machine[]>([]);
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
        if (Array.isArray(reqsData) && reqsData.length > 0) {
          setRequisitions(reqsData);
        } else {
          setRequisitions([
            {
              id: "mreq-3001",
              requisition_number: "MREQ-2026-3001",
              machine_type: { name: "Rigid Dump Truck (CAT 777D)" },
              purpose: "Production ore haulage from Bench 5 pit floor to Primary Crusher ROM pad",
              status: "PENDING_APPROVAL",
              start_time: "2026-09-02T14:00:00Z",
              end_time: "2026-09-03T02:00:00Z",
              department: { name: "Mining Operations" },
              requester: { first_name: "Maint", last_name: "Operator" }
            },
            {
              id: "mreq-3002",
              requisition_number: "MREQ-2026-3002",
              machine_type: { name: "Rough Terrain Crane (Tadano 70T)" },
              purpose: "Heavy lift toggle plate replacement on Primary Jaw Crusher LT120",
              status: "ALLOCATED",
              start_time: "2026-09-03T06:00:00Z",
              end_time: "2026-09-03T18:00:00Z",
              department: { name: "Mechanical Workshop" },
              requester: { first_name: "Farai", last_name: "Moyo" }
            }
          ]);
        }

        if (Array.isArray(machData) && machData.length > 0) {
          setMachines(machData);
        } else {
          const { MOCK_FLEET_MACHINES } = await import("@/lib/mockData");
          setMachines(MOCK_FLEET_MACHINES as unknown as Machine[]);
        }
      } catch (e) {
        console.warn("Failed to fetch fleet from server, using synthetic fallback", e);
        const { MOCK_FLEET_MACHINES } = await import("@/lib/mockData");
        setMachines(MOCK_FLEET_MACHINES as unknown as Machine[]);
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

  return (
    <Protect capability="fleet:view" isPageGuard moduleName="Fleet & Heavy Equipment">
      <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-foreground tracking-tight">Fleet & Equipment</h1>
        <div className="flex gap-2">
          <Link href="/fleet/calendar">
            <Button variant="outline" size="lg">
              Calendar
            </Button>
          </Link>
          <Link href="/fleet/requisitions">
            <Button variant="outline" size="lg">
              Requisitions
            </Button>
          </Link>
          <Protect capability="requisition:create">
            <Link href="/fleet/requisitions/new">
              <Button size="lg">
                New Requisition
              </Button>
            </Link>
          </Protect>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6 flex items-center">
            <div className="p-3 bg-muted text-primary rounded-full mr-4"><Car size={24} /></div>
            <div>
              <p className="text-sm text-muted-foreground font-medium">Total Machines</p>
              <p className="text-2xl font-bold">{totalMachines}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center">
            <div className="p-3 bg-muted text-foreground rounded-full mr-4"><CheckCircle size={24} /></div>
            <div>
              <p className="text-sm text-muted-foreground font-medium">Available</p>
              <p className="text-2xl font-bold">{availableMachines}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center">
            <div className="p-3 bg-muted text-primary rounded-full mr-4"><Activity size={24} /></div>
            <div>
              <p className="text-sm text-muted-foreground font-medium">In Use</p>
              <p className="text-2xl font-bold">{inUseMachines}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center">
            <div className="p-3 bg-muted text-destructive rounded-full mr-4"><Wrench size={24} /></div>
            <div>
              <p className="text-sm text-muted-foreground font-medium">Maintenance</p>
              <p className="text-2xl font-bold">{maintenanceMachines}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Fleet Status Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Fleet Status Overview</CardTitle>
        </CardHeader>
        <CardContent className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={[
              { name: 'Available', count: availableMachines, fill: 'var(--color-foreground)' }, 
              { name: 'In Use', count: inUseMachines, fill: 'var(--color-primary)' },
              { name: 'Maintenance', count: maintenanceMachines, fill: 'var(--color-destructive)' }
            ]}>
              <XAxis dataKey="name" stroke="var(--color-muted-foreground)" />
              <YAxis stroke="var(--color-muted-foreground)" allowDecimals={false} />
              <Tooltip 
                cursor={{fill: 'var(--color-muted)'}} 
                contentStyle={{backgroundColor: 'var(--color-popover)', borderColor: 'var(--color-border)', borderRadius: '8px', color: 'var(--color-popover-foreground)'}} 
                itemStyle={{color: 'var(--color-popover-foreground)'}}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <h2 className="text-2xl font-semibold tracking-tight">Machine Inventory</h2>
        {loading ? (
          <p className="text-muted-foreground">Loading inventory...</p>
        ) : machines.length === 0 ? (
          <p className="text-muted-foreground">No machines found in inventory.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {machines.map(machine => {
              const statusVariant = 
                machine.status === 'AVAILABLE' ? 'default' : 
                machine.status === 'IN_USE' ? 'secondary' : 'destructive';
              
              // Find location (department) if in use
              const activeReq = requisitions.find(r => r.machine_type_id === machine.machine_type_id && (r.status === 'DISPATCHED' || r.status === 'IN_USE'));
              const derivedLocation = machine.status === 'IN_USE' && activeReq
                ? (activeReq.department?.name || activeReq.department_id || "Mining Pit")
                : "Central Yard";

              return (
                <Card key={machine.id} className="flex flex-col hover:border-primary/50 transition-colors">
                  <CardHeader className="pb-2">
                    <div className="flex justify-between items-start">
                      <CardTitle className="text-lg font-bold">{machine.identifier}</CardTitle>
                      <Badge variant={statusVariant as "default" | "secondary" | "destructive" | "outline"}>{machine.status.replace("_", " ")}</Badge>
                    </div>
                    <p className="text-xs font-mono text-muted-foreground truncate" title={machine.machine_type_id}>
                      Type: {machine.machine_type_id}
                    </p>
                  </CardHeader>
                  <CardContent className="py-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Location:</span>
                      <span className="font-medium truncate max-w-30" title={derivedLocation}>{derivedLocation}</span>
                    </div>
                  </CardContent>
                  <CardFooter className="pt-2 pb-4 mt-auto">
                    {machine.status === 'AVAILABLE' && (
                       <Button 
                         variant="outline"
                         className="w-full text-xs"
                         onClick={() => handleStatusChange(machine.id, 'UNDER_MAINTENANCE')}
                         disabled={updatingId === machine.id}
                       >
                         {updatingId === machine.id ? 'Updating...' : 'Send to Maintenance'}
                       </Button>
                    )}
                    {machine.status === 'UNDER_MAINTENANCE' && (
                       <Button 
                         variant="default"
                         className="w-full text-xs"
                         onClick={() => handleStatusChange(machine.id, 'AVAILABLE')}
                         disabled={updatingId === machine.id}
                       >
                         {updatingId === machine.id ? 'Updating...' : 'Mark Available'}
                       </Button>
                    )}
                    {machine.status === 'IN_USE' && (
                      <Button variant="secondary" className="w-full text-xs" disabled>
                        Currently In Use
                      </Button>
                    )}
                  </CardFooter>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Active Requisitions</CardTitle>
          <Link href="/fleet/requisitions" className="text-xs font-semibold text-primary hover:underline">
            View All ({requisitions.length}) &rarr;
          </Link>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-muted/50">
              <TableRow>
                <TableHead>Requisition #</TableHead>
                <TableHead>Machine Type / Purpose</TableHead>
                <TableHead>Department</TableHead>
                <TableHead>Start Time</TableHead>
                <TableHead>End Time</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-muted-foreground h-24">Loading requisitions...</TableCell>
                </TableRow>
              ) : requisitions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-muted-foreground h-24">No active requisitions.</TableCell>
                </TableRow>
              ) : (
                requisitions.map((req) => (
                  <TableRow key={req.id}>
                    <TableCell className="font-mono text-xs font-semibold">
                      {req.requisition_number || req.id.substring(0, 8)}
                    </TableCell>
                    <TableCell>
                      <div className="text-sm font-medium text-foreground">
                        {req.machine_type?.name || "Heavy Equipment"}
                      </div>
                      {req.purpose && (
                        <div className="text-xs text-muted-foreground truncate max-w-xs" title={req.purpose}>
                          {req.purpose}
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {req.department?.name || req.department_id || "Mining Ops"}
                    </TableCell>
                    <TableCell className="text-xs">{new Date(req.start_time).toLocaleString()}</TableCell>
                    <TableCell className="text-xs">{new Date(req.end_time).toLocaleString()}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{req.status.replace("_", " ")}</Badge>
                    </TableCell>
                    <TableCell>
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
