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
  Building2,
  ListFilter,
  Sparkles,
  Rocket,
  Share2,
  UserPlus,
  ArrowRight,
  Star,
  ShieldCheck,
  Smartphone,
  Eye,
  FileText,
  Clock
} from 'lucide-react';
import {
  Business,
  createJob,
  getBusinesses,
  getExportUrl,
  getJob,
} from '@/lib/api';

// ── helper classes ───────────────────────────────────────────────────────────
function cls(...c: (string | false | undefined)[]) { return c.filter(Boolean).join(' '); }

const formatCategory = (cat: string | null) => {
  if (!cat) return '—';
  return cat
    .replace(/[\uE000-\uF8FF\u0000-\u001F\u007F-\u009F\uFFFD\u2022\u00B7]/g, '')
    .replace(/[·•]/g, '')
    .trim();
};

// ── custom premium badge ──────────────────────────────────────────────────────
function Badge({ children, color = 'slate' }: { children: React.ReactNode; color?: string }) {
  const map: Record<string, string> = {
    green: 'bg-[#00885d]/10 text-[#4edea3] border-[#00885d]/30',
    red: 'bg-[#93000a]/10 text-[#ffb4ab] border-[#93000a]/30',
    yellow: 'bg-[#00a2e6]/10 text-[#89ceff] border-[#00a2e6]/30',
    slate: 'bg-white/5 text-[#c7c4d7] border-white/10',
  };
  return (
    <span className={cls('inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase', map[color] ?? map.slate)}>
      {children}
    </span>
  );
}

// ── premium website audit pill ────────────────────────────────────────────────
function AuditPill({ active, label, icon: Icon }: { active: boolean | undefined; label: string; icon: any }) {
  return (
    <div className={cls(
      "flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all duration-200",
      active 
        ? "bg-[#00885d]/10 text-[#4edea3] border-[#00885d]/30" 
        : "bg-white/[0.02] text-[#c7c4d7]/50 border-white/5"
    )}>
      <Icon className={cls("h-3.5 w-3.5", active ? "text-[#4edea3]" : "text-[#c7c4d7]/30")} />
      <span>{label}</span>
      {active ? (
        <span className="ml-1 text-[9px] px-1 bg-[#4edea3]/20 rounded font-bold">ON</span>
      ) : (
        <span className="ml-1 text-[9px] px-1 bg-white/5 rounded font-bold">OFF</span>
      )}
    </div>
  );
}

// ── lead opportunity score bar ────────────────────────────────────────────────
function ScoreBar({ score, max = 100 }: { score: number; max?: number }) {
  const pct = Math.min(100, (score / max) * 100);
  const colorClass = pct >= 70 ? 'bg-[#4edea3]' : pct >= 40 ? 'bg-[#89ceff]' : 'bg-[#ffb4ab]';
  return (
    <div className="flex items-center gap-3 w-full">
      <span className="w-8 font-mono-data text-xs font-bold text-white">{score}</span>
      <div className="h-2 flex-1 rounded-full bg-white/5 overflow-hidden">
        <div 
          style={{ width: `${pct}%` }} 
          className={cls("h-full rounded-full transition-all duration-1000 ease-out", colorClass)} 
        />
      </div>
    </div>
  );
}

// ── detail drawer / right slide-in inspection panel ───────────────────────────
function DetailDrawer({ biz, onClose }: { biz: Business; onClose: () => void }) {
  const socials = biz.social_accounts ?? [];
  const ws = biz.website_record;
  const ls = biz.lead_score;
  const allPhones = [biz.phone_number, ...(biz.website_phones ?? [])].filter(Boolean) as string[];

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm transition-opacity duration-300" onClick={onClose}>
      <div
        className="relative h-full w-full max-w-[420px] overflow-y-auto bg-[#0f0f12]/95 backdrop-blur-xl border-l border-white/10 p-6 flex flex-col justify-between shadow-2xl animate-in slide-in-from-right duration-300"
        onClick={e => e.stopPropagation()}
      >
        <div>
          {/* Close button */}
          <div className="flex justify-end mb-6">
            <button 
              onClick={onClose} 
              className="w-8 h-8 rounded-full border border-white/10 flex items-center justify-center text-[#c7c4d7] hover:text-white hover:bg-white/5 transition-all"
            >
              <XCircle className="h-5 w-5" />
            </button>
          </div>

          <div className="mb-6">
            <h3 className="font-display-lg text-[28px] font-bold text-white mb-2 leading-tight tracking-tight">
              {biz.name}
            </h3>
            <div className="flex items-center gap-2 text-[#4edea3] font-label-caps text-[11px] font-semibold tracking-wider uppercase mb-4">
              <Building2 className="h-4 w-4" />
              <span>{formatCategory(biz.category) || 'Business'} • {biz.business_status || 'Open'}</span>
            </div>
            {biz.address && (
              <div className="flex items-start gap-2 text-sm text-[#c7c4d7]/70 leading-relaxed">
                <MapPin className="h-4 w-4 shrink-0 text-[#c0c1ff] mt-0.5" />
                <span>{biz.address}</span>
              </div>
            )}
          </div>

          {/* Lead Scores Card */}
          {ls && (
            <div className="bg-[#131314] border border-white/5 rounded-xl p-5 mb-6 transition-all duration-200 hover:border-white/10">
              <div className="flex items-center gap-2 mb-4 text-[#c7c4d7] border-b border-white/5 pb-2">
                <Activity className="h-4 w-4 text-[#c0c1ff]" />
                <h4 className="font-label-caps text-[11px] font-bold uppercase tracking-wider">Lead Intelligence</h4>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-[#c7c4d7]/70">Digital Presence</span>
                    <span className="text-xs font-bold text-[#4edea3]">{ls.digital_presence_score}</span>
                  </div>
                  <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-[#4edea3] rounded-full transition-all duration-1000 ease-out" 
                      style={{ width: `${ls.digital_presence_score}%` }} 
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-[#c7c4d7]/70">Opportunity Score</span>
                    <span className="text-xs font-bold text-[#89ceff]">{ls.lead_opportunity_score}</span>
                  </div>
                  <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-[#89ceff] rounded-full transition-all duration-1000 ease-out" 
                      style={{ width: `${ls.lead_opportunity_score}%` }} 
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Contact Information Card */}
          <div className="bg-[#131314] border border-white/5 rounded-xl p-5 mb-6 transition-all duration-200 hover:border-white/10">
            <div className="flex items-center gap-2 mb-4 text-[#c7c4d7] border-b border-white/5 pb-2">
              <Phone className="h-4 w-4 text-[#c0c1ff]" />
              <h4 className="font-label-caps text-[11px] font-bold uppercase tracking-wider">Contact & Socials</h4>
            </div>
            <div className="space-y-4">
              {allPhones.length > 0 && (
                <div className="flex gap-3">
                  <Phone className="h-4 w-4 text-[#c7c4d7]/40 shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    {allPhones.map(p => (
                      <a key={p} href={`tel:${p}`} className="block text-sm text-[#4edea3] hover:text-[#4edea3]/85 transition-colors font-mono-data">{p}</a>
                    ))}
                  </div>
                </div>
              )}
              {biz.website && (
                <div className="flex gap-3 items-center border-t border-white/5 pt-3">
                  <Globe className="h-4 w-4 text-[#c7c4d7]/40 shrink-0" />
                  <a href={biz.website} target="_blank" rel="noopener noreferrer" className="text-sm text-[#c7c4d7] hover:text-[#c0c1ff] transition-colors flex items-center gap-1.5">
                    {biz.website.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                    <ExternalLink className="h-3.5 w-3.5 text-[#c7c4d7]/40" />
                  </a>
                </div>
              )}
              {(biz.emails ?? []).length > 0 && (
                <div className="flex gap-3 border-t border-white/5 pt-3">
                  <Mail className="h-4 w-4 text-[#c7c4d7]/40 shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    {biz.emails.map(e => (
                      <div key={e.address} className="flex items-center gap-2">
                        <a href={`mailto:${e.address}`} className="text-sm text-[#89ceff] hover:text-[#89ceff]/85 transition-colors">
                          {e.address}
                        </a>
                        {e.is_primary && <span className="rounded bg-white/5 px-1 py-0.25 text-[9px] text-[#c7c4d7]/60">Primary</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {socials.length > 0 && (
                <div className="border-t border-white/5 pt-3 space-y-2">
                  <span className="text-xs text-[#c7c4d7]/50 block mb-1">Social Accounts</span>
                  <div className="grid grid-cols-2 gap-2">
                    {socials.map(s => (
                      <a 
                        key={s.url} 
                        href={s.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 rounded-lg border border-white/5 bg-white/[0.01] p-2 text-xs text-[#c7c4d7] hover:bg-white/[0.04] transition-all"
                      >
                        <Globe className="h-3.5 w-3.5 text-[#c0c1ff]" />
                        <span className="capitalize font-semibold truncate">{s.platform}</span>
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Website Audit Card */}
          {ws && (
            <div className="bg-[#131314] border border-white/5 rounded-xl p-5 mb-6 transition-all duration-200 hover:border-white/10">
              <div className="flex items-center gap-2 mb-4 text-[#c7c4d7] border-b border-white/5 pb-2">
                <ShieldCheck className="h-4 w-4 text-[#c0c1ff]" />
                <h4 className="font-label-caps text-[11px] font-bold uppercase tracking-wider">Website Quality Audit</h4>
              </div>
              <div className="grid grid-cols-2 gap-2 mb-4">
                <AuditPill active={ws.ssl_enabled} label="SSL Secure" icon={ShieldCheck} />
                <AuditPill active={ws.mobile_viewport} label="Mobile Ready" icon={Smartphone} />
                <AuditPill active={ws.contact_page_found} label="Contact Page" icon={Mail} />
                <AuditPill active={ws.google_analytics} label="GA Analytics" icon={Eye} />
              </div>
              <div className="space-y-3 pt-3 border-t border-white/5">
                {ws.meta_title && (
                  <div>
                    <span className="text-[10px] text-[#c7c4d7]/50 uppercase font-semibold block mb-0.5">Meta Title</span>
                    <p className="text-xs text-[#c7c4d7] line-clamp-2 leading-relaxed">{ws.meta_title}</p>
                  </div>
                )}
                {ws.load_speed_ms && (
                  <div className="flex justify-between items-center bg-white/[0.02] p-2 rounded-lg border border-white/5">
                    <span className="text-xs text-[#c7c4d7]/70 flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5 text-[#c0c1ff]" /> Page Speed
                    </span>
                    <span className="font-mono-data text-xs font-bold text-[#4edea3]">{ws.load_speed_ms}ms</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Convert Lead Action Footer */}
        <div className="pt-4 border-t border-white/5">
          <div className="grid grid-cols-2 gap-2 mb-4">
            <button className="flex flex-col items-center justify-center gap-1 py-2 px-3 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-all active:scale-[0.98]">
              <UserPlus className="h-4 w-4 text-[#4edea3]" />
              <span className="font-label-caps text-[9px] tracking-wider text-[#c7c4d7]">Add Lead</span>
            </button>
            <button className="flex flex-col items-center justify-center gap-1 py-2 px-3 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-all active:scale-[0.98]">
              <Share2 className="h-4 w-4 text-[#c0c1ff]" />
              <span className="font-label-caps text-[9px] tracking-wider text-[#c7c4d7]">Share</span>
            </button>
          </div>
          <button className="w-full py-3 bg-[#c0c1ff] text-[#0d0096] font-bold text-sm rounded-xl flex items-center justify-center gap-2 hover:brightness-110 active:scale-[0.98] transition-all shadow-lg shadow-[#c0c1ff]/20">
            Convert Lead
            <Rocket className="h-4 w-4 fill-[#0d0096]/20" />
          </button>
        </div>
      </div>
    </div>
  );
}

// ── leads table component ─────────────────────────────────────────────────────
function LeadsTable({ businesses, jobId }: { businesses: Business[]; jobId: number }) {
  const [selected, setSelected] = useState<Business | null>(null);
  const [search, setSearch] = useState('');

  const filtered = businesses.filter(b =>
    `${b.name} ${b.category} ${b.address} ${b.phone_number}`.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <section className="bg-[#131314] rounded-xl border border-white/5 overflow-hidden transition-all duration-200 glow-card animate-blur-reveal" style={{ animationDelay: '400ms' }}>
      <div className="px-lg py-md border-b border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#201f20]/20">
        <div className="flex items-center gap-2">
          <h3 className="font-headline-sm text-lg text-white">Active Leads</h3>
          <span className="bg-white/5 px-2 py-0.5 rounded text-mono-data text-xs text-[#c7c4d7]">
            {businesses.length} Total
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#c7c4d7]/50" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search leads..."
              className="bg-[#0e0e0f] border border-[#464554]/30 rounded-lg pl-9 pr-4 py-1.5 text-xs text-white placeholder-[#c7c4d7]/40 focus:outline-none focus:border-[#c0c1ff] transition-all w-64"
            />
          </div>
          <div className="flex gap-2">
            <a 
              href={getExportUrl(jobId, 'csv')} 
              className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs font-bold text-[#c7c4d7] hover:bg-white/10 transition-colors flex items-center gap-1.5"
            >
              <Download className="h-3.5 w-3.5" /> CSV
            </a>
            <a 
              href={getExportUrl(jobId, 'excel')} 
              className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs font-bold text-[#c7c4d7] hover:bg-white/10 transition-colors flex items-center gap-1.5"
            >
              <Download className="h-3.5 w-3.5" /> Excel
            </a>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-white/[0.01] border-b border-white/5 font-label-caps text-[10px] text-[#c7c4d7]/60 uppercase tracking-wider">
              <th className="px-lg py-4 font-semibold">Business</th>
              <th className="px-lg py-4 font-semibold">Category</th>
              <th className="px-lg py-4 font-semibold">Contact Info</th>
              <th className="px-lg py-4 font-semibold">Website</th>
              <th className="px-lg py-4 font-semibold">Rating</th>
              <th className="px-lg py-4 font-semibold">Score</th>
              <th className="px-lg py-4 font-semibold">Priority</th>
              <th className="px-lg py-4 font-semibold"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} className="py-16 text-center text-[#c7c4d7]/50">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <Search className="h-8 w-8 opacity-20" />
                    <p className="text-sm">No leads found matching your search.</p>
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
                <tr 
                  key={b.id} 
                  className="hover:bg-[#c0c1ff]/5 transition-colors cursor-pointer group"
                  onClick={() => setSelected(b)}
                >
                  <td className="px-lg py-4 relative">
                    <div className="absolute left-0 top-1/4 bottom-1/4 w-[2px] bg-[#c0c1ff] opacity-0 group-hover:opacity-100 transition-opacity" />
                    <p className="font-semibold text-white max-w-[200px] truncate">{b.name}</p>
                    {b.address && <p className="text-[11px] text-[#c7c4d7]/50 truncate max-w-[200px] mt-0.5">{b.address}</p>}
                  </td>
                  <td className="px-lg py-4">
                    <span className="text-xs text-[#c7c4d7]/70 font-medium whitespace-nowrap block max-w-[130px] truncate">
                      {formatCategory(b.category)}
                    </span>
                  </td>
                  <td className="px-lg py-4">
                    {phone !== '—' ? (
                      <a 
                        href={`tel:${phone}`} 
                        onClick={e => e.stopPropagation()} 
                        className="text-[#4edea3] hover:text-[#4edea3]/85 hover:underline whitespace-nowrap font-mono-data text-xs"
                      >
                        {phone}
                      </a>
                    ) : (
                      <span className="text-white/20">—</span>
                    )}
                    {email !== '—' ? (
                      <a 
                        href={`mailto:${email}`} 
                        onClick={e => e.stopPropagation()} 
                        className="text-[#89ceff] hover:text-[#89ceff]/85 hover:underline max-w-[180px] truncate block text-xs mt-0.5"
                      >
                        {email}
                      </a>
                    ) : (
                      <span className="text-white/20 block text-xs mt-0.5">—</span>
                    )}
                  </td>
                  <td className="px-lg py-4">
                    {b.website ? (
                      <a 
                        href={b.website} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        onClick={e => e.stopPropagation()}
                        className="text-[#c7c4d7] hover:text-[#c0c1ff] transition-colors max-w-[160px] truncate flex items-center gap-1.5 text-xs decoration-white/10 underline underline-offset-4"
                      >
                        {b.website.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                        <ExternalLink className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </a>
                    ) : (
                      <span className="text-white/20">—</span>
                    )}
                  </td>
                  <td className="px-lg py-4">
                    {b.rating ? (
                      <div className="flex items-center gap-1">
                        <Star className="h-3.5 w-3.5 text-yellow-400 fill-yellow-400" />
                        <span className="font-mono-data text-xs text-white">{b.rating}</span>
                        <span className="text-[#c7c4d7]/40 text-[10px]">({b.review_count ?? 0})</span>
                      </div>
                    ) : (
                      <span className="text-white/20">—</span>
                    )}
                  </td>
                  <td className="px-lg py-4">
                    {score != null ? (
                      <div className="flex items-center gap-2">
                        <span className="font-mono-data font-bold text-white text-xs">{score}</span>
                        <div className="w-16 h-1.5 bg-white/5 rounded-full overflow-hidden hidden sm:block">
                          <div 
                            className="h-full lead-gradient-bar" 
                            style={{ width: `${score}%` }} 
                          />
                        </div>
                      </div>
                    ) : (
                      <span className="text-white/20">—</span>
                    )}
                  </td>
                  <td className="px-lg py-4">
                    {priority !== '—' ? (
                      <Badge color={scoreColor}>{priority}</Badge>
                    ) : (
                      <span className="text-white/20">—</span>
                    )}
                  </td>
                  <td className="px-lg py-4 text-right">
                    <ChevronRight className="h-4 w-4 text-[#c7c4d7]/40 group-hover:text-[#c0c1ff] group-hover:translate-x-0.5 transition-all ml-auto" />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="px-lg py-3 border-t border-white/5 flex items-center justify-between bg-white/[0.01]">
        <div className="text-xs text-[#c7c4d7]/50">
          Showing 1 to {filtered.length} of {filtered.length} leads
        </div>
      </div>

      {selected && <DetailDrawer biz={selected} onClose={() => setSelected(null)} />}
    </section>
  );
}

// ── main page ────────────────────────────────────────────────────────────────
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

  const status = jobQuery.data?.status as string | undefined;
  const statusColor = status === 'completed' ? 'green' : status === 'failed' ? 'red' : status === 'running' ? 'yellow' : 'slate';

  const businessesQuery = useQuery({
    queryKey: ['businesses', jobId, status],
    queryFn: () => getBusinesses(jobId as number),
    enabled: jobId !== null,
    refetchInterval: () => {
      return status === 'running' ? 2500 : false;
    },
  });

  const leads = businessesQuery.data ?? [];
  
  // Real-time statistics calculations
  const totalLeads = leads.length;
  const avgOpportunityScore = totalLeads > 0 
    ? Math.round(leads.reduce((acc, b) => acc + (b.lead_score?.lead_opportunity_score ?? 0), 0) / totalLeads * 10) / 10
    : 0;
  const totalEmails = leads.reduce((acc, b) => acc + (b.emails?.length ?? 0), 0);
  const highPriorityCount = leads.filter(b => (b.lead_score?.lead_opportunity_score ?? 0) >= 70).length;

  const getProgressMessage = (progress: number, status: string) => {
    if (status === 'queued') return 'Job queued... Waiting for execution slots';
    if (status === 'failed') return 'Discovery process failed';
    if (status === 'completed') return 'Discovery complete!';
    if (progress === 0) return 'Launching headless Playwright context...';
    if (progress <= 30) return `Extracting business profiles from Google Maps (${progress}%)...`;
    if (progress <= 60) return `Finalizing Google Maps raw data collection (${progress}%)...`;
    if (progress <= 80) return `Concurrently auditing business websites for SSL, mobile and speed (${progress}%)...`;
    return `Enriching contact info & scoring leads with AI engine (${progress}%)...`;
  };

  return (
    <div className="space-y-lg animate-in fade-in duration-500">
      
      {/* Command Center */}
      <section className="bg-[#0F0F12] border border-white/5 rounded-xl p-6 md:p-xl relative overflow-hidden group glow-card animate-blur-reveal">
        <div className="absolute -right-20 -top-20 w-96 h-96 bg-[#8083ff]/10 blur-[100px] rounded-full pointer-events-none" />
        
        <div className="max-w-4xl relative z-10">
          <div className="mb-6">
            <h2 className="font-display-lg text-3xl md:text-[40px] font-bold mb-2 leading-tight tracking-tight">
              <span className="shiny-text">Discover local leads, </span>
              <span className="text-[#c0c1ff] italic font-extrabold">automatically.</span>
            </h2>
            <p className="font-body-md text-[#c7c4d7]/70 leading-relaxed max-w-2xl">
              Enter target parameters to trigger deep discovery. LeadForge automates Google Maps profiling, page-by-page website audit, email extraction, and premium lead scoring.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
            <div className="md:col-span-4">
              <label className="font-label-caps text-[10px] mb-1.5 block text-[#c7c4d7]/60 tracking-wider font-semibold uppercase">Target Industry</label>
              <div className="bg-[#0e0e0f] border border-[#464554]/30 p-2.5 rounded-lg flex items-center gap-2 focus-within:border-[#c0c1ff]/60 transition-colors">
                <Building2 className="h-4 w-4 text-[#c0c1ff]" />
                <input 
                  value={industry} 
                  onChange={e => setIndustry(e.target.value)} 
                  placeholder="e.g. Restaurants, Cafe"
                  className="bg-transparent border-none p-0 focus:ring-0 text-xs text-white w-full placeholder-[#c7c4d7]/30"
                  type="text"
                />
              </div>
            </div>

            <div className="md:col-span-4">
              <label className="font-label-caps text-[10px] mb-1.5 block text-[#c7c4d7]/60 tracking-wider font-semibold uppercase">Location</label>
              <div className="bg-[#0e0e0f] border border-[#464554]/30 p-2.5 rounded-lg flex items-center gap-2 focus-within:border-[#c0c1ff]/60 transition-colors">
                <MapPin className="h-4 w-4 text-[#c0c1ff]" />
                <input 
                  value={location} 
                  onChange={e => setLocation(e.target.value)} 
                  placeholder="e.g. London, New York"
                  className="bg-transparent border-none p-0 focus:ring-0 text-xs text-white w-full placeholder-[#c7c4d7]/30"
                  type="text"
                />
              </div>
            </div>

            <div className="md:col-span-2">
              <label className="font-label-caps text-[10px] mb-1.5 block text-[#c7c4d7]/60 tracking-wider font-semibold uppercase">Limit</label>
              <div className="bg-[#0e0e0f] border border-[#464554]/30 p-2.5 rounded-lg flex items-center gap-2 focus-within:border-[#c0c1ff]/60 transition-colors">
                <ListFilter className="h-4 w-4 text-[#c0c1ff]" />
                <input 
                  value={limit} 
                  onChange={e => setLimit(Number(e.target.value) || 10)} 
                  type="number" 
                  min={1} 
                  max={500} 
                  placeholder="Max"
                  className="bg-transparent border-none p-0 focus:ring-0 text-xs text-white w-full placeholder-[#c7c4d7]/30"
                />
              </div>
            </div>

            <button 
              onClick={() => createMutation.mutate({ industry, location, limit })}
              disabled={createMutation.isPending || (status === 'running' || status === 'queued')}
              className="md:col-span-2 bg-[#c0c1ff] text-[#0d0096] py-3 rounded-lg font-bold font-label-caps text-[11px] tracking-wider uppercase flex items-center justify-center gap-2 hover:brightness-110 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-[#c0c1ff]/10"
            >
              {createMutation.isPending ? (
                <RotateCcw className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Play className="h-4 w-4 fill-[#0d0096]" />
                  RUN DISCOVERY
                </>
              )}
            </button>
          </div>

          {/* Job status & live sub-task reporting */}
          {jobId && (
            <div className="mt-6 bg-white/[0.02] border border-white/5 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 animate-in fade-in slide-in-from-top-2">
              <div className="flex flex-1 items-center gap-3">
                <Badge color={statusColor}>{status ?? 'queued'}</Badge>
                
                {jobQuery.data && (
                  <div className="flex flex-1 items-center gap-3">
                    <div className="h-2 flex-1 max-w-md bg-white/5 rounded-full overflow-hidden relative">
                      <div 
                        className={cls(
                          "h-full lead-gradient-bar transition-all duration-500 rounded-full",
                          status === 'running' && "animate-pulse"
                        )} 
                        style={{ width: `${jobQuery.data.progress}%` }} 
                      />
                    </div>
                    <span className="font-mono-data text-xs text-white font-bold">{jobQuery.data.progress}%</span>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between md:justify-end gap-4 border-t md:border-t-0 border-white/5 pt-3 md:pt-0">
                <span className="text-xs text-[#c7c4d7]/70 italic font-semibold">
                  {getProgressMessage(jobQuery.data?.progress ?? 0, status ?? 'queued')}
                </span>
                <button 
                  onClick={() => setJobId(null)} 
                  className="flex items-center gap-1.5 text-xs font-bold text-[#c7c4d7]/40 hover:text-white transition-colors"
                >
                  <RotateCcw className="h-3.5 w-3.5" /> Reset
                </button>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Dynamic Results Dashboard */}
      {businessesQuery.isPending && jobQuery.data?.status === 'completed' && (
        <div className="flex flex-col items-center justify-center py-24 text-[#c7c4d7]/50">
          <RotateCcw className="h-8 w-8 animate-spin text-[#c0c1ff] mb-4" />
          <p className="text-sm font-semibold tracking-wide">Syncing extracted intelligence database...</p>
        </div>
      )}

      {leads.length > 0 && jobId && (
        <div className="space-y-lg animate-in fade-in duration-500">
          {/* Bento Stats Section */}
          <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-[#0F0F12] border border-white/5 p-5 rounded-xl flex items-center gap-4 glow-card animate-blur-reveal transition-all duration-200" style={{ animationDelay: '100ms' }}>
              <div className="w-12 h-12 rounded-full bg-[#c0c1ff]/10 flex items-center justify-center text-[#c0c1ff]">
                <Activity className="h-6 w-6" />
              </div>
              <div>
                <div className="text-[#c7c4d7]/50 font-label-caps text-[10px] tracking-wider uppercase font-semibold">Average Lead Opportunity</div>
                <div className="text-2xl font-bold text-white tracking-tight">{avgOpportunityScore}%</div>
              </div>
            </div>

            <div className="bg-[#0F0F12] border border-white/5 p-5 rounded-xl flex items-center gap-4 glow-card animate-blur-reveal transition-all duration-200" style={{ animationDelay: '200ms' }}>
              <div className="w-12 h-12 rounded-full bg-[#4edea3]/10 flex items-center justify-center text-[#4edea3]">
                <Mail className="h-6 w-6" />
              </div>
              <div>
                <div className="text-[#c7c4d7]/50 font-label-caps text-[10px] tracking-wider uppercase font-semibold">Contact Details Found</div>
                <div className="text-2xl font-bold text-white tracking-tight">{totalEmails} Emails / Socials</div>
              </div>
            </div>

            <div className="bg-[#0F0F12] border border-white/5 p-5 rounded-xl flex items-center gap-4 glow-card animate-blur-reveal transition-all duration-200" style={{ animationDelay: '300ms' }}>
              <div className="w-12 h-12 rounded-full bg-[#89ceff]/10 flex items-center justify-center text-[#89ceff]">
                <Sparkles className="h-6 w-6" />
              </div>
              <div>
                <div className="text-[#c7c4d7]/50 font-label-caps text-[10px] tracking-wider uppercase font-semibold">High Priority Opportunities</div>
                <div className="text-2xl font-bold text-white tracking-tight">{highPriorityCount} Leads</div>
              </div>
            </div>
          </section>

          {/* Active Leads Table */}
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <LeadsTable businesses={leads} jobId={jobId} />
          </div>
        </div>
      )}

      {!jobId && (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="h-16 w-16 rounded-full bg-white/5 border border-white/10 flex items-center justify-center mb-4 text-[#c0c1ff]/60">
            <Search className="h-6 w-6" />
          </div>
          <h3 className="text-lg font-bold text-white">Prospector Ready</h3>
          <p className="mt-2 text-sm text-[#c7c4d7]/50 max-w-sm">Enter search parameters above to initiate Google Maps agent discovery & enrichment.</p>
        </div>
      )}
    </div>
  );
}
