import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Icon } from '../../components/Icon';
import { RiskBadge, StatusBadge } from '../../components/RiskBadge';
import { Sheet, SheetHeader } from '../../components/Sheet';
import { useToast } from '../../components/Toast';
import { TrajectoryChart } from '../../components/TrajectoryChart';
import { copy } from '../../lib/copy';
import { clock, dayMonth, since, timeLabel, wibDate } from '../../lib/time';
import type { CaseDetail as Detail, CaseNote, ScreeningScore, TriggerMessages } from '../../lib/types';
import { staffApi } from '../../lib/api';
import { useStaff } from './StaffApp';

const t = copy.caseDetail;
const CARD = 'flex flex-col rounded-16 border border-sand-200 bg-white px-18 py-16';
const BTN = 'flex h-46 items-center gap-8 rounded-12 px-18 text-14 font-bold';

type Action = { action: 'contacted' | 'done' } | { action: 'refer'; referred_to: string };

const initials = (name: string) =>
  name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

function Score({ label, s }: { label: string; s: ScreeningScore }) {
  return (
    <div className="flex flex-col gap-2">
      <span className="text-12 font-bold text-muted">{label}</span>
      <span className="text-26 font-extrabold">{s.total ?? '–'}</span>
      <span className="text-12 text-muted">{s.severity ? t.severity[s.severity] : t.incomplete}</span>
    </div>
  );
}

export function CaseDetail({ id, onBack }: { id: string; onBack?: () => void }) {
  const { settings, now } = useStaff();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [note, setNote] = useState('');
  const [reveal, setReveal] = useState(false);
  const [referOpen, setReferOpen] = useState(false);
  // Setiap muat = satu baris audit, jadi tidak di-refetch otomatis.
  const detail = useQuery({ queryKey: ['case', id], queryFn: () => staffApi<Detail>(`/cases/${id}`), staleTime: Infinity });
  const snippets = useQuery({
    queryKey: ['case-messages', id],
    queryFn: () => staffApi<TriggerMessages>(`/cases/${id}/messages`),
    enabled: !settings.compact || reveal,
    staleTime: Infinity,
  });

  const done = (c: Detail) => {
    queryClient.setQueryData(['case', id], c);
    void queryClient.invalidateQueries({ queryKey: ['cases'] });
  };
  const act = useMutation({
    mutationFn: (body: Action) => staffApi<Detail>(`/cases/${id}`, { method: 'PATCH', body: { ...body, note: note.trim() } }),
    onSuccess: (c, body) => {
      done(c);
      setNote('');
      setReferOpen(false);
      if (body.action === 'refer') toast(t.toastReferred(body.referred_to));
      else toast(body.action === 'contacted' ? t.toastContacted : t.toastDone);
    },
    onError: () => toast(t.actionFailed),
  });
  const saveNote = useMutation({
    mutationFn: () => staffApi<CaseNote[]>(`/cases/${id}/notes`, { method: 'POST', body: { text: note.trim() } }),
    onSuccess: (notes) => {
      queryClient.setQueryData<Detail>(['case', id], (c) => c && { ...c, notes });
      setNote('');
      toast(t.toastNote);
    },
    onError: () => toast(t.actionFailed),
  });

  const back = onBack && (
    <button type="button" onClick={onBack} className="flex h-40 items-center gap-4 self-start bg-transparent pl-4 pr-10 text-14 font-bold">
      <Icon name="back" className="h-20 w-20 stroke-navy" strokeWidth={2} />
      {t.back}
    </button>
  );
  const c = detail.data;
  if (!c) {
    return (
      <div className="flex min-w-0 flex-1 flex-col gap-14 overflow-y-auto p-20">
        {back}
        {/* DESIGN-GAP: state gagal memuat detail. */}
        {detail.isError && <p className="m-0 text-14 text-muted">{t.loadFailed}</p>}
      </div>
    );
  }

  const at = new Date(c.detected_at);
  const closed = c.status === 'selesai' || c.status === 'dirujuk';
  const busy = act.isPending || saveNote.isPending;
  const to = wibDate(c.trajectory_from);
  const until = new Date(to.getTime() + 13 * 86_400_000);
  const hasTrajectory = c.trajectory.some((v) => v !== null);

  return (
    <div className="flex min-w-0 flex-1 flex-col gap-14 overflow-y-auto p-20">
      {back}
      <div className="flex flex-wrap items-center gap-14">
        <div className="flex h-52 w-52 items-center justify-center rounded-full bg-teal-100 text-17 font-extrabold text-teal-800">
          {initials(c.pseudonym)}
        </div>
        <div className="flex flex-shrink flex-grow basis-220 flex-col gap-4">
          <div className="flex flex-wrap items-center gap-10">
            <span className="text-22 font-extrabold tracking-tight">{c.pseudonym}</span>
            <RiskBadge level={c.level} prefix />
          </div>
          <span className="text-13 text-muted">{t.subline(c.kelurahan, c.age, timeLabel(at, now), since(at, now))}</span>
        </div>
        <StatusBadge status={c.status} large />
      </div>

      <div className="grid grid-cols-fit-280 gap-14">
        <div className="flex flex-col gap-10 rounded-16 border border-sand-200 bg-white p-18">
          <div className="flex items-baseline justify-between gap-8">
            <span className="text-14 font-bold">{t.trajectory}</span>
            <span className="text-12 text-muted">{t.trajectorySource}</span>
          </div>
          {/* DESIGN-GAP: lintasan kosong (belum ada jurnal/obrolan). */}
          {hasTrajectory ? <TrajectoryChart points={c.trajectory} /> : <p className="m-0 text-13 text-muted">{t.trajectoryEmpty}</p>}
          <div className="flex justify-between text-11 text-muted">
            <span>{dayMonth(to)}</span>
            <span>{t.trajectoryAxis}</span>
            <span>{dayMonth(until)}</span>
          </div>
        </div>
        <div className="flex flex-col gap-14">
          <div className={`${CARD} gap-8`}>
            <span className="text-14 font-bold">{t.dominant}</span>
            <div className="flex flex-wrap gap-8">
              {c.dominant.map((d, i) => (
                <span key={d.emotion} className={`rounded-10 px-10 py-6 text-13 font-bold ${i === 0 ? 'bg-lavender-100' : 'bg-sky-100'}`}>
                  {t.dominantDays(copy.jurnal.emotions[d.emotion], d.days)}
                </span>
              ))}
              {c.dominant.length === 0 && <span className="text-13 text-muted">–</span>}
            </div>
          </div>
          <div className={`${CARD} grid grid-cols-2 gap-10`}>
            <Score label="PHQ-9" s={c.phq9} />
            <Score label="GAD-7" s={c.gad7} />
          </div>
        </div>
      </div>

      <div className={`${CARD} gap-10`}>
        <span className="text-14 font-bold">{t.markers}</span>
        <div className="flex flex-wrap gap-8">
          {c.markers.map((m) => (
            <span key={m} className="flex min-h-32 items-center rounded-10 border border-sand-300 bg-cream px-12 py-6 text-13 font-semibold">
              {m}
            </span>
          ))}
        </div>
      </div>

      <div className={`${CARD} gap-12`}>
        <div className="flex flex-wrap items-center justify-between gap-8">
          <span className="text-14 font-bold">{t.snippets}</span>
          {snippets.data && (
            <span className="flex min-h-26 items-center gap-6 rounded-8 bg-sky-100 px-10 py-4 text-12 font-bold">
              <Icon name="lockSmall" className="h-13 w-13 stroke-navy" strokeWidth={2.2} />
              {t.accessLogged(snippets.data.accessed_by ?? '', clock(new Date(snippets.data.accessed_at)))}
            </span>
          )}
        </div>
        {settings.compact && !reveal ? (
          <div className="flex flex-col gap-6">
            <button
              type="button"
              onClick={() => setReveal(true)}
              className="flex h-44 items-center justify-center gap-8 rounded-12 border-1.5 border-sand-400 bg-cream text-14 font-bold"
            >
              <Icon name="eye" className="h-18 w-18 stroke-navy" />
              {t.showSnippets}
            </button>
            <span className="text-12 text-muted">{t.showSnippetsNote}</span>
          </div>
        ) : (
          snippets.data?.messages.map((m, i) => (
            <div key={i} className="flex justify-between gap-12 rounded-12 bg-cream px-14 py-10 text-14 leading-150">
              <span>“{m.text}”</span>
              <span className="flex-none text-12 text-muted">{clock(new Date(m.created_at))}</span>
            </div>
          ))
        )}
        {snippets.data?.messages.length === 0 && <span className="text-13 text-muted">{t.snippetsEmpty}</span>}
        <span className="text-12 text-muted">{t.snippetsFooter}</span>
      </div>

      <div className={`${CARD} gap-12`}>
        <span className="text-14 font-bold">{t.notes}</span>
        {c.notes.map((n) => (
          <div key={n.id} className="flex gap-10 text-13 leading-150">
            <span className="mt-6 h-8 w-8 flex-none rounded-full bg-teal-500" />
            <span className="flex-1">{n.text}</span>
            <span className="flex-none text-muted">{timeLabel(new Date(n.created_at), now)}</span>
          </div>
        ))}
        <textarea
          aria-label={t.notes}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          maxLength={2000}
          placeholder={t.notePlaceholder}
          className="h-76 resize-none rounded-12 border-1.5 border-sand-400 bg-cream px-14 py-12 text-15 outline-none"
        />
        <div className="flex flex-wrap gap-10">
          <button
            type="button"
            disabled={busy || !note.trim()}
            onClick={() => saveNote.mutate()}
            className="h-46 rounded-12 border-1.5 border-sand-400 bg-white px-16 text-14 font-bold"
          >
            {t.saveNote}
          </button>
          <button
            type="button"
            disabled={closed || busy}
            onClick={() => act.mutate({ action: c.status === 'baru' ? 'contacted' : 'done' })}
            className={`${BTN} text-white ${closed ? 'bg-teal-disabled' : 'bg-teal-600'}`}
          >
            <Icon name="check" className="h-18 w-18 stroke-white" strokeWidth={2.4} />
            {c.status === 'baru' ? t.contacted : t.markDone}
          </button>
          <button
            type="button"
            disabled={closed || busy}
            onClick={() => setReferOpen(true)}
            className={`${BTN} border-1.5 border-navy bg-white ${closed ? 'opacity-45' : ''}`}
          >
            <Icon name="next" className="h-18 w-18 stroke-navy" strokeWidth={2} />
            {t.refer}
          </button>
        </div>
      </div>

      <Sheet open={referOpen} onClose={() => setReferOpen(false)} labelledBy="refer-title">
        <div className="flex flex-col gap-12 px-20 py-22">
          <SheetHeader id="refer-title" title={copy.referSheet.title(c.pseudonym)} onClose={() => setReferOpen(false)} />
          <div className="text-14 leading-150 text-muted">{copy.referSheet.lead}</div>
          {copy.referSheet.targets.map((r) => (
            <button
              key={r.label}
              type="button"
              disabled={busy}
              onClick={() => act.mutate({ action: 'refer', referred_to: r.label })}
              className="flex min-h-62 items-center justify-between rounded-14 border border-sand-200 bg-cream px-16 text-left hover:border-teal-600"
            >
              <span className="flex flex-col">
                <span className="text-16 font-bold">{r.label}</span>
                <span className="text-13 text-muted">{r.sub}</span>
              </span>
              <Icon name="chevronRight" className="h-20 w-20 stroke-teal-600" strokeWidth={2} />
            </button>
          ))}
        </div>
      </Sheet>
    </div>
  );
}
