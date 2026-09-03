'use client';

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Protect } from "@/components/auth/Protect";
import { StatusBadge } from "@/components/ui/status-badge";
import { Button } from "@/components/ui/button";
import { RefreshCw, Calendar as CalendarIcon, Wrench, ArrowLeft, ArrowRight, Truck } from "lucide-react";

interface ScheduledSlot {
  requisition_id?: string;
  requisition_number?: string;
  purpose: string;
  department_name?: string;
  start_time: string;
  end_time: string;
  status: string;
  reservation_type: string;
}

interface MachineAvailabilityItem {
  machine_id: string;
  identifier: string;
  machine_type_id: string;
  machine_type_name: string;
  status: string;
  location?: string;
  capacity_rating?: string;
  is_available_for_window: boolean;
  scheduled_slots: ScheduledSlot[];
}

export default function FleetCalendarPage() {
  const [items, setItems] = useState<MachineAvailabilityItem[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    apiFetch("/api/v1/fleet/availability")
      .then((res) => {
        if (res) setItems(Array.isArray(res) ? res : []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <Protect capability="fleet_calendar:view" isPageGuard moduleName="Fleet Schedule & Availability Calendar">
      <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-5">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link 
              href="/fleet" 
              className="text-xs font-mono text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
            >
              <ArrowLeft className="size-3.5" /> Back to Fleet & Machines
            </Link>
          </div>
          <div className="flex items-center gap-2">
            <CalendarIcon className="size-5 text-primary" />
            <h1 className="text-xl font-bold text-foreground">Fleet Scheduling & Availability Calendar</h1>
          </div>
          <p className="text-xs text-muted-foreground font-mono mt-0.5">
            Real-time equipment allocation timeline and scheduled maintenance windows
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/fleet/requisitions/new">
            <Button size="sm">
              <Truck className="size-3.5 mr-1" /> New Requisition
            </Button>
          </Link>
          <Button variant="outline" size="sm" onClick={load} className="gap-1.5">
            <RefreshCw className="size-3.5" /> Refresh
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="p-8 text-center text-xs font-mono text-muted-foreground animate-pulse">
          Acquiring machine telemetry and reservation calendar...
        </div>
      ) : items.length === 0 ? (
        <div className="p-8 text-center text-xs font-mono text-muted-foreground border border-border rounded-lg bg-card">
          No fleet assets or availability windows registered.
        </div>
      ) : (
        <div className="space-y-4">
          {items.map((m) => (
            <div key={m.machine_id} className="border border-border rounded-lg p-4 bg-card shadow-xs">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3 pb-2 border-b border-border/50">
                <div className="flex items-center gap-3">
                  <h3 className="font-bold text-sm text-foreground flex items-center gap-2">
                    {m.identifier} 
                    <span className="text-[11px] font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded">
                      {m.machine_type_name}
                    </span>
                  </h3>
                  <StatusBadge status={m.status} size="sm" />
                </div>
                {m.location && (
                  <span className="text-[11px] font-mono text-muted-foreground">
                    Depot: {m.location}
                  </span>
                )}
              </div>

              {m.scheduled_slots.length === 0 ? (
                <p className="text-xs text-muted-foreground italic py-2">
                  No upcoming reservations or maintenance periods for this unit.
                </p>
              ) : (
                <div className="space-y-2 mt-2">
                  {m.scheduled_slots.map((slot, idx) => {
                    const isMaintenance = slot.reservation_type === "MAINTENANCE";
                    const slotCard = (
                      <div
                        className={`p-3 rounded-lg border text-xs transition-colors ${
                          isMaintenance
                            ? 'bg-destructive/10 border-destructive/20 text-destructive'
                            : 'bg-primary/5 border-primary/20 text-foreground hover:border-primary/50 cursor-pointer'
                        }`}
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div className="font-medium flex items-center gap-2">
                            {isMaintenance && <Wrench className="size-3.5" />}
                            <span className="font-semibold">{isMaintenance ? 'Maintenance Window' : (slot.purpose || 'Operations Deployment')}</span>
                            {slot.requisition_number && (
                              <span className="text-[10px] font-mono opacity-80">
                                ({slot.requisition_number})
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono text-muted-foreground bg-background/80 px-2 py-0.5 rounded border border-border/50">
                              {new Date(slot.start_time).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                              {' → '}
                              {new Date(slot.end_time).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                            </span>
                            {!isMaintenance && slot.requisition_id && (
                              <span className="text-primary text-[11px] font-bold flex items-center gap-0.5">
                                View <ArrowRight className="size-3" />
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    );

                    if (!isMaintenance && slot.requisition_id) {
                      return (
                        <Link key={idx} href={`/fleet/requisitions/${slot.requisition_id}`} className="block">
                          {slotCard}
                        </Link>
                      );
                    }
                    return <div key={idx}>{slotCard}</div>;
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      </div>
    </Protect>
  );
}
