import { zodResolver } from '@hookform/resolvers/zod';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Navigate, useNavigate } from 'react-router';
import { z } from 'zod';
import { Button } from '../components/Button';
import { OnboardingFrame } from '../components/OnboardingFrame';
import { useToast } from '../components/Toast';
import { useSession } from '../lib/auth';
import { copy } from '../lib/copy';
import { supabase } from '../lib/supabase';

const t = copy.login;
const emailSchema = z.object({ email: z.string().trim().email() });
type EmailForm = z.infer<typeof emailSchema>;

/** Langkah 1 onboarding: masuk dengan email OTP / Google (Supabase Auth, §3). Langkah 2–4 di M6. */
export function Login() {
  const { session } = useSession();
  const navigate = useNavigate();
  const toast = useToast();
  const [sentTo, setSentTo] = useState<string | null>(null);
  const [otp, setOtp] = useState('');
  const [busy, setBusy] = useState(false);
  const [otpError, setOtpError] = useState(false);
  const form = useForm<EmailForm>({ resolver: zodResolver(emailSchema), defaultValues: { email: '' } });

  if (session) return <Navigate to="/mulai" replace />;

  async function sendCode({ email }: EmailForm) {
    if (!supabase) return;
    setBusy(true);
    const { error } = await supabase.auth.signInWithOtp({ email });
    setBusy(false);
    if (error) return toast(t.failed);
    if (sentTo) toast(t.resent(email));
    setSentTo(email);
  }

  async function verify() {
    if (!supabase || !sentTo) return;
    setBusy(true);
    const { error } = await supabase.auth.verifyOtp({ email: sentTo, token: otp, type: 'email' });
    setBusy(false);
    if (error) return setOtpError(true);
    navigate('/mulai', { replace: true });
  }

  async function google() {
    await supabase?.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: `${window.location.origin}/mulai` } });
  }

  const emailError = form.formState.errors.email;
  return (
    <OnboardingFrame progress={{ step: 1, total: 4, onBack: () => navigate('/') }}>
      <div className="flex flex-1 animate-in-30 flex-col gap-20 p-24">
        <div className="flex flex-col gap-8">
          <h1 className="m-0 text-26 font-extrabold leading-120 tracking-tight">{t.title}</h1>
          <p className="m-0 text-15 leading-155 text-muted">{t.lead}</p>
        </div>
        {/* DESIGN-GAP: peringatan konfigurasi untuk lingkungan dev */}
        {!supabase && <p className="m-0 text-13 font-semibold text-warn-text">{t.notConfigured}</p>}
        <form onSubmit={form.handleSubmit(sendCode)} className="flex flex-col gap-20" noValidate>
          <div className="flex flex-col gap-6">
            <label htmlFor="ob-email" className="text-14 font-semibold">
              {t.emailLabel}
            </label>
            <input
              id="ob-email"
              type="email"
              autoComplete="email"
              placeholder={t.emailPlaceholder}
              aria-invalid={!!emailError}
              {...form.register('email')}
              className={`h-52 rounded-14 border-1.5 bg-white px-16 text-16 ${emailError ? 'border-warn' : 'border-sand-400'}`}
            />
            {emailError && <span className="text-13 font-semibold text-warn-text">{t.emailError}</span>}
          </div>
          {!sentTo && (
            <Button type="submit" disabled={busy || !supabase}>
              {t.sendCode}
            </Button>
          )}
        </form>
        {sentTo && (
          <div className="flex animate-in-30 flex-col gap-10 rounded-16 border border-sand-200 bg-white p-16">
            <label htmlFor="ob-otp" className="text-14 font-bold">
              {t.otpLabel}
            </label>
            <span className="text-13 leading-150 text-muted">{t.otpSentTo(sentTo)}</span>
            <input
              id="ob-otp"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              value={otp}
              placeholder={t.otpPlaceholder}
              onChange={(e) => {
                setOtp(e.target.value.replace(/\D/g, '').slice(0, 6));
                setOtpError(false);
              }}
              className="h-56 rounded-12 border-1.5 border-sand-400 bg-cream px-16 text-center text-24 font-bold tracking-widest"
            />
            {otpError && <span className="text-13 font-semibold text-warn-text">{t.otpWrong}</span>}
            <Button disabled={otp.length < 6 || busy} onClick={verify}>
              {t.submit}
            </Button>
            <Button variant="link" disabled={busy} onClick={form.handleSubmit(sendCode)}>
              {t.resend}
            </Button>
          </div>
        )}
        <div className="flex items-center gap-12 text-13 text-muted">
          <div className="h-1 flex-1 bg-sand-300" />
          {t.or}
          <div className="h-1 flex-1 bg-sand-300" />
        </div>
        <Button variant="outline" disabled={!supabase} onClick={google} className="flex items-center justify-center gap-10">
          <span className="flex h-22 w-22 items-center justify-center rounded-full border-2 border-navy text-11 font-extrabold">
            G
          </span>
          {t.google}
        </Button>
      </div>
    </OnboardingFrame>
  );
}
