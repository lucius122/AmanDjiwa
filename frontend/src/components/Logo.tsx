import { copy } from '../lib/copy';

/** Hati + wajah (logo AmanDjiwa) dari prototipe. */
export function LogoMark({ className }: { className: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path
        className="fill-teal-500"
        d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
      />
      <circle className="fill-white" cx="12" cy="9" r="2.1" />
      <path
        className="stroke-white"
        d="M8.4 15.2c.7-1.9 2-2.9 3.6-2.9s2.9 1 3.6 2.9"
        strokeWidth="1.7"
        fill="none"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function Wordmark({ className, accent = 'text-teal-500' }: { className: string; accent?: string }) {
  return (
    <span className={`font-extrabold tracking-tight ${className}`}>
      {copy.brand.aman}
      <span className={accent}>{copy.brand.djiwa}</span>
    </span>
  );
}

/** Avatar robot Djiwa di kepala chat. */
export function DjiwaAvatar() {
  return (
    <svg viewBox="0 0 40 40" className="h-44 w-44 flex-none" aria-hidden="true">
      <circle className="fill-teal-100" cx="20" cy="20" r="20" />
      <path className="stroke-teal-500" d="M20 7.5v4" strokeWidth="2" strokeLinecap="round" />
      <circle className="fill-teal-500" cx="20" cy="6.5" r="2.2" />
      <rect className="fill-teal-500" x="9" y="11" width="22" height="19" rx="8" />
      <rect className="fill-white" x="12.5" y="15" width="15" height="8.5" rx="4.25" />
      <circle className="fill-navy" cx="16.8" cy="19.2" r="1.6" />
      <circle className="fill-navy" cx="23.2" cy="19.2" r="1.6" />
      <path className="stroke-white" d="M17.5 26.2q2.5 1.6 5 0" strokeWidth="1.6" fill="none" strokeLinecap="round" />
    </svg>
  );
}
