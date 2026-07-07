const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '');

// ── Types ─────────────────────────────────────────────────────────────────────

export type SocialSearchCreate = {
  industry: string;
  location: string;
  keywords?: string;
  sources: string[];
  filters: Record<string, unknown>;
  limit: number;
};

export type SocialSearch = {
  id: number;
  status: 'queued' | 'running' | 'completed' | 'failed';
  industry: string;
  location: string;
  keywords: string | null;
  sources: string[];
  filters: Record<string, unknown>;
  query_summary: string | null;
  target_limit: number;
  progress: number;
  total_found: number;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
};

export type SocialLead = {
  id: number;
  search_id: number;
  name: string;
  source_platform: string;
  profile_url: string | null;
  website: string | null;
  email: string | null;
  phone: string | null;
  linkedin: string | null;
  facebook: string | null;
  instagram: string | null;
  twitter: string | null;
  github: string | null;
  youtube: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  industry: string | null;
  services: string[];
  employee_estimate: string | null;
  description: string | null;
  technologies: string[];
  google_rating: number | null;
  review_count: number | null;
  last_activity: string | null;
  confidence_score: number;
  lead_score: number;
  digital_score: number;
  has_website: boolean;
  has_ssl: boolean;
  has_email: boolean;
  has_phone: boolean;
  created_at: string;
};

// ── API functions ─────────────────────────────────────────────────────────────

export async function createSocialSearch(payload: SocialSearchCreate): Promise<SocialSearch> {
  const res = await fetch(`${API_BASE_URL}/api/v1/social-searches`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to create social search');
  return res.json();
}

export async function getSocialSearch(id: number): Promise<SocialSearch> {
  const res = await fetch(`${API_BASE_URL}/api/v1/social-searches/${id}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch social search');
  return res.json();
}

export async function listSocialSearches(): Promise<SocialSearch[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/social-searches`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to list social searches');
  return res.json();
}

export async function getSocialLeads(searchId: number): Promise<SocialLead[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/social-searches/${searchId}/leads`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch leads');
  return res.json();
}

export async function deleteSocialSearch(id: number): Promise<void> {
  await fetch(`${API_BASE_URL}/api/v1/social-searches/${id}`, { method: 'DELETE' });
}

export function getSocialExportUrl(searchId: number) {
  return `${API_BASE_URL}/api/v1/social-searches/${searchId}/exports/csv`;
}
