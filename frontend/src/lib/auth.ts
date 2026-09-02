import { getApiUrl } from './api';
import { resolveUserRole, getDefaultLandingRoute } from './rbac';

export async function login(email: string, password: string) {
  try {
    const apiUrl = await getApiUrl();
    const response = await fetch(`${apiUrl}/api/v1/iam/auth/login`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: email,
        password: password,
      }),
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      return { error: data?.detail || data?.error || 'Invalid credentials or account locked.' };
    }

    if (typeof window !== 'undefined') {
      if (data?.access_token) {
        localStorage.setItem('session', data.access_token);
      }
      if (data?.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
      }
      if (data?.csrf_token) {
        localStorage.setItem('csrf_token', data.csrf_token);
      }
      const role = resolveUserRole(email);
      localStorage.setItem('user_email', email);
      localStorage.setItem('user_role', role);

      const targetRoute = getDefaultLandingRoute(role);
      window.location.href = targetRoute;
    }
  } catch (e: unknown) {
    const err = e as { message?: string };
    return { error: err.message || 'Unable to connect to authentication server.' };
  }
}

export function logout() {
  if (typeof window !== 'undefined') {
    const csrfToken = getCsrfToken();
    const url = '/api/v1/iam/auth/logout';
    const body = new URLSearchParams();
    if (csrfToken) {
      // sendBeacon only supports blob/form/arraybuffer; use a small form payload
      body.set('csrf_token', csrfToken);
    }
    const blob = new Blob([body.toString()], { type: 'application/x-www-form-urlencoded' });
    if (navigator.sendBeacon) {
      navigator.sendBeacon(url, blob);
    } else {
      // Fallback for browsers without sendBeacon
      fetch(url, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
        keepalive: true,
      });
    }
    localStorage.removeItem('session');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('csrf_token');
    localStorage.removeItem('user_email');
    localStorage.removeItem('user_role');
    window.location.href = '/login';
  }
}

export function getCsrfToken(): string | null {
  if (typeof window !== 'undefined') {
    const fromStorage = localStorage.getItem('csrf_token');
    if (fromStorage) return fromStorage;
  }
  if (typeof document === 'undefined') return null;
  const cookie = document.cookie.split('; ').find((entry) => entry.startsWith('dwrms_csrf_token='));
  return cookie ? decodeURIComponent(cookie.split('=', 2)[1]) : null;
}

export function getSession() {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('session');
  }
  return null;
}
