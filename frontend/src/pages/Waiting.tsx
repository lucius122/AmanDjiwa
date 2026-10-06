import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router';
import { hotlineDisplay } from '../components/CrisisCard';
import { WaitingIllustration } from '../components/Illustrations';
import { OnboardingFrame } from '../components/OnboardingFrame';
import { useToast } from '../components/Toast';
import { ApiError, api } from '../lib/api';
import { copy } from '../lib/copy';
import { useGate } from '../lib/me';
import type { Hotline } from '../lib/types';

const t = copy.waiting;
const POLL_MS = 5000; // cek otomatis apakah orang tua sudah menyetujui

export function Waiting() {
  const gate = useGate(POLL_MS);
  const navigate = useNavigate();
  const toast = useToast();
  const location = useLocation();
  // Email ortu hanya diketahui sesaat setelah dikirim (backend menyimpannya terenkripsi, tidak dikembalikan).
  const [parentEmail] = useState<string | null>((location.state as { parentEmail?: string } | null)?.parentEmail ?? null);
  const [busy, setBusy] = useState(false);
  const hotlines = useQuery({ queryKey: ['hotlines'], queryFn: () => api<Hotline[]>('/hotlines'), staleTime: Infinity });
  const [wasPending, setWasPending] = useState(false);

  useEffect(() => {
    if (gate.state === 'pending') setWasPending(true);
    if (gate.state === 'active' && wasPending) toast(t.approved);
  }, [gate.state, wasPending, toast]);

  if (gate.state === 'loading') return null;
  if (gate.state !== 'pending') {
    const to = { anon: '/masuk', needs_profile: '/daftar', active: '/ngobrol' }[gate.state];
    return <Navigate to={to} replace />;
  }

  const changeEmail = () => navigate('/daftar', { state: { from: '/menunggu' } });
  async function resend() {
    if (!parentEmail) return changeEmail();
    setBusy(true);
    try {
      await api('/consent/guardian', { method: 'POST', body: { email: parentEmail } });
      toast(t.resent(parentEmail));
    } catch (e) {
      toast(e instanceof ApiError ? e.message : copy.register.failed);
    } finally {
      setBusy(false);
    }
  }

  const emergency = hotlines.data?.[0];
  return (
    <OnboardingFrame>
      <div className="flex flex-1 animate-in-30 flex-col items-center gap-16 px-24 py-28 text-center">
        <div className="aspect-4/3 max-h-220 w-full overflow-hidden rounded-24 bg-lavender-100">
          <WaitingIllustration label={t.illustrationAlt} />
        </div>
        <h1 className="m-0 mt-8 text-24 font-extrabold leading-120 tracking-tight">{t.title}</h1>
        <p className="m-0 text-pretty text-15 leading-155 text-muted">
          {parentEmail ? (
            <>
              {t.bodyBefore}
              <b className="text-navy">{parentEmail}</b>
              {t.bodyAfter}
            </>
          ) : (
            t.bodyNoEmail
          )}
        </p>
        <div className="flex items-center gap-8 rounded-full border border-sand-200 bg-white px-14 py-10 text-13 font-semibold">
          <span className="h-8 w-8 rounded-full bg-teal-500" />
          {t.sent}
        </div>
        <div className="mt-auto flex w-full flex-col gap-8">
          <button
            type="button"
            disabled={busy}
            onClick={resend}
            className="h-48 rounded-14 border-1.5 border-teal-600 bg-white text-15 font-bold text-teal-600"
          >
            {t.resend}
          </button>
          <button type="button" onClick={changeEmail} className="h-44 bg-transparent text-14 font-semibold">
            {t.change}
          </button>
        </div>
        <div className="w-full rounded-14 bg-peach-100 px-14 py-12 text-left text-13 leading-150 text-peach-800">
          {t.emergency}
          <b>{emergency ? hotlineDisplay(emergency) : '[ nomor ]'}</b>
        </div>
      </div>
    </OnboardingFrame>
  );
}
