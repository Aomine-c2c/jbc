'use client';

import React, { useEffect, useState, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import { StatusBadge } from "@/components/ui/status-badge";
import { Button } from "@/components/ui/button";
import { RefreshCw, Calendar as CalendarIcon, Wrench } from "lucide-react";

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
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-5">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2">
            <CalendarIcon className="w-5 h-5 text-primary" />
            <h1 className="text-xl font-semibold text-foreground">Fleet Scheduling Calendar</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            View resource availability and scheduled maintenance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={load} className="gap-1.5">
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="p-8 text-center text-muted-foreground">Loading calendar data...</div>
      ) : (
        <div className="space-y-4">
          {items.map((m) => (
            <div key={m.machine_id} className="border border-border rounded-md p-4 bg-card shadow-sm">
              <div className="flex justify-between items-center mb-3">
                <div>
                  <h3 className="font-semibold text-foreground flex items-center gap-2">
                    {m.identifier} 
                    <span className="text-xs font-normal text-muted-foreground bg-muted px-2 py-0.5 rounded">
                      {m.machine_type_name}
                    </span>
                  </h3>
                  <p className="text-xs text-muted-foreground mt-1">Status: <StatusBadge status={m.status} size="sm" /></p>
                </div>
              </div>

              {m.scheduled_slots.length === 0 ? (
                <p className="text-sm text-muted-foreground italic">No upcoming reservations or maintenance.</p>
              ) : (
                <div className="space-y-2 mt-3">
                  {m.scheduled_slots.map((slot, idx) => {
                    const isMaintenance = slot.reservation_type === "MAINTENANCE";
                    return (
                      <div key={idx} className={`p-3 rounded-md border text-sm ${isMaintenance ? 'bg-destructive/10 border-destructive/20 text-destructive' : 'bg-primary/10 border-primary/20 text-primary-foreground'}`}>
                        <div className="flex items-center justify-between">
                          <div className="font-medium flex items-center gap-2">
                            {isMaintenance && <Wrench className="w-3.5 h-3.5" />}
                            {isMaintenance ? 'Maintenance Period' : slot.purpose}
                            {slot.requisition_number && <span className="text-xs opacity-80">({slot.requisition_number})</span>}
                          </div>
                          <div className="text-xs opacity-80 bg-background/50 px-2 py-1 rounded text-foreground">
                            {new Date(slot.start_time).toLocaleString()} - {new Date(slot.end_time).toLocaleString()}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
