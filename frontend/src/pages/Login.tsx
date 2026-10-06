import { zodResolver } from '@hookform/resolvers/zod';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router';
import { z } from 'zod';
import { Button } from '../components/Button';
import { OnboardingFrame } from '../components/OnboardingFrame';
import { ApiError, api, teenToken } from '../lib/api';
import { useSession } from '../lib/auth';
import { copy } from '../lib/copy';

const t = copy.login;
const schema = z.object({
  email: z.string().trim().email(),
  password: z.string().min(8).max(128),
  confirm: z.string(),
});
type Form = z.infer<typeof schema>;
export const FIELD = 'h-52 rounded-14 border-1.5 bg-white px-16 text-16';

/** Langkah 1 onboarding: buat akun / masuk dengan email + password (keputusan 2026-10-06).
 * DESIGN-GAP: desain memakai kode OTP email + Google; bingkai, judul, dan teks pembuka tetap. */
export function Login() {
  const { token } = useSession();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  // Dari tombol "Mulai ngobrol" kebanyakan pengguna baru → default Daftar. Remaja yang sudah
  // punya akun biasanya masih punya sesi (7 hari), jadi langsung diarahkan ke chat.
  const [mode, setMode] = useState<'daftar' | 'masuk'>(params.get('mode') === 'masuk' ? 'masuk' : 'daftar');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const form = useForm<Form>({ resolver: zodResolver(schema), defaultValues: { email: '', password: '', confirm: '' } });

  if (token) return <Navigate to="/mulai" replace />;
  const isRegister = mode === 'daftar';
  const errors = form.formState.errors;

  async function submit(v: Form) {
    if (isRegister && v.password !== v.confirm) return form.setError('confirm', { message: t.confirmMismatch });
    setBusy(true);
    setError(null);
    try {
      const res = await api<{ access_token: string }>(isRegister ? '/auth/teen/register' : '/auth/teen/login', {
        method: 'POST',
        body: { email: v.email.trim(), password: v.password },
        auth: false,
      });
      teenToken.set(res.access_token);
      navigate('/mulai', { replace: true });
    } catch (e) {
      // 401 salah password, 409 email sudah terdaftar, 429 terkunci: pesan backend sudah ramah.
      setError(e instanceof ApiError && [401, 409, 429].includes(e.status) ? e.message : t.failed);
    } finally {
      setBusy(false);
    }
  }

  function switchMode() {
    setMode(isRegister ? 'masuk' : 'daftar');
    setError(null);
    form.clearErrors();
  }

  return (
    <OnboardingFrame progress={{ step: 1, total: 4, onBack: () => navigate('/') }}>
      <div className="flex flex-1 animate-in-30 flex-col gap-20 p-24">
        <div className="flex flex-col gap-8">
          <h1 className="m-0 text-26 font-extrabold leading-120 tracking-tight">{isRegister ? t.titleRegister : t.title}</h1>
          <p className="m-0 text-15 leading-155 text-muted">{t.lead}</p>
        </div>
        <form onSubmit={form.handleSubmit(submit)} className="flex flex-col gap-16" noValidate>
          <div className="flex flex-col gap-6">
            <label htmlFor="ob-email" className="text-14 font-semibold">
              {t.emailLabel}
            </label>
            <input
              id="ob-email"
              type="email"
              autoComplete="email"
              placeholder={t.emailPlaceholder}
              aria-invalid={!!errors.email}
              {...form.register('email')}
              className={`${FIELD} ${errors.email ? 'border-warn' : 'border-sand-400'}`}
            />
            {errors.email && <span className="text-13 font-semibold text-warn-text">{t.emailError}</span>}
          </div>
          <div className="flex flex-col gap-6">
            <label htmlFor="ob-password" className="text-14 font-semibold">
              {t.passwordLabel}
            </label>
            <input
              id="ob-password"
              type="password"
              autoComplete={isRegister ? 'new-password' : 'current-password'}
              aria-invalid={!!errors.password}
              {...form.register('password')}
              className={`${FIELD} ${errors.password ? 'border-warn' : 'border-sand-400'}`}
            />
            {errors.password ? (
              <span className="text-13 font-semibold text-warn-text">{t.passwordShort}</span>
            ) : (
              isRegister && <span className="text-13 text-muted">{t.passwordHint}</span>
            )}
          </div>
          {isRegister && (
            <div className="flex flex-col gap-6">
              <label htmlFor="ob-confirm" className="text-14 font-semibold">
                {t.confirmLabel}
              </label>
              <input
                id="ob-confirm"
                type="password"
                autoComplete="new-password"
                aria-invalid={!!errors.confirm}
                {...form.register('confirm')}
                className={`${FIELD} ${errors.confirm ? 'border-warn' : 'border-sand-400'}`}
              />
              {errors.confirm && <span className="text-13 font-semibold text-warn-text">{t.confirmMismatch}</span>}
            </div>
          )}
          {error && (
            <p role="alert" className="m-0 text-13 font-semibold text-warn-text">
              {error}
            </p>
          )}
          <Button type="submit" disabled={busy}>
            {isRegister ? t.submitRegister : t.submitLogin}
          </Button>
          {!isRegister && (
            <Link to="/lupa-password" className="self-center text-13 font-bold text-teal-600">
              {t.forgot}
            </Link>
          )}
        </form>
        <p className="m-0 text-center text-14 text-muted">
          {isRegister ? t.toLogin : t.toRegister}{' '}
          <button type="button" onClick={switchMode} className="h-44 bg-transparent px-4 font-bold text-teal-600">
            {isRegister ? t.toLoginLink : t.toRegisterLink}
          </button>
        </p>
      </div>
    </OnboardingFrame>
  );
}
