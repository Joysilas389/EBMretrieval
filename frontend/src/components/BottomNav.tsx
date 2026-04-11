import type { View } from '../utils/types';

interface Props {
  view: View;
  setView: (v: View) => void;
}

const NAV_ITEMS: { id: View; icon: string; label: string }[] = [
  { id: 'home', icon: '🔍', label: 'Search' },
  { id: 'compare', icon: '⚖️', label: 'Compare' },
  { id: 'history', icon: '🕐', label: 'History' },
  { id: 'bookmarks', icon: '★', label: 'Saved' },
  { id: 'settings', icon: '⚙️', label: 'More' },
];

export default function BottomNav({ view, setView }: Props) {
  return (
    <nav className="bottom-nav">
      {NAV_ITEMS.map((item) => (
        <button
          key={item.id}
          className={`nav-item ${view === item.id || (item.id === 'home' && view === 'answer') ? 'active' : ''}`}
          onClick={() => setView(item.id)}
        >
          <span className="nav-icon">{item.icon}</span>
          <span>{item.label}</span>
        </button>
      ))}
    </nav>
  );
}
