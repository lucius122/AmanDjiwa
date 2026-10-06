import { zodResolver } from '@hookform/resolvers/zod';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Navigate, useNavigate } from 'react-router';
import { z } from 'zod';
import { Button } from '../../components/Button';
import { LogoMark, Wordmark } from '../../components/Logo';
import { ApiError, api, staffToken } from '../../lib/api';
import { copy } from '../../lib/copy';
import type { StaffToken } from '../../lib/types';

const t = copy.staffLogin;
const schema = z.object({ email: z.string().trim().email(), password: z.string().min(1).max(256) });
type Form = z.infer<typeof schema>;
const FIELD = 'h-52 rounded-14 border-1.5 border-sand-400 bg-white px-16 text-16';

/** DESIGN-GAP: login staf (email + kata sandi → TOTP) tidak ada di desain; diturunkan dari login remaja. */
export function StaffLogin() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [pre, setPre] = useState<string | null>(null);
  const [code, setCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const form = useForm<Form>({ resolver: zodResolver(schema), defaultValues: { email: '', password: '' } });

  if (staffToken.get()) return <Navigate to="/staf" replace />;

  // Pesan 401/429 dari backend sudah berbahasa Indonesia (salah sandi / kode / terkunci).
  async function run<T>(fn: () => Promise<T>): Promise<T | undefined> {
    setBusy(true);
    setError(null);
    try {
      return await fn();
    } catch (e) {
      setError(e instanceof ApiError && (e.status === 401 || e.status === 429) ? e.message : t.failed);
    } finally {
      setBusy(false);
    }
  }

  const login = (body: Form) =>
    run(() => api<{ pre_auth_token: string }>('/auth/staff/login', { method: 'POST', body, auth: false })).then(
      (r) => r && setPre(r.pre_auth_token),
    );

  async function verify() {
    const r = await run(() =>
      api<StaffToken>('/auth/staff/totp', { method: 'POST', body: { pre_auth_token: pre, code }, auth: false }),
    );
    if (!r) return setCode('');
    const { access_token, ...me } = r;
    staffToken.set(access_token);
    queryClient.setQueryData(['staff-me'], me);
    navigate('/staf', { replace: true });
  }

  return (
    <main className="flex min-h-dvh items-center justify-center bg-cream p-16">
      <div className="flex w-full max-w-420 animate-in-30 flex-col gap-20 rounded-24 border border-sand-200 bg-white p-24 shadow-panel">
        <div className="flex items-center gap-8">
          <LogoMark className="h-30 w-30" />
          <Wordmark className="text-18" />
        </div>
        <div className="flex flex-col gap-8">
          <h1 className="m-0 text-26 font-extrabold leading-120 tracking-tight">{t.title}</h1>
          <p className="m-0 text-15 leading-155 text-muted">{pre ? t.totpLead : t.lead}</p>
        </div>
        {!pre ? (
          <form onSubmit={form.handleSubmit(login)} className="flex flex-col gap-14" noValidate>
            <label className="flex flex-col gap-6 text-14 font-semibold">
              {t.email}
              <input type="email" autoComplete="username" {...form.register('email')} className={FIELD} />
            </label>
            <label className="flex flex-col gap-6 text-14 font-semibold">
              {t.password}
              <input type="password" autoComplete="current-password" {...form.register('password')} className={FIELD} />
            </label>
            {error && <span className="text-13 font-semibold text-warn-text">{error}</span>}
            <Button type="submit" disabled={busy}>
              {t.submit}
            </Button>
          </form>
        ) : (
          <div className="flex flex-col gap-10">
            <label htmlFor="staff-totp" className="text-14 font-bold">
              {t.totpLabel}
            </label>
            <input
              id="staff-totp"
              inputMode="numeric"
              autoComplete="one-time-code"
              autoFocus
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              onKeyDown={(e) => e.key === 'Enter' && code.length === 6 && void verify()}
              className="h-56 rounded-12 border-1.5 border-sand-400 bg-cream px-16 text-center text-24 font-bold tracking-widest"
            />
            {error && <span className="text-13 font-semibold text-warn-text">{error}</span>}
            <Button disabled={code.length < 6 || busy} onClick={verify}>
              {t.totpSubmit}
            </Button>
          </div>
        )}
      </div>
    </main>
  );
}
