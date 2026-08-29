# Global Navigation Redesign

## Overview
The DWRMS application currently uses a vertical left-hand Sidebar for global navigation. To maximize horizontal screen real estate (particularly on field tablets) and improve visual consistency with our new Industrial High-Contrast dark theme, we are migrating to a Top Horizontal Tab Bar layout.

## Structure (5 Flat Tabs)
The new navigation will feature a top horizontal header containing 5 primary navigation tabs, representing all core modules of the application. The tabs will be arranged sequentially:
1. **Dashboard** (`/`)
2. **Job Cards** (`/jobs`)
3. **Fleet & Availability** (`/fleet`)
4. **Users** (`/admin/users`)
5. **Settings** (`/admin/settings`)

## UI & Aesthetics (Stealth Header with Neon Accents)
- **Header Container:** The header will have a "stealth" design, meaning it will seamlessly blend with the application's dark background (`bg-background` or `bg-card`). It will have a subtle bottom border (`border-border`) to separate it from the page content.
- **Brand Element:** The top-left corner will contain the DWRMS logo or title, keeping the neon orange accent (`text-primary`).
- **Tab Design:** 
  - Inactive tabs will use `text-muted-foreground` and have no background highlight.
  - Active tabs will feature a bright neon underline (e.g., a bottom border using `border-primary` or `border-secondary`) and high-contrast text (`text-foreground`).
  - Hover states will feature a subtle background highlight (`hover:bg-muted/50`).
- **User Profile:** The top-right corner will contain the user avatar and profile details.

## Component Changes
- `frontend/src/components/layout/Sidebar.tsx` will be deleted or heavily refactored into a `TopNav.tsx` component.
- `frontend/src/components/layout/AppLayout.tsx` will be restructured. The `flex h-screen` container will switch from a `flex-row` (Sidebar + Content) to a `flex-col` (Top Header + Scrollable Content) layout.

## Security & Permissions
- The existing `<Protect>` wrappers around navigation links will be preserved. If a user lacks the capability for a specific tab (e.g., `users:manage`), that tab will simply not render in the header.
