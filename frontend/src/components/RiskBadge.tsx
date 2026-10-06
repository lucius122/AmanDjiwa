// HANYA untuk dasbor staf. Jangan pernah dipakai di halaman remaja (CLAUDE.md §2, §6.7).
import { copy } from '../lib/copy';
import type { CaseStatus, RiskLevel } from '../lib/types';

const RISK: Record<RiskLevel, { pill: string; dot: string }> = {
  merah: { pill: 'bg-risk-red-tint text-risk-red-text', dot: 'rounded-risk-red bg-risk-red-dot' },
  oranye: { pill: 'bg-risk-orange-tint text-risk-orange-text', dot: 'rounded-risk-orange bg-risk-orange-dot' },
  kuning: { pill: 'bg-risk-yellow-tint text-risk-yellow-text', dot: 'rounded-risk-yellow bg-risk-yellow-dot' },
};

/** Level dibedakan warna DAN bentuk titik (persegi / bulat / tetes), bukan warna saja. */
export function RiskBadge({ level, prefix = false }: { level: RiskLevel; prefix?: boolean }) {
  const s = RISK[level];
  const label = copy.staff.risk[level];
  return (
    <span className={`flex h-26 items-center gap-6 whitespace-nowrap rounded-full px-10 text-12 font-extrabold ${s.pill}`}>
      <span className={`h-8 w-8 ${s.dot}`} />
      {prefix ? `${copy.staff.riskPrefix} ${label}` : label}
    </span>
  );
}

const STATUS: Record<CaseStatus, string> = {
  baru: 'bg-sky-100 text-navy',
  ditangani: 'bg-teal-100 text-teal-800',
  selesai: 'bg-sand-100 text-muted',
  dirujuk: 'bg-lavender-100 text-lavender-700',
};

export function StatusBadge({ status, large = false }: { status: CaseStatus; large?: boolean }) {
  const size = large ? 'h-32 rounded-10 px-12 text-13' : 'h-24 rounded-8 px-8 text-11';
  return (
    <span className={`flex items-center whitespace-nowrap font-bold ${size} ${STATUS[status]}`}>
      {copy.staff.status[status]}
    </span>
  );
}
