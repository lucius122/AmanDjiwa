import { useQuery } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { BreathingSheet } from '../components/BreathingSheet';
import { ChatBubble, TypingIndicator } from '../components/ChatBubble';
import { CrisisCard } from '../components/CrisisCard';
import { HelpSheet, useDial } from '../components/HelpSheet';
import { Icon } from '../components/Icon';
import { DjiwaAvatar } from '../components/Logo';
import { FollowupCard, ScreeningCard } from '../components/ScreeningCard';
import { TelegramSheet } from '../components/TelegramSheet';
import { useToast } from '../components/Toast';
import { ApiError, api } from '../lib/api';
import { copy } from '../lib/copy';
import type { ChatAction, ChatTurn, History, Me, MessageKind, ScreeningQuestion, Sender } from '../lib/types';

const t = copy.chat;
const CHIP = 'h-40 flex-none rounded-full border-1.5 border-teal-200 bg-white px-14 text-14 font-semibold hover:bg-teal-100';

interface Item {
  key: string;
  sender: Sender;
  kind: MessageKind;
  text: string;
  author?: string | null;
}

let seq = 0;
const item = (sender: Sender, text: string, kind: MessageKind = 'text'): Item => ({
  key: `local-${seq++}`,
  sender,
  kind,
  text,
});

export function Chat({ me }: { me: Me }) {
  const toast = useToast();
  const dial = useDial();
  const [connected, setConnected] = useState(false);
  const [typing, setTyping] = useState(false);
  // Sudah minta pendamping → cek berkala apakah sapaannya sudah masuk.
  const history = useQuery({
    queryKey: ['chat-history'],
    queryFn: () => api<History>('/chat/history'),
    refetchInterval: connected && !typing ? 15_000 : false,
  });
  const [items, setItems] = useState<Item[]>([]);
  const [question, setQuestion] = useState<ScreeningQuestion | null>(null);
  const [followup, setFollowup] = useState(false);
  const [offerConnect, setOfferConnect] = useState(false);
  const [input, setInput] = useState('');
  const [sheet, setSheet] = useState<'help' | 'tg' | 'napas' | null>(null);
  const list = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!history.data) return;
    setItems(
      history.data.messages.map((m) => ({ key: m.id, sender: m.sender, kind: m.kind, text: m.text, author: m.author })),
    );
    setQuestion(history.data.screening);
    setFollowup(history.data.followup_offer);
    setConnected(history.data.connected);
  }, [history.data]);

  useEffect(() => {
    list.current?.scrollTo({ top: list.current.scrollHeight });
  }, [items, typing, question, followup]);

  function apply(turn: ChatTurn) {
    setItems((prev) => [...prev, ...turn.messages.map((m) => item(m.sender, m.text, m.kind))]);
    setQuestion(turn.screening);
    setFollowup(turn.followup_offer);
    setConnected(turn.connected);
    setOfferConnect(turn.offer_connect && !turn.card && !turn.connected);
    if (turn.client_action === 'open_napas') window.setTimeout(() => setSheet('napas'), 500);
    // Menanyakan nomor/kontak layanan → daftar resmi (hotlines.yaml) di sheet bantuan.
    if (turn.client_action === 'open_help') window.setTimeout(() => setSheet('help'), 500);
  }

  async function call<T extends object>(path: string, body: T, mine?: string) {
    if (typing) return;
    if (mine) setItems((prev) => [...prev, item('remaja', mine)]);
    setTyping(true);
    try {
      apply(await api<ChatTurn>(path, { method: 'POST', body }));
    } catch (e) {
      toast(e instanceof ApiError && e.status === 429 ? e.message : t.sendFailed); // DESIGN-GAP
    } finally {
      setTyping(false);
    }
  }

  const send = (raw: string) => {
    const text = raw.trim();
    if (!text) return;
    setInput('');
    void call('/chat/message', { text }, text);
  };
  const act = (type: ChatAction, value: number | null = null, mine?: string) =>
    void call('/chat/action', { type, value }, mine);
  const connect = () => {
    setSheet(null);
    if (!connected) act('connect');
  };
  const chip = (label: string) => {
    if (label === t.chipBreathing) setSheet('napas');
    else send(label === t.chipScreening ? t.chipScreeningText : label);
  };

  const hotlines = history.data?.hotlines ?? [];
  return (
    <div className="mx-auto flex min-h-0 w-full max-w-820 flex-1 flex-col">
      <header className="flex flex-none flex-wrap items-center gap-10 border-b border-sand-200 bg-white py-10 pl-16 pr-12">
        <div className="flex shrink grow basis-200 items-center gap-12">
          <DjiwaAvatar />
          <div className="flex flex-1 flex-col gap-2">
            <div className="text-16 font-extrabold">{t.name}</div>
            <div className="flex items-center gap-6 text-12 text-muted">
              <span className="h-8 w-8 rounded-full bg-teal-500" />
              {typing ? t.typing : t.online}
            </div>
          </div>
        </div>
        <div className="flex flex-auto justify-end gap-8">
          <button
            type="button"
            onClick={() => setSheet('help')}
            className="flex h-40 max-w-260 flex-auto items-center justify-center gap-6 rounded-full bg-peach-100 px-14 text-13 font-bold text-peach-800 hover:bg-peach-200"
          >
            <Icon name="phone" className="h-16 w-16 stroke-peach-600" strokeWidth={2} />
            {t.help}
          </button>
          <button
            type="button"
            onClick={() => setSheet('tg')}
            className="flex h-40 items-center gap-6 rounded-full bg-sky-100 px-14 text-13 font-bold hover:bg-sky-200"
          >
            <Icon name="telegram" className="h-16 w-16 stroke-navy" strokeWidth={2} />
            {t.telegram}
          </button>
        </div>
      </header>

      <div ref={list} className="flex min-h-0 flex-1 flex-col gap-10 overflow-y-auto px-16 py-18">
        <div className="self-center text-12 font-semibold text-muted">{t.today}</div>
        {history.isPending && <TypingIndicator label={t.typingLong} />}
        {history.isError && (
          // DESIGN-GAP: state gagal memuat tidak ada di desain
          <div className="flex flex-col items-center gap-8 self-center text-14 text-muted">
            {t.loadFailed}
            <button type="button" className={CHIP} onClick={() => void history.refetch()}>
              {t.retry}
            </button>
          </div>
        )}
        {items.map((m) =>
          m.kind === 'crisis_card' && history.data ? (
            <CrisisCard
              key={m.key}
              card={history.data.card}
              hotline={hotlines[0]}
              connected={connected}
              onCall={dial}
              onConnect={connect}
            />
          ) : (
            <ChatBubble key={m.key} sender={m.sender}>
              {m.sender === 'pendamping' ? `${t.pendamping(m.author)}\n${m.text}` : m.text}
            </ChatBubble>
          ),
        )}
        {offerConnect && (
          // DESIGN-GAP: tawaran pendamping di luar kartu krisis memakai gaya chip.
          <button type="button" className={`${CHIP} self-start`} onClick={connect}>
            {t.connectOffer}
          </button>
        )}
        {question && (
          <ScreeningCard
            q={question}
            busy={typing}
            onAnswer={(v) => act('answer', v, question.options[v])}
            onSkip={() => act('skip', null, 'Lewati')}
            onStop={() => act('stop')}
          />
        )}
        {followup && <FollowupCard busy={typing} onContinue={() => act('continue')} onStop={() => act('stop')} />}
        {typing && <TypingIndicator label={t.typingLong} />}
      </div>

      <div className="flex flex-none flex-col gap-10 px-12 pb-12 pt-8">
        <div className="flex gap-8 overflow-x-auto pb-2">
          {t.chips.map((label) => (
            <button key={label} type="button" className={CHIP} onClick={() => chip(label)}>
              {label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-8">
          <input
            aria-label={t.inputLabel}
            value={input}
            maxLength={2000}
            placeholder={t.inputPlaceholder}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                send(input);
              }
            }}
            className="h-48 min-w-0 flex-1 rounded-full border-1.5 border-sand-400 bg-white px-18 text-16"
          />
          <button
            type="button"
            aria-label={t.send}
            onClick={() => send(input)}
            className="flex h-48 w-48 flex-none items-center justify-center rounded-full bg-teal-600 hover:bg-teal-700"
          >
            <Icon name="send" className="h-20 w-20 stroke-white" strokeWidth={2} />
          </button>
        </div>
      </div>

      <HelpSheet
        open={sheet === 'help'}
        onClose={() => setSheet(null)}
        hotlines={hotlines}
        kelurahan={me.kelurahan_name}
        onCall={dial}
        onConnect={connect}
      />
      <TelegramSheet open={sheet === 'tg'} onClose={() => setSheet(null)} />
      <BreathingSheet open={sheet === 'napas'} onClose={() => setSheet(null)} />
    </div>
  );
}
