import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { copy } from '../lib/copy';
import type { TelegramLink } from '../lib/types';
import { Button } from './Button';
import { Sheet, SheetHeader } from './Sheet';

export function TelegramSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [link, setLink] = useState<TelegramLink | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    if (!open) return;
    setLink(null);
    setFailed(false);
    api<TelegramLink>('/telegram/link-token', { method: 'POST' }).then(setLink, () => setFailed(true));
  }, [open]);
  return (
    <Sheet open={open} onClose={onClose} labelledBy="tg-title">
      <div className="flex flex-col gap-14 px-20 py-22">
        <SheetHeader id="tg-title" title={copy.telegram.title} onClose={onClose} />
        <div className="text-14 leading-155 text-muted">{copy.telegram.lead}</div>
        <div className="flex flex-col items-center gap-4 rounded-14 bg-sky-100 p-16">
          <span className="text-13 font-semibold text-muted-strong">
            {link ? `@${link.bot_username}` : copy.brand.botHandle}
          </span>
          {/* DESIGN-GAP: state loading & gagal tidak ada di desain */}
          <span className="text-28 font-extrabold tracking-wider">{link?.code ?? copy.telegram.loading}</span>
          {failed && <span className="text-13 font-semibold text-warn-text">{copy.telegram.failed}</span>}
        </div>
        <Button variant="dark" disabled={!link} onClick={() => link && window.open(link.deep_link, '_blank', 'noopener')}>
          {copy.telegram.open}
        </Button>
      </div>
    </Sheet>
  );
}
