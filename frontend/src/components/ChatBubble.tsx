import type { Sender } from '../lib/types';

const STYLE: Record<Sender, string> = {
  remaja: 'self-end rounded-bubble-out border-teal-600 bg-teal-600 text-white',
  bot: 'self-start rounded-bubble-in border-sand-200 bg-white text-navy',
  pendamping: 'self-start rounded-bubble-in border-lavender-200 bg-lavender-100 text-navy',
};

export function ChatBubble({ sender, children }: { sender: Sender; children: string }) {
  return (
    <div className={`max-w-bubble animate-in-25 whitespace-pre-wrap border px-14 py-12 text-15 leading-150 ${STYLE[sender]}`}>
      {children}
    </div>
  );
}

export function TypingIndicator({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-8 self-start">
      <div className="flex gap-5 rounded-bubble-in border border-sand-200 bg-white px-16 py-14">
        {[0, 0.15, 0.3].map((delay) => (
          <span key={delay} className="block h-7 w-7 animate-dot rounded-full bg-teal-500" style={{ animationDelay: `${delay}s` }} />
        ))}
      </div>
      <span className="text-12 text-muted">{label}</span>
    </div>
  );
}
