// Ilustrasi flat pengganti placeholder desain (disetujui 2026-10-05). Hanya warna token.
// Hero: "remaja memegang HP, tersenyum tenang". Menunggu: "remaja duduk santai, amplop terbang".

/** Bintang empat sudut (aksen). */
function Sparkle({ x, y, r, className }: { x: number; y: number; r: number; className: string }) {
  return (
    <path
      className={className}
      d={`M${x} ${y - r}Q${x} ${y} ${x + r} ${y}Q${x} ${y} ${x} ${y + r}Q${x} ${y} ${x - r} ${y}Q${x} ${y} ${x} ${y - r}Z`}
    />
  );
}

/** Remaja setengah badan memegang HP. Koordinat asli: viewBox 0 0 500 400. */
function TeenBust({ transform }: { transform?: string }) {
  return (
    <g transform={transform}>
      {/* hoodie & tudung */}
      <path className="fill-teal-500" d="M128 400C134 318 182 280 250 278C318 280 366 318 372 400Z" />
      <path className="fill-teal-600" d="M196 294C202 262 222 248 250 248C278 248 298 262 304 294C286 280 270 276 250 276C230 276 214 280 196 294Z" />
      <path className="stroke-white" d="M238 300v24M262 300v24" strokeWidth="3" strokeLinecap="round" />
      {/* leher, kepala, telinga */}
      <rect className="fill-peach-300" x="236" y="232" width="28" height="48" rx="12" />
      <circle className="fill-peach-300" cx="201" cy="203" r="9" />
      <circle className="fill-peach-300" cx="299" cy="203" r="9" />
      <circle className="fill-peach-300" cx="250" cy="196" r="50" />
      {/* rambut */}
      <path className="fill-navy" d="M197 202C190 150 221 131 252 131C285 131 311 152 303 202C296 178 280 165 257 163C235 161 213 172 204 196Z" />
      <path className="fill-navy" d="M212 174C230 150 270 147 294 170C272 161 246 163 226 184Z" />
      {/* wajah: mata terpejam senang, senyum, pipi */}
      <path className="stroke-navy" d="M226 203q7 7 14 0M260 203q7 7 14 0M238 222q12 10 24 0" strokeWidth="3.2" strokeLinecap="round" fill="none" />
      <ellipse className="fill-emo-malu-tile" cx="222" cy="216" rx="7" ry="4.5" />
      <ellipse className="fill-emo-malu-tile" cx="278" cy="216" rx="7" ry="4.5" />
      {/* lengan */}
      <path className="fill-teal-600" d="M168 400L208 340Q215 331 226 338L226 362L200 400Z" />
      <path className="fill-teal-600" d="M332 400L292 340Q285 331 274 338L274 362L300 400Z" />
      {/* HP dengan obrolan di layar */}
      <rect className="fill-navy" x="222" y="296" width="56" height="92" rx="11" />
      <rect className="fill-white" x="228" y="304" width="44" height="74" rx="6" />
      <rect className="fill-teal-200" x="233" y="312" width="26" height="9" rx="4.5" />
      <rect className="fill-teal-500" x="241" y="326" width="26" height="9" rx="4.5" />
      <rect className="fill-teal-200" x="233" y="340" width="20" height="9" rx="4.5" />
      {/* tangan */}
      <ellipse className="fill-peach-300" cx="224" cy="347" rx="11" ry="15" />
      <ellipse className="fill-peach-300" cx="276" cy="347" rx="11" ry="15" />
    </g>
  );
}

export function HeroIllustration({ label }: { label: string }) {
  return (
    <svg viewBox="0 0 500 400" role="img" aria-label={label} className="block h-full w-full">
      <circle className="fill-white-60" cx="250" cy="252" r="168" />
      {/* daun */}
      <path className="fill-teal-300" d="M58 400C56 358 70 330 98 318C96 350 84 378 58 400Z" />
      <path className="fill-teal-200" d="M70 400C84 366 106 350 136 348C124 376 100 392 70 400Z" />
      {/* gelembung Djiwa sedang mengetik */}
      <g transform="translate(330 66)">
        <rect className="fill-white" width="124" height="58" rx="22" />
        <path className="fill-white" d="M22 52l-8 20 26-18Z" />
        <circle className="fill-teal-500" cx="40" cy="29" r="6" />
        <circle className="fill-teal-500" cx="62" cy="29" r="6" />
        <circle className="fill-teal-500" cx="84" cy="29" r="6" />
      </g>
      {/* gelembung pesan remaja */}
      <g transform="translate(44 146)">
        <rect className="fill-teal-600" width="112" height="50" rx="20" />
        <path className="fill-teal-600" d="M86 44l18 18-4-20Z" />
        <rect className="fill-white" x="18" y="15" width="64" height="7" rx="3.5" />
        <rect className="fill-white-60" x="18" y="28" width="42" height="7" rx="3.5" />
      </g>
      {/* hati */}
      <circle className="fill-lavender-100" cx="414" cy="198" r="26" />
      <path
        className="fill-lavender-600"
        transform="translate(400 184) scale(1.15)"
        d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
      />
      <Sparkle x={104} y={92} r={14} className="fill-butter-300" />
      <Sparkle x={432} y={300} r={10} className="fill-butter-300" />
      <Sparkle x={76} y={262} r={8} className="fill-teal-300" />
      <TeenBust />
    </svg>
  );
}

export function WaitingIllustration({ label }: { label: string }) {
  return (
    <svg viewBox="0 0 400 300" role="img" aria-label={label} className="block h-full w-full">
      <circle className="fill-white-60" cx="200" cy="176" r="124" />
      {/* jejak terbang amplop */}
      <path className="stroke-lavender-300" d="M132 176C176 104 242 160 296 92" fill="none" strokeWidth="3" strokeDasharray="2 9" strokeLinecap="round" />
      <g transform="translate(304 84) rotate(-12)">
        <path className="stroke-lavender-300" d="M-46-6h-14M-44 7h-10" strokeWidth="3" strokeLinecap="round" />
        <rect className="fill-white stroke-lavender-600" x="-30" y="-20" width="60" height="40" rx="6" strokeWidth="2.5" />
        <path className="stroke-lavender-600" d="M-28-16L0 4l28-20" fill="none" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
      </g>
      <Sparkle x={262} y={46} r={9} className="fill-butter-300" />
      <Sparkle x={350} y={150} r={7} className="fill-butter-300" />
      {/* bantal duduk + remaja santai */}
      <ellipse className="fill-lavender-300" cx="132" cy="272" rx="92" ry="36" />
      <TeenBust transform="translate(-6 66) scale(.56)" />
    </svg>
  );
}
