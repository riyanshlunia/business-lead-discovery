'use client';

import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  Search,
  Download,
  ExternalLink,
  MapPin,
  Phone,
  Mail,
  Globe,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ChevronRight,
  Activity,
  Zap,
  Play,
  RotateCcw,
  Building2
} from 'lucide-react';
import {
  Business,
  createJob,
  getBusinesses,
  getExportUrl,
  getJob,
} from '@/lib/api';

// ── tiny primitives ──────────────────────────────────────────────────────────
function cls(...c: (string | false | undefined)[]) { return c.filter(Boolean).join(' '); }

function Badge({ children, color = 'slate' }: { children: React.ReactNode; color?: string }) {
  const map: Record<string, string> = {
    teal: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
    green: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    red: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    yellow: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    slate: 'bg-slate-800/50 text-slate-300 border-slate-700/50',
  };
  return (
    <span className={cls('inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium tracking-wide uppercase', map[color] ?? map.slate)}>
      {children}
    </span>
  );
}

function Pill({ v, label }: { v: boolean | undefined; label: string }) {
  if (!v) return null;
  return (
    <span className="inline-flex items-center gap-1 rounded bg-teal-500/10 px-1.5 py-0.5 text-[10px] font-medium text-teal-400 border border-teal-500/20">
      <CheckCircle2 className="h-3 w-3" />
      {label}
    </span>
  );
}

function ScoreBar({ score, max = 100 }: { score: number; max?: number }) {
  const pct = Math.min(100, (score / max) * 100);
  const color = pct >= 70 ? '#10b981' : pct >= 40 ? '#f59e0b' : '#ef4444';
  return (
    <div className="flex items-center gap-3">
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-800">
        <div style={{ width: `${pct}%`, backgroundColor: color }} className="h-full rounded-full transition-all duration-500" />
      </div>
      <span className="w-8 text-right text-xs font-medium text-slate-300">{score}</span>
    </div>
  );
}

// ── detail drawer ─────────────────────────────────────────────────────────────
function DetailDrawer({ biz, onClose }: { biz: Business; onClose: () => void }) {
  const socials = biz.social_accounts ?? [];
  const ws = biz.website_record;
  const ls = biz.lead_score;
  const allPhones = [biz.phone_number, ...(biz.website_phones ?? [])].filter(Boolean) as string[];

  const getSocialIcon = (platform: string) => {
    return <Globe className="h-4 w-4 text-slate-400" />;
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/40 backdrop-blur-sm transition-opacity" onClick={onClose}>
      <div
        className="relative h-full w-full max-w-[440px] overflow-y-auto bg-[#0f1115] shadow-2xl border-l border-[#1e293b] p-8 space-y-6 animate-in slide-in-from-right duration-300"
        onClick={e => e.stopPropagation()}
      >
        <button onClick={onClose} className="absolute right-6 top-6 text-slate-500 hover:text-slate-300 transition-colors">
          <XCircle className="h-6 w-6" />
        </button>

        <div className="pr-8">
          <h2 className="text-2xl font-semibold text-white tracking-tight">{biz.name}</h2>
          <div className="mt-2 flex items-center gap-2 text-sm text-teal-400">
            <Building2 className="h-4 w-4" />
            <span>{biz.category || 'Business'}</span>
          </div>
          {biz.address && (
            <div className="mt-2 flex items-start gap-2 text-sm text-slate-400">
              <MapPin className="h-4 w-4 shrink-0 mt-0.5" />
              <span>{biz.address}</span>
            </div>
          )}
        </div>

        {/* Scores */}
        {ls && (
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
              <Activity className="h-4 w-4" /> Lead Scores
            </div>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-slate-400">Digital Presence</span>
                </div>
                <ScoreBar score={ls.digital_presence_score} />
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-slate-400">Lead Opportunity</span>
                </div>
                <ScoreBar score={ls.lead_opportunity_score} />
              </div>
            </div>
          </div>
        )}

        {/* Contact */}
        <div className="glass-card p-5 space-y-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
            <Phone className="h-4 w-4" /> Contact Information
          </div>
          <div className="space-y-3">
            {allPhones.length > 0 && (
              <div className="flex gap-3">
                <Phone className="h-4 w-4 text-slate-500 shrink-0 mt-0.5" />
                <div className="space-y-1.5">
                  {allPhones.map(p => (
                    <a key={p} href={`tel:${p}`} className="block text-sm text-teal-400 hover:text-teal-300 transition-colors">{p}</a>
                  ))}
                </div>
              </div>
            )}
            {(biz.emails ?? []).length > 0 && (
              <div className="flex gap-3">
                <Mail className="h-4 w-4 text-slate-500 shrink-0 mt-0.5" />
                <div className="space-y-1.5">
                  {biz.emails.map(e => (
                    <div key={e.address} className="flex items-center gap-2">
                      <a href={`mailto:${e.address}`} className="text-sm text-indigo-400 hover:text-indigo-300 transition-colors">
                        {e.address}
                      </a>
                      {e.is_primary && <span className="rounded bg-indigo-500/20 px-1 text-[10px] text-indigo-300">Primary</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {biz.website && (
              <div className="flex gap-3">
                <Globe className="h-4 w-4 text-slate-500 shrink-0 mt-0.5" />
                <a href={biz.website} target="_blank" rel="noopener noreferrer" className="text-sm text-slate-300 hover:text-white transition-colors flex items-center gap-1.5">
                  {biz.website.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            )}
          </div>
        </div>

        {/* Social */}
        {socials.length > 0 && (
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
              <Zap className="h-4 w-4" /> Social Profiles
            </div>
            <div className="grid grid-cols-1 gap-2">
              {socials.map(s => (
                <a key={s.url} href={s.url} target="_blank" rel="noopener noreferrer"
                  className="flex items-center gap-3 rounded-lg border border-transparent p-2 text-sm text-slate-300 hover:bg-slate-800/50 hover:border-slate-700/50 transition-all">
                  {getSocialIcon(s.platform)}
                  <span className="capitalize font-medium">{s.platform}</span>
                  <ExternalLink className="ml-auto h-3 w-3 text-slate-500" />
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Website audit */}
        {ws && (
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
              <Activity className="h-4 w-4" /> Website Audit
            </div>
            <div className="flex flex-wrap gap-2">
              <Pill v={ws.ssl_enabled} label="SSL" />
              <Pill v={ws.mobile_viewport} label="Mobile" />
              <Pill v={ws.contact_page_found} label="Contact" />
              <Pill v={ws.google_analytics} label="Analytics" />
              <Pill v={ws.facebook_pixel} label="FB Pixel" />
              <Pill v={ws.robots_txt} label="robots.txt" />
              <Pill v={ws.sitemap_xml} label="Sitemap" />
            </div>
            <div className="pt-2 space-y-2 border-t border-slate-800/50">
              {ws.meta_title && <p className="text-xs text-slate-300"><span className="text-slate-500 block mb-0.5">Meta Title</span>{ws.meta_title}</p>}
              {ws.load_speed_ms && <p className="text-xs text-slate-300"><span className="text-slate-500 block mb-0.5">Load Speed</span>{ws.load_speed_ms}ms</p>}
            </div>
          </div>
        )}

        {/* Maps */}
        <a href={biz.google_maps_url} target="_blank" rel="noopener noreferrer"
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-slate-800 py-2.5 text-sm font-medium text-white hover:bg-slate-700 transition-colors">
          <MapPin className="h-4 w-4" />
          View on Google Maps
        </a>
      </div>
    </div>
  );
}

// ── leads table ────────────────────────────────────────────────────────────────
function LeadsTable({ businesses, jobId }: { businesses: Business[]; jobId: number }) {
  const [selected, setSelected] = useState<Business | null>(null);
  const [search, setSearch] = useState('');

  const filtered = businesses.filter(b =>
    `${b.name} ${b.category} ${b.address} ${b.phone_number}`.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <section className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-medium text-white tracking-tight">Leads</h2>
          <Badge color="slate">{businesses.length}</Badge>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search leads..."
              className="glass-input pl-9 w-64"
            />
          </div>
          <div className="flex gap-2">
            <a href={getExportUrl(jobId, 'csv')} className="glass-button bg-slate-800/50 hover:bg-slate-700 text-slate-300 border border-slate-700/50">
              <Download className="h-4 w-4" />
              CSV
            </a>
            <a href={getExportUrl(jobId, 'excel')} className="glass-button bg-slate-800/50 hover:bg-slate-700 text-slate-300 border border-slate-700/50">
              <Download className="h-4 w-4" />
              Excel
            </a>
          </div>
        </div>
      </div>

      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm text-left">
            <thead className="border-b border-[#1e293b] bg-[#0f1115]/50">
              <tr>
                {['Business', 'Category', 'Phone', 'Email', 'Website', 'Rating', 'Score', 'Priority', ''].map(h => (
                  <th key={h} className="px-5 py-3.5 text-xs font-semibold text-slate-400 tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e293b]/50 bg-[#15181e]">
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={8} className="py-16 text-center text-slate-500">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <Search className="h-8 w-8 opacity-20" />
                      <p>No leads found matching your search.</p>
                    </div>
                  </td>
                </tr>
              )}
              {filtered.map(b => {
                const phone = b.phone_number || b.website_phones?.[0] || '—';
                const email = b.emails?.find(e => e.is_primary)?.address || b.emails?.[0]?.address || '—';
                const score = b.lead_score?.lead_opportunity_score;
                const scoreColor = score == null ? 'slate' : score >= 70 ? 'green' : score >= 40 ? 'yellow' : 'red';
                const priority = score == null ? '—' : score >= 70 ? 'High' : score >= 40 ? 'Mid' : 'Low';

                return (
                  <tr key={b.id} 
                    className="group hover:bg-[#1e293b]/30 transition-colors cursor-pointer"
                    onClick={() => setSelected(b)}>
                    <td className="px-5 py-3.5">
                      <p className="font-medium text-slate-200 max-w-[200px] truncate">{b.name}</p>
                      {b.address && <p className="text-[11px] text-slate-500 truncate max-w-[200px] mt-0.5">{b.address}</p>}
                    </td>
                    <td className="px-5 py-3.5 text-slate-400 max-w-[140px] truncate">{b.category || '—'}</td>
                    <td className="px-5 py-3.5">
                      {phone !== '—'
                        ? <a href={`tel:${phone}`} onClick={e => e.stopPropagation()} className="text-teal-400/90 hover:text-teal-300 hover:underline whitespace-nowrap">{phone}</a>
                        : <span className="text-slate-600">—</span>}
                    </td>
                    <td className="px-5 py-3.5">
                      {email !== '—'
                        ? <a href={`mailto:${email}`} onClick={e => e.stopPropagation()} className="text-indigo-400/90 hover:text-indigo-300 hover:underline max-w-[180px] truncate block">{email}</a>
                        : <span className="text-slate-600">—</span>}
                    </td>
                    <td className="px-5 py-3.5">
                      {b.website
                        ? <a href={b.website} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}
                            className="text-slate-400 hover:text-white transition-colors max-w-[160px] truncate flex items-center gap-1.5">
                            {b.website.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                            <ExternalLink className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                          </a>
                        : <span className="text-slate-600">—</span>}
                    </td>
                    <td className="px-5 py-3.5 text-slate-400">
                      {b.rating ? (
                        <div className="flex items-center gap-1.5">
                          <span className="text-amber-400">★</span>
                          <span>{b.rating}</span>
                          <span className="text-slate-600 text-xs">({b.review_count ?? 0})</span>
                        </div>
                      ) : '—'}
                    </td>
                    <td className="px-5 py-3.5">
                      {score != null ? <span className="text-slate-300 font-medium">{score}</span> : <span className="text-slate-600">—</span>}
                    </td>
                    <td className="px-5 py-3.5">
                      {priority !== '—' ? <Badge color={scoreColor}>{priority}</Badge> : <span className="text-slate-600">—</span>}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <ChevronRight className="h-4 w-4 text-slate-600 group-hover:text-teal-500 transition-colors ml-auto" />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {selected && <DetailDrawer biz={selected} onClose={() => setSelected(null)} />}
    </section>
  );
}

// ── main page ──────────────────────────────────────────────────────────────────
export default function HomePage() {
  const [industry, setIndustry] = useState('Digital Marketing Agencies');
  const [location, setLocation] = useState('London');
  const [limit, setLimit] = useState(20);
  const [jobId, setJobId] = useState<number | null>(null);

  const createMutation = useMutation({
    mutationFn: createJob,
    onSuccess: d => setJobId(d.job_id),
  });

  const jobQuery = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => getJob(jobId as number),
    enabled: jobId !== null,
    refetchInterval: q => {
      const status = (q.state.data as { status?: string } | undefined)?.status;
      return status === 'completed' || status === 'failed' ? false : 2500;
    },
  });

  const businessesQuery = useQuery({
    queryKey: ['businesses', jobId],
    queryFn: () => getBusinesses(jobId as number),
    enabled: jobId !== null && jobQuery.data?.status === 'completed',
  });

  const status = jobQuery.data?.status as string | undefined;
  const statusColor = status === 'completed' ? 'green' : status === 'failed' ? 'red' : status === 'running' ? 'yellow' : 'slate';

  return (
    <main className="mx-auto max-w-7xl px-6 py-8">
      <div className="space-y-8">
        
        {/* Command Center */}
        <section className="glass-card p-6 md:p-8 relative overflow-hidden">
          {/* Subtle gradient background */}
          <div className="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 rounded-full bg-teal-500/5 blur-[100px] pointer-events-none" />
          
          <div className="relative z-10 max-w-3xl">
            <div className="mb-8">
              <h1 className="mt-4 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
                Discover local leads, automatically.
              </h1>
              <p className="mt-2 text-slate-400 text-sm sm:text-base leading-relaxed">
                Enter your target audience and location. LeadForge handles the Maps discovery, website analysis, contact extraction, and AI scoring.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <div className="sm:col-span-2">
                <input value={industry} onChange={e => setIndustry(e.target.value)} placeholder="Target Industry"
                  className="glass-input w-full h-11" />
              </div>
              <div className="sm:col-span-1">
                <input value={location} onChange={e => setLocation(e.target.value)} placeholder="City, Area"
                  className="glass-input w-full h-11" />
              </div>
              <div className="sm:col-span-1 flex gap-3">
                <input value={limit} onChange={e => setLimit(Number(e.target.value) || 10)} type="number" min={1} max={500} placeholder="Max"
                  className="glass-input w-20 h-11 text-center" />
                <button onClick={() => createMutation.mutate({ industry, location, limit })}
                  disabled={createMutation.isPending}
                  className="glass-button flex-1 bg-white text-slate-900 hover:bg-slate-200 disabled:opacity-50 disabled:cursor-not-allowed">
                  {createMutation.isPending ? (
                    <RotateCcw className="h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      <Play className="h-4 w-4 fill-slate-900" />
                      Run
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Job status bar */}
            {jobId && (
              <div className="mt-6 flex flex-wrap items-center gap-4 rounded-lg bg-[#0f1115] border border-[#1e293b] px-4 py-3 text-sm animate-in fade-in slide-in-from-top-2">
                <Badge color={statusColor}>{status ?? 'queued'}</Badge>
                
                {jobQuery.data && (
                  <div className="flex flex-1 items-center gap-3 ml-2">
                    <div className="h-1.5 flex-1 max-w-xs rounded-full bg-slate-800 overflow-hidden">
                      <div className="h-full rounded-full bg-teal-500 transition-all duration-500" style={{ width: `${jobQuery.data.progress}%` }} />
                    </div>
                    <span className="text-xs font-medium text-slate-400">{jobQuery.data.progress}%</span>
                  </div>
                )}
                
                {jobQuery.data?.error_message && (
                  <span className="text-rose-400 text-xs flex items-center gap-1.5">
                    <AlertCircle className="h-3.5 w-3.5" />
                    {jobQuery.data.error_message}
                  </span>
                )}
                
                <button onClick={() => setJobId(null)} className="ml-auto flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-300 transition-colors">
                  <RotateCcw className="h-3 w-3" /> Reset
                </button>
              </div>
            )}
          </div>
        </section>

        {/* Results */}
        {businessesQuery.isPending && jobQuery.data?.status === 'completed' && (
          <div className="flex flex-col items-center justify-center py-24 text-slate-500">
            <RotateCcw className="h-8 w-8 animate-spin text-slate-700 mb-4" />
            <p className="text-sm font-medium">Loading intelligence data...</p>
          </div>
        )}

        {businessesQuery.data && businessesQuery.data.length > 0 && jobId && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <LeadsTable businesses={businessesQuery.data} jobId={jobId} />
          </div>
        )}

        {!jobId && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="h-16 w-16 rounded-full bg-[#1e293b]/50 flex items-center justify-center mb-4">
              <Search className="h-6 w-6 text-slate-500" />
            </div>
            <h3 className="text-lg font-medium text-slate-300">Ready to discover</h3>
            <p className="mt-1 text-sm text-slate-500 max-w-sm">Configure your search parameters above to begin extracting local leads.</p>
          </div>
        )}
      </div>
    </main>
  );
}
