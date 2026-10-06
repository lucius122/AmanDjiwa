// 8 avatar onboarding (urutan = nilai `avatar` 0–7 di backend). Dari array `AV` prototipe.
export const AVATARS = [
  { bg: 'bg-teal-100', ink: 'stroke-teal-600', d: 'M12 3l2.6 5.5 6 .8-4.4 4.2 1.1 6L12 16.6 6.7 19.5l1.1-6L3.4 9.3l6-.8z' },
  { bg: 'bg-lavender-100', ink: 'stroke-lavender-600', d: 'M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z' },
  { bg: 'bg-butter-100', ink: 'stroke-butter-700', d: 'M12 8a4 4 0 1 1 0 8 4 4 0 0 1 0-8zM12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.4 1.4M17.6 17.6L19 19M5 19l1.4-1.4M17.6 6.4L19 5' },
  { bg: 'bg-leaf-100', ink: 'stroke-leaf-700', d: 'M5 19C5 10 11 5 20 4c0 9-5 15-14 15zM5 19l7-7' },
  { bg: 'bg-sky-100', ink: 'stroke-navy', d: 'M7 18a4 4 0 0 1-.5-8A5.5 5.5 0 0 1 17 8.5 4.5 4.5 0 0 1 17.5 18z' },
  { bg: 'bg-rose-100', ink: 'stroke-rose-700', d: 'M12 21s-7.5-4.6-9.6-9.2C.9 8.4 3 4.5 6.7 4.5c2.1 0 3.6 1.1 4.3 2.4.7-1.3 2.2-2.4 4.3-2.4 3.7 0 5.8 3.9 4.3 7.3C19.5 16.4 12 21 12 21z' },
  { bg: 'bg-peach-100', ink: 'stroke-peach-600', d: 'M9 18V6l10-2v12M6 15a3 3 0 1 1 0 6 3 3 0 0 1 0-6zM16 13a3 3 0 1 1 0 6 3 3 0 0 1 0-6z' },
  { bg: 'bg-sand-150', ink: 'stroke-muted', d: 'M3 12c3-4 6 4 9 0s6 4 9 0M3 17c3-4 6 4 9 0s6 4 9 0' },
] as const;

export function Avatar({ index, size }: { index: number; size: 'sm' | 'lg' }) {
  const a = AVATARS[index] ?? AVATARS[0];
  const box = size === 'sm' ? 'h-40 w-40' : 'h-64 w-64';
  const icon = size === 'sm' ? 'h-22 w-22' : 'h-32 w-32';
  return (
    <span className={`flex flex-none items-center justify-center rounded-full ${box} ${a.bg}`}>
      <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={`${icon} ${a.ink}`} aria-hidden="true">
        <path d={a.d} />
      </svg>
    </span>
  );
}
