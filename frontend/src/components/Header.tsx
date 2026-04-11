import type { View } from '../utils/types';

interface Props {
  onHome: () => void;
  view: View;
  setView: (v: View) => void;
}

function Logo() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Shield shape */}
      <path d="M16 2L4 7V15C4 22.18 9.12 28.84 16 30C22.88 28.84 28 22.18 28 15V7L16 2Z" fill="#1a5276" stroke="#2d5fa6" strokeWidth="1.5"/>
      {/* Cross */}
      <rect x="13.5" y="9" width="5" height="14" rx="1.2" fill="white"/>
      <rect x="9" y="13.5" width="14" height="5" rx="1.2" fill="white"/>
      {/* DNA helix accent */}
      <path d="M10 24C12 22 14 23 16 21C18 23 20 22 22 24" stroke="#5dade2" strokeWidth="1.2" strokeLinecap="round" fill="none"/>
    </svg>
  );
}

export default function Header({ onHome, view, setView }: Props) {
  return (
    <header className="header">
      <div className="header-logo" onClick={onHome}>
        <Logo />
        <span>EBMRetrieval</span>
      </div>
      <div className="header-actions">
        <button className="btn-icon" title="Compare" onClick={() => setView(view === 'compare' ? 'home' : 'compare')}>⚖️</button>
        <button className="btn-icon" title="ICD-11" onClick={() => setView(view === 'icd' ? 'home' : 'icd')}>🏷️</button>
        <button className="btn-icon" title="Animations" onClick={() => setView(view === 'animations' ? 'home' : 'animations')}>🫀</button>
        <button className="btn-icon" title="Settings" onClick={() => setView(view === 'settings' ? 'home' : 'settings')}>⚙️</button>
      </div>
    </header>
  );
}
