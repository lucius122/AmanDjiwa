import { useEffect, useRef, type ReactNode } from 'react';
import { copy } from '../lib/copy';
import { Icon } from './Icon';

interface Props {
  open: boolean;
  onClose: () => void;
  labelledBy: string;
  children: ReactNode;
}

/** Bottom sheet di mobile, dialog di tengah di layar lebar (≥ 900px). Esc / klik luar = tutup. */
export function Sheet({ open, onClose, labelledBy, children }: Props) {
  const panel = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement as HTMLElement | null;
    panel.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('keydown', onKey);
      previous?.focus();
    };
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex flex-col items-center justify-end bg-overlay lg:justify-center lg:p-24"
    >
      <div
        ref={panel}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
        onClick={(e) => e.stopPropagation()}
        className="max-h-90vh w-full max-w-480 animate-in-25 overflow-y-auto rounded-sheet bg-white outline-none lg:rounded-24"
      >
        {children}
      </div>
    </div>
  );
}

export function SheetHeader({ id, title, onClose }: { id: string; title: string; onClose: () => void }) {
  return (
    <div className="flex items-center justify-between">
      <div id={id} className="text-20 font-extrabold">
        {title}
      </div>
      <CloseButton onClose={onClose} />
    </div>
  );
}

export function CloseButton({ onClose }: { onClose: () => void }) {
  return (
    <button
      type="button"
      onClick={onClose}
      aria-label={copy.help.close}
      className="flex h-44 w-44 items-center justify-center rounded-12 bg-transparent"
    >
      <Icon name="close" className="h-22 w-22 stroke-navy" strokeWidth={2} />
    </button>
  );
}
