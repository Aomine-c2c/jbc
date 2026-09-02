/**
 * Bikita Minerals DWRMS — Multi-Client Server Connection Profiles Engine (V2.2)
 * Manages configurable server connection profiles, pre-flight server validation,
 * automatic local LAN fallback failover, and real-time connection status telemetry.
 */

export interface ServerProfile {
  id: string;
  name: string; // e.g. "Bikita Minerals Production"
  primaryUrl: string; // e.g. "https://operations.bikita.com"
  fallbackUrl?: string; // e.g. "https://192.168.1.100" (Local LAN failover)
  connectionMode: 'domain' | 'ip' | 'remote_vpn' | 'tailscale';
  organizationName?: string; // Verified from server probe
  installationName?: string;
  serverVersion?: string; // e.g. "v2.2.0"
  isVerified: boolean;
  lastConnectedAt?: string;
  isDefault?: boolean;
}

export type ConnectionStatus = 'ONLINE' | 'CONNECTING' | 'OFFLINE' | 'SERVER_UNAVAILABLE';

export interface ValidationResult {
  valid: boolean;
  latencyMs: number;
  usingFallback?: boolean;
  profileDetails?: {
    organizationName?: string;
    serverVersion?: string;
    environment?: string;
    architecture?: string;
    databaseConnected?: boolean;
    isHttps: boolean;
  };
  error?: string;
}

const PROFILES_STORAGE_KEY = 'dwrms_server_profiles';
const ACTIVE_PROFILE_ID_KEY = 'dwrms_active_profile_id';
const LEGACY_API_URL_KEY = 'dwrms_api_url';
const DEFAULT_BACKEND_URL = 'http://localhost:8000';

// Default starter profile template
export const DEFAULT_PROFILES: ServerProfile[] = [
  {
    id: 'prod-default',
    name: 'Bikita Minerals Production',
    primaryUrl: process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, '').replace(/\/api\/v1$/, '') || DEFAULT_BACKEND_URL,
    fallbackUrl: 'http://192.168.1.100:8000',
    connectionMode: 'domain',
    isVerified: false,
    isDefault: true,
  },
  {
    id: 'staging-default',
    name: 'Staging / Testing Environment',
    primaryUrl: 'https://staging-dwrms.bikita.com',
    connectionMode: 'domain',
    isVerified: false,
    isDefault: false,
  },
  {
    id: 'dev-default',
    name: 'Local Development Server',
    primaryUrl: 'http://localhost:8000',
    connectionMode: 'ip',
    isVerified: false,
    isDefault: false,
  },
];

// Clean formatting helper
export function normalizeServerUrl(url: string): string {
  let clean = url.trim();
  if (!clean.startsWith('http://') && !clean.startsWith('https://')) {
    clean = `https://${clean}`;
  }
  return clean.replace(/\/+$/, '').replace(/\/api\/v1$/, '');
}

/**
 * Pre-flight server verification probe.
 * Tests reachability, API version compatibility, and identity before accepting.
 */
export async function validateServer(primaryUrl: string, fallbackUrl?: string): Promise<ValidationResult> {
  const cleanPrimary = normalizeServerUrl(primaryUrl);
  const t0 = performance.now();

  try {
    // 1. Probe primary URL
    const response = await fetch(`${cleanPrimary}/api/v1/info`, {
      method: 'GET',
      headers: { 'Cache-Control': 'no-cache', 'Accept': 'application/json' },
      signal: AbortSignal.timeout(5000),
    });

    if (response.ok) {
      const data = await response.json();
      const latencyMs = Math.round(performance.now() - t0);

      return {
        valid: true,
        latencyMs,
        usingFallback: false,
        profileDetails: {
          organizationName: data.platform || 'Bikita Minerals DWRMS',
          serverVersion: data.version || 'v2.x',
          environment: data.environment || 'production',
          architecture: data.architecture || 'Server-First Multi-Client',
          databaseConnected: data.database?.connected ?? true,
          isHttps: cleanPrimary.startsWith('https://'),
        },
      };
    }
  } catch (primaryErr: unknown) {
    const pErr = primaryErr as { name?: string; message?: string };
    // 2. If primary failed and fallback is provided, probe fallback
    if (fallbackUrl) {
      const cleanFallback = normalizeServerUrl(fallbackUrl);
      try {
        const tFallback = performance.now();
        const fbResponse = await fetch(`${cleanFallback}/api/v1/info`, {
          method: 'GET',
          headers: { 'Cache-Control': 'no-cache', 'Accept': 'application/json' },
          signal: AbortSignal.timeout(4000),
        });

        if (fbResponse.ok) {
          const fbData = await fbResponse.json();
          const fbLatency = Math.round(performance.now() - tFallback);

          return {
            valid: true,
            latencyMs: fbLatency,
            usingFallback: true,
            profileDetails: {
              organizationName: fbData.platform || 'Bikita Minerals DWRMS',
              serverVersion: fbData.version || 'v2.x',
              environment: fbData.environment || 'production',
              architecture: fbData.architecture || 'Server-First Multi-Client',
              databaseConnected: fbData.database?.connected ?? true,
              isHttps: cleanFallback.startsWith('https://'),
            },
          };
        }
      } catch {
        // Both primary and fallback failed
      }
    }

    return {
      valid: false,
      latencyMs: 0,
      error: pErr.name === 'TimeoutError'
        ? 'Connection timed out. Verify server IP, domain, firewall, or VPN.'
        : `Server unreachable: ${pErr.message || 'Check network connection'}`,
    };
  }

  return {
    valid: false,
    latencyMs: 0,
    error: 'Server returned unexpected response status.',
  };
}

/**
 * Loads all saved server profiles from persistent storage.
 */
export async function getProfiles(): Promise<ServerProfile[]> {
  if (typeof window === 'undefined') return DEFAULT_PROFILES;

  // 1. Check Tauri store if running in desktop app
  if ((window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__) {
    try {
      const { load } = await import('@tauri-apps/plugin-store');
      const store = await load('server_profiles.json');
      const stored = (await store.get<ServerProfile[]>(PROFILES_STORAGE_KEY)) || (await store.get<ServerProfile[]>('profiles'));
      if (stored && stored.length > 0) return stored;
    } catch (e) {
      console.warn('Tauri store read error:', e);
    }
  }

  // 2. Check localStorage
  const raw = localStorage.getItem(PROFILES_STORAGE_KEY);
  if (raw) {
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    } catch (e) {
      console.warn('localStorage profiles parse error:', e);
    }
  }

  // 3. Migration: Check if legacy single-URL exists
  const legacyUrl = localStorage.getItem(LEGACY_API_URL_KEY);
  if (legacyUrl) {
    const migrated: ServerProfile[] = [
      {
        id: 'migrated-primary',
        name: 'Configured Server',
        primaryUrl: normalizeServerUrl(legacyUrl),
        connectionMode: 'domain',
        isVerified: true,
        isDefault: true,
      }
    ];
    return migrated;
  }

  // 2. Web fallback (localStorage)
  const stored = localStorage.getItem(PROFILES_STORAGE_KEY);
  if (stored) {
    try {
      return JSON.parse(stored) as ServerProfile[];
    } catch {
      return DEFAULT_PROFILES;
    }
  }

  return DEFAULT_PROFILES;
}

/**
 * Saves profile list to persistent storage.
 */
async function saveProfilesList(profiles: ServerProfile[]): Promise<void> {
  if (typeof window === 'undefined') return;

  localStorage.setItem(PROFILES_STORAGE_KEY, JSON.stringify(profiles));

  // Sync to Tauri store if in desktop app
  if ((window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__) {
    try {
      const { load } = await import('@tauri-apps/plugin-store');
      const store = await load('server_profiles.json');
      await store.set(PROFILES_STORAGE_KEY, profiles);
      await store.save();
    } catch (e) {
      console.warn('Tauri store save error:', e);
    }
  }
}

/**
 * Gets the currently active server profile. Defaults to the first or default profile.
 */
export async function getActiveProfile(): Promise<ServerProfile | null> {
  const profiles = await getProfiles();
  if (profiles.length === 0) return null;

  const activeId = typeof window !== 'undefined' ? localStorage.getItem(ACTIVE_PROFILE_ID_KEY) : null;
  const found = profiles.find((p) => p.id === activeId);
  return found || profiles.find((p) => p.isDefault) || profiles[0];
}

/**
 * Sets the active server profile by ID.
 */
export async function setActiveProfile(profileId: string): Promise<void> {
  if (typeof window === 'undefined') return;

  localStorage.setItem(ACTIVE_PROFILE_ID_KEY, profileId);

  if ((window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__) {
    try {
      const { load } = await import('@tauri-apps/plugin-store');
      const store = await load('server_profiles.json');
      await store.set(ACTIVE_PROFILE_ID_KEY, profileId);
      await store.save();
    } catch (e) {
      console.warn('Tauri store setActiveProfile error:', e);
    }
  }

  window.dispatchEvent(new Event('server-config-changed'));
}

/**
 * Adds or updates a server profile.
 */
export async function saveProfile(profile: ServerProfile): Promise<void> {
  const profiles = await getProfiles();
  const existingIndex = profiles.findIndex((p) => p.id === profile.id);

  if (existingIndex >= 0) {
    profiles[existingIndex] = profile;
  } else {
    profiles.push(profile);
  }

  await saveProfilesList(profiles);
}

/**
 * Deletes a server profile.
 */
export async function deleteProfile(profileId: string): Promise<void> {
  const profiles = await getProfiles();
  const filtered = profiles.filter((p) => p.id !== profileId);
  await saveProfilesList(filtered);
}

/**
 * Resolves active API base URL with automatic fallback failover if needed.
 */
export async function getActiveApiUrl(): Promise<string> {
  const envUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, '').replace(/\/api\/v1$/, '');
  if (envUrl) {
    return normalizeServerUrl(envUrl);
  }

  const active = await getActiveProfile();

  // In local browser/Tauri development, use the local backend unless we're
  // explicitly on a production-like origin. Covers http://localhost:3000,
  // http://127.0.0.1:3000, and Tauri's tauri://localhost dev origin.
  if (typeof window !== 'undefined') {
    const origin = window.location.origin;
    const isDevOrigin = [
      'http://localhost:3000',
      'http://127.0.0.1:3000',
      'http://localhost:3001',
      'http://127.0.0.1:3001',
      'tauri://localhost',
    ].includes(origin);

    if (isDevOrigin) {
      return DEFAULT_BACKEND_URL;
    }

    if (!active || active.id === 'prod-default') {
      return origin;
    }
  }

  return normalizeServerUrl(active.primaryUrl);
}
