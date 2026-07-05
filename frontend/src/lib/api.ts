const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000').replace(/\/+$/, '');

export type CreateJobPayload = {
  industry: string;
  location: string;
  limit: number;
  project_name?: string;
};

export type EmailRecord = { address: string; source: string; is_primary: boolean };
export type SocialAccount = { platform: string; url: string; handle: string | null };
export type WebsiteRecord = {
  url: string;
  final_url: string | null;
  ssl_enabled: boolean;
  https_enabled: boolean;
  meta_title: string | null;
  meta_description: string | null;
  image_count: number;
  contact_page_found: boolean;
  form_count: number;
  load_speed_ms: number | null;
  mobile_viewport: boolean;
  google_analytics: boolean;
  facebook_pixel: boolean;
  robots_txt: boolean;
  sitemap_xml: boolean;
};
export type LeadScore = {
  digital_presence_score: number;
  lead_opportunity_score: number;
  explanation: Record<string, unknown>;
};

export type Business = {
  id: number;
  name: string;
  website: string | null;
  phone_number: string | null;
  website_phones: string[];
  address: string | null;
  category: string | null;
  rating: number | null;
  review_count: number | null;
  latitude: number | null;
  longitude: number | null;
  google_maps_url: string;
  business_status: string | null;
  opening_hours: string | null;
  created_at: string;
  emails: EmailRecord[];
  social_accounts: SocialAccount[];
  website_record: WebsiteRecord | null;
  lead_score: LeadScore | null;
  raw_payload: Record<string, unknown>;
};

export async function createJob(payload: CreateJobPayload): Promise<{ job_id: number; status: string; query: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Unable to create job');
  return response.json();
}

export async function getJob(jobId: number) {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Unable to load job');
  return response.json();
}

export async function getBusinesses(jobId: number): Promise<Business[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}/businesses`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Unable to load businesses');
  return response.json();
}

export function getExportUrl(jobId: number, format: 'csv' | 'excel') {
  return `${API_BASE_URL}/api/v1/jobs/${jobId}/exports/${format}`;
}
