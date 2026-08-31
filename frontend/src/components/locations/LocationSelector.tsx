'use client';

import React, { useState, useEffect, useRef } from 'react';
import { apiFetch } from '@/lib/api';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  MapPin,
  Search,
  ChevronRight,
  Clock,
  X,
  Building2,
  Layers,
  Check,
  FolderTree,
} from 'lucide-react';

export interface LocationOption {
  id: string;
  code: string;
  name: string;
  location_type: string;
  breadcrumb?: string;
  hierarchy_level: number;
  site_name?: string;
  barcode_or_nfc?: string;
}

interface LocationSelectorProps {
  value?: string | null;
  locationName?: string | null;
  onChange: (locationId: string | null, breadcrumb: string | null, locationObj?: LocationOption | null) => void;
  onTextChange?: (text: string) => void;
  siteId?: string;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

const RECENT_KEY = 'dwrms_recent_locations';

export function LocationSelector({
  value,
  locationName,
  onChange,
  onTextChange,
  siteId,
  placeholder = 'Search site, facility, area, section or specific location...',
  disabled = false,
  className = '',
}: LocationSelectorProps) {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<LocationOption[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<LocationOption | null>(null);
  const [recentLocations, setRecentLocations] = useState<LocationOption[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  // Load recent locations from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(RECENT_KEY);
      if (stored) {
        setRecentLocations(JSON.parse(stored).slice(0, 5));
      }
    } catch {
      // Ignore localStorage errors
    }
  }, []);

  // Fetch location details if value is provided
  useEffect(() => {
    if (value) {
      apiFetch<LocationOption>(`/api/v1/locations/${value}`)
        .then((loc) => setSelectedLocation(loc))
        .catch(() => setSelectedLocation(null));
    } else {
      setSelectedLocation(null);
    }
  }, [value]);

  // Click outside to close
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({ q: query.trim(), limit: '15' });
        if (siteId) params.append('site_id', siteId);
        const data = await apiFetch<LocationOption[]>(`/api/v1/locations/search?${params.toString()}`);
        setSearchResults(data || []);
      } catch {
        setSearchResults([]);
      } finally {
        setLoading(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query, siteId]);

  const handleSelect = (loc: LocationOption) => {
    setSelectedLocation(loc);
    setIsOpen(false);
    setQuery('');
    onChange(loc.id, loc.breadcrumb || loc.name, loc);
    if (onTextChange) {
      onTextChange(loc.name);
    }

    // Save to recents
    try {
      const updated = [loc, ...recentLocations.filter((r) => r.id !== loc.id)].slice(0, 5);
      setRecentLocations(updated);
      localStorage.setItem(RECENT_KEY, JSON.stringify(updated));
    } catch {
      // Ignore
    }
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedLocation(null);
    setQuery('');
    onChange(null, null, null);
    if (onTextChange) {
      onTextChange('');
    }
  };

  const getTypeColor = (type: string) => {
    switch (type?.toUpperCase()) {
      case 'SITE':
        return 'bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/30';
      case 'FACILITY':
      case 'PLANT':
        return 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30';
      case 'AREA':
        return 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30';
      case 'SECTION':
        return 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30';
      case 'WORK_CENTER':
      case 'ROOM':
      case 'SPECIFIC_LOCATION':
        return 'bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 border-indigo-500/30';
      default:
        return 'bg-muted text-muted-foreground border-border';
    }
  };

  return (
    <div className={`relative w-full ${className}`} ref={containerRef}>
      {/* Active Selection Display or Search Trigger */}
      {selectedLocation ? (
        <div className="flex items-center justify-between p-2.5 rounded-lg border border-primary/40 bg-primary/5 hover:bg-primary/10 transition-colors">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="p-1.5 rounded-md bg-primary/10 text-primary shrink-0">
              <MapPin className="size-4" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-xs text-foreground truncate">
                  {selectedLocation.name}
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                  {selectedLocation.code}
                </span>
                <Badge variant="outline" className={`text-[9px] px-1.5 py-0 uppercase font-mono ${getTypeColor(selectedLocation.location_type)}`}>
                  {selectedLocation.location_type}
                </Badge>
              </div>
              {selectedLocation.breadcrumb && (
                <p className="text-[11px] text-muted-foreground truncate font-mono mt-0.5">
                  {selectedLocation.breadcrumb}
                </p>
              )}
            </div>
          </div>
          {!disabled && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="size-7 text-muted-foreground hover:text-foreground shrink-0"
              onClick={handleClear}
            >
              <X className="size-3.5" />
            </Button>
          )}
        </div>
      ) : (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            type="text"
            value={query}
            disabled={disabled}
            onChange={(e) => {
              setQuery(e.target.value);
              setIsOpen(true);
              if (onTextChange) {
                onTextChange(e.target.value);
              }
            }}
            onFocus={() => setIsOpen(true)}
            placeholder={locationName || placeholder}
            className="pl-9 pr-8 text-xs font-medium"
          />
          {query && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="absolute right-1.5 top-1/2 -translate-y-1/2 size-6 text-muted-foreground hover:text-foreground"
              onClick={() => {
                setQuery('');
                setSearchResults([]);
              }}
            >
              <X className="size-3" />
            </Button>
          )}
        </div>
      )}

      {/* Dropdown Menu */}
      {isOpen && !disabled && (
        <div className="absolute z-50 mt-1.5 w-full rounded-lg border border-border bg-popover text-popover-foreground shadow-xl overflow-hidden animate-in fade-in-0 zoom-in-95 duration-100 max-h-80 overflow-y-auto">
          {loading && (
            <div className="p-4 text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
              <span className="size-3.5 rounded-full border-2 border-primary border-t-transparent animate-spin" />
              Searching spatial hierarchy...
            </div>
          )}

          {!loading && searchResults.length > 0 && (
            <div className="py-1">
              <div className="px-3 py-1.5 text-[10px] font-mono uppercase tracking-wider text-muted-foreground/70 font-semibold bg-muted/30">
                Search Results ({searchResults.length})
              </div>
              {searchResults.map((loc) => (
                <button
                  key={loc.id}
                  type="button"
                  onClick={() => handleSelect(loc)}
                  className="w-full px-3 py-2 text-left hover:bg-muted/60 transition-colors flex items-start justify-between gap-2 border-b border-border/40 last:border-0"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-xs text-foreground truncate">
                        {loc.name}
                      </span>
                      <span className="text-[10px] font-mono px-1 rounded bg-muted text-muted-foreground">
                        {loc.code}
                      </span>
                      <Badge variant="outline" className={`text-[9px] px-1 py-0 uppercase font-mono ${getTypeColor(loc.location_type)}`}>
                        {loc.location_type}
                      </Badge>
                    </div>
                    {loc.breadcrumb && (
                      <p className="text-[11px] text-muted-foreground truncate font-mono mt-0.5">
                        {loc.breadcrumb}
                      </p>
                    )}
                  </div>
                  {loc.barcode_or_nfc && (
                    <span className="text-[10px] font-mono text-muted-foreground/80 shrink-0">
                      🏷️ {loc.barcode_or_nfc}
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}

          {!loading && query.trim() && searchResults.length === 0 && (
            <div className="p-4 text-center text-xs text-muted-foreground">
              No matching locations found for &ldquo;{query}&rdquo;
            </div>
          )}

          {!loading && !query.trim() && recentLocations.length > 0 && (
            <div className="py-1">
              <div className="px-3 py-1.5 text-[10px] font-mono uppercase tracking-wider text-muted-foreground/70 font-semibold bg-muted/30 flex items-center gap-1.5">
                <Clock className="size-3" />
                Recent Locations
              </div>
              {recentLocations.map((loc) => (
                <button
                  key={loc.id}
                  type="button"
                  onClick={() => handleSelect(loc)}
                  className="w-full px-3 py-2 text-left hover:bg-muted/60 transition-colors flex items-start justify-between gap-2 border-b border-border/40 last:border-0"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-xs text-foreground truncate">
                        {loc.name}
                      </span>
                      <span className="text-[10px] font-mono px-1 rounded bg-muted text-muted-foreground">
                        {loc.code}
                      </span>
                      <Badge variant="outline" className={`text-[9px] px-1 py-0 uppercase font-mono ${getTypeColor(loc.location_type)}`}>
                        {loc.location_type}
                      </Badge>
                    </div>
                    {loc.breadcrumb && (
                      <p className="text-[11px] text-muted-foreground truncate font-mono mt-0.5">
                        {loc.breadcrumb}
                      </p>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
