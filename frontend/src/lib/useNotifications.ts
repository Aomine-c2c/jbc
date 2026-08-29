import { useState, useEffect, useCallback } from 'react';
import { apiFetch, getApiUrl } from './api';

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  title: string;
  message: string;
  resource_type: string;
  resource_id: string;
  priority: number;
  is_read: boolean;
  created_at: string;
}

export interface NotificationListResponse {
  total_unread: number;
  items: Notification[];
}

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchInitial = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiFetch('/api/v1/notifications', { method: 'GET' }) as NotificationListResponse;
      setNotifications(data.items);
      setUnreadCount(data.total_unread);
    } catch (err) {
      console.error('Error fetching notifications:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInitial();

    let ws: WebSocket;
    let reconnectTimer: NodeJS.Timeout;

    const connect = async () => {
      const apiUrl = await getApiUrl();
      const wsUrl = apiUrl.replace(/^http/, 'ws') + '/api/v1/notifications/ws';
      ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        try {
          if (event.data === 'PONG') return;
          const data = JSON.parse(event.data);
          if (data.type === 'NEW_NOTIFICATION') {
            const newNotif = data.payload as Notification;
            setNotifications(prev => [newNotif, ...prev]);
            setUnreadCount(prev => prev + 1);
          }
        } catch (err) {
          console.error('Failed to parse WS message:', err);
        }
      };

      ws.onclose = () => {
        // Attempt to reconnect after 5s
        reconnectTimer = setTimeout(connect, 5000);
      };
    };

    connect();

    const handleLiveEvent = () => {
      fetchInitial();
    };
    window.addEventListener('dwrms-live-event', handleLiveEvent);

    return () => {
      clearTimeout(reconnectTimer);
      if (ws) ws.close();
      window.removeEventListener('dwrms-live-event', handleLiveEvent);
    };
  }, [fetchInitial]);

  const markAsRead = async (id: string) => {
    try {
      await apiFetch(`/api/v1/notifications/${id}/read`, { method: 'PUT' });
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
    }
  };

  const markAllAsRead = async () => {
    try {
      await apiFetch(`/api/v1/notifications/read-all`, { method: 'PUT' });
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all as read:', err);
    }
  };

  return {
    notifications,
    unreadCount,
    loading,
    markAsRead,
    markAllAsRead,
    refresh: fetchInitial
  };
}
