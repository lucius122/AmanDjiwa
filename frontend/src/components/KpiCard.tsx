/** Kartu angka di dasbor kota. `tone` = warna catatan kecil di bawah angka. */
const TONE = { muted: 'text-muted', good: 'text-success-text', warn: 'text-risk-orange-text' } as const;

export function KpiCard({ label, value, note, tone = 'muted' }: { label: string; value: string; note: string; tone?: keyof typeof TONE }) {
  return (
    <div className="flex flex-col gap-6 rounded-16 border border-sand-200 bg-white px-20 py-18">
      <span className="text-13 font-semibold text-muted">{label}</span>
      <span className="text-32 font-extrabold tracking-tight">{value}</span>
      <span className={`text-12 font-semibold ${TONE[tone]}`}>{note}</span>
    </div>
  );
}
