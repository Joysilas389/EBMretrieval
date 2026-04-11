import type { AnswerResponse, CompareResponse, ICDCode } from './types';

const API_BASE = import.meta.env.VITE_API_URL || 'https://ebmretrieval-api.onrender.com/api';

export async function fetchAnswer(params: {
  query: string;
  max_sources?: number;
  max_words?: number;
  teaching_mode?: boolean;
  citation_density?: string;
  source_preference?: string;
  specialty_filter?: string | null;
  language?: string;
}): Promise<AnswerResponse> {
  const resp = await fetch(`${API_BASE}/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: params.query,
      max_sources: params.max_sources ?? 10,
      max_words: params.max_words ?? 2000,
      teaching_mode: params.teaching_mode ?? false,
      citation_density: params.citation_density ?? 'standard',
      source_preference: params.source_preference ?? 'balanced',
      specialty_filter: params.specialty_filter ?? null,
      language: params.language ?? null,
    }),
  });
  if (!resp.ok) throw new Error(`API error ${resp.status}: ${await resp.text()}`);
  return resp.json();
}

export async function fetchCompare(a: string, b: string, maxSources = 8): Promise<CompareResponse> {
  const resp = await fetch(`${API_BASE}/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ condition_a: a, condition_b: b, max_sources: maxSources }),
  });
  if (!resp.ok) throw new Error(`Compare error ${resp.status}`);
  return resp.json();
}

export async function searchICD(query: string): Promise<ICDCode[]> {
  const resp = await fetch(`${API_BASE}/icd?q=${encodeURIComponent(query)}`);
  if (!resp.ok) return [];
  return resp.json();
}

export async function fetchSpecialties(category?: string) {
  const url = category ? `${API_BASE}/specialties?category=${category}` : `${API_BASE}/specialties`;
  const resp = await fetch(url);
  return resp.json();
}

export async function fetchLanguages(): Promise<Record<string, string>> {
  const resp = await fetch(`${API_BASE}/languages`);
  return resp.json();
}

export async function fetchSuggestions(q: string): Promise<string[]> {
  if (q.length < 2) return [];
  const resp = await fetch(`${API_BASE}/suggest?q=${encodeURIComponent(q)}`);
  return resp.json();
}

export async function fetchHealth() {
  const resp = await fetch(`${API_BASE}/health`);
  return resp.json();
}

export async function seedIndex(): Promise<{ status: string; documents: number }> {
  const resp = await fetch(`${API_BASE}/admin/seed`, { method: 'POST' });
  return resp.json();
}
