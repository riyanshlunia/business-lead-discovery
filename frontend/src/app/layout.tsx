import type { Metadata } from 'next';
import { Providers } from '@/app/providers';
import Sidebar from '@/components/Sidebar';
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
          {/* Sidebar Navigation */}
          <Sidebar />

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
