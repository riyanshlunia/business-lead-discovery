import type { Metadata } from 'next';
import { Providers } from '@/app/providers';
import { Search, Zap } from 'lucide-react';
import './globals.css';

export const metadata: Metadata = {
  title: 'LeadForge | AI Local Lead Generator',
  description: 'AI-powered Google Maps lead generation and website analysis',
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#050505] text-[#e5e2e3] overflow-hidden flex h-screen select-none">
        <Providers>
          {/* Slim Sidebar */}
          <aside className="fixed h-screen w-[220px] left-0 top-0 glass-sidebar flex flex-col py-6 px-4 z-40 border-r border-[#464554]/20">
            {/* Brand — text only, no logo icon */}
            <div className="px-2 mb-8">
              <h1 className="font-bold text-[20px] text-[#c0c1ff] tracking-tight leading-none">LeadForge</h1>
              <p className="text-[9px] text-[#c7c4d7]/50 tracking-widest uppercase mt-0.5">AI Lead Engine</p>
            </div>

            {/* Nav — Prospector only */}
            <nav className="flex-1">
              <a
                href="#"
                className="flex items-center gap-3 px-3 py-2.5 bg-[#c0c1ff]/10 text-[#c0c1ff] border border-[#c0c1ff]/20 rounded-lg font-semibold text-[11px] tracking-wider uppercase"
              >
                <Search className="h-4 w-4 shrink-0" />
                Prospector
              </a>
            </nav>
          </aside>

          {/* Main Content */}
          <main className="ml-[220px] flex-1 flex flex-col h-screen overflow-hidden relative">
            <div className="absolute inset-0 topographic-bg pointer-events-none opacity-40" />
            <div className="flex-1 overflow-y-auto p-6">
              {children}
            </div>
          </main>
        </Providers>
      </body>
    </html>
  );
}
