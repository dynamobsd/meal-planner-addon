// Alerte aubaines (IA). Colle le texte d'une circulaire -> l'IA repère les
// produits qui matchent la liste d'épicerie. Les aubaines PERTINENTES (sur ta
// liste) sont mises en avant. Nécessite une clé API Anthropic côté add-on.
import { useEffect, useState } from 'react';
import { getDealsStatus, scanDeals, ApiError } from '../api/client';
import type { DealMatch } from '../api/types';

interface Props {
  semaine: string;
  onBack: () => void;
}

export function DealsView({ semaine, onBack }: Props) {
  const [status, setStatus] = useState<'loading' | 'on' | 'off' | 'error'>(
    'loading',
  );
  const [texte, setTexte] = useState('');
  const [magasin, setMagasin] = useState('');
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<DealMatch[] | null>(null);

  useEffect(() => {
    getDealsStatus()
      .then((s) => setStatus(s.disponible ? 'on' : 'off'))
      .catch(() => setStatus('error'));
  }, []);

  const scan = async () => {
    if (texte.trim() === '') return;
    setScanning(true);
    setError(null);
    setResults(null);
    try {
      const res = await scanDeals({
        texte_circulaire: texte,
        semaine,
        magasin: magasin.trim() || undefined,
      });
      if (!res.ok || !res.disponible) {
        setError(res.message || 'Analyse indisponible.');
      } else {
        setResults(res.aubaines);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Analyse impossible.');
    } finally {
      setScanning(false);
    }
  };

  const pertinentes = (results ?? []).filter((d) => d.pertinent);
  const autres = (results ?? []).filter((d) => !d.pertinent);

  return (
    <div>
      <button className="btn secondary" onClick={onBack}>
        ← Retour à l'épicerie
      </button>

      <h2 className="section-title">🏷️ Alerte aubaines</h2>

      {status === 'loading' && (
        <div className="state-center">
          <div className="spinner" />
        </div>
      )}

      {status === 'error' && (
        <div className="notice error">
          Impossible de vérifier la disponibilité du service IA.
        </div>
      )}

      {status === 'off' && (
        <div className="notice info">
          Fonctionnalité IA désactivée. Configure ta clé API Anthropic dans les
          options de l'add-on Home Assistant pour l'activer.
        </div>
      )}

      {status === 'on' && (
        <>
          <div className="field">
            <label htmlFor="d-magasin">Magasin (optionnel)</label>
            <input
              id="d-magasin"
              value={magasin}
              onChange={(e) => setMagasin(e.target.value)}
              placeholder="Ex : Metro, IGA…"
            />
          </div>
          <div className="field">
            <label htmlFor="d-texte">Texte de la circulaire</label>
            <textarea
              id="d-texte"
              value={texte}
              onChange={(e) => setTexte(e.target.value)}
              placeholder="Colle ici le texte de la circulaire…"
              style={{ minHeight: 160 }}
            />
          </div>
          <button
            className="btn block"
            onClick={scan}
            disabled={scanning || texte.trim() === ''}
          >
            {scanning ? 'Analyse en cours…' : 'Trouver les aubaines'}
          </button>

          {error && (
            <div className="notice error" style={{ marginTop: 16 }}>
              {error}
            </div>
          )}

          {results && results.length === 0 && !error && (
            <div className="state-center">
              <p>Aucune aubaine détectée dans ce texte.</p>
            </div>
          )}

          {pertinentes.length > 0 && (
            <>
              <h3 className="section-title">Sur ta liste</h3>
              {pertinentes.map((d, i) => (
                <DealCard key={`p-${i}`} deal={d} highlight />
              ))}
            </>
          )}

          {autres.length > 0 && (
            <>
              <h3 className="section-title">Autres aubaines</h3>
              {autres.map((d, i) => (
                <DealCard key={`a-${i}`} deal={d} />
              ))}
            </>
          )}
        </>
      )}
    </div>
  );
}

function DealCard({ deal, highlight }: { deal: DealMatch; highlight?: boolean }) {
  return (
    <div className={`deal-card${highlight ? ' highlight' : ''}`}>
      <div className="deal-top">
        <span className="deal-produit">{deal.produit}</span>
        {highlight && <span className="deal-badge">Sur ta liste !</span>}
      </div>
      <div className="deal-meta">
        {deal.prix && <span className="deal-prix">{deal.prix}</span>}
        {deal.rabais && <span className="deal-rabais">{deal.rabais}</span>}
      </div>
      {deal.ingredient_liste && (
        <div className="deal-lien">↳ {deal.ingredient_liste}</div>
      )}
      {deal.note && <div className="deal-note">{deal.note}</div>}
    </div>
  );
}
