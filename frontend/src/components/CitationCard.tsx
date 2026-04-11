import type { Citation } from '../utils/types';

function stripHtml(text: string): string {
  return text.replace(/<[^>]+>/g, '').replace(/&[a-zA-Z]+;/g, ' ').replace(/\s+/g, ' ').trim();
}

interface Props {
  citation: Citation;
  index: number;
  onClick: () => void;
}

const LEVEL_LABELS: Record<string, string> = {
  systematic_review: 'Systematic Review',
  rct: 'RCT',
  guideline: 'Guideline',
  cohort: 'Cohort',
  case_control: 'Case-Control',
  case_report: 'Case Report',
  expert_opinion: 'Expert Opinion',
  textbook: 'Textbook',
  public_health: 'Public Health',
  unknown: '',
};

export default function CitationCard({ citation, index, onClick }: Props) {
  const levelLabel = LEVEL_LABELS[citation.evidence_level] || '';

  return (
    <div className="citation-card" onClick={onClick}>
      <div style={{ display: 'flex', alignItems: 'flex-start' }}>
        <span className="citation-number">{index + 1}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="citation-title">{stripHtml(citation.title)}</div>
          <div className="citation-meta">
            {citation.source_name && (
              <span className="citation-meta-item">📄 {citation.source_name}</span>
            )}
            {citation.journal && (
              <span className="citation-meta-item">· {citation.journal}</span>
            )}
            {citation.year && (
              <span className="citation-meta-item">· {citation.year}</span>
            )}
            {levelLabel && (
              <span className="evidence-badge">{levelLabel}</span>
            )}
          </div>
          {citation.excerpt && (
            <div className="citation-excerpt">{stripHtml(citation.excerpt)}</div>
          )}
        </div>
      </div>
    </div>
  );
}
