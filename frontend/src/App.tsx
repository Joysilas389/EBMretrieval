import { useState, useEffect, useCallback } from 'react';
import type { View, AnswerResponse } from './utils/types';
import { useSettings, useHistory, useBookmarks } from './utils/storage';
import { fetchAnswer } from './utils/api';
import Header from './components/Header';
import HomeView from './components/HomeView';
import AnswerView from './components/AnswerView';
import HistoryView from './components/HistoryView';
import BookmarksView from './components/BookmarksView';
import SettingsView from './components/SettingsView';
import SpecialtiesView from './components/SpecialtiesView';
import CompareView from './components/CompareView';
import ICDView from './components/ICDView';
import AnimationsView from './components/AnimationsView';
import SearchBar from './components/SearchBar';
import BottomNav from './components/BottomNav';

export default function App() {
  const [view, setView] = useState<View>('home');
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState<AnswerResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { settings, updateSetting, resetSettings } = useSettings();
  const { history, addToHistory, deleteItem, renameItem, togglePin, clearHistory, searchHistory } = useHistory();
  const { bookmarks, addBookmark, removeBookmark, renameBookmark, clearBookmarks, isBookmarked } = useBookmarks();

  useEffect(() => {
    const theme = settings.theme === 'system'
      ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      : settings.theme;
    document.documentElement.setAttribute('data-theme', theme);
  }, [settings.theme]);

  useEffect(() => {
    document.documentElement.style.fontSize = `${settings.fontSize}px`;
  }, [settings.fontSize]);

  const handleSearch = useCallback(async (q: string) => {
    if (!q.trim()) return;
    setQuery(q);
    setLoading(true);
    setError(null);
    setView('answer');
    window.scrollTo(0, 0);
    try {
      const result = await fetchAnswer({
        query: q,
        max_sources: settings.maxSources,
        max_words: settings.maxWords,
        teaching_mode: settings.teachingMode,
        citation_density: settings.citationDensity,
        source_preference: settings.sourcePreference,
        specialty_filter: settings.specialtyFilter,
        language: settings.language !== 'en' ? settings.language : undefined,
      });
      setAnswer(result);
      addToHistory(q, result);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve evidence.');
    } finally {
      setLoading(false);
    }
  }, [settings, addToHistory]);

  const handleHistoryOpen = useCallback((item: any) => {
    setQuery(item.query); setAnswer(item.answer); setView('answer');
  }, []);

  const handleBookmarkOpen = useCallback((item: any) => {
    setQuery(item.query); setAnswer(item.answer); setView('answer');
  }, []);

  const handleGoHome = useCallback(() => {
    setView('home'); setAnswer(null); setQuery(''); setError(null);
  }, []);

  const showSearch = view === 'home' || view === 'answer';

  return (
    <div className="app-container">
      <Header onHome={handleGoHome} view={view} setView={setView} />

      <div className="main-content" style={{ paddingBottom: showSearch ? 140 : 70 }}>
        {view === 'home' && <HomeView onSearch={handleSearch} />}
        {view === 'answer' && (
          <AnswerView
            query={query} answer={answer} loading={loading} error={error}
            onBookmark={() => answer && (isBookmarked(query) ? removeBookmark(bookmarks.find(b => b.query === query)?.id || '') : addBookmark(query, answer))}
            isBookmarked={isBookmarked(query)} teachingMode={settings.teachingMode}
          />
        )}
        {view === 'compare' && <CompareView />}
        {view === 'icd' && <ICDView />}
        {view === 'animations' && <AnimationsView />}
        {view === 'history' && (
          <HistoryView history={history} onOpen={handleHistoryOpen} onDelete={deleteItem}
            onRename={renameItem} onTogglePin={togglePin} onClear={clearHistory} onSearch={searchHistory} />
        )}
        {view === 'bookmarks' && (
          <BookmarksView bookmarks={bookmarks} onOpen={handleBookmarkOpen} onRemove={removeBookmark}
            onRename={renameBookmark} onClear={clearBookmarks} />
        )}
        {view === 'settings' && (
          <SettingsView settings={settings} onUpdate={updateSetting} onReset={resetSettings}
            onClearHistory={clearHistory} onClearBookmarks={clearBookmarks} />
        )}
        {view === 'specialties' && (
          <SpecialtiesView onSelect={(s) => { updateSetting('specialtyFilter', s); setView('home'); }} />
        )}
      </div>

      {showSearch && (
        <div className="search-fixed-wrapper">
          <div className="main-content" style={{ padding: 0 }}>
            <SearchBar onSearch={handleSearch} loading={loading} />
          </div>
        </div>
      )}

      <BottomNav view={view} setView={setView} />
    </div>
  );
}
