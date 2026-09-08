'use client';

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { apiFetch } from '@/lib/api';
import {
  Truck,
  CheckCircle2,
  AlertTriangle,
  Flame,
  ShieldAlert,
  Gauge,
  Droplets,
  Disc,
  Disc3,
  Sliders,
  AlertOctagon,
  RefreshCw,
  Clock,
  Info,
} from 'lucide-react';

export interface MachineOption {
  id: string;
  identifier: string;
  status: string;
  current_hour_meter?: number;
  location?: string;
  machine_type?: {
    name: string;
    category?: string;
  };
}

interface ChecklistItem {
  id: string;
  domain: string;
  title: string;
  description: string;
  isCritical: boolean;
  status: 'PASS' | 'MINOR_DEFECT' | 'CRITICAL_RED_TAG';
  notes?: string;
}

const DEFAULT_CHECKLIST: ChecklistItem[] = [
  // Domain 1: Fluids & Leaks
  {
    id: 'fluid_oil',
    domain: 'Fluids & Leaks',
    title: 'Engine Oil Level & Leaks',
    description: 'Dipstick verified between MIN/MAX. No active pooling under engine bay.',
    isCritical: false,
    status: 'PASS',
  },
  {
    id: 'fluid_hydraulic',
    domain: 'Fluids & Leaks',
    title: 'Hydraulic Tank Level & High-Pressure Hoses',
    description: 'Sight glass verified. Hoses checked for weeping, fraying, or bulges.',
    isCritical: false,
    status: 'PASS',
  },
  {
    id: 'fluid_coolant',
    domain: 'Fluids & Leaks',
    title: 'Radiator Coolant Level & Caps',
    description: 'Expansion tank level checked. Radiator core free of heavy mud/blockages.',
    isCritical: false,
    status: 'PASS',
  },

  // Domain 2: Brakes & Steering (Critical)
  {
    id: 'brake_service',
    domain: 'Brakes & Steering',
    title: 'Service Foot Brake Response',
    description: 'Pedal firmness verified; machine holds and stops cleanly under load test.',
    isCritical: true,
    status: 'PASS',
  },
  {
    id: 'brake_park',
    domain: 'Brakes & Steering',
    title: 'Park Brake / Emergency Retarder Holding',
    description: 'Park brake locks drive train on grade; retarder actuation verified.',
    isCritical: true,
    status: 'PASS',
  },
  {
    id: 'steering_response',
    domain: 'Brakes & Steering',
    title: 'Steering Articulation & Emergency Steering',
    description: 'Smooth full lock-to-lock travel without binding or hydraulic shudder.',
    isCritical: true,
    status: 'PASS',
  },

  // Domain 3: Tires, Tracks & Ground Engaging Tools
  {
    id: 'tires_tracks',
    domain: 'Tires & Ground Tools',
    title: 'Tire Pressures, Deep Cuts or Track Tension',
    description: 'No sidewall bulges, severe rock cuts, or missing track pin keepers.',
    isCritical: false,
    status: 'PASS',
  },
  {
    id: 'wheel_nuts',
    domain: 'Tires & Ground Tools',
    title: 'Wheel Nuts, Studs & Rim Flanges',
    description: 'All wheel nuts torqued in place; no rust streaks indicating loose studs.',
    isCritical: false,
    status: 'PASS',
  },
  {
    id: 'ground_tools',
    domain: 'Tires & Ground Tools',
    title: 'Bucket Teeth, Ripper Shank or Blade Edges',
    description: 'Lock pins intact; wear within operating tolerance without cracking.',
    isCritical: false,
    status: 'PASS',
  },

  // Domain 4: Cab, Controls & Alarms
  {
    id: 'alarm_reverse',
    domain: 'Cab & Controls',
    title: 'Reversing Siren & Flashing Strobe Light',
    description: 'Audio alarm audible at 15m; roof strobe light operating visibly.',
    isCritical: false,
    status: 'PASS',
  },
  {
    id: 'cab_seatbelt',
    domain: 'Cab & Controls',
    title: 'Operator Seatbelt & ROPS/FOPS Structure',
    description: 'Seatbelt latches and locks on tug; ROPS roll-cage free of weld cracks.',
    isCritical: true,
    status: 'PASS',
  },
  {
    id: 'cab_visibility',
    domain: 'Cab & Controls',
    title: 'Horn, Wipers, Washer & Convex Mirrors',
    description: 'Horn sounds clearly; wipers clear glass; mirrors aligned for blind spots.',
    isCritical: false,
    status: 'PASS',
  },

  // Domain 5: Fire Extinguisher & Emergency Stops (Critical)
  {
    id: 'fire_extinguisher',
    domain: 'Emergency & Fire Safety',
    title: 'Fire Extinguisher Charge & Inspection Tag',
    description: 'Pressure gauge in green; inspection tag current; pin seal unbroken.',
    isCritical: true,
    status: 'PASS',
  },
  {
    id: 'emergency_stops',
    domain: 'Emergency & Fire Safety',
    title: 'Cabin & External Ground E-Stop Buttons',
    description: 'E-stop mushrooms unhindered, accessible, and mechanically functional.',
    isCritical: true,
    status: 'PASS',
  },
];

interface OperatorPreStartModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (result: {
    referenceNumber: string;
    isGrounded: boolean;
    machineName: string;
    overallStatus: string;
  }) => void;
  initialMachineId?: string;
}

export function OperatorPreStartModal({
  isOpen,
  onClose,
  onSuccess,
  initialMachineId,
}: OperatorPreStartModalProps) {
  const [machines, setMachines] = useState<MachineOption[]>([]);
  const [loadingMachines, setLoadingMachines] = useState(false);
  const [selectedMachineId, setSelectedMachineId] = useState<string>(initialMachineId || '');
  const [hourMeterInput, setHourMeterInput] = useState<string>('');
  const [checklist, setChecklist] = useState<ChecklistItem[]>(DEFAULT_CHECKLIST);
  const [operatorNotes, setOperatorNotes] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load available fleet machines
  useEffect(() => {
    if (!isOpen) return;
    setLoadingMachines(true);
    setErrorMessage(null);
    setChecklist(DEFAULT_CHECKLIST);
    setOperatorNotes('');

    apiFetch<MachineOption[]>('/api/v1/fleet/machines')
      .then((data) => {
        if (Array.isArray(data)) {
          setMachines(data);
          if (initialMachineId) {
            setSelectedMachineId(initialMachineId);
            const m = data.find((x) => x.id === initialMachineId);
            if (m && m.current_hour_meter !== undefined) {
              setHourMeterInput(String(m.current_hour_meter));
            }
          } else if (data.length > 0) {
            setSelectedMachineId(data[0].id);
            if (data[0].current_hour_meter !== undefined) {
              setHourMeterInput(String(data[0].current_hour_meter));
            }
          }
        }
      })
      .catch((err) => {
        console.error('Failed to load fleet machines', err);
        setErrorMessage('Failed to retrieve fleet machine list. Please check your network connection.');
      })
      .finally(() => setLoadingMachines(false));
  }, [isOpen, initialMachineId]);

  // Sync hour meter input when machine changes
  const handleMachineChange = (id: string) => {
    setSelectedMachineId(id);
    const m = machines.find((x) => x.id === id);
    if (m && m.current_hour_meter !== undefined) {
      setHourMeterInput(String(m.current_hour_meter));
    }
  };

  // Toggle item status
  const setItemStatus = (id: string, status: 'PASS' | 'MINOR_DEFECT' | 'CRITICAL_RED_TAG') => {
    setChecklist((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status } : item))
    );
  };

  const selectedMachine = machines.find((m) => m.id === selectedMachineId);
  const hasCritical = checklist.some((i) => i.status === 'CRITICAL_RED_TAG');
  const hasMinor = checklist.some((i) => i.status === 'MINOR_DEFECT');

  const overallStatus = hasCritical
    ? 'CRITICAL_RED_TAG'
    : hasMinor
    ? 'DEFECTS_NOTED'
    : 'PASSED';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMachineId) {
      setErrorMessage('Please select an equipment unit.');
      return;
    }

    const hours = parseFloat(hourMeterInput);
    if (isNaN(hours) || hours < 0) {
      setErrorMessage('Please enter a valid non-negative hour-meter reading.');
      return;
    }

    const minHours = selectedMachine?.current_hour_meter || 0;
    if (hours < minHours) {
      setErrorMessage(
        `Hour-meter reading (${hours}) cannot be less than the last recorded meter (${minHours}).`
      );
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const payload = {
        machine_id: selectedMachineId,
        hour_meter_reading: hours,
        operator_notes: operatorNotes.trim() || undefined,
        checklist_results: checklist.map((i) => ({
          category: i.domain,
          item: i.title,
          status: i.status,
          notes: i.notes || undefined,
        })),
      };

      const res = await apiFetch<{
        reference_number: string;
        is_grounded: boolean;
        machine_name: string;
        overall_status: string;
      }>('/api/v1/work/pre-starts', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      onSuccess({
        referenceNumber: res.reference_number,
        isGrounded: res.is_grounded,
        machineName: res.machine_name,
        overallStatus: res.overall_status,
      });
      onClose();
    } catch (err: unknown) {
      console.error('Failed to submit pre-start inspection', err);
      const msg = err instanceof Error ? err.message : 'Submission failed. Please check inputs and retry.';
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Group items by domain
  const domains = Array.from(new Set(checklist.map((i) => i.domain)));

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-3xl max-h-[92vh] flex flex-col p-0 gap-0 overflow-hidden bg-background border-border">
        {/* HEADER */}
        <DialogHeader className="p-5 border-b border-border bg-card/60 shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-primary/10 text-primary">
                <Truck className="size-5" />
              </div>
              <div>
                <DialogTitle className="text-base font-bold flex items-center gap-2">
                  Machine Pre-Start Walkaround Inspection
                </DialogTitle>
                <DialogDescription className="text-xs text-muted-foreground mt-0.5">
                  Mandatory shift-start safety check. Critical defects immediately ground the unit.
                </DialogDescription>
              </div>
            </div>
            {overallStatus === 'CRITICAL_RED_TAG' ? (
              <Badge className="bg-rose-500/15 text-rose-500 border-rose-500/30 gap-1.5 px-2.5 py-1">
                <ShieldAlert className="size-3.5" />
                CRITICAL RED-TAG
              </Badge>
            ) : overallStatus === 'DEFECTS_NOTED' ? (
              <Badge className="bg-amber-500/15 text-amber-500 border-amber-500/30 gap-1.5 px-2.5 py-1">
                <AlertTriangle className="size-3.5" />
                DEFECTS NOTED
              </Badge>
            ) : (
              <Badge className="bg-emerald-500/15 text-emerald-500 border-emerald-500/30 gap-1.5 px-2.5 py-1">
                <CheckCircle2 className="size-3.5" />
                READY FOR SHIFT
              </Badge>
            )}
          </div>
        </DialogHeader>

        {/* SCROLLABLE BODY */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {errorMessage && (
            <div className="p-3.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs flex items-center gap-2.5">
              <AlertOctagon className="size-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* GATING WARNING BANNER */}
          {hasCritical && (
            <div className="p-4 rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-400 space-y-1">
              <div className="flex items-center gap-2 font-bold text-xs">
                <Flame className="size-4" />
                <span>SAFETY LOCKOUT: UNIT WILL BE TAKEN OUT OF SERVICE</span>
              </div>
              <p className="text-[11px] text-rose-300/90 leading-relaxed">
                One or more critical safety items failed. Upon submission, this machine will be marked <strong>OUT OF SERVICE</strong>, locking it from dispatch and generating an urgent maintenance repair order.
              </p>
            </div>
          )}

          {/* EQUIPMENT SELECTION & TELEMETRY */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-foreground flex items-center gap-1.5 mb-1.5">
                <Truck className="size-3.5 text-primary" />
                Select Assigned Machine
              </label>
              {loadingMachines ? (
                <div className="h-10 border border-border rounded-md px-3 flex items-center text-xs text-muted-foreground gap-2">
                  <RefreshCw className="size-3.5 animate-spin" />
                  Loading fleet machines...
                </div>
              ) : (
                <select
                  value={selectedMachineId}
                  onChange={(e) => handleMachineChange(e.target.value)}
                  className="w-full h-10 px-3 rounded-md bg-card border border-border text-xs text-foreground focus:outline-hidden focus:ring-1 focus:ring-primary"
                >
                  <option value="">-- Choose Machine --</option>
                  {machines.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.identifier} — {m.machine_type?.name || 'Heavy Equipment'} ({m.status})
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div>
              <label className="text-xs font-semibold text-foreground flex items-center justify-between mb-1.5">
                <span className="flex items-center gap-1.5">
                  <Gauge className="size-3.5 text-primary" />
                  Current Hour-Meter Reading
                </span>
                {selectedMachine?.current_hour_meter !== undefined && (
                  <span className="text-[11px] text-muted-foreground font-mono">
                    Last logged: {selectedMachine.current_hour_meter} hrs
                  </span>
                )}
              </label>
              <input
                type="number"
                step="0.1"
                min={selectedMachine?.current_hour_meter || 0}
                value={hourMeterInput}
                onChange={(e) => setHourMeterInput(e.target.value)}
                placeholder="e.g. 1250.5"
                className="w-full h-10 px-3 rounded-md bg-card border border-border text-xs font-mono text-foreground focus:outline-hidden focus:ring-1 focus:ring-primary"
                required
              />
            </div>
          </div>

          {/* 5-DOMAIN SAFETY CHECKLIST */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Walkaround Safety Checklist ({checklist.length} Points)
              </h3>
              <span className="text-[11px] text-muted-foreground">
                Touch buttons to flag defects
              </span>
            </div>

            {domains.map((domain) => {
              const itemsInDomain = checklist.filter((i) => i.domain === domain);
              return (
                <Card key={domain} className="bg-card border-border overflow-hidden">
                  <div className="px-4 py-2.5 bg-muted/40 border-b border-border flex items-center justify-between">
                    <span className="text-xs font-bold text-foreground flex items-center gap-2">
                      {domain === 'Fluids & Leaks' && <Droplets className="size-3.5 text-blue-400" />}
                      {domain === 'Brakes & Steering' && <Disc className="size-3.5 text-rose-400" />}
                      {domain === 'Tires & Ground Tools' && <Disc3 className="size-3.5 text-amber-400" />}
                      {domain === 'Cab & Controls' && <Sliders className="size-3.5 text-emerald-400" />}
                      {domain === 'Emergency & Fire Safety' && <Flame className="size-3.5 text-red-500" />}
                      {domain}
                    </span>
                    {domain.includes('Emergency') || domain.includes('Brakes') ? (
                      <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded-sm bg-rose-500/15 text-rose-400 border border-rose-500/20">
                        Critical Safety Gate
                      </span>
                    ) : null}
                  </div>
                  <CardContent className="p-0 divide-y divide-border">
                    {itemsInDomain.map((item) => (
                      <div key={item.id} className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-muted/20 transition-colors">
                        <div className="space-y-0.5 max-w-md">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-foreground">
                              {item.title}
                            </span>
                            {item.isCritical && (
                              <Badge variant="outline" className="text-[9px] px-1 py-0 text-rose-400 border-rose-500/30">
                                Grounding
                              </Badge>
                            )}
                          </div>
                          <p className="text-[11px] text-muted-foreground leading-snug">
                            {item.description}
                          </p>
                        </div>

                        {/* 3-STATE TOUCH BUTTONS */}
                        <div className="flex items-center gap-1.5 shrink-0">
                          <button
                            type="button"
                            onClick={() => setItemStatus(item.id, 'PASS')}
                            className={`px-2.5 py-1.5 rounded-md text-[11px] font-semibold transition-colors flex items-center gap-1 ${
                              item.status === 'PASS'
                                ? 'bg-emerald-500 text-white shadow-xs'
                                : 'bg-muted text-muted-foreground hover:bg-muted/80'
                            }`}
                          >
                            <CheckCircle2 className="size-3" />
                            Pass
                          </button>
                          <button
                            type="button"
                            onClick={() => setItemStatus(item.id, 'MINOR_DEFECT')}
                            className={`px-2.5 py-1.5 rounded-md text-[11px] font-semibold transition-colors flex items-center gap-1 ${
                              item.status === 'MINOR_DEFECT'
                                ? 'bg-amber-500 text-white shadow-xs'
                                : 'bg-muted text-muted-foreground hover:bg-muted/80'
                            }`}
                          >
                            <AlertTriangle className="size-3" />
                            Minor
                          </button>
                          <button
                            type="button"
                            onClick={() => setItemStatus(item.id, 'CRITICAL_RED_TAG')}
                            className={`px-2.5 py-1.5 rounded-md text-[11px] font-semibold transition-colors flex items-center gap-1 ${
                              item.status === 'CRITICAL_RED_TAG'
                                ? 'bg-rose-600 text-white shadow-xs animate-pulse'
                                : 'bg-muted text-muted-foreground hover:bg-rose-500/20 hover:text-rose-400'
                            }`}
                          >
                            <Flame className="size-3" />
                            Red-Tag
                          </button>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* OPERATOR DEFECT NOTES */}
          <div>
            <label className="text-xs font-semibold text-foreground flex items-center gap-1.5 mb-1.5">
              <Info className="size-3.5 text-primary" />
              Operator Defect Description & Field Observations
            </label>
            <textarea
              rows={3}
              value={operatorNotes}
              onChange={(e) => setOperatorNotes(e.target.value)}
              placeholder="Describe any flagged leaks, brake stiffness, tire cracks, or odd noises observed during test..."
              className="w-full p-3 rounded-md bg-card border border-border text-xs text-foreground focus:outline-hidden focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>

        {/* FOOTER */}
        <DialogFooter className="p-4 border-t border-border bg-card/60 shrink-0 flex items-center justify-between sm:justify-between">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="size-3.5" />
            <span>Shift Alpha • Bikita Open Pit</span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleSubmit}
              disabled={isSubmitting || !selectedMachineId}
              className={`gap-1.5 ${
                hasCritical
                  ? 'bg-rose-600 hover:bg-rose-700 text-white'
                  : 'bg-primary hover:bg-primary/90 text-primary-foreground'
              }`}
            >
              {isSubmitting ? (
                <>
                  <RefreshCw className="size-3.5 animate-spin" />
                  Recording...
                </>
              ) : hasCritical ? (
                <>
                  <Flame className="size-3.5" />
                  Submit Red-Tag & Ground Unit
                </>
              ) : (
                <>
                  <CheckCircle2 className="size-3.5" />
                  Submit Pre-Start Certification
                </>
              )}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
