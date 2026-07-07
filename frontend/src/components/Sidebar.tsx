'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { Search, Network } from 'lucide-react';

function cls(...c: (string | false | undefined)[]) { return c.filter(Boolean).join(' '); }

export default function Sidebar() {
  const pathname = usePathname();

  const navItems = [
    {
      name: 'Prospector',
      href: '/',
      icon: Search,
    },
    {
      name: 'Social Lead Finder',
      href: '/social-finder',
      icon: Network,
    },
  ];

  return (
    <aside className="fixed h-screen w-[220px] left-0 top-0 bg-[#0d0d11]/85 backdrop-blur-xl flex flex-col py-6 px-4 z-40 border-r border-[#464554]/20">
      {/* Brand — text only, no logo icon */}
      <div className="px-2 mb-8">
        <h1 className="font-bold text-[20px] text-[#c0c1ff] tracking-tight leading-none">LeadForge</h1>
        <p className="text-[9px] text-[#c7c4d7]/50 tracking-widest uppercase mt-0.5">AI Lead Engine</p>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-2">
        {navItems.map((item) => {
          const active = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cls(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg font-semibold text-[11px] tracking-wider uppercase transition-all duration-200 border",
                active
                  ? "bg-[#c0c1ff]/10 text-[#c0c1ff] border-[#c0c1ff]/20"
                  : "text-[#c7c4d7]/60 hover:text-white border-transparent hover:bg-white/[0.02]"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
