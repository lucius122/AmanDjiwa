import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { copy } from '../lib/copy';
import type { EmotionKey, JournalEntry, JournalSave } from '../lib/types';
import { Button } from './Button';
import { EMOTIONS, EmotionFace } from './Emotion';
import { useToast } from './Toast';

const t = copy.jurnal;
export const JOURNAL_DAYS = 14;
export const JOURNAL_QUERY = { queryKey: ['journal'], queryFn: () => api<JournalEntry[]>(`/journal?days=${JOURNAL_DAYS}`) };

/** Tanggal hari ini (YYYY-MM-DD) menurut WIB, sama dengan tanggal jurnal di backend. */
export const todayWib = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Jakarta' }).format(new Date());

/** Form jurnal hari ini: dipakai halaman Jurnal dan popup jurnal di Ngobrol. */
export function JournalForm({ todayEntry, onSaved }: { todayEntry?: JournalEntry; onSaved: (res: JournalSave) => void }) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [emotion, setEmotion] = useState<EmotionKey | null>(null);
  const [intensity, setIntensity] = useState(3);
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);

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
      await queryClient.invalidateQueries({ queryKey: JOURNAL_QUERY.queryKey });
      onSaved(res);
    } catch {
      toast(t.saveFailed);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
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
    </>
  );
}
