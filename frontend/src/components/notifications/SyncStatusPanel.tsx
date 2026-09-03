'use client';

import React, { useEffect, useState } from 'react';
import { CloudOff, RefreshCw, AlertTriangle, Trash2 } from 'lucide-react';
import { offlineStore, SyncRequest } from '@/lib/offlineStore';
import { useConnection } from '@/lib/providers/ConnectionProvider';
import { useSyncManager } from '@/lib/SyncManager';

export function SyncStatusPanel() {
  const [requests, setRequests] = useState<SyncRequest[]>([]);
  const { isOnline } = useConnection();
  const { processSyncQueue } = useSyncManager();

  const loadRequests = async () => {
    const reqs = await offlineStore.getSyncRequests();
    setRequests(reqs);
  };

  useEffect(() => {
    loadRequests();
    // Refresh periodically if there are pending requests
    const interval = setInterval(loadRequests, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleDelete = async (id: string) => {
    await offlineStore.deleteSyncRequest(id);
    loadRequests();
  };

  const handleRetry = async () => {
    if (isOnline) {
      await processSyncQueue();
      loadRequests();
    }
  };

  if (requests.length === 0) return null;

  const pendingCount = requests.filter(r => r.status === 'PENDING').length;

  return (
    <div className="absolute right-0 top-14 w-80 bg-card border border-border shadow-lg rounded-b-lg p-4 z-50">
      <div className="flex items-center justify-between mb-3 border-b border-border pb-2">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          {isOnline ? <RefreshCw className="size-4 animate-spin text-emerald-500" /> : <CloudOff className="size-4 text-destructive" />}
          Offline Sync Queue
        </h3>
        {isOnline && pendingCount > 0 && (
          <button onClick={handleRetry} className="text-xs text-emerald-500 hover:underline">
            Sync Now
          </button>
        )}
      </div>

      <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
        {requests.map(req => (
          <div key={req.id} className="text-xs border border-border rounded p-2 bg-muted/30">
            <div className="flex justify-between items-start mb-1">
              <span className="font-mono text-[10px] text-muted-foreground uppercase">{req.method} {new URL(req.url).pathname}</span>
              <button onClick={() => handleDelete(req.id)} className="text-muted-foreground hover:text-destructive">
                <Trash2 className="size-3" />
              </button>
            </div>
            
            {req.status === 'PENDING' && (
              <div className="flex items-center gap-1 text-amber-500">
                <RefreshCw className="size-3" /> Pending Sync
              </div>
            )}
            {req.status === 'CONFLICTED' && (
              <div className="flex items-center gap-1 text-destructive">
                <AlertTriangle className="size-3" /> Conflict detected
              </div>
            )}
            {req.status === 'FAILED' && (
              <div className="flex items-center gap-1 text-destructive">
                <AlertTriangle className="size-3" /> {req.error || 'Sync Failed'}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
