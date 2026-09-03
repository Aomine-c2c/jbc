# Global Navigation Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the vertical left-hand Sidebar with a Top Horizontal Tab Bar featuring 5 primary tabs and a stealth neon-accented header.

**Architecture:** We will replace `Sidebar.tsx` with a new `TopNav.tsx` component and restructure `AppLayout.tsx` to use a `flex-col` layout instead of `flex-row`.

**Tech Stack:** React, Next.js, Tailwind CSS v4, Lucide React (for icons if needed).

## Global Constraints

- Follow the new Industrial High-Contrast theme (oklch colors).
- Use `text-primary` (neon orange) for active tab accents.
- Preserve existing `<Protect>` wrappers around navigation links.

---

### Task 1: Create TopNav Component

**Files:**

- Create: `frontend/src/components/layout/TopNav.tsx`

**Interfaces:**

- Consumes: Next.js `usePathname` for active route detection, `Protect` component for RBAC.
- Produces: `TopNav` component.

- [ ] **Step 1: Write the TopNav component implementation**

```tsx
'use client';

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Protect } from "@/components/auth/Protect";
import { LayoutDashboard, Wrench, Truck, Users, Settings } from "lucide-react";

export function TopNav() {
  const pathname = usePathname();

  const navItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard, exact: true },
    { name: "Job Cards", href: "/jobs", icon: Wrench, capability: "job_card:read" },
    { name: "Fleet", href: "/fleet", icon: Truck },
    { name: "Users", href: "/admin/users", icon: Users, capability: "users:manage" },
    { name: "Settings", href: "/admin/settings", icon: Settings, capability: "settings:manage" },
  ];

  return (
    <header className="h-16 bg-card border-b border-border flex items-center px-6 shrink-0 justify-between">
      <div className="flex items-center space-x-8 h-full">
        <div className="font-bold text-xl text-primary tracking-tight">DWRMS</div>
        
        <nav className="flex items-center space-x-1 h-full">
          {navItems.map((item) => {
            const isActive = item.exact 
              ? pathname === item.href 
              : pathname?.startsWith(item.href);

            const content = (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center px-4 h-full border-b-2 transition-colors duration-200 ${
                  isActive 
                    ? "border-primary text-foreground" 
                    : "border-transparent text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                }`}
              >
                <item.icon className="w-4 h-4 mr-2" />
                <span className="font-medium text-sm">{item.name}</span>
              </Link>
            );

            if (item.capability) {
              return (
                <Protect key={item.name} capability={item.capability as any}>
                  {content}
                </Protect>
              );
            }
            return content;
          })}
        </nav>
      </div>

      <div className="flex items-center space-x-4">
        <div className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-sm">
          JD
        </div>
      </div>
    </header>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/layout/TopNav.tsx
git commit -m "feat: create top horizontal tab navigation"
```

---

### Task 2: Restructure AppLayout & Remove Sidebar

**Files:**

- Modify: `frontend/src/components/layout/AppLayout.tsx`
- Delete: `frontend/src/components/layout/Sidebar.tsx`

**Interfaces:**

- Consumes: `TopNav` component.

- [ ] **Step 1: Update AppLayout.tsx**

```tsx
import React from "react";
import { TopNav } from "./TopNav";

export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background text-foreground font-sans">
      <TopNav />
      <main className="flex-1 overflow-auto p-6 bg-background">
        {children}
      </main>
    </div>
  );
}
```

- [ ] **Step 2: Remove Sidebar.tsx**

```bash
rm frontend/src/components/layout/Sidebar.tsx
```

- [ ] **Step 3: Run TypeScript compiler to ensure no type errors**

```bash
npx tsc --noEmit
```

Expected: PASS (or pre-existing errors in unrelated files, but no new errors in layout).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/layout/AppLayout.tsx frontend/src/components/layout/Sidebar.tsx
git commit -m "refactor: switch layout to flex-col and replace Sidebar with TopNav"
```
