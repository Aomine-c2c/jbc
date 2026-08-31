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
    <div className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-slate-950/95 border-t border-slate-800 backdrop-blur-md px-2 py-1.5 flex items-center justify-around shadow-2xl safe-area-pb">
      {navButtons.map((btn) => {
        const isActive = pathname === btn.href || (btn.href !== '/' && pathname?.startsWith(btn.href));
        const Icon = btn.icon;

        return (
          <Link
            key={btn.name}
            href={btn.href}
            className={`flex flex-col items-center justify-center py-1 px-3 rounded-lg transition-all relative ${
              isActive ? 'text-amber-400 font-bold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <div className="relative">
              <Icon className="w-5 h-5" />
              {btn.badge !== null && btn.badge !== undefined && (
                <span className="absolute -top-1.5 -right-2 bg-amber-500 text-slate-950 font-bold text-[9px] w-4 h-4 rounded-full flex items-center justify-center shadow-xs">
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
        className="flex flex-col items-center justify-center py-1 px-3 rounded-lg text-slate-400 hover:text-slate-200 transition"
      >
        <Menu className="w-5 h-5" />
        <span className="text-[10px] mt-0.5 tracking-tight">More</span>
      </button>
    </div>
  );
}
