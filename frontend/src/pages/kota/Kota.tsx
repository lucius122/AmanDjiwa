import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { Icon } from '../../components/Icon';
import { KpiCard } from '../../components/KpiCard';
import { staffApi } from '../../lib/api';
import { copy } from '../../lib/copy';
import { dayMonth, lastWeeks, wibDate } from '../../lib/time';
import type { CityAggregate, EmotionKey, KelurahanStat } from '../../lib/types';

const t = copy.kota;
const CARD = 'flex min-w-0 flex-col rounded-16 border border-sand-200 bg-white p-20';

// Posisi petak (kolom, baris) di peta tile grid — tata letak dari prototipe di design/.
const TILE_POS: Record<string, [number, number]> = {
  Tambakharjo: [0, 0],
  Tawangsari: [2, 0],
  Tawangmas: [3, 0],
  'Kalibanteng Kulon': [0, 1],
  'Kalibanteng Kidul': [1, 1],
  Krobokan: [2, 1],
  Karangayu: [3, 1],
  Salamanmloyo: [4, 1],
  Krapyak: [0, 2],
  Gisikdrono: [1, 2],
  Bojongsalaman: [2, 2],
  Cabean: [3, 2],
  Bongsari: [4, 2],
  Kembangarum: [1, 3],
  Manyaran: [2, 3],
  'Ngemplak Simongan': [3, 3],
};

/** Skala warna peta (% oranye + merah); null = disembunyikan (k < 10). */
const fill = (v: number | null) =>
  v === null
    ? 'bg-hatch text-muted'
    : v < 7
      ? 'bg-map-1 text-navy'
      : v < 11
        ? 'bg-map-2 text-navy'
        : v < 15
          ? 'bg-map-3 text-navy'
          : 'bg-map-4 text-white';
const LEGEND = ['bg-map-1', 'bg-map-2', 'bg-map-3', 'bg-map-4'];

const BAR = { hijau: 'bg-risk-green-bar', kuning: 'bg-risk-yellow-bar', oranye: 'bg-risk-orange-bar', merah: 'bg-risk-red-bar' } as const;

// Empat seri tren di desain (marah & malu tidak digambar). Garis putus-putus = pembeda selain warna.
const SERIES: { key: EmotionKey; stroke: string; swatch: string; dash: string }[] = [
  { key: 'senang', stroke: 'stroke-chart-senang', swatch: 'bg-chart-senang', dash: '0' },
  { key: 'cemas', stroke: 'stroke-chart-cemas', swatch: 'bg-chart-cemas', dash: '9 6' },
  { key: 'sedih', stroke: 'stroke-chart-sedih', swatch: 'bg-chart-sedih', dash: '2 6' },
  { key: 'netral', stroke: 'stroke-chart-netral', swatch: 'bg-chart-netral', dash: '14 5 2 5' },
];

const pctLabel = (v: number | null) => (v === null ? t.hidden : `${v}%`);
const num = (n: number) => n.toLocaleString('id-ID');

/** Ringkasan agregat (desain "Dasbor Kota"). Akses & header ada di KotaLayout. */
export function Kota() {
  const [weeks, setWeeks] = useState(8);
  const [mode, setMode] = useState<'peta' | 'tabel'>('peta');
  const [picked, setPicked] = useState<number | null>(null);
  const [focus, setFocus] = useState(false);
  const [weekIdx, setWeekIdx] = useState<number | null>(null);
  const range = lastWeeks(weeks);
  const agg = useQuery({
    queryKey: ['aggregate', range.from, range.to],
    queryFn: () => staffApi<CityAggregate>(`/dashboard/aggregate?from=${range.from}&to=${range.to}`),
    placeholderData: (prev) => prev,
  });

  const d = agg.data;
  const k = d?.min_cell ?? 10;
  const kels = d?.kelurahan ?? [];
  const visible = kels.filter((x) => x.risk_pct !== null);
  const top = visible.slice().sort((a, b) => (b.risk_pct ?? 0) - (a.risk_pct ?? 0))[0];
  const sel = kels.find((x) => x.id === picked) ?? top ?? kels[0];
  const pick = (x: KelurahanStat) => {
    setPicked(x.id);
    setFocus(true);
  };
  const dim = (x: KelurahanStat) => (focus && x.id !== sel?.id ? 'opacity-35' : '');

  return (
    <>
      <main className="mx-auto flex max-w-1440 flex-col gap-16 p-20">
        <div className="flex flex-wrap items-center gap-10">
          <h1 className="m-0 flex-shrink flex-grow basis-280 text-fluid-24 font-extrabold tracking-tight">{t.title}</h1>
          <div className="flex gap-4 rounded-12 border border-sand-300 bg-white p-4 print:hidden">
            {t.ranges.map((r) => (
              <button
                key={r.weeks}
                type="button"
                aria-pressed={weeks === r.weeks}
                onClick={() => {
                  setWeeks(r.weeks);
                  setWeekIdx(null);
                }}
                className={`h-36 whitespace-nowrap rounded-9 px-12 text-13 font-bold transition-colors duration-200 ${weeks === r.weeks ? 'bg-teal-600 text-white' : 'bg-white text-navy'}`}
              >
                {r.label}
              </button>
            ))}
          </div>
          {/* Policy brief = halaman ini dicetak ke PDF lewat dialog cetak browser (tanpa library). */}
          <button
            type="button"
            onClick={() => window.print()}
            className="flex h-44 flex-none items-center gap-8 whitespace-nowrap rounded-12 bg-teal-600 px-16 text-14 font-bold text-white hover:bg-teal-700 print:hidden"
          >
            <Icon name="download" className="h-18 w-18 stroke-white" strokeWidth={2} />
            {t.exportPdf}
          </button>
        </div>

        <div className="flex items-start gap-10 rounded-12 bg-sky-100 px-16 py-12 text-14 font-semibold leading-150">
          <Icon name="shieldPlain" className="mt-1 h-18 w-18 flex-none stroke-navy" />
          <span>
            {t.notice(k)}{' '}
            <span className="font-medium text-muted-strong">
              {t.noticeSub}
              {d?.demo && ` ${t.noticeDemo}`}
            </span>
          </span>
        </div>

        {agg.isError && !d && (
          // DESIGN-GAP: state gagal memuat.
          <div className="flex items-center gap-12 text-14 text-muted">
            {t.loadFailed}
            <button type="button" onClick={() => void agg.refetch()} className="h-36 rounded-full border-1.5 border-sand-400 bg-white px-14 font-bold text-navy">
              {t.retry}
            </button>
          </div>
        )}

        {d && (
          <>
            <Kpis d={d} />
            <div className="grid grid-cols-fit-520 gap-14">
              <section className={`${CARD} gap-14`}>
                <div className="flex flex-wrap items-center justify-between gap-10">
                  <div className="flex flex-col gap-2">
                    <h2 className="m-0 text-16 font-extrabold">{t.mapTitle}</h2>
                    <span className="text-12 text-muted">{t.mapSub}</span>
                  </div>
                  <div role="tablist" aria-label="Tampilan" className="flex gap-3 rounded-10 bg-sand-100 p-3 print:hidden">
                    {(['peta', 'tabel'] as const).map((m) => (
                      <button
                        key={m}
                        type="button"
                        role="tab"
                        aria-selected={mode === m}
                        onClick={() => setMode(m)}
                        className={`h-34 rounded-8 px-14 text-13 font-bold text-navy transition-colors duration-200 ${mode === m ? 'bg-white' : 'bg-transparent'}`}
                      >
                        {t.modes[m]}
                      </button>
                    ))}
                  </div>
                </div>

                {mode === 'peta' ? (
                  <div className="overflow-x-auto p-4">
                    <div className="relative aspect-map w-full min-w-500">
                      {kels.map((x) => {
                        const [col, row] = TILE_POS[x.name] ?? [0, 0];
                        return (
                          <button
                            key={x.id}
                            type="button"
                            onClick={() => pick(x)}
                            aria-label={t.tileAria(x.name, x.risk_pct)}
                            // Posisi petak dihitung dari grid (data), bukan nilai gaya statis.
                            style={{ left: `${col * 20}%`, top: `${row * 25.3}%`, width: '18.6%', height: '22.4%' }}
                            className={`absolute flex flex-col items-start justify-between rounded-12 border-2.5 px-9 py-7 text-left transition hover:-translate-y-2 hover:shadow-lift ${fill(x.risk_pct)} ${x.id === sel?.id ? 'border-navy' : 'border-white'} ${dim(x)}`}
                          >
                            <span className="text-12 font-bold leading-120">{x.name}</span>
                            <span className={`font-extrabold ${x.risk_pct === null ? 'text-11' : 'text-15'}`}>{pctLabel(x.risk_pct)}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div role="table" aria-label={t.mapTitle} className="flex animate-in-25 flex-col overflow-hidden rounded-12 border border-sand-200">
                    <div role="row" className="grid grid-cols-kota-table gap-8 bg-cream px-14 py-10 text-12 font-bold text-muted">
                      <span role="columnheader">{t.tableKel}</span>
                      <span role="columnheader" className="text-right">
                        {t.tableUsers}
                      </span>
                      <span role="columnheader" className="text-right">
                        {t.tableRisk}
                      </span>
                    </div>
                    {kels
                      .slice()
                      .sort((a, b) => (b.risk_pct ?? -1) - (a.risk_pct ?? -1))
                      .map((x) => (
                        <button
                          key={x.id}
                          type="button"
                          role="row"
                          onClick={() => pick(x)}
                          className={`grid min-h-44 grid-cols-kota-table items-center gap-8 border-t border-sand-100 px-14 py-8 text-left text-14 transition-colors hover:bg-teal-25 ${focus && x.id === sel?.id ? 'bg-teal-50' : 'bg-white'}`}
                        >
                          <span role="cell" className="flex min-w-0 items-center gap-8 font-semibold">
                            <span className={`h-12 w-12 flex-none rounded-4 border border-sand-300 ${fill(x.risk_pct)}`} />
                            {x.name}
                          </span>
                          <span role="cell" className="text-right">
                            {x.users === null ? t.fewUsers(k) : num(x.users)}
                          </span>
                          <span role="cell" className="text-right font-extrabold">
                            {pctLabel(x.risk_pct)}
                          </span>
                        </button>
                      ))}
                  </div>
                )}

                <div className="flex flex-wrap items-center justify-between gap-12">
                  <div className="flex flex-wrap items-center gap-12 text-12 font-semibold text-muted-strong">
                    {t.legend.map((label, i) => (
                      <span key={label} className="flex items-center gap-6">
                        <span className={`h-12 w-16 rounded-4 ${LEGEND[i]}`} />
                        {label}
                      </span>
                    ))}
                    <span className="flex items-center gap-6">
                      <span className="h-12 w-16 rounded-4 bg-hatch-sm" />
                      {t.hidden}
                    </span>
                  </div>
                  {sel && (
                    <div className="flex flex-wrap items-center gap-12 rounded-12 bg-cream py-8 pl-14 pr-8 text-13">
                      <b>{sel.name}</b>
                      <span>{t.selUsers(sel.users === null ? t.fewUsers(k) : num(sel.users))}</span>
                      <span>{t.selRisk(pctLabel(sel.risk_pct))}</span>
                      {focus && (
                        <button
                          type="button"
                          onClick={() => setFocus(false)}
                          className="h-32 rounded-8 border border-sand-400 bg-white px-10 text-12 font-bold print:hidden"
                        >
                          {t.showAll}
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </section>

              <section className={`${CARD} gap-12`}>
                <div className="flex flex-wrap items-baseline justify-between gap-8">
                  <h2 className="m-0 text-16 font-extrabold">{t.distTitle}</h2>
                  <span className="text-12 text-muted">{t.distSub}</span>
                </div>
                <div className="flex flex-wrap gap-12 text-12 font-semibold text-muted-strong">
                  {(Object.keys(BAR) as (keyof typeof BAR)[]).map((lv) => (
                    <span key={lv} className="flex items-center gap-6">
                      <span className={`h-12 w-12 rounded-3 ${BAR[lv]}`} />
                      {t.levels[lv]}
                    </span>
                  ))}
                </div>
                <div className="flex flex-col gap-7">
                  {visible
                    .slice()
                    .sort((a, b) => (b.levels?.merah ?? 0) - (a.levels?.merah ?? 0))
                    .map((x) => {
                      const l = x.levels!;
                      return (
                        <button
                          key={x.id}
                          type="button"
                          onClick={() => pick(x)}
                          title={t.distTip(x.name, l)}
                          aria-label={t.distTip(x.name, l)}
                          className={`grid grid-cols-kota-bar items-center gap-10 rounded-8 px-6 py-4 text-left transition hover:bg-teal-25 ${focus && x.id === sel?.id ? 'bg-teal-25' : 'bg-transparent'} ${dim(x)}`}
                        >
                          <span className="truncate text-12 font-semibold">{x.name}</span>
                          <span className="flex h-16 gap-2 overflow-hidden rounded-5">
                            {(Object.keys(BAR) as (keyof typeof BAR)[]).map((lv) => (
                              <span key={lv} style={{ width: `${l[lv]}%` }} className={`transition-all duration-500 ${BAR[lv]}`} />
                            ))}
                          </span>
                          <span className="text-right text-12 font-bold text-risk-red-text">{l.merah}%</span>
                        </button>
                      );
                    })}
                  {visible.length === 0 && <p className="m-0 text-13 text-muted">{t.distEmpty}</p>}
                </div>
              </section>
            </div>

            <div className="grid grid-cols-fit-420 gap-14">
              <Trend d={d} weekIdx={weekIdx ?? d.trend.length - 1} onWeek={setWeekIdx} k={k} />
              <section className={`${CARD} gap-14`}>
                <div className="flex flex-wrap items-baseline justify-between gap-8">
                  <h2 className="m-0 text-16 font-extrabold">{t.topicsTitle}</h2>
                  <span className="text-12 text-muted">{t.topicsSub}</span>
                </div>
                {d.topics.map((x) => (
                  <div key={x.key} className="flex flex-col gap-5">
                    <div className="flex justify-between text-13 font-semibold">
                      <span>{x.label}</span>
                      <span className="font-extrabold">{x.pct}%</span>
                    </div>
                    <div className="h-10 overflow-hidden rounded-5 bg-sand-100">
                      <div
                        style={{ width: `${(x.pct / d.topics[0].pct) * 100}%` }}
                        className="h-full rounded-5 bg-teal-500 transition-all duration-500"
                      />
                    </div>
                  </div>
                ))}
                {d.topics.length === 0 && <p className="m-0 text-13 text-muted">{t.topicsEmpty(k)}</p>}
              </section>
            </div>
          </>
        )}
      </main>
    </>
  );
}

function Kpis({ d }: { d: CityAggregate }) {
  const k = t.kpi;
  const x = d.kpis;
  const hidden = k.hidden(d.min_cell);
  const change = x?.active_users_change_pct ?? null;
  const avg = x && x.active_users ? (Math.round((x.sessions / x.active_users) * 10) / 10).toLocaleString('id-ID') : '0';
  return (
    <div className="grid grid-cols-fit-170 gap-14">
      <KpiCard
        label={k.active}
        value={x ? num(x.active_users) : '–'}
        note={!x ? hidden : change === null ? k.activeNoPrev : k.activeChange(change)}
        tone={x && change !== null && change >= 0 ? 'good' : 'muted'}
      />
      <KpiCard label={k.sessions} value={x ? num(x.sessions) : '–'} note={x ? k.sessionsNote(avg) : hidden} />
      <KpiCard
        label={k.handled}
        value={x?.handled_15m_pct != null ? `${x.handled_15m_pct}%` : '–'}
        note={x ? k.handledNote : hidden}
        tone={x?.handled_15m_pct != null ? (x.handled_15m_pct >= 90 ? 'good' : 'warn') : 'muted'}
      />
      <KpiCard label={k.referrals} value={x ? num(x.referrals) : '–'} note={x ? k.referralsNote : hidden} />
    </div>
  );
}

/** Tren mingguan: SVG 640×220 seperti prototipe. Minggu yang disembunyikan (k < 10) = celah garis. */
function Trend({ d, weekIdx, onWeek, k }: { d: CityAggregate; weekIdx: number; onWeek: (i: number) => void; k: number }) {
  const n = d.trend.length;
  const x = (i: number) => (n > 1 ? (i * 640) / (n - 1) : 320);
  const max = Math.max(36, ...d.trend.flatMap((w) => (w.pct ? SERIES.map((s) => w.pct![s.key]) : [])));
  const y = (v: number) => 200 - v * (198 / max);
  const path = (key: EmotionKey) =>
    d.trend
      .map((w, i) => (w.pct ? `${i > 0 && d.trend[i - 1].pct ? 'L' : 'M'}${x(i).toFixed(1)} ${y(w.pct[key]).toFixed(1)}` : ''))
      .join(' ');
  const week = d.trend[weekIdx];
  const label = (w: string) => dayMonth(wibDate(w));
  return (
    <section className={`${CARD} gap-12`}>
      <div className="flex flex-wrap items-baseline justify-between gap-8">
        <h2 className="m-0 text-16 font-extrabold">{t.trendTitle}</h2>
        <span className="text-12 text-muted">{t.trendSub}</span>
      </div>
      <div className="flex flex-wrap gap-14 text-12 font-semibold text-muted-strong">
        {SERIES.map((s) => (
          <span key={s.key} className="flex items-center gap-6">
            <svg width="24" height="8" aria-hidden="true">
              <line x1="2" y1="4" x2="22" y2="4" className={s.stroke} strokeWidth="3" strokeDasharray={s.dash} strokeLinecap="round" />
            </svg>
            {copy.jurnal.emotions[s.key]}
          </span>
        ))}
      </div>
      <svg viewBox="0 0 640 220" preserveAspectRatio="none" className="h-200 w-full" aria-hidden="true">
        {[20, 80, 140].map((gy) => (
          <line key={gy} x1="0" y1={gy} x2="640" y2={gy} className="stroke-sand-100" />
        ))}
        <line x1="0" y1="200" x2="640" y2="200" className="stroke-sand-300" />
        {SERIES.map((s) => (
          <path
            key={s.key}
            d={path(s.key)}
            fill="none"
            className={s.stroke}
            strokeWidth="3"
            strokeDasharray={s.dash}
            strokeLinejoin="round"
            strokeLinecap="round"
            vectorEffect="non-scaling-stroke"
          />
        ))}
        <line
          x1={x(weekIdx)}
          y1="8"
          x2={x(weekIdx)}
          y2="204"
          className="stroke-navy"
          strokeWidth="1.5"
          strokeDasharray="3 4"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
      <div className="flex gap-2 print:hidden">
        {d.trend.map((w, i) => (
          <button
            key={w.week}
            type="button"
            onClick={() => onWeek(i)}
            aria-pressed={i === weekIdx}
            aria-label={t.week(label(w.week))}
            className={`h-36 min-w-0 flex-1 whitespace-nowrap rounded-8 px-4 text-12 font-bold transition-colors ${i === weekIdx ? 'bg-navy text-white' : 'bg-transparent text-muted'}`}
          >
            <span className="2xl:hidden">{label(w.week).split(' ')[0]}</span>
            <span className="hidden 2xl:inline">{label(w.week)}</span>
          </button>
        ))}
      </div>
      {week && (
        <div aria-live="polite" className="grid grid-cols-fit-120 gap-8 rounded-12 bg-cream p-12">
          <span className="col-span-full text-12 font-bold text-muted">{t.week(label(week.week))}</span>
          {week.pct ? (
            SERIES.map((s) => (
              <span key={s.key} className="flex items-center gap-8 text-13 font-semibold">
                <span className={`h-10 w-10 flex-none rounded-3 ${s.swatch}`} />
                {copy.jurnal.emotions[s.key]}
                <b className="ml-auto">{week.pct![s.key]}%</b>
              </span>
            ))
          ) : (
            <span className="col-span-full text-13 text-muted">{t.weekHidden(k)}</span>
          )}
        </div>
      )}
    </section>
  );
}
