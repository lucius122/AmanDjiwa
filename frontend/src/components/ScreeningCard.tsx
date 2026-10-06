import type { ReactNode } from 'react';
import { copy } from '../lib/copy';
import type { ScreeningQuestion } from '../lib/types';

const OPTION =
  'min-h-44 rounded-full border-1.5 border-sand-400 bg-cream px-16 text-14 font-semibold hover:border-teal-500 hover:bg-teal-100 disabled:opacity-55';
const FOOTER = 'min-h-44 bg-transparent text-13 font-semibold text-muted';

function Card({ children }: { children: ReactNode }) {
  return (
    <div className="flex max-w-460 animate-in-30 flex-col gap-14 rounded-20 border-1.5 border-teal-200 bg-white p-16">
      {children}
    </div>
  );
}

interface Props {
  q: ScreeningQuestion;
  busy: boolean;
  onAnswer: (value: number) => void;
  onSkip: () => void;
  onStop: () => void;
}

export function ScreeningCard({ q, busy, onAnswer, onSkip, onStop }: Props) {
  return (
    <Card>
      <div className="flex items-center gap-10">
        <span className="text-12 font-bold text-teal-800">{copy.chat.question(q.n, q.total)}</span>
        <div className="h-5 flex-1 overflow-hidden rounded-3 bg-sand-200">
          <div
            className="h-full rounded-3 bg-teal-500 transition-[width] duration-300"
            style={{ width: `${(q.n / q.total) * 100}%` }}
          />
        </div>
      </div>
      <div className="text-16 font-bold leading-150">{q.text}</div>
      <div className="flex flex-wrap gap-8">
        {q.options.map((label, value) => (
          <button key={label} type="button" disabled={busy} onClick={() => onAnswer(value)} className={OPTION}>
            {label}
          </button>
        ))}
      </div>
      <div className="flex justify-between gap-8">
        <button type="button" disabled={busy} onClick={onSkip} className={FOOTER}>
          {copy.chat.skip}
        </button>
        <button type="button" disabled={busy} onClick={onStop} className={FOOTER}>
          {copy.chat.stop}
        </button>
      </div>
    </Card>
  );
}

// DESIGN-GAP: tawaran lanjut skrining (alur bertahap) tidak ada di desain; memakai gaya kartu skrining.
export function FollowupCard({ busy, onContinue, onStop }: { busy: boolean; onContinue: () => void; onStop: () => void }) {
  return (
    <Card>
      <div className="flex flex-wrap gap-8">
        <button type="button" disabled={busy} onClick={onContinue} className={OPTION}>
          {copy.chat.followupContinue}
        </button>
        <button type="button" disabled={busy} onClick={onStop} className={OPTION}>
          {copy.chat.followupStop}
        </button>
      </div>
    </Card>
  );
}
