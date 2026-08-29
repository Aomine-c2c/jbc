'use client';

import React, { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import {
  ServerProfile,
  getActiveProfile,
} from '@/lib/serverProfiles';
import { networkResilience, ConnectionDiagnostics } from '@/lib/networkResilience';
import { ServerProfileManagerDialog } from '@/components/config/ServerProfileManagerDialog';

export function ConnectionStatusBadge() {
  const [diagnostics, setDiagnostics] = useState<ConnectionDiagnostics>({
    status: 'CONNECTING',
    consecutiveFailures: 0,
    isOnline: true,
    reconnectAttempts: 0,
  });
  const [activeProfile, setActiveProfile] = useState<ServerProfile | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    getActiveProfile().then(setActiveProfile);

    const unsubscribe = networkResilience.subscribe((diag) => {
      setDiagnostics(diag);
    });

    const handleProfileChange = () => {
      getActiveProfile().then(setActiveProfile);
    };

    window.addEventListener('server-config-changed', handleProfileChange);
    window.addEventListener('server-profiles-changed', handleProfileChange);

    return () => {
      unsubscribe();
      window.removeEventListener('server-config-changed', handleProfileChange);
      window.removeEventListener('server-profiles-changed', handleProfileChange);
    };
  }, []);

  const { status, latencyMs, reconnectAttempts } = diagnostics;

  return (
    <>
      <button
        type="button"
        onClick={() => setDialogOpen(true)}
        className="flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-medium transition-all hover:ring-2 hover:ring-slate-700 bg-slate-900 border border-slate-800"
        title="Click to manage server connection profiles and network diagnostics"
      >
        {/* Status Dot */}
        {status === 'ONLINE' && (
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
        )}
        {status === 'CONNECTING' && (
          <span className="relative flex h-2 w-2">
            <span className="animate-pulse relative inline-flex rounded-full h-2 w-2 bg-blue-400"></span>
          </span>
        )}
        {status === 'RECONNECTING' && (
          <span className="relative flex h-2 w-2">
            <span className="animate-pulse relative inline-flex rounded-full h-2 w-2 bg-amber-400"></span>
          </span>
        )}
        {status === 'OFFLINE' && (
          <span className="relative inline-flex rounded-full h-2 w-2 bg-slate-500"></span>
        )}
        {status === 'SERVER_UNAVAILABLE' && (
          <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
        )}

        {/* Profile Name & Label */}
        <span className="text-slate-300 font-semibold max-w-[130px] truncate">
          {activeProfile?.name || 'Central Server'}
        </span>

        {/* Status Badge */}
        {status === 'ONLINE' && (
          <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-emerald-500/40 text-emerald-400 bg-emerald-500/10">
            ONLINE {latencyMs ? `(${latencyMs}ms)` : ''}
          </Badge>
        )}
        {status === 'CONNECTING' && (
          <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-blue-500/40 text-blue-400 bg-blue-500/10">
            CONNECTING
          </Badge>
        )}
        {status === 'RECONNECTING' && (
          <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-amber-500/40 text-amber-400 bg-amber-500/10 flex items-center gap-1">
            <RefreshCw className="size-2.5 animate-spin" />
            RECONNECTING {reconnectAttempts > 0 ? `(${reconnectAttempts})` : ''}
          </Badge>
        )}
        {status === 'OFFLINE' && (
          <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-slate-700 text-slate-400">
            OFFLINE
          </Badge>
        )}
        {status === 'SERVER_UNAVAILABLE' && (
          <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-red-500/40 text-red-400 bg-red-500/10">
            UNAVAILABLE
          </Badge>
        )}
      </button>

      <ServerProfileManagerDialog
        isOpen={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onConfigured={() => networkResilience.triggerImmediateCheck()}
      />
    </>
  );
}
