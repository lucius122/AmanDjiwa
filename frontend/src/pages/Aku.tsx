import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Avatar } from '../components/Avatar';
import { Button } from '../components/Button';
import { HelpSheet, useConnectFromOutside, useDial } from '../components/HelpSheet';
import { Icon } from '../components/Icon';
import { Sheet } from '../components/Sheet';
import { TelegramSheet } from '../components/TelegramSheet';
import { useToast } from '../components/Toast';
import { api } from '../lib/api';
import { copy } from '../lib/copy';
import { supabase } from '../lib/supabase';
import type { Hotline, Me } from '../lib/types';

const t = copy.aku;
const d = copy.deleteSheet;
const ROW = 'flex min-h-56 items-center gap-12 rounded-14 px-18 text-left text-15 font-bold';

export function Aku({ me }: { me: Me }) {
  const navigate = useNavigate();
  const toast = useToast();
  const dial = useDial();
  const connect = useConnectFromOutside();
  const queryClient = useQueryClient();
  const hotlines = useQuery({ queryKey: ['hotlines'], queryFn: () => api<Hotline[]>('/hotlines', { auth: false }), staleTime: Infinity });
  const [sheet, setSheet] = useState<'tg' | 'help' | 'delete' | null>(null);
  const [busy, setBusy] = useState(false);

  async function leave(message: string) {
    // Pindah ke landing DULU: kalau signOut duluan, guard aplikasi sempat membelokkan ke /masuk.
    navigate('/', { replace: true });
    await supabase?.auth.signOut();
    queryClient.clear(); // jangan tinggalkan data remaja di cache browser
    toast(message);
  }

  async function deleteAll() {
    setBusy(true);
    try {
      await api('/me', { method: 'DELETE' }); // §7: hard delete + cascade, termasuk akun login
      await leave(d.done);
    } catch {
      toast(d.failed);
      setBusy(false);
    }
  }

  return (
    <div className="min-h-0 flex-1 overflow-y-auto">
      <div className="mx-auto flex max-w-560 flex-col gap-14 px-16 pb-32 pt-24">
        <div className="flex items-center gap-14 rounded-20 border border-sand-200 bg-white p-20">
          <Avatar index={me.avatar} size="lg" />
          <div className="flex flex-col gap-2">
            <h1 className="m-0 text-20 font-extrabold">{me.pseudonym}</h1>
            <span className="text-14 text-muted">
              {me.kelurahan_name} · {t.age(new Date().getFullYear() - me.birth_year)}
            </span>
          </div>
        </div>
        <section className="flex flex-col gap-8 rounded-20 bg-teal-100 p-20" aria-labelledby="aku-privasi">
          <h2 id="aku-privasi" className="m-0 text-16 font-extrabold">
            {t.privacyTitle}
          </h2>
          <p className="m-0 text-14 leading-155">{t.privacyBody}</p>
        </section>
        <button type="button" onClick={() => setSheet('tg')} className={`${ROW} border border-sand-200 bg-white`}>
          <Icon name="telegram" className="h-20 w-20 stroke-navy" />
          {t.telegram}
        </button>
        <button type="button" onClick={() => setSheet('help')} className={`${ROW} bg-peach-100 text-peach-800`}>
          <Icon name="phone" className="h-20 w-20 stroke-peach-600" />
          {t.help}
        </button>
        <button type="button" onClick={() => setSheet('delete')} className={`${ROW} border border-sand-200 bg-white`}>
          <Icon name="trash" className="h-20 w-20 stroke-navy" />
          {t.delete}
        </button>
        <button type="button" onClick={() => void leave(t.loggedOut)} className="min-h-48 bg-transparent text-15 font-bold">
          {t.logout}
        </button>
        <div className="text-center text-12 leading-150 text-muted">{copy.brand.notDiagnosis}</div>
      </div>

      <TelegramSheet open={sheet === 'tg'} onClose={() => setSheet(null)} />
      <HelpSheet
        open={sheet === 'help'}
        onClose={() => setSheet(null)}
        hotlines={hotlines.data ?? []}
        kelurahan={me.kelurahan_name}
        onCall={dial}
        onConnect={() => {
          setSheet(null);
          void connect();
        }}
      />
      <Sheet open={sheet === 'delete'} onClose={() => setSheet(null)} labelledBy="del-title">
        <div className="flex flex-col gap-14 px-20 py-24">
          <h2 id="del-title" className="m-0 text-20 font-extrabold">
            {d.title}
          </h2>
          <p className="m-0 text-14 leading-155 text-muted">{d.body}</p>
          <Button variant="dark" disabled={busy} onClick={deleteAll}>
            {d.confirm}
          </Button>
          <button
            type="button"
            onClick={() => setSheet(null)}
            className="h-48 rounded-14 border-1.5 border-sand-400 bg-white text-15 font-bold"
          >
            {d.cancel}
          </button>
        </div>
      </Sheet>
    </div>
  );
}
