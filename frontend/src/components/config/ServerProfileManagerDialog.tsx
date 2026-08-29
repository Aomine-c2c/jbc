'use client';

import React, { useEffect, useState, useCallback } from 'react';
import {
  Server,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  X,
  Plus,
  Trash2,
  Radio,
  Globe,
  HardDrive,
  ShieldCheck,
  Zap,
  Activity,
} from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  ServerProfile,
  getProfiles,
  getActiveProfile,
  saveProfile,
  deleteProfile,
  setActiveProfile,
  validateServer,
  ValidationResult,
  normalizeServerUrl,
} from '@/lib/serverProfiles';

interface ServerProfileManagerDialogProps {
  isOpen?: boolean;
  onClose?: () => void;
  onConfigured?: () => void;
}

export function ServerProfileManagerDialog({ isOpen, onClose, onConfigured }: ServerProfileManagerDialogProps) {
  const [open, setOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'profiles' | 'add'>('profiles');
  const [profiles, setProfiles] = useState<ServerProfile[]>([]);
  const [activeProfile, setActiveProfileState] = useState<ServerProfile | null>(null);

  // New Profile Form State
  const [newProfileName, setNewProfileName] = useState('Bikita Production Server');
  const [newPrimaryUrl, setNewPrimaryUrl] = useState('');
  const [newFallbackUrl, setNewFallbackUrl] = useState('');
  const [connectionMode, setConnectionMode] = useState<'domain' | 'ip' | 'remote_vpn' | 'tailscale'>('domain');

  // Validation State
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const isControlled = isOpen !== undefined;
  const dialogOpen = isControlled ? isOpen : open;

  // Load profiles on mount
  const loadData = useCallback(async () => {
    const list = await getProfiles();
    setProfiles(list);
    const active = await getActiveProfile();
    setActiveProfileState(active);

    if (active) {
      setNewPrimaryUrl(active.primaryUrl);
      setNewFallbackUrl(active.fallbackUrl || '');
    }

    // First-launch detection on desktop
    if (!isControlled && typeof window !== 'undefined' && (window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__) {
      const isConfigured = localStorage.getItem('dwrms_active_profile_id');
      if (!isConfigured) {
        setOpen(true);
      }
    }
  }, [isControlled]);

  useEffect(() => {
    loadData();

    const handleUpdate = () => loadData();
    window.addEventListener('server-profiles-changed', handleUpdate);
    return () => window.removeEventListener('server-profiles-changed', handleUpdate);
  }, [loadData]);

  const handleClose = () => {
    if (isControlled && onClose) {
      onClose();
    } else {
      setOpen(false);
      if (onConfigured) onConfigured();
    }
  };

  // Validate server probe
  const handleValidate = async () => {
    if (!newPrimaryUrl) {
      setActionMessage({ type: 'error', text: 'Please enter a valid primary server URL or host.' });
      return;
    }

    setIsValidating(true);
    setActionMessage(null);
    setValidationResult(null);

    const result = await validateServer(newPrimaryUrl, newFallbackUrl);
    setIsValidating(false);
    setValidationResult(result);

    if (!result.valid) {
      setActionMessage({ type: 'error', text: result.error || 'Server validation failed.' });
    }
  };

  // Save and switch to profile
  const handleSaveProfile = async () => {
    if (!newPrimaryUrl) return;

    const newId = `profile-${Date.now()}`;
    const newProfile: ServerProfile = {
      id: newId,
      name: newProfileName || 'Custom Server',
      primaryUrl: normalizeServerUrl(newPrimaryUrl),
      fallbackUrl: newFallbackUrl ? normalizeServerUrl(newFallbackUrl) : undefined,
      connectionMode,
      organizationName: validationResult?.profileDetails?.organizationName,
      serverVersion: validationResult?.profileDetails?.serverVersion,
      isVerified: validationResult?.valid || false,
      lastConnectedAt: new Date().toISOString(),
      isDefault: profiles.length === 0,
    };

    await saveProfile(newProfile);
    setActionMessage({ type: 'success', text: `Profile '${newProfile.name}' saved and activated.` });

    setTimeout(() => {
      handleClose();
      if (onConfigured) onConfigured();
    }, 800);
  };

  // Switch active profile
  const handleSelectProfile = async (profileId: string) => {
    await setActiveProfile(profileId);
    const updatedActive = (await getProfiles()).find((p) => p.id === profileId);
    setActiveProfileState(updatedActive || null);
    setActionMessage({ type: 'success', text: `Switched to '${updatedActive?.name}'` });

    setTimeout(() => {
      handleClose();
      if (onConfigured) onConfigured();
    }, 600);
  };

  // Delete profile
  const handleDeleteProfile = async (profileId: string) => {
    await deleteProfile(profileId);
    await loadData();
  };

  return (
    <Dialog open={dialogOpen} onOpenChange={(s) => !s && handleClose()}>
      <DialogContent className="sm:max-w-2xl bg-slate-900 border-slate-800 text-slate-100 p-0 overflow-hidden" showCloseButton={false}>
        {/* Header */}
        <DialogHeader className="p-6 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center justify-between">
            <DialogTitle className="text-lg font-bold flex items-center gap-2 text-white">
              <Server className="w-5 h-5 text-amber-500" />
              Server Connection Profiles & Multi-Client Gateway
            </DialogTitle>
            {isControlled && (
              <button
                type="button"
                onClick={handleClose}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          <DialogDescription className="text-slate-400 text-xs mt-1">
            Configure, validate, and switch between authoritative organization servers, on-site LAN failover endpoints, or remote VPNs.
          </DialogDescription>
        </DialogHeader>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 bg-slate-950/40 px-6">
          <button
            type="button"
            onClick={() => { setActiveTab('profiles'); setActionMessage(null); }}
            className={`py-3 px-4 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === 'profiles'
                ? 'border-amber-500 text-amber-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Activity className="w-3.5 h-3.5" /> Saved Server Profiles ({profiles.length})
          </button>
          <button
            type="button"
            onClick={() => { setActiveTab('add'); setActionMessage(null); }}
            className={`py-3 px-4 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === 'add'
                ? 'border-amber-500 text-amber-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Plus className="w-3.5 h-3.5" /> Connect to Organization Server / Add Profile
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 max-h-[60vh] overflow-y-auto space-y-4">
          {actionMessage && (
            <div
              className={`p-3 rounded-lg flex items-center gap-2 text-xs border ${
                actionMessage.type === 'error'
                  ? 'bg-red-500/10 border-red-500/30 text-red-400'
                  : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
              }`}
            >
              {actionMessage.type === 'error' ? <AlertTriangle className="w-4 h-4 shrink-0" /> : <CheckCircle2 className="w-4 h-4 shrink-0" />}
              <span>{actionMessage.text}</span>
            </div>
          )}

          {/* ── TAB 1: SAVED PROFILES LIST ──────────────────────────────── */}
          {activeTab === 'profiles' && (
            <div className="space-y-3">
              {profiles.map((profile) => {
                const isActive = activeProfile?.id === profile.id;
                return (
                  <div
                    key={profile.id}
                    className={`p-4 rounded-xl border transition-all ${
                      isActive
                        ? 'bg-amber-500/10 border-amber-500/50 shadow-md shadow-amber-500/5'
                        : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-9 h-9 rounded-lg flex items-center justify-center font-bold text-xs ${
                            isActive ? 'bg-amber-500 text-slate-950' : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          <Server className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-sm text-white">{profile.name}</span>
                            {isActive && <Badge className="bg-amber-500 text-slate-950 text-[10px] font-bold">ACTIVE</Badge>}
                          </div>
                          <div className="text-xs font-mono text-slate-400">{profile.primaryUrl}</div>
                          {profile.fallbackUrl && (
                            <div className="text-[10px] font-mono text-slate-500">LAN Failover: {profile.fallbackUrl}</div>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {!isActive ? (
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => handleSelectProfile(profile.id)}
                            className="bg-slate-800 hover:bg-slate-700 text-xs"
                          >
                            Connect
                          </Button>
                        ) : (
                          <Badge variant="outline" className="border-emerald-500/40 text-emerald-400 text-xs">
                            <CheckCircle2 className="w-3 h-3 mr-1" /> Connected
                          </Badge>
                        )}

                        {profiles.length > 1 && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDeleteProfile(profile.id)}
                            className="text-slate-500 hover:text-red-400 hover:bg-red-500/10 p-1 h-8 w-8"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* ── TAB 2: CONNECT TO SERVER / ADD PROFILE ──────────────────── */}
          {activeTab === 'add' && (
            <div className="space-y-4">
              {/* Connection Mode Tabs */}
              <div className="grid grid-cols-3 gap-2">
                <div
                  onClick={() => setConnectionMode('domain')}
                  className={`p-3 rounded-lg border cursor-pointer text-center transition ${
                    connectionMode === 'domain'
                      ? 'border-amber-500 bg-amber-500/10 text-white'
                      : 'border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <Globe className="w-4 h-4 mx-auto mb-1 text-blue-400" />
                  <div className="text-xs font-bold">Domain Name</div>
                </div>

                <div
                  onClick={() => setConnectionMode('ip')}
                  className={`p-3 rounded-lg border cursor-pointer text-center transition ${
                    connectionMode === 'ip'
                      ? 'border-amber-500 bg-amber-500/10 text-white'
                      : 'border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <HardDrive className="w-4 h-4 mx-auto mb-1 text-emerald-400" />
                  <div className="text-xs font-bold">Direct IP / LAN</div>
                </div>

                <div
                  onClick={() => setConnectionMode('tailscale')}
                  className={`p-3 rounded-lg border cursor-pointer text-center transition ${
                    connectionMode === 'tailscale'
                      ? 'border-amber-500 bg-amber-500/10 text-white'
                      : 'border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <Radio className="w-4 h-4 mx-auto mb-1 text-purple-400" />
                  <div className="text-xs font-bold">Secure Remote Mesh</div>
                </div>
              </div>

              <div className="space-y-3">
                <div className="space-y-1.5">
                  <Label className="text-xs">Profile Name</Label>
                  <Input
                    placeholder="e.g. Bikita Mining Site Production"
                    value={newProfileName}
                    onChange={(e) => setNewProfileName(e.target.value)}
                    className="bg-slate-950 border-slate-700 text-sm"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label className="text-xs">Primary Server URL or Host</Label>
                  <Input
                    placeholder="e.g. https://dwrms.bikita.com or 192.168.1.100:8000"
                    value={newPrimaryUrl}
                    onChange={(e) => setNewPrimaryUrl(e.target.value)}
                    className="bg-slate-950 border-slate-700 font-mono text-xs"
                  />
                  <p className="text-[10px] text-slate-500">Authoritative endpoint for all platform APIs and data sync.</p>
                </div>

                <div className="space-y-1.5">
                  <Label className="text-xs">Optional Fallback Server URL (Local LAN Failover)</Label>
                  <Input
                    placeholder="e.g. https://192.168.1.100"
                    value={newFallbackUrl}
                    onChange={(e) => setNewFallbackUrl(e.target.value)}
                    className="bg-slate-950 border-slate-700 font-mono text-xs"
                  />
                  <p className="text-[10px] text-slate-500">Used automatically if the primary domain is temporarily unreachable on-site.</p>
                </div>
              </div>

              {/* Pre-flight validation box */}
              {validationResult?.valid && (
                <div className="p-4 bg-emerald-950/30 border border-emerald-800/40 rounded-xl space-y-2 text-xs">
                  <div className="flex items-center justify-between text-emerald-400 font-bold">
                    <span className="flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4" /> Server Verified Successfully
                    </span>
                    <Badge className="bg-emerald-600 text-white font-mono text-[10px]">
                      {validationResult.latencyMs} ms
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-slate-300 pt-1">
                    <div>Organization: <span className="text-white font-semibold">{validationResult.profileDetails?.organizationName}</span></div>
                    <div>Platform Version: <span className="text-white font-semibold">{validationResult.profileDetails?.serverVersion}</span></div>
                    <div>Environment: <span className="text-white font-semibold">{validationResult.profileDetails?.environment}</span></div>
                    <div>Connection: <span className={validationResult.profileDetails?.isHttps ? 'text-emerald-400' : 'text-amber-400'}>{validationResult.profileDetails?.isHttps ? 'HTTPS Secure' : 'HTTP Unencrypted'}</span></div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <Button
            type="button"
            variant="ghost"
            onClick={handleClose}
            className="text-slate-400 hover:text-white text-xs"
          >
            Cancel
          </Button>

          {activeTab === 'add' ? (
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="secondary"
                onClick={handleValidate}
                disabled={isValidating || !newPrimaryUrl}
                className="bg-slate-800 hover:bg-slate-700 text-xs"
              >
                {isValidating ? <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" /> : <Zap className="w-3.5 h-3.5 mr-1.5 text-amber-400" />}
                Validate Server
              </Button>

              <Button
                type="button"
                onClick={handleSaveProfile}
                disabled={!newPrimaryUrl || isValidating}
                className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs"
              >
                Save & Connect Profile
              </Button>
            </div>
          ) : (
            <Button
              type="button"
              onClick={() => setActiveTab('add')}
              className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs"
            >
              <Plus className="w-3.5 h-3.5 mr-1" /> Add New Profile
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
