import { useState } from 'react';
import type { AnswerResponse, Citation } from '../utils/types';
import CitationModal from './CitationModal';

function stripHtml(t: string): string {
  return t.replace(/<[^>]+>/g, '').replace(/&[a-zA-Z]+;/g, ' ').replace(/\s+/g, ' ').trim();
}

const JOURNAL_MAP: Record<string, { short: string; color: string }> = {
  'nejm':{ short:'NEJM', color:'#c0392b' }, 'new england':{ short:'NEJM', color:'#c0392b' },
  'lancet':{ short:'Lancet', color:'#8e44ad' }, 'jama':{ short:'JAMA', color:'#2980b9' },
  'bmj':{ short:'BMJ', color:'#27ae60' }, 'cochrane':{ short:'Cochrane', color:'#e67e22' },
  'circulation':{ short:'Circulation', color:'#e74c3c' }, 'blood':{ short:'Blood', color:'#c0392b' },
  'chest':{ short:'Chest', color:'#2c3e50' }, 'annals':{ short:'Ann Int Med', color:'#16a085' },
  'critical care':{ short:'Crit Care', color:'#d35400' }, 'diabetes care':{ short:'Diabetes Care', color:'#e74c3c' },
  'pubmed':{ short:'PubMed', color:'#326599' }, 'europe_pmc':{ short:'Europe PMC', color:'#27ae60' },
  'who':{ short:'WHO', color:'#3498db' }, 'cdc':{ short:'CDC', color:'#2c3e50' },
  'medlineplus':{ short:'MedlinePlus', color:'#27ae60' }, 'openfda':{ short:'FDA', color:'#e67e22' },
  'ncbi_books':{ short:'NCBI Books', color:'#8e44ad' }, 'web_search':{ short:'Web', color:'#7f8c8d' },
  'thorax':{ short:'Thorax', color:'#9b59b6' }, 'plos':{ short:'PLoS', color:'#f39c12' },
};

function getJournalInfo(cit: Citation): { short: string; color: string } {
  const combined = `${cit.journal||''} ${cit.source_name||''} ${cit.source_id||''}`.toLowerCase();
  for (const [key, val] of Object.entries(JOURNAL_MAP)) {
    if (combined.includes(key)) return val;
  }
  return { short: (cit.journal || cit.source_name || 'Source').slice(0, 14), color: '#7f8c8d' };
}

function isNew(cit: Citation): boolean { return !!(cit.year && cit.year >= 2026) || !!(cit.pub_date && cit.pub_date.includes('2026')); }
function isGuideline(cit: Citation): boolean { const t = `${cit.title||''} ${cit.evidence_level||''}`.toLowerCase(); return t.includes('guideline') || t.includes('consensus') || t.includes('recommendation') || t.includes('standard') || cit.evidence_level === 'clinical_guideline'; }
function isMetaAnalysis(cit: Citation): boolean { const t = (cit.title||'').toLowerCase(); return t.includes('meta-analysis') || t.includes('meta analysis') || t.includes('systematic review'); }

function renderTextWithCitations(text: string, citations: Citation[], onCitClick: (c: Citation) => void): JSX.Element {
  const parts = text.split(/(\[\d+(?:,\s*\d+)*\])/g);
  return <>
    {parts.map((part, i) => {
      const m = part.match(/^\[(\d+(?:,\s*\d+)*)\]$/);
      if (m) {
        const nums = m[1].split(',').map(n => parseInt(n.trim()) - 1);
        const first = citations[nums[0]];
        if (!first) return <sup key={i} style={{color:'var(--accent-text)'}}>[{nums[0]+1}]</sup>;
        const info = getJournalInfo(first);
        const extra = nums.length - 1;
        return (
          <span key={i} onClick={() => onCitClick(first)} style={{
            display:'inline-flex', alignItems:'center', gap:3,
            background:info.color+'1a', border:`1px solid ${info.color}40`,
            borderRadius:12, padding:'2px 8px', margin:'0 2px',
            fontSize:11, fontWeight:600, color:info.color,
            cursor:'pointer', verticalAlign:'middle', lineHeight:'18px',
          }}>
            <span style={{width:7,height:7,borderRadius:'50%',background:info.color,display:'inline-block'}}/>
            {info.short}{extra > 0 && <span style={{opacity:0.7}}>{` + ${extra}`}</span>}
          </span>
        );
      }
      return <span key={i}>{part}</span>;
    })}
  </>;
}

interface Props { query: string; answer: AnswerResponse | null; loading: boolean; error: string | null; onBookmark: () => void; isBookmarked: boolean; teachingMode: boolean; }

export default function AnswerView({ query, answer, loading, error, onBookmark, isBookmarked }: Props) {
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [showAllRefs, setShowAllRefs] = useState(false);

  if (loading) return (
    <div className="answer-view">
      <div className="user-query-bubble">{query}</div>
      <div className="loading-container">
        <div className="loading-dots"><div className="loading-dot"/><div className="loading-dot"/><div className="loading-dot"/></div>
        <div className="loading-text">Searching evidence + AI synthesis…</div>
        <div className="loading-text" style={{fontSize:11,marginTop:4,opacity:0.6}}>PubMed · WHO · CDC · Europe PMC · Web Search</div>
      </div>
    </div>
  );

  if (error) return (
    <div className="answer-view">
      <div className="user-query-bubble">{query}</div>
      <div className="answer-card"><div className="warning-banner warning-info"><span>⚠️</span><span>{error}</span></div></div>
    </div>
  );

  if (!answer) return null;

  const refs = answer.citations.slice(0, 15);
  const visibleRefs = showAllRefs ? refs : refs.slice(0, 6);
  const lastUpdated = new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

  return (
    <div className="answer-view">
      <div className="user-query-bubble">{query}</div>
      <div className="answer-card">
        <div className="answer-meta">
          <span className={`answer-badge badge-${answer.confidence}`}>
            {answer.confidence === 'high' ? '✓ HIGH CONFIDENCE' : answer.confidence === 'ai-generated' ? '🤖 AI-GENERATED' : `~ ${answer.confidence.toUpperCase()} CONFIDENCE`}
          </span>
          {answer.teaching_mode && <span className="answer-badge badge-moderate">📚 Teaching</span>}
          <span className="answer-timing">{(answer.retrieval_time_ms / 1000).toFixed(1)}s · {refs.length} sources</span>
        </div>

        {answer.warnings.map((w, i) => (
          <div key={i} className={`warning-banner ${w.includes('EMERGENCY') ? 'warning-emergency' : 'warning-info'}`}>
            <span>{w.includes('EMERGENCY') ? '🚨' : 'ℹ️'}</span><span>{w}</span>
          </div>
        ))}

        {/* Answer body with inline OpenEvidence-style citation badges */}
        <div className="answer-body">
          {answer.blocks.map((block, i) => (
            <div key={i} className="answer-block">
              {block.block_type === 'heading' ? (
                <h3 style={{fontSize:'var(--fs-md)',fontWeight:700,color:'var(--text-heading)',marginTop:20,marginBottom:8}}>{block.text.replace(/\*/g, '')}</h3>
              ) : (
                <p style={{lineHeight:1.8}}>
                  {renderTextWithCitations(block.text, refs, setSelectedCitation)}
                </p>
              )}
            </div>
          ))}
        </div>

        <div className="answer-actions">
          <button className="btn btn-ghost" onClick={onBookmark}>{isBookmarked ? '★ Bookmarked' : '☆ Bookmark'}</button>
          <button className="btn btn-ghost" onClick={() => navigator.clipboard?.writeText(answer.blocks.map(b => b.text).join('\n\n'))}>📋 Copy</button>
        </div>

        {/* References — OpenEvidence style */}
        {refs.length > 0 && (
          <div style={{borderTop:'1px solid var(--border)',marginTop:16,paddingTop:16}}>
            <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:14}}>
              <div style={{display:'flex',alignItems:'center',gap:8}}>
                <span style={{fontSize:14,fontWeight:700,color:'var(--text-tertiary)'}}>📋</span>
                <h3 style={{fontSize:'var(--fs-md)',fontWeight:700,color:'var(--text-heading)',margin:0}}>References</h3>
              </div>
              <span style={{fontSize:11,color:'var(--text-tertiary)'}}>Updated: {lastUpdated}</span>
            </div>

            {visibleRefs.map((cit, i) => {
              const info = getJournalInfo(cit);
              return (
                <div key={cit.id}
                  onClick={() => cit.url ? window.open(cit.url, '_blank') : setSelectedCitation(cit)}
                  style={{display:'flex',gap:12,padding:'12px 0',borderBottom:i<visibleRefs.length-1?'1px solid var(--border-light)':'none',cursor:'pointer'}}>
                  <div style={{width:28,height:28,borderRadius:'50%',background:info.color,color:'white',display:'flex',alignItems:'center',justifyContent:'center',fontSize:12,fontWeight:700,flexShrink:0,marginTop:2}}>
                    {i + 1}
                  </div>
                  <div style={{flex:1,minWidth:0}}>
                    <div style={{fontSize:'var(--fs-sm)',fontWeight:600,color:'var(--text-primary)',lineHeight:1.4,marginBottom:4}}>
                      {stripHtml(cit.title)}
                    </div>
                    <div style={{display:'flex',alignItems:'center',gap:6,flexWrap:'wrap'}}>
                      <span style={{display:'inline-flex',alignItems:'center',gap:3,fontSize:11,color:info.color,fontWeight:600}}>
                        <span style={{width:6,height:6,borderRadius:'50%',background:info.color}}/>
                        {cit.journal || info.short}
                      </span>
                      {cit.year && <span style={{fontSize:11,color:'var(--text-tertiary)'}}>· {cit.year}</span>}
                      {cit.authors && <span style={{fontSize:11,color:'var(--text-tertiary)'}}>· {cit.authors.length > 40 ? cit.authors.slice(0,40)+'…' : cit.authors}</span>}
                    </div>
                    <div style={{display:'flex',gap:5,marginTop:5,flexWrap:'wrap'}}>
                      {isGuideline(cit) && <span style={{fontSize:10,fontWeight:700,color:'#27ae60',background:'#27ae6018',border:'1px solid #27ae6040',borderRadius:4,padding:'1px 6px'}}>Guideline</span>}
                      {isMetaAnalysis(cit) && <span style={{fontSize:10,fontWeight:700,color:'#e67e22',background:'#e67e2218',border:'1px solid #e67e2240',borderRadius:4,padding:'1px 6px'}}>Meta-Analysis</span>}
                      {isNew(cit) && <span style={{fontSize:10,fontWeight:700,color:'#3498db',background:'#3498db18',border:'1px solid #3498db40',borderRadius:4,padding:'1px 6px'}}>New</span>}
                    </div>
                  </div>
                </div>
              );
            })}

            {refs.length > 6 && !showAllRefs && (
              <button className="btn btn-ghost" style={{width:'100%',marginTop:10}} onClick={() => setShowAllRefs(true)}>
                Show all {refs.length} references ▾
              </button>
            )}
          </div>
        )}
      </div>

      {selectedCitation && <CitationModal citation={selectedCitation} onClose={() => setSelectedCitation(null)} />}
    </div>
  );
}
