import type { Metadata } from 'next';
import { Providers } from '@/app/providers';
import './globals.css';

export const metadata: Metadata = {
  title: 'LeadForge | AI Local Lead Generator',
  description: 'AI-powered Google Maps lead generation and website analysis',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0f1115] text-slate-200">
        <Providers>
          <div className="flex min-h-screen flex-col">
            {/* Minimal Top Nav */}
            <header className="sticky top-0 z-40 flex h-14 items-center justify-between border-b border-[#1e293b] bg-[#0f1115]/80 px-6 backdrop-blur-md">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-tr from-teal-500 to-emerald-400 shadow-sm">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-slate-950">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                  </svg>
                </div>
                <span className="font-semibold text-white tracking-tight">LeadForge</span>
              </div>
              <div className="flex items-center gap-4 text-sm font-medium text-slate-400">
                <a href="#" className="text-white">Dashboard</a>
              </div>
            </header>
            
            {/* Main Content */}
            <div className="flex-1">
              {children}
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
