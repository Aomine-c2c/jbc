'use client';

import { useEffect, useCallback } from 'react';
import { offlineStore } from './offlineStore';
import { useConnection } from './providers/ConnectionProvider';

export function useSyncManager() {
  const { isOnline } = useConnection();

  const processSyncQueue = useCallback(async () => {
    if (!isOnline) return;

    try {
      const requests = await offlineStore.getSyncRequests();
      const pending = requests.filter(r => r.status === 'PENDING');

      for (const req of pending) {
        try {
          const res = await fetch(req.url, {
            method: req.method,
            headers: {
              ...req.headers,
              'X-Draft-Timestamp': req.created_at,
              'X-Sync-ID': req.id,
            },
            body: req.body ? JSON.stringify(req.body) : null,
          });

          if (res.ok) {
            // Success, remove from queue
            await offlineStore.deleteSyncRequest(req.id);
          } else if (res.status === 412 || res.status === 409) {
            // Conflict
            await offlineStore.updateSyncRequest({
              ...req,
              status: 'CONFLICTED',
              error: 'Conflict: Server has a newer version of this record.',
            });
          } else if (res.status >= 400 && res.status < 500) {
            // Bad request or unauthorized, mark as failed permanently
            await offlineStore.updateSyncRequest({
              ...req,
              status: 'FAILED',
              error: `Client error: ${res.statusText}`,
            });
          }
          // If 5xx, leave as PENDING for retry later
        } catch {
          // Network error during sync, will retry later
          break;
        }
      }
    } catch (error) {
      console.error('Error processing sync queue:', error);
    }
  }, [isOnline]);

  useEffect(() => {
    // Process queue when coming back online
    if (isOnline) {
      processSyncQueue();
    }
  }, [isOnline, processSyncQueue]);

  return { processSyncQueue };
}
