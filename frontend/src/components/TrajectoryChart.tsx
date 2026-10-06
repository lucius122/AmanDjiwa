// Grafik "Lintasan emosi 14 hari" (dasbor staf). Geometri sama dengan prototipe: viewBox 420×150,
// nilai −2..+2 → y = 75 − v·27.5. Hari tanpa data dilewati (garis menyambung titik yang ada).
const W = 420;
const MID = 75;
const UNIT = 27.5;

export function TrajectoryChart({ points }: { points: (number | null)[] }) {
  const step = W / (points.length - 1);
  const pts = points.flatMap((v, i) => (v === null ? [] : [[i * step, MID - v * UNIT] as const]));
  // Satu titik saja → garis nol-panjang; ujung bulat membuatnya tampil sebagai titik.
  const line = pts.length ? 'M' + pts.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join(' L') + (pts.length === 1 ? ' h0.01' : '') : '';
  const area = pts.length ? `${line} L${pts[pts.length - 1][0].toFixed(1)} 150 L${pts[0][0].toFixed(1)} 150 Z` : '';
  return (
    <svg viewBox="0 0 420 150" preserveAspectRatio="none" className="h-130 w-full" aria-hidden="true">
      <line x1="0" y1="20" x2="420" y2="20" className="stroke-sand-100" />
      <line x1="0" y1="75" x2="420" y2="75" className="stroke-sand-300" strokeDasharray="4 4" />
      <line x1="0" y1="130" x2="420" y2="130" className="stroke-sand-100" />
      {pts.length > 0 && (
        <>
          <path d={area} className="fill-teal-500" opacity=".12" />
          <path
            d={line}
            fill="none"
            className="stroke-teal-600"
            strokeWidth={pts.length === 1 ? 8 : 2.5}
            strokeLinejoin="round"
            strokeLinecap="round"
            vectorEffect="non-scaling-stroke"
          />
        </>
      )}
    </svg>
  );
}
