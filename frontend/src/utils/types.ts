export interface Citation {
  id: string;
  title: string;
  url: string;
  source_name: string;
  authors: string[];
  journal: string;
  year: number | null;
  pub_date: string;
  source_category: string;
  evidence_level: string;
  excerpt: string;
  specialty_tags: string[];
  pmid: string;
  doi: string;
  reliability: string;
  access_date: string;
}

export interface AnswerBlock {
  text: string;
  citation_indices: number[];
  block_type: 'paragraph' | 'heading' | 'list_item' | 'warning' | 'pearl';
}

export interface AnswerResponse {
  query: string;
  blocks: AnswerBlock[];
  citations: Citation[];
  specialties: string[];
  confidence: string;
  warnings: string[];
  teaching_mode: boolean;
  retrieval_time_ms: number;
  total_sources_consulted: number;
}

export interface CompareResponse {
  condition_a: {
    name: string;
    blocks: { text: string; type: string }[];
    citations: { title: string; url: string; source: string }[];
    confidence: string;
  };
  condition_b: {
    name: string;
    blocks: { text: string; type: string }[];
    citations: { title: string; url: string; source: string }[];
    confidence: string;
  };
  retrieval_time_ms: number;
}

export interface ICDCode {
  code: string;
  title: string;
  chapter: string;
  description: string;
  score: number;
}

export interface HistoryItem {
  id: string;
  query: string;
  title: string;
  preview: string;
  answer: AnswerResponse | null;
  timestamp: string;
  specialties: string[];
  bookmarked: boolean;
  pinned: boolean;
}

export interface BookmarkItem {
  id: string;
  query: string;
  title: string;
  answer: AnswerResponse;
  timestamp: string;
  specialties: string[];
}

export interface Settings {
  theme: 'light' | 'dark' | 'system';
  answerStyle: 'concise' | 'standard' | 'deep';
  teachingMode: boolean;
  citationDensity: 'standard' | 'high' | 'dense';
  specialtyFilter: string | null;
  includeBasicScience: boolean;
  sourcePreference: 'balanced' | 'guidelines' | 'studies' | 'reviews';
  freshnessPreference: 'latest' | 'balanced' | 'landmark';
  maxWords: number;
  maxSources: number;
  reducedMotion: boolean;
  fontSize: number;
  language: string;
}

export interface Specialty {
  id: string;
  name: string;
  category: string;
}

export type View = 'home' | 'answer' | 'history' | 'bookmarks' | 'settings' | 'specialties' | 'compare' | 'icd' | 'animations';
