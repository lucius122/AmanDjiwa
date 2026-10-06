import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { BreathingSheet } from '../components/BreathingSheet';
import { Button } from '../components/Button';
import { EMOTIONS, EmotionFace, TILE_OF } from '../components/Emotion';
import { GroundingSheet } from '../components/GroundingSheet';
import { HelpSheet, useConnectFromOutside, useDial } from '../components/HelpSheet';
import { Icon } from '../components/Icon';
import { useToast } from '../components/Toast';
import { api } from '../lib/api';
import { copy } from '../lib/copy';
import type { EmotionKey, Hotline, JournalEntry, JournalSave, Me } from '../lib/types';

const t = copy.jurnal;
const DAYS = 14;
const TZ = 'Asia/Jakarta'; // tanggal jurnal mengikuti WIB, sama dengan backend

/** 14 tanggal terakhir (YYYY-MM-DD) menurut WIB, lama → baru. */
function lastDays(): string[] {
  const today = new Intl.DateTimeFormat('en-CA', { timeZone: TZ }).format(new Date());
  const base = Date.parse(`${today}T00:00:00Z`);
  return Array.from({ length: DAYS }, (_, i) => new Date(base - (DAYS - 1 - i) * 86_400_000).toISOString().slice(0, 10));
}
const asDate = (iso: string) => new Date(`${iso}T00:00:00Z`);
const fmt = (iso: string, opts: Intl.DateTimeFormatOptions) =>
  new Intl.DateTimeFormat('id-ID', { ...opts, timeZone: 'UTC' }).format(asDate(iso));

function insightOf(entries: JournalEntry[]): string {
  if (entries.length === 0) return t.insightEmpty;
  const count = new Map<EmotionKey, number>();
  for (const e of entries) count.set(e.emotion, (count.get(e.emotion) ?? 0) + 1);
  const top = [...count.entries()].sort((a, b) => b[1] - a[1])[0][0];
  return top === 'cemas' ? t.insightCemas : t.insightTop(t.emotions[top]);
}

export function Jurnal({ me }: { me: Me }) {
  const toast = useToast();
  const dial = useDial();
  const connect = useConnectFromOutside();
  const queryClient = useQueryClient();
  const journal = useQuery({ queryKey: ['journal'], queryFn: () => api<JournalEntry[]>(`/journal?days=${DAYS}`) });
  const hotlines = useQuery({ queryKey: ['hotlines'], queryFn: () => api<Hotline[]>('/hotlines', { auth: false }), staleTime: Infinity });
  const [emotion, setEmotion] = useState<EmotionKey | null>(null);
  const [intensity, setIntensity] = useState(3);
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [sheet, setSheet] = useState<'napas' | 'ground' | 'help' | null>(null);

  const days = lastDays();
  const today = days[DAYS - 1];
  const entries = journal.data ?? [];
  const byDate = new Map(entries.map((e) => [e.entry_date, e]));
  const todayEntry = byDate.get(today);

  // Isi form dengan entri hari ini (tombol jadi "Perbarui jurnal").
  useEffect(() => {
    if (!todayEntry) return;
    setEmotion(todayEntry.emotion);
    setIntensity(todayEntry.intensity);
    setNote(todayEntry.note ?? '');
  }, [todayEntry?.entry_date, todayEntry?.emotion, todayEntry?.intensity, todayEntry?.note]);

  async function save() {
    if (!emotion) return;
    setBusy(true);
    try {
      const res = await api<JournalSave>('/journal', { method: 'POST', body: { emotion, intensity, note } });
      await queryClient.invalidateQueries({ queryKey: ['journal'] });
      // DESIGN-GAP: desain jurnal tidak punya kartu krisis; catatan berbahaya membuka sheet Bantuan
      // (tanpa toast, supaya nomor layanan tidak tertutup).
      if (res.help) setSheet('help');
      else toast(t.saved);
    } catch {
      toast(t.saveFailed);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-0 flex-1 overflow-y-auto">
      <div className="mx-auto grid max-w-1040 grid-cols-fit-380 items-start gap-20 px-16 pb-32 pt-20">
        <section className="flex flex-col gap-16" aria-labelledby="j-title">
          <div className="flex flex-col gap-4">
            <div className="text-13 font-semibold text-muted">
              {new Intl.DateTimeFormat('id-ID', { weekday: 'long', day: 'numeric', month: 'long', timeZone: TZ }).format(new Date())}
            </div>
            <h1 id="j-title" className="m-0 text-24 font-extrabold leading-125 tracking-tight">
              {t.title}
            </h1>
          </div>
          <div className="grid grid-cols-3 gap-10" role="radiogroup" aria-label={t.emotionsLabel}>
            {EMOTIONS.map((e) => {
              const on = emotion === e.key;
              return (
                <button
                  key={e.key}
                  type="button"
                  role="radio"
                  aria-checked={on}
                  onClick={() => setEmotion(e.key)}
                  className={`flex min-h-92 flex-col items-center justify-center gap-6 rounded-16 border-2 p-8 transition-colors duration-200 ${on ? 'border-teal-600 bg-white' : 'border-sand-200 bg-white-60'}`}
                >
                  <EmotionFace face={e.face} d={e.d} />
                  <span className="text-13 font-bold">{t.emotions[e.key]}</span>
                </button>
              );
            })}
          </div>
          <div className="flex flex-col gap-10 rounded-16 border border-sand-200 bg-white p-16">
            <div className="flex items-baseline justify-between">
              <label htmlFor="j-int" className="text-14 font-bold">
                {t.intensityLabel}
              </label>
              <span className="text-13 font-bold text-teal-600">{t.intensity[intensity - 1]}</span>
            </div>
            <input
              id="j-int"
              type="range"
              min={1}
              max={5}
              value={intensity}
              aria-valuetext={t.intensity[intensity - 1]}
              onChange={(e) => setIntensity(Number(e.target.value))}
              className="h-28 w-full"
            />
            <div className="flex justify-between text-12 text-muted">
              <span>{t.intensityMin}</span>
              <span>{t.intensityMax}</span>
            </div>
          </div>
          <div className="flex flex-col gap-6">
            <label htmlFor="j-note" className="text-14 font-bold">
              {t.noteLabel} <span className="font-medium text-muted">{t.noteOptional}</span>
            </label>
            <textarea
              id="j-note"
              value={note}
              maxLength={1000}
              placeholder={t.notePlaceholder}
              onChange={(e) => setNote(e.target.value)}
              className="h-90 resize-none rounded-14 border-1.5 border-sand-400 bg-white px-14 py-12 text-16"
            />
          </div>
          <Button disabled={!emotion || busy} onClick={save}>
            {todayEntry ? t.update : t.save}
          </Button>
        </section>

        <div className="flex flex-col gap-14">
          <section className="flex flex-col gap-14 rounded-18 border border-sand-200 bg-white p-16" aria-labelledby="j-hist">
            <div className="flex items-baseline justify-between">
              <h2 id="j-hist" className="m-0 text-15 font-bold">
                {t.historyTitle}
              </h2>
              <span className="text-12 text-muted">
                {fmt(days[0], { day: 'numeric', month: 'short' })} – {fmt(today, { day: 'numeric', month: 'short' })}
              </span>
            </div>
            {journal.isError ? (
              <p className="m-0 text-13 text-muted">{t.loadFailed}</p>
            ) : (
              <div className="grid grid-cols-7 gap-6">
                {days.map((iso) => {
                  const entry = byDate.get(iso);
                  const label = `${fmt(iso, { day: 'numeric', month: 'short' })}: ${entry ? t.emotions[entry.emotion] : t.notFilled}`;
                  return (
                    <div key={iso} className="flex flex-col items-center gap-4">
                      <span className="text-10 font-semibold text-muted" aria-hidden="true">
                        {fmt(iso, { weekday: 'short' }).charAt(0)}
                      </span>
                      <div
                        role="img"
                        aria-label={label}
                        title={label}
                        className={`flex aspect-square w-full max-w-44 items-center justify-center rounded-12 border-2 text-12 font-bold transition-colors duration-300 ${entry ? TILE_OF[entry.emotion] : 'bg-sand-100'} ${iso === today ? 'border-navy' : 'border-transparent'}`}
                      >
                        {asDate(iso).getUTCDate()}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            <div className="flex flex-wrap gap-x-12 gap-y-6">
              {EMOTIONS.map((e) => (
                <span key={e.key} className="flex items-center gap-5 text-11 font-semibold text-muted">
                  <span className={`h-10 w-10 rounded-4 ${e.tile}`} />
                  {t.emotions[e.key]}
                </span>
              ))}
            </div>
            <p className="m-0 rounded-12 bg-cream p-12 text-13 leading-150 text-muted-strong">{insightOf(entries)}</p>
          </section>

          <h2 className="m-0 text-16 font-extrabold">{t.exercisesTitle}</h2>
          <button
            type="button"
            onClick={() => setSheet('napas')}
            className="flex items-center gap-14 rounded-18 bg-teal-100 p-16 text-left hover:ring-2 hover:ring-teal-300"
          >
            <span className="flex h-56 w-56 flex-none items-center justify-center rounded-full bg-white">
              <span className="h-30 w-30 rounded-full bg-teal-500" />
            </span>
            <span className="flex flex-1 flex-col gap-3">
              <span className="text-15 font-bold">{t.breathingTitle}</span>
              <span className="text-13 leading-145 text-muted-deep">{t.breathingBody}</span>
              <span className="text-12 font-bold text-teal-800">{t.breathingTime}</span>
            </span>
            <Icon name="chevronRight" className="h-20 w-20 stroke-teal-600" strokeWidth={2} />
          </button>
          <button
            type="button"
            onClick={() => setSheet('ground')}
            className="flex items-center gap-14 rounded-18 bg-butter-100 p-16 text-left hover:ring-2 hover:ring-butter-300"
          >
            <span className="flex h-56 w-56 flex-none items-center justify-center rounded-full bg-white text-13 font-extrabold text-butter-700">
              {t.groundingBadge}
            </span>
            <span className="flex flex-1 flex-col gap-3">
              <span className="text-15 font-bold">{t.groundingTitle}</span>
              <span className="text-13 leading-145 text-butter-800">{t.groundingBody}</span>
              <span className="text-12 font-bold text-butter-700">{t.groundingTime}</span>
            </span>
            <Icon name="chevronRight" className="h-20 w-20 stroke-butter-700" strokeWidth={2} />
          </button>
        </div>
      </div>

      <BreathingSheet open={sheet === 'napas'} onClose={() => setSheet(null)} />
      <GroundingSheet open={sheet === 'ground'} onClose={() => setSheet(null)} />
      <HelpSheet
        open={sheet === 'help'}
        onClose={() => setSheet(null)}
        hotlines={hotlines.data ?? []}
        kelurahan={me.kelurahan_name}
        onCall={dial}
        onConnect={() => {
          setSheet(null);
          void connect();
        }}
      />
    </div>
  );
}
