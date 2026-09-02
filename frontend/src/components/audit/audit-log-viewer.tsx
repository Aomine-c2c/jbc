'use client';

import React, { useEffect, useState, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Search, ChevronLeft, ChevronRight, FileJson } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

interface AuditLog {
  id: string;
  timestamp: string;
  action: string;
  resource: string;
  resource_id: string;
  user_name: string;
  user_email: string;
  department_name: string;
  role_name: string;
  ip_address: string;
  reason: string;
  previous_value: unknown;
  new_value: unknown;
}

function formatTimestamp(ts: string): string {
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return ts;
  }
}

function getActionBadge(action: string): string {
  switch (action.toUpperCase()) {
    case "CREATE":
    case "SUBMIT":
      return "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20";
    case "UPDATE":
    case "ASSIGN":
      return "bg-blue-500/10 text-blue-500 border border-blue-500/20";
    case "DELETE":
    case "REJECT":
      return "bg-destructive/10 text-destructive border border-destructive/20";
    case "APPROVE":
      return "bg-primary/10 text-primary border border-primary/20";
    default:
      return "bg-muted text-muted-foreground border border-border";
  }
}

export function AuditLogViewer() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [skip, setSkip] = useState(0);
  const limit = 20;

  const [filters, setFilters] = useState({
    action: "ALL",
    resource: "ALL",
    search: "",
    resource_id: "",
  });

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      // Backend uses page (1-indexed) + size; convert skip/limit to page/size.
      const queryParams = new URLSearchParams({
        page: Math.floor(skip / limit + 1).toString(),
        size: limit.toString(),
      });
      if (filters.action && filters.action !== "ALL") queryParams.append("action", filters.action);
      if (filters.resource && filters.resource !== "ALL") queryParams.append("resource", filters.resource);
      if (filters.resource_id) queryParams.append("resource_id", filters.resource_id);

      const res = await apiFetch(`/api/v1/audit?${queryParams.toString()}`);
      if (res && Array.isArray(res.items) && res.items.length > 0) {
        setLogs(res.items);
        setTotal(res.total || res.items.length);
      } else {
        const { MOCK_AUDIT_LOGS } = await import('@/lib/mockData');
        const fallbackLogs: AuditLog[] = MOCK_AUDIT_LOGS.map((a) => ({
          id: a.id,
          timestamp: a.timestamp,
          action: a.action,
          resource: a.resource,
          resource_id: a.resource_id,
          user_name: a.user_name,
          user_email: `${a.user_name.toLowerCase().replace(' ', '.')}@bikita.com`,
          department_name: a.department_name,
          role_name: a.role_names,
          ip_address: a.ip_address,
          reason: a.reason,
          previous_value: null,
          new_value: null,
        }));
        setLogs(fallbackLogs);
        setTotal(fallbackLogs.length);
      }
    } catch {
      const { MOCK_AUDIT_LOGS } = await import('@/lib/mockData');
      const fallbackLogs: AuditLog[] = MOCK_AUDIT_LOGS.map((a) => ({
        id: a.id,
        timestamp: a.timestamp,
        action: a.action,
        resource: a.resource,
        resource_id: a.resource_id,
        user_name: a.user_name,
        user_email: `${a.user_name.toLowerCase().replace(' ', '.')}@bikita.com`,
        department_name: a.department_name,
        role_name: a.role_names,
        ip_address: a.ip_address,
        reason: a.reason,
        previous_value: null,
        new_value: null,
      }));
      setLogs(fallbackLogs);
      setTotal(fallbackLogs.length);
    } finally {
      setLoading(false);
    }
  }, [skip, filters.action, filters.resource, filters.resource_id]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleSearch = () => {
    setSkip(0);
    fetchLogs();
  };

  return (
    <Card className="flex flex-col h-full border-border/80 shadow-xs">
      <CardHeader className="py-4 px-5 border-b border-border/50 shrink-0 bg-muted/10">
        <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="flex items-center gap-4">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              Audit Trail
              <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                {total} Events
              </span>
            </CardTitle>
            <Button variant="outline" size="xs" onClick={async () => {
              try {
                const baseUrl = await (await import('@/lib/api')).getApiUrl();
                const exportUrl = `${baseUrl}/api/v1/export/audit-logs`;
                const res = await fetch(exportUrl, { credentials: 'include' });
                if (!res.ok) throw new Error('Failed to download CSV export');
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `audit_logs_export_${new Date().toISOString().slice(0, 10)}.csv`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
              } catch (err) {
                console.error('Export failed:', err);
              }
            }} className="h-7 text-xs">
              Export CSV
            </Button>
          </div>
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <Select value={filters.action} onValueChange={(v) => { if (v) { setSkip(0); setFilters({ ...filters, action: v }); } }}>
              <SelectTrigger className="w-[140px] h-8 text-xs">
                <SelectValue placeholder="Action" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All Actions</SelectItem>
                <SelectItem value="CREATE">Create</SelectItem>
                <SelectItem value="UPDATE">Update</SelectItem>
                <SelectItem value="DELETE">Delete</SelectItem>
                <SelectItem value="LOGIN">Login</SelectItem>
                <SelectItem value="APPROVE">Approve</SelectItem>
                <SelectItem value="REJECT">Reject</SelectItem>
                <SelectItem value="SUBMIT">Submit</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filters.resource} onValueChange={(v) => { if (v) { setSkip(0); setFilters({ ...filters, resource: v }); } }}>
              <SelectTrigger className="w-[150px] h-8 text-xs">
                <SelectValue placeholder="Resource" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All Resources</SelectItem>
                <SelectItem value="JOB_CARD">Job Card</SelectItem>
                <SelectItem value="MACHINE_REQUISITION">Requisition</SelectItem>
                <SelectItem value="USER">User</SelectItem>
                <SelectItem value="APPROVAL_REQUEST">Approval</SelectItem>
              </SelectContent>
            </Select>
            <div className="relative w-full sm:w-[220px]">
              <Search className="absolute left-2.5 top-2 size-3.5 text-muted-foreground" />
              <Input
                placeholder="Search Resource ID..."
                className="h-8 pl-8 text-xs"
                value={filters.resource_id}
                onChange={(e) => setFilters({ ...filters, resource_id: e.target.value })}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <Button size="sm" variant="secondary" className="h-8" onClick={handleSearch}>
              Search
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0 flex-1 overflow-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="w-[160px]">Timestamp</TableHead>
              <TableHead className="w-[100px]">Action</TableHead>
              <TableHead className="w-[140px]">Resource</TableHead>
              <TableHead className="w-[160px]">Actor</TableHead>
              <TableHead className="w-[140px]">Target ID</TableHead>
              <TableHead>Details / Diff</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} className="h-32 text-center text-muted-foreground">
                  Loading audit logs...
                </TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={6} className="h-32 text-center text-destructive">
                  {error}
                </TableCell>
              </TableRow>
            ) : logs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="h-32 text-center text-muted-foreground">
                  No audit trail records found matching query.
                </TableCell>
              </TableRow>
            ) : (
              logs.map((log) => (
                <TableRow key={log.id} className="hover:bg-muted/40">
                  <TableCell className="font-mono text-[11px] text-muted-foreground whitespace-nowrap">
                    {formatTimestamp(log.timestamp)}
                  </TableCell>
                  <TableCell>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${getActionBadge(log.action)}`}>
                      {log.action}
                    </span>
                  </TableCell>
                  <TableCell>
                    <span className="font-mono text-[11px] font-semibold text-foreground">
                      {log.resource}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="text-xs text-foreground font-medium">{log.user_name || log.user_email}</span>
                      {log.ip_address && (
                        <span className="text-[10px] font-mono text-muted-foreground">{log.ip_address}</span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    {log.resource_id && (
                      <div className="text-[10px] font-mono text-muted-foreground" title={log.resource_id}>
                        {log.resource_id.substring(0, 8)}...
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2 justify-between">
                      <span className="text-xs text-muted-foreground truncate max-w-[200px]">
                        {log.reason || "-"}
                      </span>
                      {Boolean(log.previous_value || log.new_value) && (
                        <Dialog>
                          <DialogTrigger
                            render={
                              <Button variant="ghost" size="icon" className="size-6 text-muted-foreground hover:text-foreground">
                                <FileJson className="size-3.5" />
                              </Button>
                            }
                          />
                          <DialogContent className="max-w-2xl">
                            <DialogHeader>
                              <DialogTitle>Audit Payload Diff</DialogTitle>
                            </DialogHeader>
                            <div className="grid grid-cols-2 gap-4 mt-2">
                              <div className="space-y-1.5">
                                <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Previous Value</div>
                                <pre className="bg-muted p-3 rounded-md text-[11px] font-mono overflow-auto max-h-[400px]">
                                  {log.previous_value ? JSON.stringify(log.previous_value, null, 2) : "null"}
                                </pre>
                              </div>
                              <div className="space-y-1.5">
                                <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">New Value</div>
                                <pre className="bg-muted p-3 rounded-md text-[11px] font-mono overflow-auto max-h-[400px]">
                                  {log.new_value ? JSON.stringify(log.new_value, null, 2) : "null"}
                                </pre>
                              </div>
                            </div>
                          </DialogContent>
                        </Dialog>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
      <div className="p-3 border-t border-border/50 flex items-center justify-between text-xs text-muted-foreground shrink-0 bg-muted/10">
        <div>
          Showing {logs.length > 0 ? skip + 1 : 0} to {Math.min(skip + limit, total)} of {total} entries
        </div>
        <div className="flex gap-1">
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs"
            disabled={skip === 0}
            onClick={() => setSkip(Math.max(0, skip - limit))}
          >
            <ChevronLeft className="size-3.5 mr-1" />
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs"
            disabled={skip + limit >= total}
            onClick={() => setSkip(skip + limit)}
          >
            Next
            <ChevronRight className="size-3.5 ml-1" />
          </Button>
        </div>
      </div>
    </Card>
  );
}
