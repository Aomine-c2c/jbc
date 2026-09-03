'use client';

import React, { useEffect, useState } from 'react';
import { WifiOff, RefreshCw, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { networkResilience, ConnectionDiagnostics } from '@/lib/networkResilience';

export function NetworkStatusBar() {
  const [diagnostics, setDiagnostics] = useState<ConnectionDiagnostics>({
    status: 'ONLINE',
    consecutiveFailures: 0,
    isOnline: true,
    reconnectAttempts: 0,
  });

  useEffect(() => {
    const unsubscribe = networkResilience.subscribe((diag) => {
      setDiagnostics(diag);
    });
    return unsubscribe;
  }, []);

  const handleReconnect = () => {
    networkResilience.triggerImmediateCheck();
  };

  // Only display when connectivity is impaired
  if (diagnostics.status === 'ONLINE' || diagnostics.status === 'CONNECTING') {
    return null;
  }

  return (
    <div
      role="status"
      aria-live="polite"
      className={`w-full py-1.5 px-4 text-xs font-mono flex items-center justify-between transition-all z-40 ${
        diagnostics.status === 'RECONNECTING'
          ? 'bg-amber-950/90 text-amber-300 border-b border-amber-500/40'
          : diagnostics.status === 'OFFLINE'
          ? 'bg-slate-900/90 text-slate-300 border-b border-slate-700'
          : 'bg-red-950/90 text-red-300 border-b border-red-500/40'
      }`}
    >
      <div className="flex items-center gap-2">
        {diagnostics.status === 'RECONNECTING' && (
          <>
            <RefreshCw className="size-3.5 animate-spin text-amber-400" />
            <span>
              Reconnecting to central server... (Attempt {diagnostics.reconnectAttempts}) • Unsaved drafts preserved locally.
            </span>
          </>
        )}

        {diagnostics.status === 'OFFLINE' && (
          <>
            <WifiOff className="size-3.5 text-slate-400" />
            <span>
              Network offline. Form drafts are safely preserved in browser storage.
            </span>
          </>
        )}

        {diagnostics.status === 'SERVER_UNAVAILABLE' && (
          <>
            <AlertTriangle className="size-3.5 text-red-400" />
            <span>
              Authoritative server is temporarily unreachable. Auto-retrying with exponential backoff...
            </span>
          </>
        )}
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleReconnect}
          className="h-6 px-2 text-[11px] font-mono bg-slate-950/60 border-current hover:bg-slate-900"
        >
          <RefreshCw className="size-3 mr-1" />
          Reconnect Now
        </Button>
      </div>
    </div>
  );
}
