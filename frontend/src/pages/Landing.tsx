import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router';
import { hotlineDisplay, UNVERIFIED } from '../components/CrisisCard';
import { Icon, type IconName } from '../components/Icon';
import { HeroIllustration } from '../components/Illustrations';
import { LogoMark, Wordmark } from '../components/Logo';
import { useToast } from '../components/Toast';
import { api } from '../lib/api';
import { copy } from '../lib/copy';
import type { Hotline } from '../lib/types';

const t = copy.landing;
const STEP_STYLE: { bg: string; ink: string; icon: IconName }[] = [
  { bg: 'bg-teal-100', ink: 'stroke-teal-600', icon: 'chat' },
  { bg: 'bg-peach-100', ink: 'stroke-peach-600', icon: 'emo' },
  { bg: 'bg-lavender-100', ink: 'stroke-lavender-600', icon: 'people' },
];
const PRIVACY_ICON: IconName[] = ['aku', 'lock', 'trash'];
const NAV_LINK = 'text-navy no-underline hover:text-teal-600';

/** Tombol utama "Mulai ngobrol" (hero & CTA penutup). /mulai mengarahkan sesuai status remaja. */
function StartLink({ className = '' }: { className?: string }) {
  return (
    <Link
      to="/mulai"
      className={`flex h-56 items-center justify-center gap-10 rounded-14 bg-teal-600 px-28 text-17 font-bold text-white no-underline hover:bg-teal-700 hover:text-white ${className}`}
    >
      {t.cta}
      <Icon name="next" className="h-18 w-18 stroke-white" strokeWidth={2} />
    </Link>
  );
}

function HotlineButton({ h }: { h: Hotline }) {
  const toast = useToast();
  const inner = (
    <>
      <span className="flex flex-col">
        <span className="text-13 text-peach-700">{h.label}</span>
        <span className="text-18 font-bold">{hotlineDisplay(h)}</span>
      </span>
      <Icon name="phone" className="h-22 w-22 stroke-teal-600" />
    </>
  );
  const style =
    'flex min-h-64 items-center justify-between rounded-14 bg-white px-18 text-left text-navy no-underline hover:text-navy hover:ring-2 hover:ring-peach-300';
  // Nomor hanya dari hotlines.yaml (§6.6); sebelum diverifikasi tidak bisa ditelepon.
  return h.number === UNVERIFIED ? (
    <button type="button" className={style} onClick={() => toast(t.hotlineUnverified)}>
      {inner}
    </button>
  ) : (
    <a className={style} href={`tel:${h.number.replace(/[^\d+]/g, '')}`}>
      {inner}
    </a>
  );
}

export function Landing() {
  const hotlines = useQuery({
    queryKey: ['hotlines'],
    queryFn: () => api<Hotline[]>('/hotlines', { auth: false }),
    staleTime: Infinity,
  });

  return (
    <div>
      <a
        href="#utama"
        className="sr-only focus:not-sr-only focus:fixed focus:left-16 focus:top-16 focus:z-60 focus:rounded-12 focus:bg-white focus:px-16 focus:py-12 focus:text-15 focus:font-bold focus:text-navy focus:shadow-panel"
      >
        {t.skip}
      </a>

      <header className="mx-auto flex max-w-1200 items-center justify-between gap-12 px-20 py-12">
        <div className="flex items-center gap-8">
          <LogoMark className="h-32 w-32" />
          <Wordmark className="text-20" />
        </div>
        <div className="flex items-center gap-24 text-15 font-semibold">
          <nav aria-label={t.nav.how} className="hidden gap-24 lg:flex">
            <a href="#cara" className={NAV_LINK}>
              {t.nav.how}
            </a>
            <a href="#privasi" className={NAV_LINK}>
              {t.nav.privacy}
            </a>
            <a href="#bantuan" className={NAV_LINK}>
              {t.nav.help}
            </a>
          </nav>
          <Link
            to="/mulai"
            className="flex h-44 items-center rounded-12 border-1.5 border-navy bg-transparent px-18 text-15 font-bold text-navy no-underline hover:bg-white hover:text-navy"
          >
            {t.nav.login}
          </Link>
        </div>
      </header>

      <main id="utama">
        <section className="mx-auto grid max-w-1200 grid-cols-fit-380 items-center gap-40 px-20 pb-56 pt-24">
          <div className="flex animate-in-50 flex-col gap-20">
            <div className="self-start rounded-full bg-teal-100 px-14 py-7 text-13 font-semibold text-teal-800">
              {t.badge}
            </div>
            <h1 className="m-0 text-balance text-fluid-60 font-extrabold leading-106 tracking-tightest">{t.title}</h1>
            <p className="m-0 max-w-480 text-pretty text-fluid-19 leading-155 text-muted">{t.lead}</p>
            <div className="flex flex-wrap gap-10">
              <StartLink className="max-w-280 flex-auto" />
              <a
                href={copy.brand.botUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex h-56 items-center gap-8 rounded-14 bg-transparent px-20 text-16 font-semibold text-navy no-underline hover:bg-white hover:text-navy"
              >
                <Icon name="telegram" className="h-20 w-20 stroke-navy" />
                {t.telegram}
              </a>
            </div>
          </div>
          <div className="aspect-5/4 overflow-hidden rounded-28 bg-teal-100">
            <HeroIllustration label={t.heroAlt} />
          </div>
        </section>

        <section id="cara" aria-labelledby="cara-title" className="bg-white px-20 py-56">
          <div className="mx-auto flex max-w-1200 flex-col gap-24">
            <h2 id="cara-title" className="m-0 text-fluid-34 font-extrabold tracking-tight">
              {t.howTitle}
            </h2>
            <div className="grid grid-cols-fit-280 gap-16">
              {t.steps.map((s, i) => (
                <div key={s.n} className="flex flex-col gap-12 rounded-16 bg-cream p-24">
                  <div className="flex items-center justify-between">
                    <div className={`flex h-52 w-52 items-center justify-center rounded-16 ${STEP_STYLE[i].bg}`}>
                      <Icon name={STEP_STYLE[i].icon} className={`h-26 w-26 ${STEP_STYLE[i].ink}`} />
                    </div>
                    {/* angka dekoratif: kontras rendah disengaja, maknanya ada di judul */}
                    <span aria-hidden="true" className="text-36 font-extrabold text-sand-300">
                      {s.n}
                    </span>
                  </div>
                  <h3 className="m-0 text-19 font-bold">{s.title}</h3>
                  <p className="m-0 text-15 leading-155 text-muted">{s.body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <div className="mx-auto grid max-w-1200 grid-cols-fit-420 gap-16 px-20 py-56">
          <section id="privasi" aria-labelledby="privasi-title" className="flex flex-col gap-20 rounded-24 bg-teal-100 p-28">
            <div className="flex items-center gap-10">
              <Icon name="shield" className="h-28 w-28 stroke-teal-800" />
              <h2 id="privasi-title" className="m-0 text-fluid-30 font-extrabold tracking-tight">
                {t.privacyTitle}
              </h2>
            </div>
            <div className="grid grid-cols-fit-150 gap-16">
              {t.privacy.map((p, i) => (
                <div key={p.title} className="flex flex-col gap-8">
                  <div className="flex h-44 w-44 items-center justify-center rounded-12 bg-white">
                    <Icon name={PRIVACY_ICON[i]} className="h-22 w-22 stroke-teal-600" />
                  </div>
                  <h3 className="m-0 text-16 font-bold">{p.title}</h3>
                  <p className="m-0 text-14 leading-150 text-muted-strong">{p.body}</p>
                </div>
              ))}
            </div>
            <div className="flex items-start gap-12 rounded-14 bg-white p-16">
              <Icon name="info" className="h-22 w-22 flex-none stroke-navy" />
              <p className="m-0 text-pretty text-14 leading-155 text-muted">
                <b className="text-navy">{t.notDiagnosisBold}</b>
                {t.notDiagnosisRest}
              </p>
            </div>
          </section>

          <section id="bantuan" aria-labelledby="bantuan-title" className="flex flex-col gap-12 rounded-24 bg-peach-100 p-28">
            <h2 id="bantuan-title" className="m-0 text-fluid-26 font-extrabold tracking-tight">
              {t.helpTitle}
            </h2>
            <p className="m-0 text-15 leading-150 text-peach-800">{t.helpLead}</p>
            {hotlines.data?.map((h) => <HotlineButton key={h.id} h={h} />)}
            {/* DESIGN-GAP: ruang dipesan saat memuat supaya layout tidak loncat */}
            {hotlines.isPending && [0, 1].map((i) => <div key={i} className="min-h-64 rounded-14 bg-white-60" />)}
            {hotlines.isError && <p className="m-0 text-14 font-semibold text-peach-800">{t.hotlineLoadFailed}</p>}
          </section>
        </div>

        {/* Tambahan yang disetujui 2026-10-05: CTA penutup sebelum footer. */}
        <section aria-labelledby="mulai-title" className="bg-white px-20 py-56">
          <div className="mx-auto flex max-w-1200 flex-col items-center gap-16 text-center">
            <h2 id="mulai-title" className="m-0 text-balance text-fluid-34 font-extrabold tracking-tight">
              {t.closingTitle}
            </h2>
            <p className="m-0 max-w-480 text-pretty text-fluid-19 leading-155 text-muted">{t.closingBody}</p>
            <StartLink className="w-full max-w-280" />
          </div>
        </section>
      </main>

      <footer className="bg-navy px-20 py-36 text-white">
        <div className="mx-auto flex max-w-1200 flex-wrap items-center justify-between gap-24">
          <div className="flex flex-col gap-6">
            <Wordmark className="text-20" accent="text-teal-400" />
            <span className="text-13 text-on-navy-muted">{t.tagline}</span>
          </div>
          <div className="flex flex-wrap items-center gap-10">
            <span className="text-13 text-on-navy-muted">{t.supportedBy}</span>
            {t.partners.map((name, i) => (
              <div
                key={name}
                className={`flex h-56 items-center justify-center rounded-12 border-1.5 border-on-navy-line p-4 text-center text-12 font-semibold leading-130 ${i === 0 ? 'w-170' : 'w-110'}`}
              >
                {name}
              </div>
            ))}
          </div>
          {/* DESIGN-GAP: halaman kebijakan privasi & kontak tim belum ada; sementara ke bagian terkait */}
          <nav aria-label={t.privacyPolicy} className="flex gap-20 text-14 font-semibold">
            <a href="#privasi" className="text-white hover:text-on-navy-muted">
              {t.privacyPolicy}
            </a>
            <a href="#bantuan" className="text-white hover:text-on-navy-muted">
              {t.contact}
            </a>
          </nav>
        </div>
      </footer>
    </div>
  );
}
