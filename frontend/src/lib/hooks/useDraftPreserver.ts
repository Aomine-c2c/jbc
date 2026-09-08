'use client';

import { useState, useEffect, useCallback } from 'react';

/**
 * React Hook for automatic form draft preservation in localStorage.
 * Ensures unsaved technician/user work is never lost during network drops or browser refreshes.
 * 
 * Strict Security Invariant:
 * Local drafts only preserve raw form values for UI resilience.
 * Draft submission strictly requires full authentication, RBAC capabilities,
 * and workflow authorization upon server delivery.
 */
export function useDraftPreserver<T extends Record<string, unknown>>(
  draftKey: string,
  initialValues: T
) {
  const [values, setValues] = useState<T>(initialValues);
  const [hasSavedDraft, setHasSavedDraft] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  // Check for existing draft on initial mount
  useEffect(() => {
    if (typeof window === 'undefined') return;

    try {
      const saved = localStorage.getItem(`dwrms_draft_${draftKey}`);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed && typeof parsed === 'object' && Object.keys(parsed).length > 0) {
          setHasSavedDraft(true);
        }
      }
    } catch (e) {
      console.warn('Failed to read draft from localStorage:', e);
    } finally {
      setIsLoaded(true);
    }
  }, [draftKey]);

  // Save changes to draft
  const updateValues = useCallback(
    (newValues: Partial<T> | ((prev: T) => T)) => {
      setValues((prev) => {
        const updated = typeof newValues === 'function' ? newValues(prev) : { ...prev, ...newValues };
        if (typeof window !== 'undefined') {
          try {
            localStorage.setItem(`dwrms_draft_${draftKey}`, JSON.stringify(updated));
          } catch (e) {
            console.warn('Failed to save draft to localStorage:', e);
          }
        }
        return updated;
      });
    },
    [draftKey]
  );

  // Restore saved draft into active form
  const restoreDraft = useCallback(() => {
    if (typeof window === 'undefined') return;

    try {
      const saved = localStorage.getItem(`dwrms_draft_${draftKey}`);
      if (saved) {
        const parsed = JSON.parse(saved);
        setValues(parsed);
        setHasSavedDraft(false);
      }
    } catch (e) {
      console.error('Failed to restore draft:', e);
    }
  }, [draftKey]);

  // Discard saved draft
  const clearDraft = useCallback(() => {
    if (typeof window === 'undefined') return;

    try {
      localStorage.removeItem(`dwrms_draft_${draftKey}`);
      setHasSavedDraft(false);
      setValues(initialValues);
    } catch (e) {
      console.warn('Failed to clear draft from localStorage:', e);
    }
  }, [draftKey, initialValues]);

  return {
    values,
    setValues: updateValues,
    hasSavedDraft,
    restoreDraft,
    clearDraft,
    isLoaded,
  };
}
