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
const CODE = 'h-56 rounded-12 border-1.5 border-sand-400 bg-cream px-16 text-center text-24 font-bold tracking-widest';
const digits = (v: string) => v.replace(/\D/g, '').slice(0, 6);

interface LoginOut {
  pre_auth_token: string;
  setup_required: boolean;
}

/** DESIGN-GAP: login staf (email + kata sandi → TOTP) tidak ada di desain; diturunkan dari login remaja.
 * Akun baru/di-reset admin kota: langkah "Atur akunmu" (pasang authenticator + password baru). */
export function StaffLogin() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [pre, setPre] = useState<string | null>(null);
  const [setup, setSetup] = useState<{ secret: string; otpauth_uri: string } | null>(null);
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const form = useForm<Form>({ resolver: zodResolver(schema), defaultValues: { email: '', password: '' } });

  if (staffToken.get()) return <Navigate to="/staf" replace />;

  // Pesan 401/422/429 dari backend sudah berbahasa Indonesia (salah sandi / kode / terkunci).
  async function run<T>(fn: () => Promise<T>): Promise<T | undefined> {
    setBusy(true);
    setError(null);
    try {
      return await fn();
    } catch (e) {
      setError(e instanceof ApiError && [401, 422, 429].includes(e.status) ? e.message : t.failed);
    } finally {
      setBusy(false);
    }
  }

  async function login(body: Form) {
    const r = await run(() => api<LoginOut>('/auth/staff/login', { method: 'POST', body, auth: false }));
    if (!r) return;
    setPre(r.pre_auth_token);
    if (!r.setup_required) return;
    const s = await run(() =>
      api<{ secret: string; otpauth_uri: string }>('/auth/staff/setup/start', {
        method: 'POST',
        body: { pre_auth_token: r.pre_auth_token },
        auth: false,
      }),
    );
    if (s) setSetup(s);
  }

  function signedIn({ access_token, ...me }: StaffToken) {
    staffToken.set(access_token);
    queryClient.setQueryData(['staff-me'], me);
    navigate(me.role === 'admin_kota' ? '/kota' : '/staf', { replace: true });
  }

  async function verify() {
    const r = await run(() =>
      api<StaffToken>('/auth/staff/totp', { method: 'POST', body: { pre_auth_token: pre, code }, auth: false }),
    );
    if (r) signedIn(r);
    else setCode('');
  }

  async function finishSetup() {
    if (newPassword.length < 12) return setError(t.passwordShort);
    if (newPassword !== confirm) return setError(t.passwordMismatch);
    const r = await run(() =>
      api<StaffToken>('/auth/staff/setup/finish', {
        method: 'POST',
        body: { pre_auth_token: pre, code, new_password: newPassword },
        auth: false,
      }),
    );
    if (r) signedIn(r);
    else setCode('');
  }

  const errorText = error && <span className="text-13 font-semibold text-warn-text">{error}</span>;
  return (
    <main className="flex min-h-dvh items-center justify-center bg-cream p-16">
      <div className="flex w-full max-w-420 animate-in-30 flex-col gap-20 rounded-24 border border-sand-200 bg-white p-24 shadow-panel">
        <div className="flex items-center gap-8">
          <LogoMark className="h-30 w-30" />
          <Wordmark className="text-18" />
        </div>
        <div className="flex flex-col gap-8">
          <h1 className="m-0 text-26 font-extrabold leading-120 tracking-tight">{setup ? t.setupTitle : t.title}</h1>
          <p className="m-0 text-15 leading-155 text-muted">{setup ? t.setupLead : pre ? t.totpLead : t.lead}</p>
        </div>
        {!pre && (
          <form onSubmit={form.handleSubmit(login)} className="flex flex-col gap-14" noValidate>
            <label className="flex flex-col gap-6 text-14 font-semibold">
              {t.email}
              <input type="email" autoComplete="username" {...form.register('email')} className={FIELD} />
            </label>
            <label className="flex flex-col gap-6 text-14 font-semibold">
              {t.password}
              <input type="password" autoComplete="current-password" {...form.register('password')} className={FIELD} />
            </label>
            {errorText}
            <Button type="submit" disabled={busy}>
              {t.submit}
            </Button>
          </form>
        )}
        {pre && !setup && (
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
              onChange={(e) => setCode(digits(e.target.value))}
              onKeyDown={(e) => e.key === 'Enter' && code.length === 6 && void verify()}
              className={CODE}
            />
            {errorText}
            <Button disabled={code.length < 6 || busy} onClick={verify}>
              {t.totpSubmit}
            </Button>
          </div>
        )}
        {setup && (
          <div className="flex flex-col gap-14">
            <div className="flex flex-col gap-8 rounded-14 bg-sky-100 p-16">
              <span className="text-13 font-bold">{t.setupKeyLabel}</span>
              <span className="select-all break-all text-18 font-extrabold tracking-wide">
                {setup.secret.match(/.{1,4}/g)?.join(' ')}
              </span>
              <span className="text-13 leading-150 text-muted-strong">{t.setupKeyHelp}</span>
              <a href={setup.otpauth_uri} className="text-13 font-bold text-teal-600">
                {t.setupOpenApp}
              </a>
            </div>
            <label className="flex flex-col gap-6 text-14 font-semibold">
              {t.newPassword}
              <input
                type="password"
                autoComplete="new-password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className={FIELD}
              />
              <span className="text-13 font-normal text-muted">{t.newPasswordHint}</span>
            </label>
            <label className="flex flex-col gap-6 text-14 font-semibold">
              {t.confirmPassword}
              <input
                type="password"
                autoComplete="new-password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className={FIELD}
              />
            </label>
            <label className="flex flex-col gap-6 text-14 font-semibold">
              {t.setupCode}
              <input
                inputMode="numeric"
                autoComplete="one-time-code"
                maxLength={6}
                value={code}
                onChange={(e) => setCode(digits(e.target.value))}
                className={CODE}
              />
            </label>
            {errorText}
            <Button disabled={busy || code.length < 6} onClick={finishSetup}>
              {t.setupSubmit}
            </Button>
          </div>
        )}
      </div>
    </main>
  );
}
