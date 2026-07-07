'use client';

import { useEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Search,
  Download,
  ExternalLink,
  MapPin,
  Phone,
  Mail,
  Globe,
  XCircle,
  ChevronRight,
  Activity,
  Play,
  RotateCcw,
  Building2,
  ListFilter,
  Sparkles,
  ShieldCheck,
  Clock,
  Trash2,
  Network,
  Briefcase,
  MessageSquare,
  TrendingUp,
  Rocket,
  Cat,
  GitBranch,
  Star,
  UserCheck,
  Send,
  Users
} from 'lucide-react';
import {
  createSocialSearch,
  deleteSocialSearch,
  getSocialExportUrl,
  getSocialLeads,
  listSocialSearches,
  SocialLead,
  SocialSearch
} from '@/lib/social-api';

function cls(...c: (string | false | undefined)[]) { return c.filter(Boolean).join(' '); }

function Badge({ children, color = 'slate' }: { children: React.ReactNode; color?: string }) {
  const map: Record<string, string> = {
    green: 'bg-[#00885d]/10 text-[#4edea3] border-[#00885d]/30',
    red: 'bg-[#93000a]/10 text-[#ffb4ab] border-[#93000a]/30',
    yellow: 'bg-[#00a2e6]/10 text-[#89ceff] border-[#00a2e6]/30',
    slate: 'bg-white/5 text-[#c7c4d7] border-white/10',
    indigo: 'bg-[#5856d6]/10 text-[#afacff] border-[#5856d6]/30',
  };
  return (
    <span className={cls('inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase', map[color] ?? map.slate)}>
      {children}
    </span>
  );
}

function ScoreBar({ score, max = 100 }: { score: number; max?: number }) {
  const pct = Math.min(100, (score / max) * 100);
  const colorClass = pct >= 70 ? 'bg-[#4edea3]' : pct >= 40 ? 'bg-[#89ceff]' : 'bg-[#ffb4ab]';
  return (
    <div className="flex items-center gap-3 w-full font-mono-data">
      <span className="w-8 text-xs font-bold text-white">{score}</span>
      <div className="h-2 flex-1 rounded-full bg-white/5 overflow-hidden">
        <div 
          style={{ width: `${pct}%` }} 
          className={cls("h-full rounded-full transition-all duration-1000 ease-out", colorClass)} 
        />
      </div>
    </div>
  );
}

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
        <span className="ml-1 text-[9px] px-1 bg-[#4edea3]/20 rounded font-bold text-[#4edea3]">ON</span>
      ) : (
        <span className="ml-1 text-[9px] px-1 bg-white/5 rounded font-bold text-[#c7c4d7]/40">OFF</span>
      )}
    </div>
  );
}

// ── detail drawer / right slide-in inspection panel ───────────────────────────
function DetailDrawer({ lead, onClose }: { lead: SocialLead; onClose: () => void }) {
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
              {lead.name}
            </h3>
            <div className="flex items-center gap-2 text-[#c0c1ff] font-label-caps text-[11px] font-semibold tracking-wider uppercase mb-4">
              <Network className="h-4 w-4" />
              <span>{lead.source_platform} • Confidence {lead.confidence_score}%</span>
            </div>
            {lead.description && (
              <p className="text-sm text-[#c7c4d7]/70 leading-relaxed mb-4 italic">
                "{lead.description}"
              </p>
            )}
            {(lead.city || lead.country) && (
              <div className="flex items-start gap-2 text-sm text-[#c7c4d7]/70 leading-relaxed">
                <MapPin className="h-4 w-4 shrink-0 text-[#c0c1ff] mt-0.5" />
                <span>{[lead.city, lead.state, lead.country].filter(Boolean).join(', ')}</span>
              </div>
            )}
          </div>

          {/* Lead Scores Card */}
          <div className="bg-[#131314] border border-white/5 rounded-xl p-5 mb-6 transition-all duration-200 hover:border-white/10">
            <div className="flex items-center gap-2 mb-4 text-[#c7c4d7] border-b border-white/5 pb-2">
              <Activity className="h-4 w-4 text-[#c0c1ff]" />
              <h4 className="font-label-caps text-[11px] font-bold uppercase tracking-wider">Lead Intelligence</h4>
            </div>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs text-[#c7c4d7]/70">Digital Presence</span>
                  <span className="text-xs font-bold text-[#4edea3]">{lead.digital_score}</span>
                </div>
                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-[#4edea3] rounded-full transition-all duration-1000 ease-out" 
                    style={{ width: `${lead.digital_score}%` }} 
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs text-[#c7c4d7]/70">Opportunity Score</span>
                  <span className="text-xs font-bold text-[#89ceff]">{lead.lead_score}</span>
                </div>
                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-[#89ceff] rounded-full transition-all duration-1000 ease-out" 
                    style={{ width: `${lead.lead_score}%` }} 
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Contact Information Card */}
          <div className="bg-[#131314] border border-white/5 rounded-xl p-5 mb-6 transition-all duration-200 hover:border-white/10">
            <div className="flex items-center gap-2 mb-4 text-[#c7c4d7] border-b border-white/5 pb-2">
              <Phone className="h-4 w-4 text-[#c0c1ff]" />
              <h4 className="font-label-caps text-[11px] font-bold uppercase tracking-wider">Contact & Socials</h4>
            </div>
            <div className="space-y-4 font-mono-data">
              {lead.phone && (
                <div className="flex gap-3">
                  <Phone className="h-4 w-4 text-[#c7c4d7]/40 shrink-0 mt-0.5" />
                  <a href={`tel:${lead.phone}`} className="text-sm text-[#4edea3] hover:text-[#4edea3]/85 transition-colors">{lead.phone}</a>
                </div>
              )}
              {lead.website && (
                <div className="flex gap-3 items-center border-t border-white/5 pt-3">
                  <Globe className="h-4 w-4 text-[#c7c4d7]/40 shrink-0" />
                  <a href={lead.website} target="_blank" rel="noopener noreferrer" className="text-sm text-[#c7c4d7] hover:text-[#c0c1ff] transition-colors flex items-center gap-1.5 truncate">
                    {lead.website.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                    <ExternalLink className="h-3.5 w-3.5 text-[#c7c4d7]/40" />
                  </a>
                </div>
              )}
              {lead.email && (
                <div className="flex gap-3 border-t border-white/5 pt-3">
                  <Mail className="h-4 w-4 text-[#c7c4d7]/40 shrink-0 mt-0.5" />
                  <a href={`mailto:${lead.email}`} className="text-sm text-[#89ceff] hover:text-[#89ceff]/85 transition-colors">
                    {lead.email}
                  </a>
                </div>
              )}
              {lead.profile_url && (
                <div className="flex gap-3 border-t border-white/5 pt-3">
                  <Network className="h-4 w-4 text-[#c7c4d7]/40 shrink-0 mt-0.5" />
                  <a href={lead.profile_url} target="_blank" rel="noopener noreferrer" className="text-sm text-[#afacff] hover:text-[#afacff]/85 transition-colors flex items-center gap-1.5 truncate">
                    Source Profile
                    <ExternalLink className="h-3.5 w-3.5 text-[#afacff]/40" />
                  </a>
                </div>
              )}
            </div>
          </div>

          {/* Website Audit Pill Grid */}
          <div className="bg-[#131314] border border-white/5 rounded-xl p-5 mb-6 transition-all duration-200 hover:border-white/10">
            <div className="flex items-center gap-2 mb-4 text-[#c7c4d7] border-b border-white/5 pb-2">
              <ShieldCheck className="h-4 w-4 text-[#c0c1ff]" />
              <h4 className="font-label-caps text-[11px] font-bold uppercase tracking-wider">Signals Audit</h4>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <AuditPill active={lead.has_website} label="Website" icon={Globe} />
              <AuditPill active={lead.has_ssl} label="SSL Secure" icon={ShieldCheck} />
              <AuditPill active={lead.has_email} label="Email Found" icon={Mail} />
              <AuditPill active={lead.has_phone} label="Phone Found" icon={Phone} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const ALL_PLATFORMS = [
  { id: 'linkedin',     name: 'LinkedIn',      Icon: Briefcase,     desc: 'B2B companies' },
  { id: 'reddit',       name: 'Reddit',        Icon: MessageSquare,  desc: 'Tech/community' },
  { id: 'crunchbase',   name: 'Crunchbase',    Icon: TrendingUp,     desc: 'VC & startups' },
  { id: 'wellfound',    name: 'Wellfound',     Icon: Rocket,         desc: 'Early startups' },
  { id: 'producthunt',  name: 'Product Hunt',  Icon: Cat,            desc: 'SaaS products' },
  { id: 'github',       name: 'GitHub',        Icon: GitBranch,      desc: 'Dev tools & tech' },
  { id: 'clutch',       name: 'Clutch',        Icon: Star,           desc: 'Agencies & devs' },
  { id: 'indeed',       name: 'Indeed',        Icon: UserCheck,      desc: 'Hiring firms' },
  { id: 'twitter',      name: 'Twitter / X',   Icon: Send,           desc: 'Solopreneurs' },
  { id: 'facebook',     name: 'Facebook',      Icon: Users,          desc: 'Local business' },
];

export default function SocialFinderPage() {
  const queryClient = useQueryClient();
  const [industry, setIndustry] = useState('Marketing Agency');
  const [location, setLocation] = useState('Austin TX');
  const [keywords, setKeywords] = useState('');
  const [selectedSources, setSelectedSources] = useState<string[]>(['linkedin', 'crunchbase']);
  const [limit, setLimit] = useState('20');
  const [activeSearchId, setActiveSearchId] = useState<number | null>(null);
  const [selectedLead, setSelectedLead] = useState<SocialLead | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [search, setSearch] = useState('');

  // Queries
  const prevStatusRef = useRef<string | null>(null);

  const { data: searches = [] } = useQuery<SocialSearch[]>({
    queryKey: ['social-searches'],
    queryFn: listSocialSearches,
    refetchInterval: (query) => {
      const data = query.state.data as SocialSearch[] | undefined;
      const hasActive = data?.some(s => s.status === 'running' || s.status === 'queued');
      return hasActive ? 2000 : 8000;
    },
  });

  // Auto-select the most recent search (any status) on first load
  const activeSearch = searches.find(s => s.id === activeSearchId) ?? searches[0] ?? null;

  useEffect(() => {
    if (activeSearch && !activeSearchId) {
      setActiveSearchId(activeSearch.id);
    }
  }, [activeSearch, activeSearchId]);

  // Detect transition to completed → force a final leads fetch
  useEffect(() => {
    if (!activeSearch) return;
    const prev = prevStatusRef.current;
    const curr = activeSearch.status;
    if (prev === 'running' && curr === 'completed') {
      queryClient.invalidateQueries({ queryKey: ['social-leads', activeSearch.id] });
    }
    prevStatusRef.current = curr;
  }, [activeSearch?.status, activeSearch?.id, queryClient]);

  const isSearchRunning = activeSearch?.status === 'running' || activeSearch?.status === 'queued';

  const { data: leads = [] } = useQuery({
    queryKey: ['social-leads', activeSearchId],
    queryFn: () => getSocialLeads(activeSearchId!),
    enabled: !!activeSearchId,
    staleTime: 0,
    refetchOnMount: true,
    refetchInterval: isSearchRunning ? 2500 : false,
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: createSocialSearch,
    onSuccess: (data) => {
      setActiveSearchId(data.id);
      queryClient.invalidateQueries({ queryKey: ['social-searches'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteSocialSearch,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-searches'] });
      if (searches.length > 1) {
        const nextId = searches.find(s => s.id !== activeSearchId)?.id;
        setActiveSearchId(nextId || null);
      } else {
        setActiveSearchId(null);
      }
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!industry.trim() || !location.trim()) return;

    createMutation.mutate({
      industry: industry.trim(),
      location: location.trim(),
      keywords: keywords.trim() || undefined,
      sources: selectedSources,
      filters: {},
      limit: parseInt(limit) || 20,
    });
  };

  const toggleSource = (src: string) => {
    setSelectedSources(prev => 
      prev.includes(src) ? prev.filter(x => x !== src) : [...prev, src]
    );
  };

  // Stat calculations
  const filteredLeads = leads.filter(l =>
    `${l.name} ${l.source_platform} ${l.email || ''} ${l.phone || ''} ${l.city || ''} ${l.country || ''}`.toLowerCase().includes(search.toLowerCase())
  );
  const totalLeadsCount = leads.length;
  const highQualityCount = leads.filter(l => l.lead_score >= 70).length;
  const avgOpportunity = totalLeadsCount > 0 
    ? Math.round(leads.reduce((acc, l) => acc + l.lead_score, 0) / totalLeadsCount) 
    : 0;

  return (
    <div className="space-y-lg animate-in fade-in duration-500">
      
      {/* Command Center */}
      <section className="bg-[#0F0F12] border border-white/5 rounded-xl p-6 md:p-xl relative overflow-hidden group glow-card animate-blur-reveal">
        <div className="absolute -right-20 -top-20 w-96 h-96 bg-[#8083ff]/10 blur-[100px] rounded-full pointer-events-none" />
        
        <div className="max-w-4xl relative z-10">
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-2">
              <Badge color="indigo">Social Engine v2.0</Badge>
              <span className="h-1.5 w-1.5 rounded-full bg-[#afacff] animate-pulse" />
              <span className="text-xs text-[#c7c4d7]/40 font-mono-data font-semibold">Ready for queries</span>
            </div>
            <h2 className="font-display-lg text-3xl md:text-[40px] font-bold mb-2 leading-tight tracking-tight">
              <span className="shiny-text">Discover B2B social leads, </span>
              <span className="text-[#c0c1ff] italic font-extrabold">globally.</span>
            </h2>
            <p className="font-body-md text-[#c7c4d7]/70 leading-relaxed max-w-2xl">
              Enter target parameters to scan top social networks and B2B directories. LeadForge automates directory queries, email lookup, and AI lead priority scoring.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
              <div className="md:col-span-4">
                <label className="font-label-caps text-[10px] mb-1.5 block text-[#c7c4d7]/60 tracking-wider font-semibold uppercase">Target Industry</label>
                <div className="bg-[#0e0e0f] border border-[#464554]/30 p-2.5 rounded-lg flex items-center gap-2 focus-within:border-[#c0c1ff]/60 transition-colors">
                  <Building2 className="h-4 w-4 text-[#c0c1ff]" />
                  <input 
                    required
                    value={industry} 
                    onChange={e => setIndustry(e.target.value)} 
                    placeholder="e.g. Software, Marketing"
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
                    required
                    value={location} 
                    onChange={e => setLocation(e.target.value)} 
                    placeholder="e.g. Austin TX, London"
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
                    onChange={e => {
                      const val = e.target.value;
                      if (val === '' || /^\d+$/.test(val)) {
                        setLimit(val);
                      }
                    }} 
                    type="text" 
                    placeholder="Max"
                    className="bg-transparent border-none p-0 focus:ring-0 text-xs text-white w-full placeholder-[#c7c4d7]/30"
                  />
                </div>
              </div>

              <button 
                type="submit"
                disabled={createMutation.isPending || !industry.trim() || !location.trim() || selectedSources.length === 0}
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

            {/* Advanced & Sources section inside the same card */}
            <div className="border-t border-white/5 pt-5 space-y-5">
              <div className="flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setShowFilters(!showFilters)}
                  className="flex items-center gap-2 text-xs font-bold text-[#c0c1ff] hover:text-[#c0c1ff]/80 transition-colors"
                >
                  <ListFilter className="h-4 w-4" />
                  <span>{showFilters ? 'Hide Advanced Filters' : 'Show Advanced Filters'}</span>
                </button>
              </div>

              {showFilters && (
                <div className="p-4 rounded-xl border border-white/5 bg-white/[0.01] space-y-4 animate-in fade-in duration-200">
                  <div>
                    <label className="block text-[10px] font-bold text-[#c7c4d7]/50 uppercase tracking-wider mb-1.5">
                      Specific Keywords (optional)
                    </label>
                    <input
                      type="text"
                      value={keywords}
                      onChange={e => setKeywords(e.target.value)}
                      placeholder="e.g. AI, Webflow, recruiting"
                      className="w-full bg-[#0e0e0f] border border-[#464554]/30 rounded-lg px-3 py-2 text-xs text-white placeholder-[#c7c4d7]/30 focus:border-[#c0c1ff]/60 focus:outline-none transition-colors"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-[10px] font-bold text-[#c7c4d7]/50 uppercase tracking-wider mb-3">
                  Social Data Sources
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                  {ALL_PLATFORMS.map(p => {
                    const active = selectedSources.includes(p.id);
                    return (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => toggleSource(p.id)}
                        className={cls(
                          "flex flex-col items-center justify-center p-3 rounded-xl border text-center transition-all duration-200 hover:scale-[1.02]",
                          active
                            ? "bg-[#c0c1ff]/10 border-[#c0c1ff]/30 text-white"
                            : "bg-white/[0.01] border-white/5 text-[#c7c4d7]/50 hover:bg-white/[0.03]"
                        )}
                      >
                        <p.Icon className={cls("h-5 w-5 mb-1", active ? "text-[#c0c1ff]" : "text-[#c7c4d7]/40")} />
                        <span className="text-xs font-bold truncate w-full">{p.name}</span>
                        <span className="text-[9px] text-[#c7c4d7]/30 truncate w-full mt-0.5">{p.desc}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </form>

          {/* Job status & live sub-task reporting */}
          {activeSearch && (activeSearch.status === 'running' || activeSearch.status === 'queued') && (
            <div className="mt-6 bg-white/[0.02] border border-white/5 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 animate-in fade-in slide-in-from-top-2">
              <div className="flex flex-1 items-center gap-3">
                <Badge color={activeSearch.status === 'running' ? 'yellow' : 'slate'}>
                  {activeSearch.status}
                </Badge>
                
                <div className="flex flex-1 items-center gap-3">
                  <div className="h-2 flex-1 max-w-md bg-white/5 rounded-full overflow-hidden relative">
                    <div 
                      className={cls(
                        "h-full bg-gradient-to-r from-[#89ceff] to-[#afacff] transition-all duration-500 rounded-full",
                        activeSearch.status === 'running' && "animate-pulse"
                      )} 
                      style={{ width: `${activeSearch.progress}%` }} 
                    />
                  </div>
                  <span className="font-mono-data text-xs text-white font-bold">{activeSearch.progress}%</span>
                </div>
              </div>

              <div className="flex items-center justify-between md:justify-end gap-4 border-t md:border-t-0 border-white/5 pt-3 md:pt-0">
                <span className="text-xs text-[#c7c4d7]/70 italic font-semibold">
                  {activeSearch.query_summary || 'Analyzing B2B directories...'}
                </span>
                <button 
                  onClick={() => setActiveSearchId(null)} 
                  className="flex items-center gap-1.5 text-xs font-bold text-[#c7c4d7]/40 hover:text-white transition-colors"
                >
                  <RotateCcw className="h-3.5 w-3.5" /> Reset
                </button>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Main Content Grid: History on Left, Stats & Table on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Discovery Runs (History Sidebar) */}
        <div className="lg:col-span-3 space-y-6">
          <section className="bg-[#0F0F12] border border-white/5 rounded-xl p-5 glow-card animate-blur-reveal" style={{ animationDelay: '100ms' }}>
            <h3 className="text-sm font-bold font-display-md text-white mb-4 flex items-center gap-2 pb-2 border-b border-white/5">
              <Clock className="h-4 w-4 text-[#c0c1ff]" />
              <span>Discovery Runs</span>
            </h3>
            {searches.length === 0 ? (
              <div className="text-xs text-[#c7c4d7]/30 text-center py-8">
                No past runs found
              </div>
            ) : (
              <div className="space-y-3 max-h-[360px] overflow-y-auto pr-1">
                {searches.map(s => {
                  const active = activeSearchId === s.id;
                  const isRunning = s.status === 'running' || s.status === 'queued';
                  return (
                    <div
                      key={s.id}
                      onClick={() => setActiveSearchId(s.id)}
                      className={cls(
                        "group flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all",
                        active 
                          ? "bg-white/5 border-white/10" 
                          : "bg-white/[0.01] border-white/5 hover:bg-white/[0.02]"
                      )}
                    >
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-bold text-white truncate">{s.industry}</span>
                          <span className="text-[10px] text-[#c7c4d7]/40">in</span>
                          <span className="text-xs text-[#c0c1ff] font-medium truncate">{s.location}</span>
                        </div>
                        <div className="flex items-center gap-2 text-[10px] text-[#c7c4d7]/40">
                          <span>{s.total_found} leads</span>
                          <span>•</span>
                          {isRunning ? (
                            <span className="text-[#89ceff] flex items-center gap-1">
                              <span className="h-1 w-1 rounded-full bg-[#89ceff] animate-pulse" />
                              {s.progress}%
                            </span>
                          ) : s.status === 'completed' ? (
                            <span className="text-[#4edea3]">Completed</span>
                          ) : (
                            <span className="text-[#ffb4ab]">Failed</span>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteMutation.mutate(s.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 hover:text-[#ffb4ab] transition-all text-[#c7c4d7]/40"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        </div>

        {/* Results Area */}
        <div className="lg:col-span-9 space-y-6">
          
          {/* Stats section if a search is active */}
          {activeSearchId && (
            <section className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-blur-reveal" style={{ animationDelay: '200ms' }}>
              <div className="bg-[#0F0F12] border border-white/5 p-5 rounded-xl flex items-center gap-4 glow-card transition-all duration-200">
                <div className="w-12 h-12 rounded-full bg-[#c0c1ff]/10 flex items-center justify-center text-[#c0c1ff]">
                  <Activity className="h-6 w-6" />
                </div>
                <div>
                  <div className="text-[#c7c4d7]/50 font-label-caps text-[10px] tracking-wider uppercase font-semibold">Average Lead Opportunity</div>
                  <div className="text-2xl font-bold text-white tracking-tight">{avgOpportunity}%</div>
                </div>
              </div>

              <div className="bg-[#0F0F12] border border-white/5 p-5 rounded-xl flex items-center gap-4 glow-card transition-all duration-200">
                <div className="w-12 h-12 rounded-full bg-[#4edea3]/10 flex items-center justify-center text-[#4edea3]">
                  <Mail className="h-6 w-6" />
                </div>
                <div>
                  <div className="text-[#c7c4d7]/50 font-label-caps text-[10px] tracking-wider uppercase font-semibold">High-Opportunity Leads</div>
                  <div className="text-2xl font-bold text-white tracking-tight">{highQualityCount} Leads</div>
                </div>
              </div>

              <div className="bg-[#0F0F12] border border-white/5 p-5 rounded-xl flex items-center gap-4 glow-card transition-all duration-200">
                <div className="w-12 h-12 rounded-full bg-[#89ceff]/10 flex items-center justify-center text-[#89ceff]">
                  <Sparkles className="h-6 w-6" />
                </div>
                <div>
                  <div className="text-[#c7c4d7]/50 font-label-caps text-[10px] tracking-wider uppercase font-semibold">Discovered Profiles</div>
                  <div className="text-2xl font-bold text-white tracking-tight">{totalLeadsCount} Profiles</div>
                </div>
              </div>
            </section>
          )}

          {/* Table section */}
          {activeSearchId ? (
            <section className="bg-[#131314] rounded-xl border border-white/5 overflow-hidden transition-all duration-200 glow-card animate-blur-reveal" style={{ animationDelay: '300ms' }}>
              <div className="px-lg py-md border-b border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#201f20]/20">
                <div className="flex items-center gap-2">
                  <h3 className="font-headline-sm text-lg text-white">Extracted Contacts</h3>
                  <span className="bg-white/5 px-2 py-0.5 rounded text-mono-data text-xs text-[#c7c4d7]">
                    {filteredLeads.length} Total
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
                  
                  {totalLeadsCount > 0 && (
                    <div className="flex gap-2">
                      <a 
                        href={getSocialExportUrl(activeSearchId)} 
                        className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs font-bold text-[#c7c4d7] hover:bg-white/10 transition-colors flex items-center gap-1.5"
                      >
                        <Download className="h-3.5 w-3.5" /> Export CSV
                      </a>
                    </div>
                  )}
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-white/5 bg-white/[0.01] text-[10px] font-bold text-[#c7c4d7]/40 uppercase tracking-wider">
                      <th className="px-lg py-4 font-semibold">Company Name</th>
                      <th className="px-lg py-4 font-semibold">Source</th>
                      <th className="px-lg py-4 font-semibold">Contacts</th>
                      <th className="px-lg py-4 font-semibold">Location</th>
                      <th className="px-lg py-4 font-semibold w-48">Opportunity</th>
                      <th className="px-lg py-4 font-semibold">Priority</th>
                      <th className="px-lg py-4 font-semibold text-right"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 text-sm">
                    {filteredLeads.length === 0 && (
                      <tr>
                        <td colSpan={7} className="py-16 text-center text-[#c7c4d7]/50">
                          <div className="flex flex-col items-center justify-center gap-2">
                            <Search className="h-8 w-8 opacity-20" />
                            <p className="text-sm">No leads found matching your search.</p>
                          </div>
                        </td>
                      </tr>
                    )}
                    {filteredLeads.map(lead => {
                      const score = lead.lead_score;
                      const scoreColor = score == null ? 'slate' : score >= 70 ? 'green' : score >= 40 ? 'yellow' : 'red';
                      const priority = score == null ? '—' : score >= 70 ? 'High' : score >= 40 ? 'Mid' : 'Low';
                      
                      return (
                        <tr
                          key={lead.id}
                          onClick={() => setSelectedLead(lead)}
                          className="hover:bg-[#c0c1ff]/5 transition-colors cursor-pointer group"
                        >
                          <td className="px-lg py-4 relative font-semibold text-white">
                            <div className="absolute left-0 top-1/4 bottom-1/4 w-[2px] bg-[#c0c1ff] opacity-0 group-hover:opacity-100 transition-opacity" />
                            {lead.name}
                          </td>
                          <td className="px-lg py-4">
                            <span className="capitalize text-xs px-2 py-0.5 bg-white/5 rounded-md border border-white/10 text-[#c7c4d7]">
                              {lead.source_platform}
                            </span>
                          </td>
                          <td className="px-lg py-4">
                            <div className="flex gap-2.5">
                              {lead.email ? (
                                <span title={lead.email}>
                                  <Mail className="h-4 w-4 text-[#89ceff]" />
                                </span>
                              ) : (
                                <Mail className="h-4 w-4 text-white/5" />
                              )}
                              {lead.phone ? (
                                <span title={lead.phone}>
                                  <Phone className="h-4 w-4 text-[#4edea3]" />
                                </span>
                              ) : (
                                <Phone className="h-4 w-4 text-white/5" />
                              )}
                              {lead.website ? (
                                <span title={lead.website}>
                                  <Globe className="h-4 w-4 text-[#c0c1ff]" />
                                </span>
                              ) : (
                                <Globe className="h-4 w-4 text-white/5" />
                              )}
                            </div>
                          </td>
                          <td className="px-lg py-4 text-xs text-[#c7c4d7]/60">
                            {lead.city || lead.country || '—'}
                          </td>
                          <td className="px-lg py-4">
                            <ScoreBar score={lead.lead_score} />
                          </td>
                          <td className="px-lg py-4">
                            <Badge color={scoreColor}>{priority}</Badge>
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
                  Showing 1 to {filteredLeads.length} of {filteredLeads.length} leads
                </div>
              </div>
            </section>
          ) : (
            <div className="bg-[#0f0f12] border border-white/5 rounded-xl p-16 text-center text-[#c7c4d7]/30">
              <Sparkles className="h-8 w-8 mx-auto mb-4 opacity-20 text-[#c0c1ff]" />
              <h3 className="text-lg font-bold text-white">Prospector Ready</h3>
              <p className="text-xs mt-1">Enter target parameters above or select a past discovery run to begin.</p>
            </div>
          )}
        </div>
      </div>

      {/* Detail Drawer */}
      {selectedLead && (
        <DetailDrawer lead={selectedLead} onClose={() => setSelectedLead(null)} />
      )}
    </div>
  );
}
