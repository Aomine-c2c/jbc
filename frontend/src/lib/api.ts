import { getActiveApiUrl, saveProfile, getActiveProfile, normalizeServerUrl } from './serverProfiles';
import { offlineStore } from './offlineStore';
import { networkResilience } from './networkResilience';

export async function getApiUrl(): Promise<string> {
  return await getActiveApiUrl();
}

export async function setApiUrl(url: string): Promise<void> {
  const cleanUrl = normalizeServerUrl(url);
  const active = await getActiveProfile();
  if (active) {
    await saveProfile({
      ...active,
      primaryUrl: cleanUrl,
      isVerified: true,
      lastConnectedAt: new Date().toISOString(),
    });
  } else {
    await saveProfile({
      id: 'custom-primary',
      name: 'Custom Server',
      primaryUrl: cleanUrl,
      connectionMode: 'domain',
      isVerified: true,
      isDefault: true,
    });
  }
}

export async function clearApiUrl(): Promise<void> {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('dwrms_active_profile_id');
    localStorage.removeItem('dwrms_api_url');
    window.dispatchEvent(new Event('server-config-changed'));
  }
}

export interface ApiRequestInit extends RequestInit {
  syncable?: boolean;
  idempotencyKey?: string;
  maxRetries?: number;
  retriedAfterRefresh?: boolean;
}

function getCsrfToken(): string | null {
  if (typeof window !== 'undefined') {
    const fromStorage = localStorage.getItem('csrf_token');
    if (fromStorage) return fromStorage;
  }
  if (typeof document === 'undefined') return null;
  const cookie = document.cookie.split('; ').find((entry) => entry.startsWith('dwrms_csrf_token='));
  return cookie ? decodeURIComponent(cookie.split('=', 2)[1]) : null;
}

export async function apiFetch(endpoint: string, options: ApiRequestInit = {}) {
  let token: string | null = null;
  if (typeof window !== 'undefined') {
    token = localStorage.getItem('session');
  }

  // Set up headers
  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const method = (options.method || 'GET').toUpperCase();
  const csrfToken = getCsrfToken();
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method) && csrfToken) {
    headers.set('X-CSRF-Token', csrfToken);
  }

  // Inject Idempotency Key on mutating operations to prevent duplicate creation
  if (['POST', 'PUT', 'PATCH'].includes(method)) {
    const key = options.idempotencyKey || networkResilience.generateIdempotencyKey();
    headers.set('X-Idempotency-Key', key);
  }

  // Construct URL via Active Profile
  const apiUrl = await getActiveApiUrl();
  const url = endpoint.startsWith('http') ? endpoint : `${apiUrl}${endpoint}`;

  // Controlled retry logic for idempotent GET requests only
  const maxRetries = method === 'GET' ? (options.maxRetries ?? 2) : 0;
  let attempt = 0;
  let res: Response | null = null;

  while (attempt <= maxRetries) {
    try {
      // 10s default timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);
      
      const fetchSignal = options.signal || controller.signal;

      res = await fetch(url, {
        ...options,
        headers,
        signal: fetchSignal,
        credentials: 'include',
      });

      clearTimeout(timeoutId);
      networkResilience.setStatus('ONLINE');
      break; // Success
    } catch (err: unknown) {
      attempt++;

      // If offline queueing is enabled and client is offline
      if (options.syncable && typeof window !== 'undefined' && !navigator.onLine) {
        const syncId = crypto.randomUUID();
        const plainHeaders: Record<string, string> = {};
        headers.forEach((val, key) => plainHeaders[key] = val);
        
        let bodyToStore: string | null = null;
        if (options.body) {
          if (typeof options.body === 'string') {
            bodyToStore = options.body;
          } else {
            bodyToStore = JSON.stringify(options.body);
          }
        }
        
        await offlineStore.addSyncRequest({
          id: syncId,
          url,
          method: options.method || 'POST',
          headers: plainHeaders,
          body: bodyToStore,
          created_at: new Date().toISOString(),
          status: 'PENDING'
        });
        
        return { _offline: true, syncId };
      }

      // If we have retries remaining for GET request, wait with backoff
      if (attempt <= maxRetries) {
        networkResilience.setStatus('RECONNECTING');
        await new Promise((resolve) => setTimeout(resolve, attempt * 1000));
        continue;
      }

      // Translate error to human-friendly message
      const friendlyError = networkResilience.translateNetworkError(err, url);
      networkResilience.setStatus(typeof navigator !== 'undefined' && !navigator.onLine ? 'OFFLINE' : 'SERVER_UNAVAILABLE');
      throw new Error(friendlyError);
    }
  }

  if (!res) {
    throw new Error(`Unable to complete network request to ${url}`);
  }

  if (res.status === 401) {
    // Renew the HttpOnly access cookie once before ending the session.
    if (typeof window !== 'undefined' && !options.retriedAfterRefresh) {
      const refreshResponse = await fetch(`${apiUrl}/api/v1/iam/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
        headers: csrfToken ? { 'X-CSRF-Token': csrfToken } : {},
        body: JSON.stringify({}),
      });
      if (refreshResponse.ok) {
        return apiFetch(endpoint, { ...options, retriedAfterRefresh: true });
      }
    }
    if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
      localStorage.removeItem('session');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_email');
      window.location.href = '/login';
      return;
    }
  }

  // Parse JSON response
  let data;
  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) {
    throw new Error(data?.detail || data?.error || res.statusText || "An API error occurred");
  }

  // Return data directly (or data.data if it's wrapped)
  return data?.data !== undefined ? data.data : data;
}

export const api = {
  get: async (endpoint: string, options: ApiRequestInit = {}) => {
    const data = await apiFetch(endpoint, { ...options, method: 'GET' });
    return { data };
  },
  post: async (endpoint: string, body?: unknown, options: ApiRequestInit = {}) => {
    const data = await apiFetch(endpoint, {
      ...options,
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    return { data };
  },
  put: async (endpoint: string, body?: unknown, options: ApiRequestInit = {}) => {
    const data = await apiFetch(endpoint, {
      ...options,
      method: 'PUT',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    return { data };
  },
  delete: async (endpoint: string, options: ApiRequestInit = {}) => {
    const data = await apiFetch(endpoint, { ...options, method: 'DELETE' });
    return { data };
  },
};

export const apiClient = api;
export default api;
