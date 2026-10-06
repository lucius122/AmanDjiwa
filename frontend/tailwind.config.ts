import type { Config } from 'tailwindcss';

// Semua nilai warna/shadow ada di src/styles/tokens.css. File ini hanya memetakan ke kelas.
const c = (name: string) => `var(--c-${name})`;
const scale = (name: string, steps: (string | number)[]) =>
  Object.fromEntries(steps.map((s) => [s, c(`${name}-${s}`)]));

// ponytail: skala px 1:1 dengan desain (w-240 = 240px, p-18 = 18px) supaya transkripsi
// dari HTML tidak butuh nilai arbitrer. Ganti ke skala bernama kalau desain dirapikan ke grid 4px.
const px = (max: number) =>
  Object.fromEntries(Array.from({ length: max + 1 }, (_, i) => [String(i), `${i}px`]));

const spacing = px(1440);

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    // Breakpoint mengikuti logika lebar di prototipe.
    screens: {
      md: '760px', // dasbor pendamping: antrian + detail berdampingan
      lg: '900px', // app remaja: sidebar (bukan bottom nav), sheet di tengah
      xl: '1200px', // dasbor pendamping: sidebar penuh
      '2xl': '1300px', // dasbor kota: label minggu lengkap
    },
    colors: {
      transparent: 'transparent',
      current: 'currentColor',
      white: { DEFAULT: c('white'), ...scale('white', [12, 35, 50, 60]) },
      navy: c('navy'),
      cream: c('cream'),
      overlay: c('overlay'),
      muted: {
        DEFAULT: c('muted'),
        strong: c('muted-strong'),
        deep: c('muted-deep'),
        placeholder: c('muted-placeholder'),
      },
      'on-navy': { muted: c('on-navy-muted'), line: c('on-navy-line') },
      sand: scale('sand', [100, 150, 200, 300, 400, 500]),
      teal: {
        ...scale('teal', [25, 30, 50, 75, 100, 200, 300, 400, 500, 600, 700, 800]),
        muted: c('teal-muted'),
        disabled: c('teal-disabled'),
      },
      sky: scale('sky', [100, 200]),
      peach: scale('peach', [100, 200, 300, 600, 700, 800]),
      lavender: scale('lavender', [100, 200, 300, 600, 700, 800]),
      butter: scale('butter', [100, 300, 700, 800]),
      rose: scale('rose', [100, 700]),
      leaf: scale('leaf', [100, 700]),
      warn: { DEFAULT: c('warn'), text: c('warn-text') },
      success: { text: c('success-text') },
      // Hanya untuk dasbor staf. Jangan pernah dipakai di halaman remaja (CLAUDE.md §2, §6.7).
      risk: {
        red: scale('risk-red', ['tint', 'text', 'dot', 'row', 'row-line', 'bar']),
        orange: scale('risk-orange', ['tint', 'text', 'dot', 'bar']),
        yellow: scale('risk-yellow', ['tint', 'text', 'dot', 'bar']),
        green: scale('risk-green', ['bar']),
      },
      map: scale('map', [1, 2, 3, 4]),
      emo: Object.fromEntries(
        ['senang', 'sedih', 'cemas', 'marah', 'malu', 'netral'].map((e) => [
          e,
          { DEFAULT: c(`emo-${e}`), tile: c(`emo-${e}-tile`) },
        ]),
      ),
      chart: scale('chart', ['senang', 'cemas', 'sedih', 'netral']),
    },
    fontFamily: { sans: 'var(--font-sans)' },
    spacing,
    maxWidth: { ...spacing, none: 'none', full: '100%', bubble: '82%' },
    minWidth: { ...spacing, full: '100%' },
    maxHeight: { ...spacing, full: '100%', '90vh': '90vh' },
    minHeight: { ...spacing, full: '100%', screen: '100vh' },
    fontSize: {
      ...px(36),
      // Judul responsif dari desain, dinamai menurut ukuran maksimumnya.
      'fluid-19': 'clamp(16px,1.6vw,19px)',
      'fluid-24': 'clamp(20px,2.4vw,24px)',
      'fluid-26': 'clamp(20px,2.4vw,26px)',
      'fluid-30': 'clamp(22px,2.6vw,30px)',
      'fluid-34': 'clamp(24px,3vw,34px)',
      'fluid-60': 'clamp(34px,5.2vw,60px)',
    },
    lineHeight: {
      normal: 'normal',
      106: '1.06',
      120: '1.2',
      125: '1.25',
      130: '1.3',
      145: '1.45',
      150: '1.5',
      155: '1.55',
      160: '1.6',
    },
    letterSpacing: {
      normal: '0',
      tightest: '-.03em',
      tight: '-.02em',
      wide: '.06em',
      wider: '.2em',
      widest: '.5em',
    },
    borderRadius: {
      ...Object.fromEntries(
        [0, 2, 3, 4, 5, 6, 8, 9, 10, 12, 14, 16, 18, 20, 22, 24, 28].map((r) => [r, `${r}px`]),
      ),
      full: '9999px',
      'bubble-in': 'var(--r-bubble-in)',
      'bubble-out': 'var(--r-bubble-out)',
      sheet: 'var(--r-sheet)',
      'risk-red': 'var(--r-risk-red)',
      'risk-orange': 'var(--r-risk-orange)',
      'risk-yellow': 'var(--r-risk-yellow)',
    },
    borderWidth: { DEFAULT: '1px', 0: '0', 1: '1px', 1.5: '1.5px', 2: '2px', 2.5: '2.5px', 3: '3px' },
    boxShadow: {
      none: 'none',
      panel: 'var(--shadow-panel)',
      toast: 'var(--shadow-toast)',
      lift: 'var(--shadow-lift)',
    },
    aspectRatio: { square: '1', '5/4': '5 / 4', '4/3': '4 / 3', map: '560 / 340' },
    keyframes: {
      'dj-dot': {
        '0%, 60%, 100%': { opacity: '.3', transform: 'translateY(0)' },
        '30%': { opacity: '1', transform: 'translateY(-3px)' },
      },
      'dj-breathe': {
        '0%': { transform: 'scale(.55)' },
        '21%': { transform: 'scale(1)' },
        '58%': { transform: 'scale(1)' },
        '100%': { transform: 'scale(.55)' },
      },
      'dj-in': {
        from: { opacity: '0', transform: 'translateY(6px)' },
        to: { opacity: '1', transform: 'none' },
      },
    },
    animation: {
      none: 'none',
      'in-25': 'dj-in .25s ease-out',
      'in-30': 'dj-in .3s ease-out',
      'in-35': 'dj-in .35s ease-out',
      'in-50': 'dj-in .5s ease-out',
      dot: 'dj-dot 1.2s infinite ease-in-out',
      breathe: 'dj-breathe 19s linear infinite',
    },
    extend: {
      // Grid responsif dari landing desain: kolom turun otomatis saat lebar < minimum.
      gridTemplateColumns: {
        'fit-150': 'repeat(auto-fit,minmax(150px,1fr))',
        'fit-280': 'repeat(auto-fit,minmax(min(100%,280px),1fr))',
        'fit-380': 'repeat(auto-fit,minmax(min(100%,380px),1fr))',
        'fit-420': 'repeat(auto-fit,minmax(min(100%,420px),1fr))',
        'queue-row': 'minmax(0,1fr) auto', // baris antrian dasbor staf
        // dasbor kota
        'fit-120': 'repeat(auto-fit,minmax(120px,1fr))',
        'fit-170': 'repeat(auto-fit,minmax(min(100%,170px),1fr))',
        'fit-520': 'repeat(auto-fit,minmax(min(100%,520px),1fr))',
        'kota-table': 'minmax(0,1.6fr) 1fr 1fr',
        'kota-bar': 'minmax(90px,130px) 1fr 38px',
      },
      // Arsir sel peta yang disembunyikan (k < 10).
      backgroundImage: {
        hatch: 'repeating-linear-gradient(45deg,var(--c-sand-100) 0 6px,var(--c-sand-300) 6px 12px)',
        'hatch-sm': 'repeating-linear-gradient(45deg,var(--c-sand-100) 0 3px,var(--c-sand-400) 3px 6px)',
      },
      opacity: { 35: '.35', 45: '.45' }, // 35: sel kota tak terpilih; 45: tombol Rujuk saat kasus ditutup
      width: { breath: '92%' }, // lingkaran napas 4-7-8
      height: { breath: '92%' },
      scale: { 70: '.7' },
      transitionDuration: { 120: '120ms' },
      zIndex: { 60: '60' },
    },
  },
  plugins: [],
} satisfies Config;
