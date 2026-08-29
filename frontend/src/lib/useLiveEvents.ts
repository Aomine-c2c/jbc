'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { getApiUrl } from './api';

export interface LiveEventMessage {
  id: string;
  type: string;
  payload: Record<string, unknown>;
  timestamp: string;
  department_id?: string | null;
  user_id?: string | null;
  channel?: string;
}

export function useLiveEvents() {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<LiveEventMessage | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(async () => {
    if (typeof window === 'undefined') return;

    try {
      const baseUrl = await getApiUrl();
      const sseUrl = `${baseUrl}/api/v1/events/stream`;

      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      const es = new EventSource(sseUrl, { withCredentials: true });
      eventSourceRef.current = es;

      es.onopen = () => {
        setIsConnected(true);
      };

      es.onerror = () => {
        setIsConnected(false);
        es.close();
        // Exponential reconnect retry after 5s
        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 5000);
      };

      // Listen to generic messages and custom event types
      const handleIncomingEvent = (e: MessageEvent) => {
        try {
          const parsed: LiveEventMessage = JSON.parse(e.data);
          setLastEvent(parsed);

          // Dispatch standard window event for decoupled React hooks and components
          window.dispatchEvent(new CustomEvent('dwrms-live-event', { detail: parsed }));
          window.dispatchEvent(new CustomEvent(`dwrms:${parsed.type}`, { detail: parsed }));
        } catch {
          // heartbeat or unparseable event ignored
        }
      };

      es.onmessage = handleIncomingEvent;
      es.addEventListener('connection.ready', handleIncomingEvent as EventListener);
      es.addEventListener('job_card.create', handleIncomingEvent as EventListener);
      es.addEventListener('job_card.submit', handleIncomingEvent as EventListener);
      es.addEventListener('job_card.assign', handleIncomingEvent as EventListener);
      es.addEventListener('job_card.start', handleIncomingEvent as EventListener);
      es.addEventListener('job_card.hold', handleIncomingEvent as EventListener);
      es.addEventListener('job_card.complete', handleIncomingEvent as EventListener);
      es.addEventListener('job_card.verify', handleIncomingEvent as EventListener);
      es.addEventListener('job_card.close', handleIncomingEvent as EventListener);
      es.addEventListener('job_card.cancel', handleIncomingEvent as EventListener);
      es.addEventListener('approval.requested', handleIncomingEvent as EventListener);
      es.addEventListener('approval.decided', handleIncomingEvent as EventListener);
      es.addEventListener('sla.escalated', handleIncomingEvent as EventListener);
    } catch (err) {
      console.warn('[SSE] Connection error:', err);
      setIsConnected(false);
    }
  }, []);

  useEffect(() => {
    connect();

    const handleAuthChange = () => connect();
    window.addEventListener('storage', handleAuthChange);
    window.addEventListener('server-config-changed', handleAuthChange);

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      window.removeEventListener('storage', handleAuthChange);
      window.removeEventListener('server-config-changed', handleAuthChange);
    };
  }, [connect]);

  return { isConnected, lastEvent };
}
