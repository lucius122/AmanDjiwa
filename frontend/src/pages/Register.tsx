import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router';
import { z } from 'zod';
import { AVATARS } from '../components/Avatar';
import { Button } from '../components/Button';
import { Icon, type IconName } from '../components/Icon';
import { OnboardingFrame } from '../components/OnboardingFrame';
import { CloseButton, Sheet } from '../components/Sheet';
import { useToast } from '../components/Toast';
import { ApiError, api } from '../lib/api';
import { copy } from '../lib/copy';
import { useGate } from '../lib/me';
import type { Me } from '../lib/types';

const t = copy.register;
type Step = 'profile' | 'consent' | 'guardian';
interface Kelurahan {
  id: number;
  name: string;
}

const THIS_YEAR = new Date().getFullYear();
const YEARS = Array.from({ length: 7 }, (_, i) => THIS_YEAR - 19 + i); // 13–19 tahun (desain: 2007–2013)
const CONTACT_LIKE = /@|\d{5,}/; // sama dengan validasi backend
const emailOk = (v: string) => z.string().trim().email().safeParse(v).success;
// Sama dengan backend (konservatif, hanya tahun lahir): mungkin < 18 → wajib izin wali.
const isMinor = (year: number | null) => year === null || THIS_YEAR - year <= 18;

const CONSENT_STYLE: { box: string; iconBg: string; ink: string; icon: IconName }[] = [
  { box: 'bg-white border-sand-200', iconBg: 'bg-teal-100', ink: 'stroke-teal-600', icon: 'list' },
  { box: 'bg-white border-sand-200', iconBg: 'bg-lavender-100', ink: 'stroke-lavender-600', icon: 'eye' },
  { box: 'bg-peach-100 border-peach-100', iconBg: 'bg-white', ink: 'stroke-peach-600', icon: 'heart' },
  { box: 'bg-white border-sand-200', iconBg: 'bg-teal-100', ink: 'stroke-teal-600', icon: 'trash' },
];
const FIELD = 'rounded-14 border-1.5 border-sand-400 bg-white px-16 text-16';
const pick = <T,>(xs: readonly T[]) => xs[Math.floor(Math.random() * xs.length)];

export function Register() {
  const gate = useGate();
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const queryClient = useQueryClient();
  const kelurahan = useQuery({ queryKey: ['kelurahan'], queryFn: () => api<Kelurahan[]>('/kelurahan'), staleTime: Infinity });

  const [step, setStep] = useState<Step>('profile');
  const [nick, setNick] = useState('');
  const [nickError, setNickError] = useState(false);
  const [avatar, setAvatar] = useState(0);
  const [kel, setKel] = useState<Kelurahan | null>(null);
  const [year, setYear] = useState<number | null>(null);
  const [agree, setAgree] = useState(false);
  const [parentEmail, setParentEmail] = useState('');
  const [kelOpen, setKelOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  if (gate.state === 'loading') return null;
  if (gate.state === 'anon') return <Navigate to="/masuk" replace />;
  if (gate.state === 'active') return <Navigate to="/ngobrol" replace />;
  // Profil sudah ada tapi masih menunggu wali → hanya form email ortu ("Ganti email orang tua").
  const guardianOnly = gate.state === 'pending';
  const current: Step = guardianOnly ? 'guardian' : step;
  const minor = guardianOnly || isMinor(year);
  const stepNumber = { profile: 2, consent: 3, guardian: 4 }[current];

  const back = () => {
    if (guardianOnly) navigate((location.state as { from?: string } | null)?.from ?? '/');
    else if (current === 'profile') navigate('/');
    else setStep(current === 'guardian' ? 'consent' : 'profile');
  };

  async function assent(): Promise<Me | null> {
    try {
      return await api<Me>('/consent/assent', {
        method: 'POST',
        body: { pseudonym: nick.trim(), avatar, kelurahan_id: kel?.id, birth_year: year, agree: true },
      });
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) return null; // profil sudah dibuat sebelumnya
      if (e instanceof ApiError && e.status === 422) {
        setNickError(true);
        setStep('profile');
      } else toast(t.failed);
      throw e;
    }
  }

  async function submitConsent() {
    if (minor) return setStep('guardian'); // profil dikirim bersama izin wali di langkah 4
    setBusy(true);
    try {
      const me = await assent();
      await queryClient.invalidateQueries({ queryKey: ['me'] });
      if (me?.status === 'pending_guardian') return setStep('guardian');
      toast(t.welcome(nick.trim()));
      navigate('/ngobrol', { replace: true });
    } catch {
      /* pesan sudah ditampilkan */
    } finally {
      setBusy(false);
    }
  }

  async function submitGuardian() {
    setBusy(true);
    try {
      if (!guardianOnly) await assent();
      await api('/consent/guardian', { method: 'POST', body: { email: parentEmail.trim() } });
      await queryClient.invalidateQueries({ queryKey: ['me'] });
      navigate('/menunggu', { replace: true, state: { parentEmail: parentEmail.trim() } });
    } catch (e) {
      if (e instanceof ApiError && (e.status === 429 || e.status === 503)) toast(e.message);
      else if (!(e instanceof ApiError && e.status === 422)) toast(t.failed);
    } finally {
      setBusy(false);
    }
  }

  const profileReady = nick.trim() !== '' && kel !== null && year !== null;
  return (
    <OnboardingFrame progress={{ step: stepNumber, total: minor ? 4 : 3, onBack: back }}>
      {current === 'profile' && (
        <div className="flex flex-1 animate-in-30 flex-col gap-18 px-24 pb-24 pt-20">
          <div className="flex flex-col gap-6">
            <h1 className="m-0 text-24 font-extrabold leading-120 tracking-tight">{t.profileTitle}</h1>
            <p className="m-0 text-14 leading-150 text-muted">{t.profileLead}</p>
          </div>
          <div className="flex flex-col gap-6">
            <label htmlFor="ob-nick" className="text-14 font-semibold">
              {t.nickLabel}
            </label>
            <div className="flex gap-8">
              <input
                id="ob-nick"
                value={nick}
                maxLength={20}
                placeholder={t.nickPlaceholder}
                aria-invalid={nickError}
                onChange={(e) => {
                  setNick(e.target.value);
                  setNickError(CONTACT_LIKE.test(e.target.value));
                }}
                className={`h-50 min-w-0 flex-1 ${FIELD} ${nickError ? 'border-warn' : ''}`}
              />
              <button
                type="button"
                onClick={() => {
                  setNick(`${pick(t.randomFirst)} ${pick(t.randomSecond)}`);
                  setNickError(false);
                }}
                className="h-50 rounded-14 bg-teal-100 px-14 text-14 font-bold text-teal-800"
              >
                {t.random}
              </button>
            </div>
            {nickError && <span className="text-13 font-semibold text-warn-text">{t.nickError}</span>}
          </div>
          <div className="flex flex-col gap-8">
            <span className="text-14 font-semibold" id="ob-avatar">
              {t.avatarLabel}
            </span>
            <div className="grid grid-cols-4 gap-10" role="radiogroup" aria-labelledby="ob-avatar">
              {AVATARS.map((a, i) => (
                <button
                  key={t.avatarNames[i]}
                  type="button"
                  role="radio"
                  aria-checked={avatar === i}
                  aria-label={t.avatarNames[i]}
                  onClick={() => setAvatar(i)}
                  className={`flex aspect-square items-center justify-center rounded-full border-3 transition-colors duration-200 ${a.bg} ${avatar === i ? 'border-teal-600' : 'border-transparent'}`}
                >
                  <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={`h-30 w-30 ${a.ink}`} aria-hidden="true">
                    <path d={a.d} />
                  </svg>
                </button>
              ))}
            </div>
          </div>
          <div className="flex flex-col gap-6">
            <span className="text-14 font-semibold" id="ob-kel">
              {t.kelLabel} <span className="font-medium text-muted">{t.kelSuffix}</span>
            </span>
            <button
              type="button"
              aria-labelledby="ob-kel"
              aria-haspopup="dialog"
              onClick={() => setKelOpen(true)}
              className={`flex h-50 items-center justify-between rounded-14 border-1.5 border-sand-400 bg-white pl-16 pr-14 text-left text-16 ${kel ? 'text-navy' : 'text-muted-placeholder'}`}
            >
              {kel?.name ?? t.kelPlaceholder}
              <Icon name="chevronDown" className="h-20 w-20 stroke-navy" strokeWidth={2} />
            </button>
          </div>
          <div className="flex flex-col gap-8">
            <span className="text-14 font-semibold" id="ob-year">
              {t.yearLabel}
            </span>
            <div className="flex flex-wrap gap-8" role="group" aria-labelledby="ob-year">
              {YEARS.map((y) => (
                <button
                  key={y}
                  type="button"
                  aria-pressed={year === y}
                  onClick={() => setYear(y)}
                  className={`h-44 rounded-12 border-1.5 px-14 text-15 font-bold ${year === y ? 'border-teal-600 bg-teal-600 text-white' : 'border-sand-400 bg-white text-navy'}`}
                >
                  {y}
                </button>
              ))}
            </div>
          </div>
          <Button className="mt-auto" disabled={!profileReady || nickError} onClick={() => setStep('consent')}>
            {t.next}
          </Button>
        </div>
      )}

      {current === 'consent' && (
        <div className="flex flex-1 animate-in-30 flex-col gap-12 px-24 pb-24 pt-18">
          <h1 className="m-0 mb-4 text-24 font-extrabold leading-120 tracking-tight">{t.consentTitle}</h1>
          {t.consent.map((c, i) => (
            <div key={c.title} className={`flex gap-12 rounded-14 border p-14 ${CONSENT_STYLE[i].box}`}>
              <div className={`flex h-36 w-36 flex-none items-center justify-center rounded-10 ${CONSENT_STYLE[i].iconBg}`}>
                <Icon name={CONSENT_STYLE[i].icon} className={`h-18 w-18 ${CONSENT_STYLE[i].ink}`} />
              </div>
              <div>
                <h2 className="m-0 text-14 font-bold">{c.title}</h2>
                <p className="m-0 text-13 leading-150 text-muted-strong">{c.body}</p>
              </div>
            </div>
          ))}
          <button
            type="button"
            role="checkbox"
            aria-checked={agree}
            onClick={() => setAgree(!agree)}
            className="mt-auto flex min-h-44 items-center gap-12 bg-transparent py-8 text-left"
          >
            <span className={`flex h-26 w-26 flex-none items-center justify-center rounded-8 border-2 border-teal-600 ${agree ? 'bg-teal-600' : 'bg-white'}`}>
              {agree && <Icon name="check" className="h-16 w-16 stroke-white" strokeWidth={3} />}
            </span>
            <span className="text-14 leading-150">{t.agree}</span>
          </button>
          <Button disabled={!agree || busy} onClick={submitConsent}>
            {t.agreeSubmit}
          </Button>
        </div>
      )}

      {current === 'guardian' && (
        <div className="flex flex-1 animate-in-30 flex-col gap-20 p-24">
          <div className="flex flex-col gap-8">
            <h1 className="m-0 text-24 font-extrabold leading-120 tracking-tight">{t.guardianTitle}</h1>
            <p className="m-0 text-pretty text-15 leading-155 text-muted">{t.guardianLead}</p>
          </div>
          <div className="flex flex-col gap-6">
            <label htmlFor="ob-pemail" className="text-14 font-semibold">
              {t.guardianEmailLabel}
            </label>
            <input
              id="ob-pemail"
              type="email"
              autoComplete="off"
              value={parentEmail}
              placeholder={t.guardianEmailPlaceholder}
              onChange={(e) => setParentEmail(e.target.value)}
              className={`h-52 ${FIELD}`}
            />
          </div>
          <div className="flex flex-col gap-8 rounded-14 bg-teal-100 p-16">
            <div className="text-14 font-bold text-teal-800">{t.guardianInfoTitle}</div>
            <p className="m-0 text-13 leading-155">{t.guardianInfo1}</p>
            <p className="m-0 text-13 leading-155">
              <b>{t.guardianInfo2Bold}</b>
              {t.guardianInfo2Rest}
            </p>
          </div>
          <Button className="mt-auto" disabled={!emailOk(parentEmail) || busy} onClick={submitGuardian}>
            {t.guardianSubmit}
          </Button>
        </div>
      )}

      <Sheet open={kelOpen} onClose={() => setKelOpen(false)} labelledBy="kel-title">
        <div className="flex flex-col gap-6 px-12 pb-16 pt-18">
          <div className="flex items-center justify-between px-8 pb-6">
            <div className="flex flex-col">
              <span id="kel-title" className="text-18 font-extrabold">
                {t.kelSheetTitle}
              </span>
              <span className="text-13 text-muted">{t.kelSheetSub}</span>
            </div>
            <CloseButton onClose={() => setKelOpen(false)} />
          </div>
          {kelurahan.data?.map((k) => {
            const on = kel?.id === k.id;
            return (
              <button
                key={k.id}
                type="button"
                onClick={() => {
                  setKel(k);
                  setKelOpen(false);
                }}
                className={`flex min-h-46 items-center justify-between rounded-12 px-12 text-left text-15 hover:bg-teal-30 ${on ? 'bg-teal-100 font-extrabold' : 'bg-transparent font-medium'}`}
              >
                {k.name}
                {on && <Icon name="check" className="h-18 w-18 stroke-teal-600" strokeWidth={2.5} />}
              </button>
            );
          })}
        </div>
      </Sheet>
    </OnboardingFrame>
  );
}
