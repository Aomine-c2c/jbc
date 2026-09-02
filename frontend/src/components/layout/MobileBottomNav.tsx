'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Wrench, ShieldCheck, Truck, Menu } from 'lucide-react';
import { getPendingApprovals } from '@/lib/approvals';

interface MobileBottomNavProps {
  onOpenDrawer: () => void;
}

export function MobileBottomNav({ onOpenDrawer }: MobileBottomNavProps) {
  const pathname = usePathname();
  const [pendingApprovals, setPendingApprovals] = useState<number>(0);

  useEffect(() => {
    getPendingApprovals()
      .then((items) => setPendingApprovals(items.length))
      .catch(() => {});
  }, [pathname]);

  const navButtons = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'My Work', href: '/my-work', icon: Wrench },
    { name: 'Approvals', href: '/approvals', icon: ShieldCheck, badge: pendingApprovals > 0 ? pendingApprovals : null },
    { name: 'Fleet', href: '/fleet', icon: Truck },
  ];

  return (
    <div className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/95 dark:bg-zinc-950/95 border-t border-zinc-200 dark:border-zinc-800 backdrop-blur-md px-2 py-1.5 flex items-center justify-around shadow-lg safe-area-pb">
      {navButtons.map((btn) => {
        const isActive = pathname === btn.href || (btn.href !== '/' && pathname?.startsWith(btn.href));
        const Icon = btn.icon;

        return (
          <Link
            key={btn.name}
            href={btn.href}
            className={`flex flex-col items-center justify-center py-1 px-3 rounded-lg transition-colors relative ${
              isActive
                ? 'text-zinc-900 dark:text-white font-bold'
                : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'
            }`}
          >
            <div className="relative">
              <Icon className="size-5" />
              {btn.badge !== null && btn.badge !== undefined && (
                <span className="absolute -top-1.5 -right-2 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 font-bold text-[9px] size-4 rounded-full flex items-center justify-center shadow-xs">
                  {btn.badge > 9 ? '9+' : btn.badge}
                </span>
              )}
            </div>
            <span className="text-[10px] mt-0.5 tracking-tight">{btn.name}</span>
          </Link>
        );
      })}

      {/* Menu / Drawer Trigger */}
      <button
        type="button"
        onClick={onOpenDrawer}
        className="flex flex-col items-center justify-center py-1 px-3 rounded-lg text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300 transition-colors"
      >
        <Menu className="size-5" />
        <span className="text-[10px] mt-0.5 tracking-tight">More</span>
      </button>
    </div>
  );
}
