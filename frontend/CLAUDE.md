# Bikita Minerals DWRMS — Frontend Architecture & Developer Guide

## Overview

The Bikita Minerals DWRMS frontend is built with **Next.js (App Router)**, **TypeScript**, **TailwindCSS**, and **Shadcn/UI** primitives. It is designed to operate seamlessly in both online mining server environments and offline-first edge deployment modes (via PWA and desktop packaging).

## Key Architecture & Conventions

- **App Router Structure**: Routes are organized under `src/app/` with route grouping (e.g., `(auth)`, `admin/`, `fleet/`, `jobs/`, `my-work/`).
- **RBAC & Route Protection**: The `<Protect>` component (`src/components/auth/Protect.tsx`) and role switches enforce role-based access control across navigation items and actionable buttons.
- **Offline & Resilience**: `SyncManager.ts` and `offlineStore.ts` preserve client state and unsaved drafts if communication with the backend is degraded.
- **API Communication**: The central API gateway (`src/lib/api.ts`) proxies requests to `/api/v1` and attaches authorization tokens and tenant headers.

## Testing & Build Commands

- Run development server: `npm run dev`
- Run production build: `npm run build`
- Run unit/component tests: `npm run test`
- Run lint checks: `npm run lint`
