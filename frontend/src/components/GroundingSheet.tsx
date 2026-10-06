import { useEffect, useState } from 'react';
import { copy } from '../lib/copy';
import { Button } from './Button';
import { Icon } from './Icon';
import { CloseButton, Sheet } from './Sheet';
import { useToast } from './Toast';

const t = copy.grounding;

/** Latihan grounding 5-4-3-2-1 (sheet `ground` di desain). */
export function GroundingSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const toast = useToast();
  const [index, setIndex] = useState(0);
  useEffect(() => {
    if (open) setIndex(0);
  }, [open]);
  const last = index >= t.steps.length - 1;

  const next = () => {
    if (!last) return setIndex(index + 1);
    onClose();
    toast(t.finished);
  };

  return (
    <Sheet open={open} onClose={onClose} labelledBy="ground-title">
      <div className="flex flex-col gap-10 px-20 pb-24 pt-16">
        <div className="flex items-center justify-between">
          <span id="ground-title" className="text-18 font-extrabold">
            {t.title}
          </span>
          <CloseButton onClose={onClose} />
        </div>
        <p className="m-0 mb-4 text-14 leading-155 text-muted">{t.lead}</p>
        <ol className="m-0 flex list-none flex-col gap-10 p-0">
          {t.steps.map((s, i) => {
            const current = i === index;
            return (
              <li
                key={s.n}
                aria-current={current ? 'step' : undefined}
                className={`flex items-center gap-14 rounded-16 border-1.5 px-14 py-12 transition-all duration-200 ${current ? 'border-butter-300 bg-butter-100' : 'border-sand-200 bg-white'} ${i > index ? 'opacity-55' : ''}`}
              >
                <div className="flex h-44 w-44 flex-none items-center justify-center rounded-12 bg-cream text-20 font-extrabold">{s.n}</div>
                <div className="flex flex-1 flex-col gap-2">
                  <span className="text-15 font-bold">{s.title}</span>
                  <span className="text-13 text-muted">{s.example}</span>
                </div>
                {i < index && <Icon name="check" className="h-22 w-22 stroke-teal-600" strokeWidth={2.5} />}
              </li>
            );
          })}
        </ol>
        <Button className="mt-6" onClick={next}>
          {last ? t.done : t.next}
        </Button>
      </div>
    </Sheet>
  );
}
