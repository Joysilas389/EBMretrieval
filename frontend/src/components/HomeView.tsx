interface Props {
  onSearch: (q: string) => void;
}

const QUICK_QUERIES = [
  'Hypertension treatment guidelines',
  'Mechanism of action of metformin',
  'Differential diagnosis of chest pain',
  'Acute MI management',
  'Asthma vs COPD',
  'Heart failure pathophysiology',
  'Antibiotic selection for pneumonia',
  'Diabetes screening guidelines',
  'Cardiac cycle physiology',
  'Stroke thrombolysis criteria',
  'Malaria treatment WHO guidelines',
  'Sickle cell disease management',
];

export default function HomeView({ onSearch }: Props) {
  return (
    <div className="home-view">
      <div>
        <div className="home-title">Evidence-Based Medicine</div>
        <div className="home-title" style={{ color: 'var(--accent)' }}>Retrieval Platform</div>
      </div>
      <p className="home-subtitle">
        Ask any medical question. Get AI-synthesized, evidence-based answers with verified citations
        from PubMed, WHO, CDC, Europe PMC, MedlinePlus, and 300+ medical journals via web search. Powered by Claude AI + real-time evidence retrieval.
      </p>
      <div className="quick-queries">
        {QUICK_QUERIES.map((q) => (
          <button key={q} className="quick-query" onClick={() => onSearch(q)}>{q}</button>
        ))}
      </div>
      <p style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-tertiary)', maxWidth: 400 }}>
        ⚕️ For educational and reference purposes only. Does not replace clinical judgment. In emergencies, call your local emergency number.
      </p>
    </div>
  );
}
