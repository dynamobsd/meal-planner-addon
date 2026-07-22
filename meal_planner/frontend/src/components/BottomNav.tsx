// Barre de navigation fixe en bas — 5 onglets, cibles tactiles >= 44px.
export type Tab =
  | 'recettes'
  | 'planning'
  | 'epicerie'
  | 'garde-manger'
  | 'reglages';

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: 'recettes', label: 'Recettes', icon: '🍽️' },
  { id: 'planning', label: 'Planning', icon: '📅' },
  { id: 'epicerie', label: 'Épicerie', icon: '🛒' },
  { id: 'garde-manger', label: 'Garde-manger', icon: '🥫' },
  { id: 'reglages', label: 'Réglages', icon: '⚙️' },
];

interface Props {
  active: Tab;
  onChange: (t: Tab) => void;
}

export function BottomNav({ active, onChange }: Props) {
  return (
    <nav className="bottom-nav" aria-label="Navigation principale">
      {TABS.map((t) => (
        <button
          key={t.id}
          className={active === t.id ? 'active' : ''}
          aria-current={active === t.id ? 'page' : undefined}
          onClick={() => onChange(t.id)}
        >
          <span className="nav-icon" aria-hidden="true">
            {t.icon}
          </span>
          <span>{t.label}</span>
        </button>
      ))}
    </nav>
  );
}
