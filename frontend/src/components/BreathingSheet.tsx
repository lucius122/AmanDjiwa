import { useEffect, useState } from 'react';
import { copy } from '../lib/copy';
import { Button } from './Button';
import { CloseButton, Sheet } from './Sheet';

const CYCLE = 19; // 4 tarik + 7 tahan + 8 buang
const ROUNDS = 4;
const TOTAL = CYCLE * ROUNDS;
type Phase = keyof typeof copy.breathing.phases;
const PHASES = Object.keys(copy.breathing.phases) as Phase[];

function phaseAt(t: number): [Phase, number] {
  const s = t % CYCLE;
  return s < 4 ? ['Tarik', 4 - s] : s < 11 ? ['Tahan', 11 - s] : ['Buang', CYCLE - s];
}

export function BreathingSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [elapsed, setElapsed] = useState(0);
  const [paused, setPaused] = useState(false);
  const [run, setRun] = useState(0); // key baru → animasi mulai dari awal
  const done = elapsed >= TOTAL;

  const restart = () => {
    setElapsed(0);
    setPaused(false);
    setRun((r) => r + 1);
  };

  useEffect(() => {
    if (open) restart();
  }, [open]);

  useEffect(() => {
    if (!open || paused || done) return;
    const id = window.setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => window.clearInterval(id);
  }, [open, paused, done]);

  const [phase, left] = phaseAt(elapsed);
  return (
    <Sheet open={open} onClose={onClose} labelledBy="breath-title">
      <div className="flex flex-col items-center gap-22 bg-teal-100 px-20 pb-24 pt-16">
        <div className="flex w-full items-center justify-between">
          <span className="w-44" />
          <span id="breath-title" className="text-16 font-extrabold">
            {copy.breathing.title}
          </span>
          <CloseButton onClose={onClose} />
        </div>
        <div className="relative flex h-240 w-240 items-center justify-center rounded-full bg-white-60">
          <div
            key={run}
            className={`h-breath w-breath rounded-full bg-teal-500 ${done ? 'scale-70' : 'animate-breathe'}`}
            style={{ animationPlayState: paused ? 'paused' : 'running' }}
          />
          <div className="absolute flex flex-col items-center gap-2" aria-live="polite">
            <span className="text-24 font-extrabold text-white">{done ? copy.breathing.done : phase}</span>
            <span className="text-18 font-bold text-white">
              {done ? copy.breathing.doneSub : copy.breathing.seconds(left)}
            </span>
          </div>
        </div>
        <div className="flex flex-wrap justify-center gap-8">
          {PHASES.map((p) => {
            const on = !done && p === phase;
            return (
              <span
                key={p}
                className={`rounded-full px-14 py-8 text-13 ${on ? 'bg-white font-extrabold' : 'bg-white-50 font-semibold'}`}
              >
                {copy.breathing.phases[p]}
              </span>
            );
          })}
        </div>
        <div className="max-w-300 text-center text-14 leading-155">{copy.breathing.hint}</div>
        <div className="flex w-full flex-col gap-8">
          <div className="text-center text-13 font-semibold text-muted-deep">
            {copy.breathing.round(Math.min(ROUNDS, Math.floor(elapsed / CYCLE) + 1))}
          </div>
          <Button variant="dark" onClick={() => (done ? restart() : setPaused((p) => !p))}>
            {done ? copy.breathing.again : paused ? copy.breathing.resume : copy.breathing.pause}
          </Button>
        </div>
      </div>
    </Sheet>
  );
}
