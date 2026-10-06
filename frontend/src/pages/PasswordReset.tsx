import { useState } from 'react';
import { Link, Navigate, useNavigate, useParams } from 'react-router';
import { z } from 'zod';
import { Button } from '../components/Button';
import { OnboardingFrame } from '../components/OnboardingFrame';
import { useToast } from '../components/Toast';
import { ApiError, api, teenToken } from '../lib/api';
import { copy } from '../lib/copy';
import { FIELD } from './Login';

// DESIGN-GAP: lupa & atur ulang password tidak ada di desain; gaya diturunkan dari langkah masuk.
const emailOk = (v: string) => z.string().trim().email().safeParse(v).success;

function Back() {
  return (
    <Link to="/masuk?mode=masuk" className="self-start text-14 font-bold text-teal-600">
      ← {copy.forgot.back}
    </Link>
  );
}

/** /lupa-password: selalu menampilkan pesan yang sama (tidak membocorkan email terdaftar). */
export function ForgotPassword() {
  const t = copy.forgot;
  const [email, setEmail] = useState('');
  const [sentTo, setSentTo] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  async function send() {
    setBusy(true);
    setFailed(false);
    try {
      await api('/auth/teen/forgot', { method: 'POST', body: { email: email.trim() }, auth: false });
      setSentTo(email.trim());
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <OnboardingFrame>
      <div className="flex flex-1 animate-in-30 flex-col gap-20 p-24">
        <Back />
        <div className="flex flex-col gap-8">
          <h1 className="m-0 text-26 font-extrabold leading-120 tracking-tight">{t.title}</h1>
          <p className="m-0 text-15 leading-155 text-muted">{sentTo ? t.sent(sentTo) : t.lead}</p>
        </div>
        {!sentTo && (
          <>
            <label className="flex flex-col gap-6 text-14 font-semibold">
              {copy.login.emailLabel}
              <input
                type="email"
                autoComplete="email"
                value={email}
                placeholder={copy.login.emailPlaceholder}
                onChange={(e) => setEmail(e.target.value)}
                className={`${FIELD} border-sand-400`}
              />
            </label>
            {failed && <p className="m-0 text-13 font-semibold text-warn-text">{copy.login.failed}</p>}
            <Button disabled={busy || !emailOk(email)} onClick={send}>
              {t.submit}
            </Button>
          </>
        )}
      </div>
    </OnboardingFrame>
  );
}

/** /reset-password/:token — tautan dari email (30 menit, sekali pakai). Berhasil = langsung masuk. */
export function ResetPassword() {
  const t = copy.reset;
  const { token = '' } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  if (!token) return <Navigate to="/lupa-password" replace />;

  async function save() {
    if (password.length < 8) return setError(copy.login.passwordShort);
    if (password !== confirm) return setError(copy.login.confirmMismatch);
    setBusy(true);
    setError(null);
    try {
      const res = await api<{ access_token: string }>('/auth/teen/reset', {
        method: 'POST',
        body: { token, password },
        auth: false,
      });
      teenToken.set(res.access_token);
      toast(t.done);
      navigate('/mulai', { replace: true });
    } catch (e) {
      setError(e instanceof ApiError && e.status === 410 ? t.invalid : copy.login.failed);
    } finally {
      setBusy(false);
    }
  }

  return (
    <OnboardingFrame>
      <div className="flex flex-1 animate-in-30 flex-col gap-20 p-24">
        <Back />
        <div className="flex flex-col gap-8">
          <h1 className="m-0 text-26 font-extrabold leading-120 tracking-tight">{t.title}</h1>
          <p className="m-0 text-15 leading-155 text-muted">{t.lead}</p>
        </div>
        <label className="flex flex-col gap-6 text-14 font-semibold">
          {copy.login.passwordLabel}
          <input
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={`${FIELD} border-sand-400`}
          />
          <span className="text-13 font-normal text-muted">{copy.login.passwordHint}</span>
        </label>
        <label className="flex flex-col gap-6 text-14 font-semibold">
          {copy.login.confirmLabel}
          <input
            type="password"
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            className={`${FIELD} border-sand-400`}
          />
        </label>
        {error && (
          <p role="alert" className="m-0 text-13 font-semibold text-warn-text">
            {error}{' '}
            {error === t.invalid && (
              <Link to="/lupa-password" className="text-teal-600">
                {copy.forgot.submit}
              </Link>
            )}
          </p>
        )}
        <Button disabled={busy} onClick={save}>
          {t.submit}
        </Button>
      </div>
    </OnboardingFrame>
  );
}
