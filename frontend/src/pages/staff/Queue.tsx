import { useQuery } from '@tanstack/react-query';
import { useState, useSyncExternalStore } from 'react';
import { useSearchParams } from 'react-router';
import { Icon } from '../../components/Icon';
import { RiskBadge, StatusBadge } from '../../components/RiskBadge';
import { copy } from '../../lib/copy';
import { headerClock, since, timeLabel } from '../../lib/time';
import type { CaseRow, CaseStatus } from '../../lib/types';
import { CaseDetail } from './CaseDetail';
import { staffApi } from '../../lib/api';
import { useStaff } from './StaffApp';

const t = copy.staff;
const LEVEL_ORDER = { merah: 0, oranye: 1, kuning: 2 } as const;
type Tab = 'semua' | 'baru' | 'ditangani';

/** Lebar ≥ 760px: antrian + detail berdampingan (sama dengan prototipe). */
const SPLIT = '(min-width: 760px)';
function useSplit() {
  return useSyncExternalStore(
    (cb) => {
      const mq = window.matchMedia(SPLIT);
      mq.addEventListener('change', cb);
      return () => mq.removeEventListener('change', cb);
    },
    () => window.matchMedia(SPLIT).matches,
  );
}

// Baru dulu, lalu merah → oranye → kuning (urutan prototipe).
const sortRows = (rows: CaseRow[]) =>
  rows
    .slice()
    .sort((a, b) => Number(a.status !== 'baru') - Number(b.status !== 'baru') || LEVEL_ORDER[a.level] - LEVEL_ORDER[b.level]);

export const Antrian = () => <Queue history={false} />;
export const Riwayat = () => <Queue history />;

function Queue({ history }: { history: boolean }) {
  const { active, arrived, now } = useStaff();
  const closed = useQuery({
    queryKey: ['cases', 'closed'],
    queryFn: () => staffApi<CaseRow[]>('/cases?status=selesai&status=dirujuk'),
    enabled: history,
  });
  const source = history ? closed : active;
  const [tab, setTab] = useState<Tab>('semua');
  const [params, setParams] = useSearchParams();
  const split = useSplit();

  const all = source.data ?? [];
  const counts: Record<Tab, number> = {
    semua: all.length,
    baru: all.filter((r) => r.status === 'baru').length,
    ditangani: all.filter((r) => r.status === 'ditangani').length,
  };
  const rows = sortRows(history || tab === 'semua' ? all : all.filter((r) => r.status === (tab as CaseStatus)));
  const picked = params.get('kasus');
  // Layar lebar: kasus terpilih yang sudah pindah tab (mis. ditandai selesai) → pilih yang teratas.
  const selected = split && !rows.some((r) => r.id === picked) ? rows[0]?.id : picked;
  const pick = (id: string | null) => setParams(id ? { kasus: id } : {}, { replace: !split && !id });

  return (
    <>
      {(split || !selected) && (
        <section className="flex min-h-0 w-full flex-none flex-col border-r border-sand-200 md:w-340 xl:w-400">
          <div className="flex flex-col gap-12 px-18 pb-12 pt-18">
            <div className="flex flex-wrap items-baseline justify-between gap-8">
              <h1 className="m-0 text-22 font-extrabold tracking-tight">{history ? t.historyTitle : t.queueTitle}</h1>
              <span className="text-12 text-muted">{headerClock(now)}</span>
            </div>
            {!history && (
              <div className="flex gap-6 overflow-x-auto">
                {(Object.keys(t.tabs) as Tab[]).map((k) => (
                  <button
                    key={k}
                    type="button"
                    onClick={() => setTab(k)}
                    aria-pressed={tab === k}
                    className={`flex h-36 flex-none items-center gap-6 whitespace-nowrap rounded-full border-1.5 px-12 text-13 font-bold ${tab === k ? 'border-navy bg-navy text-white' : 'border-sand-400 bg-white text-navy'}`}
                  >
                    {t.tabs[k]}
                    <span className="font-semibold opacity-80">{counts[k]}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="flex flex-1 flex-col gap-6 overflow-y-auto px-10 pb-16">
            {rows.map((r) => {
              const on = r.id === selected && split;
              const red = r.level === 'merah' && r.status === 'baru';
              const at = new Date(r.detected_at);
              return (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => pick(r.id)}
                  className={`grid animate-in-25 grid-cols-queue-row items-center gap-x-10 gap-y-6 rounded-14 border-1.5 px-12 py-14 text-left hover:bg-white ${on ? 'border-teal-600 bg-white' : red ? 'border-risk-red-row-line bg-risk-red-row' : 'border-transparent bg-transparent'}`}
                >
                  <span className="flex min-w-0 flex-col gap-3">
                    <span className="flex flex-wrap items-center gap-6 text-15 font-bold">
                      {r.pseudonym}
                      {arrived.has(r.id) && r.status === 'baru' && (
                        <span className="rounded-6 bg-navy px-6 py-2 text-10 font-extrabold text-white">{t.newBadge}</span>
                      )}
                    </span>
                    <span className="text-12 text-muted">
                      {r.kelurahan} · {timeLabel(at, now)}
                    </span>
                  </span>
                  <span className="flex flex-col items-end gap-5">
                    <RiskBadge level={r.level} />
                    <StatusBadge status={r.status} />
                  </span>
                  {red && (
                    <span className="col-span-full flex items-center gap-4 text-12 font-bold text-risk-red-text">
                      <Icon name="timer" className="h-13 w-13 stroke-risk-red-text" strokeWidth={2.4} />
                      {t.priority(since(at, now))}
                    </span>
                  )}
                </button>
              );
            })}
            {source.isSuccess && rows.length === 0 && (
              <div className="px-12 py-24 text-center text-14 text-muted">{t.empty}</div>
            )}
            {/* DESIGN-GAP: state gagal memuat antrian. */}
            {source.isError && !source.data && (
              <div className="flex flex-col items-center gap-10 px-12 py-24 text-center text-14 text-muted">
                {t.loadFailed}
                <button type="button" onClick={() => void source.refetch()} className="h-40 rounded-full border-1.5 border-sand-400 bg-white px-14 font-bold text-navy">
                  {t.retry}
                </button>
              </div>
            )}
          </div>
        </section>
      )}
      {selected ? (
        <CaseDetail key={selected} id={selected} onBack={split ? undefined : () => pick(null)} />
      ) : (
        // DESIGN-GAP: layar lebar tanpa kasus sama sekali.
        split && <div className="flex flex-1 items-center justify-center p-20 text-14 text-muted">{t.pickCase}</div>
      )}
    </>
  );
}
