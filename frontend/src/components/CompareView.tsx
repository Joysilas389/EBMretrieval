import { useState } from 'react';
import type { CompareResponse } from '../utils/types';
import { fetchCompare } from '../utils/api';

export default function CompareView() {
  const [condA, setCondA] = useState('');
  const [condB, setCondB] = useState('');
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCompare = async () => {
    if (!condA.trim() || !condB.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = await fetchCompare(condA.trim(), condB.trim());
      setResult(data);
    } catch (e: any) {
      setError(e.message || 'Comparison failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="list-view" style={{ paddingBottom: 120 }}>
      <h2 className="list-title" style={{ marginBottom: 8 }}>Compare Conditions</h2>
      <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', marginBottom: 16 }}>
        Compare two medical conditions side by side with evidence from trusted sources.
      </p>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        <input
          className="list-search"
          style={{ flex: 1, minWidth: 140, marginBottom: 0 }}
          placeholder="Condition A (e.g. Asthma)"
          value={condA}
          onChange={(e) => setCondA(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleCompare()}
        />
        <span style={{ alignSelf: 'center', color: 'var(--text-tertiary)', fontWeight: 600 }}>vs</span>
        <input
          className="list-search"
          style={{ flex: 1, minWidth: 140, marginBottom: 0 }}
          placeholder="Condition B (e.g. COPD)"
          value={condB}
          onChange={(e) => setCondB(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleCompare()}
        />
      </div>
      <button className="btn btn-primary" onClick={handleCompare} disabled={loading || !condA.trim() || !condB.trim()} style={{ width: '100%', marginBottom: 20 }}>
        {loading ? 'Comparing…' : 'Compare'}
      </button>

      {error && <div className="warning-banner warning-info"><span>⚠️</span><span>{error}</span></div>}

      {result && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {/* Column A */}
          <div className="answer-card" style={{ padding: 14 }}>
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: 'var(--fs-md)', fontWeight: 600, color: 'var(--accent-text)', marginBottom: 10 }}>
              {result.condition_a.name}
            </h3>
            <span className={`answer-badge badge-${result.condition_a.confidence}`} style={{ marginBottom: 8, display: 'inline-block' }}>
              {result.condition_a.confidence}
            </span>
            {result.condition_a.blocks.map((b, i) => (
              <div key={i} style={{ marginBottom: 8 }}>
                {b.type === 'heading' ? (
                  <h4 style={{ fontSize: 'var(--fs-sm)', fontWeight: 600, color: 'var(--text-heading)', margin: '12px 0 4px' }}>{b.text}</h4>
                ) : (
                  <p style={{ fontSize: 'var(--fs-xs)', lineHeight: 1.5, color: 'var(--text-primary)' }}>{b.text}</p>
                )}
              </div>
            ))}
            {result.condition_a.citations.length > 0 && (
              <div style={{ borderTop: '1px solid var(--border-light)', marginTop: 10, paddingTop: 8 }}>
                <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: 4 }}>Sources</div>
                {result.condition_a.citations.map((c, i) => (
                  <a key={i} href={c.url} target="_blank" rel="noopener noreferrer" style={{ display: 'block', fontSize: '10px', color: 'var(--citation-text)', marginBottom: 2, textDecoration: 'none' }}>
                    [{i + 1}] {c.title.replace(/<[^>]+>/g, "").slice(0, 60)}…
                  </a>
                ))}
              </div>
            )}
          </div>

          {/* Column B */}
          <div className="answer-card" style={{ padding: 14 }}>
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: 'var(--fs-md)', fontWeight: 600, color: 'var(--accent-text)', marginBottom: 10 }}>
              {result.condition_b.name}
            </h3>
            <span className={`answer-badge badge-${result.condition_b.confidence}`} style={{ marginBottom: 8, display: 'inline-block' }}>
              {result.condition_b.confidence}
            </span>
            {result.condition_b.blocks.map((b, i) => (
              <div key={i} style={{ marginBottom: 8 }}>
                {b.type === 'heading' ? (
                  <h4 style={{ fontSize: 'var(--fs-sm)', fontWeight: 600, color: 'var(--text-heading)', margin: '12px 0 4px' }}>{b.text}</h4>
                ) : (
                  <p style={{ fontSize: 'var(--fs-xs)', lineHeight: 1.5, color: 'var(--text-primary)' }}>{b.text}</p>
                )}
              </div>
            ))}
            {result.condition_b.citations.length > 0 && (
              <div style={{ borderTop: '1px solid var(--border-light)', marginTop: 10, paddingTop: 8 }}>
                <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: 4 }}>Sources</div>
                {result.condition_b.citations.map((c, i) => (
                  <a key={i} href={c.url} target="_blank" rel="noopener noreferrer" style={{ display: 'block', fontSize: '10px', color: 'var(--citation-text)', marginBottom: 2, textDecoration: 'none' }}>
                    [{i + 1}] {c.title.replace(/<[^>]+>/g, "").slice(0, 60)}…
                  </a>
                ))}
              </div>
            )}
          </div>

          <div style={{ gridColumn: '1 / -1', textAlign: 'center', fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)' }}>
            Retrieved in {result.retrieval_time_ms}ms
          </div>
        </div>
      )}
    </div>
  );
}
