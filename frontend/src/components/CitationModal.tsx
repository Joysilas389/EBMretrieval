import type { Citation } from '../utils/types';

interface Props {
  citation: Citation;
  onClose: () => void;
}

export default function CitationModal({ citation, onClose }: Props) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
          <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: 'var(--fs-lg)', fontWeight: 600, color: 'var(--text-heading)', flex: 1, lineHeight: 1.3 }}>
            {citation.title}
          </h3>
          <button className="btn-icon" onClick={onClose} style={{ flexShrink: 0 }}>✕</button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {citation.authors.length > 0 && (
            <Row label="Authors" value={citation.authors.join(', ')} />
          )}
          {citation.journal && <Row label="Journal" value={citation.journal} />}
          {citation.year && <Row label="Year" value={String(citation.year)} />}
          {citation.pub_date && <Row label="Published" value={citation.pub_date} />}
          <Row label="Source" value={citation.source_name} />
          {citation.evidence_level && citation.evidence_level !== 'unknown' && (
            <Row label="Evidence Level" value={citation.evidence_level.replace(/_/g, ' ')} />
          )}
          {citation.source_category && citation.source_category !== 'unknown' && (
            <Row label="Type" value={citation.source_category.replace(/_/g, ' ')} />
          )}
          {citation.pmid && <Row label="PMID" value={citation.pmid} />}
          {citation.doi && <Row label="DOI" value={citation.doi} />}
          {citation.reliability && <Row label="Reliability" value={citation.reliability} />}
          {citation.access_date && <Row label="Accessed" value={new Date(citation.access_date).toLocaleDateString()} />}
        </div>

        {citation.excerpt && (
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 'var(--fs-xs)', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Excerpt
            </div>
            <div style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-primary)', lineHeight: 1.6, padding: 12, background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
              {citation.excerpt}
            </div>
          </div>
        )}

        <div style={{ marginTop: 20, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <a
            href={citation.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-primary"
          >
            Open Source ↗
          </a>
          {citation.pmid && (
            <a
              href={`https://pubmed.ncbi.nlm.nih.gov/${citation.pmid}/`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-ghost"
              style={{ border: '1px solid var(--border)' }}
            >
              PubMed ↗
            </a>
          )}
          {citation.doi && (
            <a
              href={`https://doi.org/${citation.doi}`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-ghost"
              style={{ border: '1px solid var(--border)' }}
            >
              DOI ↗
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'flex', gap: 12, fontSize: 'var(--fs-sm)' }}>
      <span style={{ color: 'var(--text-tertiary)', minWidth: 100, flexShrink: 0 }}>{label}</span>
      <span style={{ color: 'var(--text-primary)', wordBreak: 'break-word' }}>{value}</span>
    </div>
  );
}
