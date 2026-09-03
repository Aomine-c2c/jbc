'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { getApiUrl } from '@/lib/api';

export type ConnectionStatus = 'ONLINE' | 'CONNECTING' | 'OFFLINE' | 'SERVER_UNAVAILABLE';

interface ConnectionContextType {
  status: ConnectionStatus;
  isOnline: boolean;
  pingServer: () => Promise<void>;
}

const ConnectionContext = createContext<ConnectionContextType | undefined>(undefined);

export function ConnectionProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<ConnectionStatus>('CONNECTING');
  
  const isOnline = status === 'ONLINE';

  const pingServer = useCallback(async () => {
    if (typeof window !== 'undefined' && !navigator.onLine) {
      setStatus('OFFLINE');
      return;
    }

    try {
      const apiUrl = await getApiUrl();
      // Use a lightweight health check endpoint or just an OPTIONS ping
      const res = await fetch(`${apiUrl}/api/v1/health`, {
        method: 'GET',
        headers: { 'Cache-Control': 'no-cache' },
        signal: AbortSignal.timeout(3000)
      });
      if (res.ok) {
        setStatus('ONLINE');
      } else {
        setStatus('SERVER_UNAVAILABLE');
      }
    } catch {
      setStatus('SERVER_UNAVAILABLE');
    }
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Initial check
    pingServer();

    // Listen to native browser and custom config events
    const handleOnline = () => pingServer();
    const handleOffline = () => setStatus('OFFLINE');
    const handleConfigChanged = () => {
      setStatus('CONNECTING');
      pingServer();
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    window.addEventListener('server-config-changed', handleConfigChanged);

    // Periodic ping to catch server drops without losing browser network
    const interval = setInterval(pingServer, 15000);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('server-config-changed', handleConfigChanged);
      clearInterval(interval);
    };
  }, [pingServer]);

  return (
    <ConnectionContext.Provider value={{ status, isOnline, pingServer }}>
      {children}
    </ConnectionContext.Provider>
  );
}

export function useConnection() {
  const context = useContext(ConnectionContext);
  if (context === undefined) {
    throw new Error('useConnection must be used within a ConnectionProvider');
  }
  return context;
}
