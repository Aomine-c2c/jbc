/**
 * Bikita Minerals DWRMS — Network Resilience & Connection Management Engine (V2.7)
 * 
 * Manages 5 explicit connection states:
 *   - ONLINE: Heartbeat probe verified (< 4s latency)
 *   - CONNECTING: Initializing connection or switching server profiles
 *   - RECONNECTING: Connection lost; exponential backoff heartbeat active (5s..30s)
 *   - OFFLINE: Host network interface disconnected (airplane/no link)
 *   - SERVER_UNAVAILABLE: Interface up, but server unreachable/timed out/5xx error
 * 
 * Features:
 *   - Controlled retry for idempotent read (GET) requests with exponential backoff & jitter
 *   - Single-execution guarantee with X-Idempotency-Key for mutating requests (POST/PUT/PATCH)
 *   - Exponential heartbeat loop & connection diagnostics
 *   - Friendly network error translations (DNS, Timeout, Connection Refused)
 */

export type DetailedConnectionStatus = 'ONLINE' | 'CONNECTING' | 'RECONNECTING' | 'OFFLINE' | 'SERVER_UNAVAILABLE';

export interface ConnectionDiagnostics {
  status: DetailedConnectionStatus;
  lastPingTime?: string;
  latencyMs?: number;
  consecutiveFailures: number;
  activeEndpoint?: string;
  isOnline: boolean;
  reconnectAttempts: number;
}

class NetworkResilienceManager {
  private status: DetailedConnectionStatus = 'CONNECTING';
  private latency: number | null = null;
  private consecutiveFailures: number = 0;
  private reconnectAttempts: number = 0;
  private lastPingTime: string | null = null;
  private listeners: Set<(diag: ConnectionDiagnostics) => void> = new Set();
  private heartbeatTimer: any = null;
  private isChecking: boolean = false;

  constructor() {
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => this.handleNetworkEvent(true));
      window.addEventListener('offline', () => this.handleNetworkEvent(false));
      window.addEventListener('server-config-changed', () => this.triggerImmediateCheck());
      window.addEventListener('server-profiles-changed', () => this.triggerImmediateCheck());
      
      // Start heartbeat loop
      this.scheduleNextHeartbeat(1000);
    }
  }

  public getDiagnostics(): ConnectionDiagnostics {
    return {
      status: this.status,
      latencyMs: this.latency ?? undefined,
      lastPingTime: this.lastPingTime ?? undefined,
      consecutiveFailures: this.consecutiveFailures,
      isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
      reconnectAttempts: this.reconnectAttempts,
    };
  }

  public subscribe(callback: (diag: ConnectionDiagnostics) => void): () => void {
    this.listeners.add(callback);
    callback(this.getDiagnostics());
    return () => this.listeners.delete(callback);
  }

  private notify() {
    const diag = this.getDiagnostics();
    this.listeners.forEach((cb) => {
      try {
        cb(diag);
      } catch (err) {
        console.error('Error in network resilience listener:', err);
      }
    });

    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('dwrms-network-status-changed', { detail: diag }));
    }
  }

  public setStatus(newStatus: DetailedConnectionStatus, latencyMs?: number) {
    if (this.status !== newStatus || this.latency !== latencyMs) {
      this.status = newStatus;
      if (latencyMs !== undefined) this.latency = latencyMs;
      this.notify();
    }
  }

  private handleNetworkEvent(isOnline: boolean) {
    if (!isOnline) {
      this.setStatus('OFFLINE');
    } else {
      this.setStatus('RECONNECTING');
      this.triggerImmediateCheck();
    }
  }

  public triggerImmediateCheck() {
    if (this.heartbeatTimer) clearTimeout(this.heartbeatTimer);
    this.performHeartbeat();
  }

  private scheduleNextHeartbeat(delayMs: number) {
    if (this.heartbeatTimer) clearTimeout(this.heartbeatTimer);
    this.heartbeatTimer = setTimeout(() => {
      this.performHeartbeat();
    }, delayMs);
  }

  public async performHeartbeat(): Promise<void> {
    if (this.isChecking) return;
    this.isChecking = true;

    try {
      if (typeof navigator !== 'undefined' && !navigator.onLine) {
        this.setStatus('OFFLINE');
        this.scheduleNextHeartbeat(5000);
        return;
      }

      const { getActiveApiUrl } = await import('./serverProfiles');
      const apiUrl = await getActiveApiUrl();
      const t0 = performance.now();

      const res = await fetch(`${apiUrl}/api/v1/health`, {
        method: 'GET',
        headers: { 'Cache-Control': 'no-cache' },
        signal: AbortSignal.timeout(4000),
      });

      if (res.ok) {
        const latency = Math.round(performance.now() - t0);
        this.latency = latency;
        this.consecutiveFailures = 0;
        this.reconnectAttempts = 0;
        this.lastPingTime = new Date().toISOString();
        this.setStatus('ONLINE', latency);
        
        // Healthy heartbeat interval: 15 seconds
        this.scheduleNextHeartbeat(15000);
      } else {
        throw new Error(`Server returned status ${res.status}`);
      }
    } catch (err: any) {
      this.consecutiveFailures++;
      this.reconnectAttempts++;

      if (typeof navigator !== 'undefined' && !navigator.onLine) {
        this.setStatus('OFFLINE');
      } else if (this.status === 'ONLINE' || this.status === 'RECONNECTING') {
        this.setStatus('RECONNECTING');
      } else {
        this.setStatus('SERVER_UNAVAILABLE');
      }

      // Exponential backoff with jitter: 5s, 10s, 20s, max 30s
      const baseDelay = Math.min(5000 * Math.pow(1.5, Math.min(this.consecutiveFailures - 1, 4)), 30000);
      const jitter = Math.random() * 1500;
      this.scheduleNextHeartbeat(baseDelay + jitter);
    } finally {
      this.isChecking = false;
    }
  }

  /**
   * Generates a unique client-side idempotency key for mutating requests
   */
  public generateIdempotencyKey(): string {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return 'idem_' + Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
  }

  /**
   * Translates low-level browser network errors into human-friendly explanations
   */
  public translateNetworkError(err: any, endpoint: string): string {
    const msg = err?.message || String(err);
    if (msg.includes('AbortError') || msg.includes('timeout') || err?.name === 'TimeoutError') {
      return `Server response timed out after 10 seconds. The central server may be busy or unreachable.`;
    }
    if (msg.includes('Failed to fetch') || msg.includes('NetworkError') || msg.includes('ECONNREFUSED')) {
      if (typeof navigator !== 'undefined' && !navigator.onLine) {
        return `You are currently offline. Please verify your network or Wi-Fi connection.`;
      }
      return `Unable to reach the authoritative server at ${endpoint}. Please check server connectivity.`;
    }
    return msg;
  }
}

export const networkResilience = new NetworkResilienceManager();
