// Placeholder propre pour les onglets non encore développés.
interface Props {
  icon: string;
  title: string;
  phase: string;
}

export function Placeholder({ icon, title, phase }: Props) {
  return (
    <div className="state-center">
      <div className="big" aria-hidden="true">
        {icon}
      </div>
      <h2 style={{ margin: '0 0 8px' }}>{title}</h2>
      <p>Bientôt disponible ({phase}).</p>
    </div>
  );
}
