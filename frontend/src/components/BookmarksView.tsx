import { useState } from 'react';
import type { BookmarkItem } from '../utils/types';

interface Props {
  bookmarks: BookmarkItem[];
  onOpen: (item: BookmarkItem) => void;
  onRemove: (id: string) => void;
  onRename: (id: string, title: string) => void;
  onClear: () => void;
}

export default function BookmarksView({ bookmarks, onOpen, onRemove, onRename, onClear }: Props) {
  const [searchQuery, setSearchQuery] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const filtered = searchQuery
    ? bookmarks.filter(b =>
        b.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        b.query.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : bookmarks;

  const handleRename = (id: string) => {
    if (editTitle.trim()) {
      onRename(id, editTitle.trim());
    }
    setEditingId(null);
  };

  return (
    <div className="list-view">
      <div className="list-header">
        <h2 className="list-title">Bookmarks</h2>
        {bookmarks.length > 0 && (
          <button className="btn btn-ghost" style={{ fontSize: 'var(--fs-xs)', color: 'var(--danger)' }} onClick={onClear}>
            Clear All
          </button>
        )}
      </div>

      {bookmarks.length > 3 && (
        <input
          type="text"
          className="list-search"
          placeholder="Search bookmarks…"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      )}

      {filtered.length === 0 ? (
        <div className="list-empty">
          {searchQuery ? 'No matching bookmarks.' : 'No bookmarks yet. Bookmark an answer to save it here.'}
        </div>
      ) : (
        filtered.map((item) => (
          <div key={item.id} className="list-item">
            <span style={{ fontSize: 16 }}>★</span>
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
                  <div className="list-item-preview">
                    {item.answer.blocks[0]?.text.slice(0, 120) || item.query}
                  </div>
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
                  title="Remove"
                  onClick={(e) => { e.stopPropagation(); onRemove(item.id); }}
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
