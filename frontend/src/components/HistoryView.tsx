import { useState } from 'react';
import type { HistoryItem } from '../utils/types';

interface Props {
  history: HistoryItem[];
  onOpen: (item: HistoryItem) => void;
  onDelete: (id: string) => void;
  onRename: (id: string, title: string) => void;
  onTogglePin: (id: string) => void;
  onClear: () => void;
  onSearch: (q: string) => HistoryItem[];
}

export default function HistoryView({ history, onOpen, onDelete, onRename, onTogglePin, onClear, onSearch }: Props) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'newest' | 'oldest'>('newest');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const filtered = searchQuery ? onSearch(searchQuery) : history;
  const sorted = [...filtered].sort((a, b) => {
    if (a.pinned !== b.pinned) return a.pinned ? -1 : 1;
    const dateA = new Date(a.timestamp).getTime();
    const dateB = new Date(b.timestamp).getTime();
    return sortBy === 'newest' ? dateB - dateA : dateA - dateB;
  });

  const handleRename = (id: string) => {
    if (editTitle.trim()) {
      onRename(id, editTitle.trim());
    }
    setEditingId(null);
  };

  return (
    <div className="list-view">
      <div className="list-header">
        <h2 className="list-title">History</h2>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <select
            className="setting-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
          >
            <option value="newest">Newest</option>
            <option value="oldest">Oldest</option>
          </select>
          {history.length > 0 && (
            <button className="btn btn-ghost" style={{ fontSize: 'var(--fs-xs)', color: 'var(--danger)' }} onClick={onClear}>
              Clear All
            </button>
          )}
        </div>
      </div>

      <input
        type="text"
        className="list-search"
        placeholder="Search history…"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
      />

      {sorted.length === 0 ? (
        <div className="list-empty">
          {searchQuery ? 'No matching history items.' : 'No history yet. Ask a question to get started.'}
        </div>
      ) : (
        sorted.map((item) => (
          <div key={item.id} className="list-item">
            {item.pinned && <span style={{ fontSize: 14 }}>📌</span>}
            <div className="list-item-content" onClick={() => onOpen(item)}>
              {editingId === item.id ? (
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  onBlur={() => handleRename(item.id)}
                  onKeyDown={(e) => e.key === 'Enter' && handleRename(item.id)}
                  autoFocus
                  className="list-search"
                  style={{ marginBottom: 0, padding: '4px 8px' }}
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <>
                  <div className="list-item-title">{item.title}</div>
                  <div className="list-item-preview">{item.preview}</div>
                </>
              )}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4, flexShrink: 0 }}>
              <span className="list-item-date">
                {new Date(item.timestamp).toLocaleDateString()}
              </span>
              <div style={{ display: 'flex', gap: 2 }}>
                <button
                  className="btn-icon"
                  style={{ width: 28, height: 28, fontSize: 12 }}
                  title="Pin"
                  onClick={(e) => { e.stopPropagation(); onTogglePin(item.id); }}
                >
                  📌
                </button>
                <button
                  className="btn-icon"
                  style={{ width: 28, height: 28, fontSize: 12 }}
                  title="Rename"
                  onClick={(e) => {
                    e.stopPropagation();
                    setEditingId(item.id);
                    setEditTitle(item.title);
                  }}
                >
                  ✏️
                </button>
                <button
                  className="btn-icon"
                  style={{ width: 28, height: 28, fontSize: 12 }}
                  title="Delete"
                  onClick={(e) => { e.stopPropagation(); onDelete(item.id); }}
                >
                  🗑️
                </button>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
