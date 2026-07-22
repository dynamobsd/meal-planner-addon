// Utilitaires de dates pour le planning et l'épicerie (semaine ISO, lundi).

/** Renvoie une nouvelle Date correspondant au LUNDI de la semaine de `d`. */
export function mondayOf(d: Date): Date {
  const date = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const day = date.getDay(); // 0 = dimanche … 6 = samedi
  const offset = day === 0 ? -6 : 1 - day; // ramène au lundi
  date.setDate(date.getDate() + offset);
  return date;
}

/** Formate une Date en 'YYYY-MM-DD' (heure locale, sans décalage UTC). */
export function toISODate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

/** Renvoie une nouvelle Date décalée de `n` jours. */
export function addDays(d: Date, n: number): Date {
  const r = new Date(d);
  r.setDate(r.getDate() + n);
  return r;
}

const JOURS = [
  'Lundi',
  'Mardi',
  'Mercredi',
  'Jeudi',
  'Vendredi',
  'Samedi',
  'Dimanche',
];

const MOIS = [
  'janv.',
  'févr.',
  'mars',
  'avr.',
  'mai',
  'juin',
  'juil.',
  'août',
  'sept.',
  'oct.',
  'nov.',
  'déc.',
];

/** Nom du jour (Lundi…Dimanche) pour un index 0..6 depuis lundi. */
export const jourNom = (i: number) => JOURS[i];

/** Ex : "21 juil." */
export function dayShort(d: Date): string {
  return `${d.getDate()} ${MOIS[d.getMonth()]}`;
}

/** Libellé de semaine, ex : "Semaine du 21 juil. au 27 juil. 2026". */
export function weekLabel(monday: Date): string {
  const sunday = addDays(monday, 6);
  return `Semaine du ${dayShort(monday)} au ${dayShort(sunday)} ${sunday.getFullYear()}`;
}
