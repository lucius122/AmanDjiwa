import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router';
import { api } from '../lib/api';
import { copy } from '../lib/copy';
import type { Hotline } from '../lib/types';
import { hotlineDisplay, UNVERIFIED } from './CrisisCard';
import { Icon } from './Icon';
import { Sheet, SheetHeader } from './Sheet';
import { useToast } from './Toast';

/** Telepon hotline. Nomor hanya dari hotlines.yaml; yang belum diverifikasi tidak bisa ditelepon (§6.6). */
export function useDial() {
  const toast = useToast();
  return (h: Hotline) => {
    if (h.number === UNVERIFIED) toast(copy.chat.hotlineUnverified);
    else window.location.href = `tel:${h.number.replace(/[^\d+]/g, '')}`;
  };
}

/** "Chat kakak pendamping" dari luar tab Ngobrol: kabari pendamping, lalu buka obrolan. */
export function useConnectFromOutside() {
  const navigate = useNavigate();
  const toast = useToast();
  const queryClient = useQueryClient();
  return async () => {
    try {
      await api('/chat/action', { method: 'POST', body: { type: 'connect', value: null } });
      await queryClient.invalidateQueries({ queryKey: ['chat-history'] });
      navigate('/ngobrol');
    } catch {
      toast(copy.chat.sendFailed);
    }
  };
}

const OPTION = 'flex min-h-62 items-center justify-between rounded-14 border border-sand-200 px-16 text-left';
// Warna latar opsi mengikuti urutan di desain: darurat (peach), kesehatan jiwa (cream).
const HOTLINE_STYLE = [
  { bg: 'bg-peach-100', ink: 'stroke-peach-600' },
  { bg: 'bg-cream', ink: 'stroke-teal-600' },
];

interface Props {
  open: boolean;
  onClose: () => void;
  hotlines: Hotline[];
  kelurahan: string;
  onCall: (h: Hotline) => void;
  onConnect: () => void;
}

export function HelpSheet({ open, onClose, hotlines, kelurahan, onCall, onConnect }: Props) {
  return (
    <Sheet open={open} onClose={onClose} labelledBy="help-title">
      <div className="flex flex-col gap-12 px-20 py-22">
        <SheetHeader id="help-title" title={copy.help.title} onClose={onClose} />
        <div className="text-14 leading-150 text-muted">{copy.help.lead}</div>
        {hotlines.map((h, i) => {
          const style = HOTLINE_STYLE[i] ?? HOTLINE_STYLE[1];
          return (
            <button key={h.id} type="button" onClick={() => onCall(h)} className={`${OPTION} ${style.bg}`}>
              <Option label={h.label} title={hotlineDisplay(h)} ink={style.ink} />
            </button>
          );
        })}
        <button type="button" onClick={onConnect} className={`${OPTION} bg-teal-100`}>
          <Option label={copy.help.pendampingLabel} title={copy.help.pendampingTitle(kelurahan)} ink="stroke-teal-600" />
        </button>
      </div>
    </Sheet>
  );
}

function Option({ label, title, ink }: { label: string; title: string; ink: string }) {
  return (
    <>
      <span className="flex flex-col">
        <span className="text-13 text-muted">{label}</span>
        <span className="text-17 font-bold">{title}</span>
      </span>
      <Icon name="next" className={`h-22 w-22 ${ink}`} strokeWidth={2} />
    </>
  );
}
