// Affichage (lecture seule) ou saisie d'une note en étoiles.
interface Props {
  value: number;
  onChange?: (v: number) => void; // si fourni -> mode saisie tactile
}

export function StarRating({ value, onChange }: Props) {
  const editable = typeof onChange === 'function';
  const stars = [1, 2, 3, 4, 5];

  if (editable) {
    return (
      <div className="stars input" role="group" aria-label="Note en étoiles">
        {stars.map((n) => (
          <span
            key={n}
            role="button"
            aria-label={`${n} étoile${n > 1 ? 's' : ''}`}
            onClick={() => onChange!(n === value ? 0 : n)}
          >
            {n <= value ? '★' : '☆'}
          </span>
        ))}
      </div>
    );
  }

  return (
    <div className="stars" aria-label={`Note ${value} sur 5`}>
      {stars.map((n) => (
        <span key={n} className={n <= value ? '' : 'empty'}>
          {n <= value ? '★' : '☆'}
        </span>
      ))}
    </div>
  );
}
