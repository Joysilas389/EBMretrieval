import { useState, useEffect, useCallback } from 'react';
import type { HistoryItem, BookmarkItem, Settings, AnswerResponse } from './types';

// ============================================================
// GENERIC LOCAL STORAGE HOOK
// ============================================================
function useLocalStorage<T>(key: string, defaultValue: T): [T, (val: T | ((prev: T) => T)) => void] {
  const [value, setValue] = useState<T>(() => {
    try {
      const stored = localStorage.getItem(key);
      return stored ? JSON.parse(stored) : defaultValue;
    } catch {
      return defaultValue;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      console.warn('localStorage write failed:', e);
    }
  }, [key, value]);

  return [value, setValue];
}

// ============================================================
// SETTINGS
// ============================================================
const DEFAULT_SETTINGS: Settings = {
  theme: 'system',
  answerStyle: 'standard',
  teachingMode: false,
  citationDensity: 'standard',
  specialtyFilter: null,
  includeBasicScience: true,
  sourcePreference: 'balanced',
  freshnessPreference: 'balanced',
  maxWords: 2000,
  maxSources: 10,
  reducedMotion: false,
  fontSize: 16,
  language: 'en',
};

export function useSettings() {
  const [settings, setSettings] = useLocalStorage<Settings>('ebm_settings', DEFAULT_SETTINGS);

  const updateSetting = useCallback(<K extends keyof Settings>(key: K, value: Settings[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  }, [setSettings]);

  const resetSettings = useCallback(() => {
    setSettings(DEFAULT_SETTINGS);
  }, [setSettings]);

  return { settings, updateSetting, resetSettings };
}

// ============================================================
// HISTORY
// ============================================================
export function useHistory() {
  const [history, setHistory] = useLocalStorage<HistoryItem[]>('ebm_history', []);

  const addToHistory = useCallback((query: string, answer: AnswerResponse) => {
    const item: HistoryItem = {
      id: `h_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      query,
      title: query.slice(0, 80),
      preview: answer.blocks[0]?.text.slice(0, 150) || '',
      answer,
      timestamp: new Date().toISOString(),
      specialties: answer.specialties,
      bookmarked: false,
      pinned: false,
    };
    setHistory(prev => [item, ...prev].slice(0, 200));
    return item;
  }, [setHistory]);

  const deleteItem = useCallback((id: string) => {
    setHistory(prev => prev.filter(h => h.id !== id));
  }, [setHistory]);

  const renameItem = useCallback((id: string, title: string) => {
    setHistory(prev => prev.map(h => h.id === id ? { ...h, title } : h));
  }, [setHistory]);

  const togglePin = useCallback((id: string) => {
    setHistory(prev => prev.map(h => h.id === id ? { ...h, pinned: !h.pinned } : h));
  }, [setHistory]);

  const clearHistory = useCallback(() => {
    setHistory([]);
  }, [setHistory]);

  const searchHistory = useCallback((query: string) => {
    const q = query.toLowerCase();
    return history.filter(h =>
      h.title.toLowerCase().includes(q) ||
      h.query.toLowerCase().includes(q) ||
      h.preview.toLowerCase().includes(q)
    );
  }, [history]);

  return { history, addToHistory, deleteItem, renameItem, togglePin, clearHistory, searchHistory };
}

// ============================================================
// BOOKMARKS
// ============================================================
export function useBookmarks() {
  const [bookmarks, setBookmarks] = useLocalStorage<BookmarkItem[]>('ebm_bookmarks', []);

  const addBookmark = useCallback((query: string, answer: AnswerResponse) => {
    const exists = bookmarks.some(b => b.query === query);
    if (exists) return;
    const item: BookmarkItem = {
      id: `bm_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      query,
      title: query.slice(0, 80),
      answer,
      timestamp: new Date().toISOString(),
      specialties: answer.specialties,
    };
    setBookmarks(prev => [item, ...prev]);
  }, [bookmarks, setBookmarks]);

  const removeBookmark = useCallback((id: string) => {
    setBookmarks(prev => prev.filter(b => b.id !== id));
  }, [setBookmarks]);

  const renameBookmark = useCallback((id: string, title: string) => {
    setBookmarks(prev => prev.map(b => b.id === id ? { ...b, title } : b));
  }, [setBookmarks]);

  const clearBookmarks = useCallback(() => {
    setBookmarks([]);
  }, [setBookmarks]);

  const isBookmarked = useCallback((query: string) => {
    return bookmarks.some(b => b.query === query);
  }, [bookmarks]);

  return { bookmarks, addBookmark, removeBookmark, renameBookmark, clearBookmarks, isBookmarked };
}
