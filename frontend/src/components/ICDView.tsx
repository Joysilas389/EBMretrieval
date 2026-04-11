import { useState } from 'react';
import type { ICDCode } from '../utils/types';
import { searchICD } from '../utils/api';

export default function ICDView() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<ICDCode[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await searchICD(query.trim());
      setResults(data);
    } catch { setResults([]); }
    finally { setLoading(false); }
  };

  return (
    <div className="list-view">
      <h2 className="list-title" style={{ marginBottom: 8 }}>ICD-11 Classification</h2>
      <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', marginBottom: 16 }}>
        Search the WHO ICD-11 classification system. ICD-11 is the current international standard (ICD-10 is outdated).
      </p>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input
          className="list-search"
          style={{ flex: 1, marginBottom: 0 }}
          placeholder="Search by condition, code, or keyword…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <button className="btn btn-primary" onClick={handleSearch} disabled={loading}>
          {loading ? '…' : 'Search'}
        </button>
      </div>

      {results.length === 0 && query && !loading && (
        <div className="list-empty">No ICD-11 codes found. Try a different term.</div>
      )}

      {results.map((icd) => (
        <div key={icd.code} className="list-item" style={{ cursor: 'default' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, width: '100%' }}>
            <span style={{
              fontFamily: 'var(--font-mono)', fontSize: 'var(--fs-sm)', fontWeight: 700,
              color: 'var(--accent-text)', background: 'var(--accent-light)',
              padding: '4px 10px', borderRadius: 'var(--radius-sm)', whiteSpace: 'nowrap',
            }}>
              {icd.code}
            </span>
            <div style={{ flex: 1 }}>
              <div className="list-item-title">{icd.title}</div>
              {icd.chapter && (
                <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)' }}>{icd.chapter}</div>
              )}
            </div>
          </div>
        </div>
      ))}

      <div style={{ marginTop: 24, padding: 16, background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
        <div style={{ fontSize: 'var(--fs-sm)', fontWeight: 600, color: 'var(--text-heading)', marginBottom: 8 }}>About ICD-11</div>
        <p style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          The International Classification of Diseases 11th Revision (ICD-11) is the current WHO global standard for
          diagnostic health information. It replaced ICD-10 and includes improved coding for clinical detail,
          safety, and electronic health records. ICD-11 came into effect January 1, 2022.
        </p>
      </div>
    </div>
  );
}
