import type { EmotionKey } from '../lib/types';

// 6 emosi jurnal dari array `E` prototipe: warna wajah, warna petak kalender, ekspresi.
// Kelas Tailwind ditulis utuh (bukan dirakit) supaya ikut terbentuk saat build.
export const EMOTIONS: { key: EmotionKey; face: string; tile: string; d: string }[] = [
  { key: 'senang', face: 'fill-emo-senang', tile: 'bg-emo-senang-tile', d: 'M8 14c1 1.6 2.4 2.4 4 2.4s3-.8 4-2.4M9 9.5h.01M15 9.5h.01' },
  { key: 'sedih', face: 'fill-emo-sedih', tile: 'bg-emo-sedih-tile', d: 'M8.5 16.5c.9-1.3 2.1-2 3.5-2s2.6.7 3.5 2M9 10h.01M15 10h.01M7.5 8l2-.8M16.5 8l-2-.8' },
  { key: 'cemas', face: 'fill-emo-cemas', tile: 'bg-emo-cemas-tile', d: 'M8 15.5q1-1 2 0t2 0 2 0 2 0M9 10.5h.01M15 10.5h.01M7.5 7.5l2 .8M16.5 7.5l-2 .8' },
  { key: 'marah', face: 'fill-emo-marah', tile: 'bg-emo-marah-tile', d: 'M9 16h6M9 11h.01M15 11h.01M7.5 8l3 1.5M16.5 8l-3 1.5' },
  { key: 'malu_bersalah', face: 'fill-emo-malu', tile: 'bg-emo-malu-tile', d: 'M10 15.5q2 1.2 4 0M8.5 10.5q1 .8 2 0M13.5 10.5q1 .8 2 0M6.8 13.2h1.6M15.6 13.2h1.6' },
  { key: 'netral', face: 'fill-emo-netral', tile: 'bg-emo-netral-tile', d: 'M9 15h6M9 10h.01M15 10h.01' },
];

export const TILE_OF: Record<EmotionKey, string> = Object.fromEntries(EMOTIONS.map((e) => [e.key, e.tile])) as Record<
  EmotionKey,
  string
>;

export function EmotionFace({ face, d }: { face: string; d: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-38 w-38 stroke-navy" aria-hidden="true">
      <circle cx="12" cy="12" r="9.5" className={face} />
      <path d={d} />
    </svg>
  );
}
