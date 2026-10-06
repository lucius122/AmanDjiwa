import { copy } from '../lib/copy';
import type { CrisisCard as Card, Hotline } from '../lib/types';
import { Icon } from './Icon';

export const UNVERIFIED = 'TODO_VERIFY';

/** Tampilan nomor: sebelum diverifikasi tetap "[ nomor ]" seperti desain (§6.6). */
export function hotlineDisplay(h: Hotline): string {
  return h.number === UNVERIFIED ? '[ nomor ]' : h.number;
}

interface Props {
  card: Card;
  hotline: Hotline | undefined;
  connected: boolean;
  onCall: (h: Hotline) => void;
  onConnect: () => void;
}

export function CrisisCard({ card, hotline, connected, onCall, onConnect }: Props) {
  return (
    <div className="flex max-w-440 animate-in-35 flex-col gap-14 rounded-22 bg-lavender-100 px-18 py-20">
      <div className="flex h-44 w-44 items-center justify-center rounded-14 bg-white">
        <Icon name="heart" className="h-24 w-24 stroke-lavender-600" />
      </div>
      <div className="flex flex-col gap-6">
        <div className="text-18 font-extrabold leading-130">{card.title}</div>
        <div className="text-14 leading-155 text-lavender-800">{card.body}</div>
      </div>
      {hotline && (
        <button
          type="button"
          onClick={() => onCall(hotline)}
          className="flex min-h-56 items-center gap-12 rounded-14 bg-navy px-16 text-left text-white"
        >
          <Icon name="phone" className="h-22 w-22 stroke-white" />
          <span className="flex flex-col">
            <span className="text-15 font-bold">{card.call_label}</span>
            <span className="text-12 text-on-navy-muted">
              {hotlineDisplay(hotline)}
              {hotline.note && ` · ${hotline.note}`}
            </span>
          </span>
        </button>
      )}
      <button
        type="button"
        onClick={onConnect}
        className={`flex min-h-56 items-center gap-12 rounded-14 px-16 text-left text-white ${connected ? 'bg-teal-muted' : 'bg-teal-600'}`}
      >
        <Icon name="people" className="h-22 w-22 stroke-white" />
        <span className="flex flex-col">
          <span className="text-15 font-bold">{connected ? copy.chat.connected : card.connect_label}</span>
          <span className="text-12 text-teal-75">{card.connect_sub}</span>
        </span>
      </button>
      <div className="text-13 leading-150 text-lavender-800">{card.footer}</div>
    </div>
  );
}
