import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useParams } from 'react-router';
import { Button } from '../components/Button';
import { Icon } from '../components/Icon';
import { LogoMark, Wordmark } from '../components/Logo';
import { useToast } from '../components/Toast';
import { ApiError, api } from '../lib/api';
import { copy } from '../lib/copy';

const t = copy.guardian;
type Status = 'pending' | 'approved' | 'declined' | 'revoked' | 'expired' | 'invalid';
type Relation = (typeof t.relations)[number]['value'];

async function fetchStatus(token: string): Promise<Status> {
  try {
    return (await api<{ status: Exclude<Status, 'invalid'> }>(`/consent/guardian/${token}`)).status;
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return 'invalid';
    throw e;
  }
}

/** Halaman persetujuan orang tua/wali dari tautan email (publik, tanpa login). */
export function GuardianApproval() {
  const { token = '' } = useParams();
  const toast = useToast();
  const queryClient = useQueryClient();
  const status = useQuery({ queryKey: ['guardian', token], queryFn: () => fetchStatus(token), retry: 1 });
  const [name, setName] = useState('');
  const [relation, setRelation] = useState<Relation>('orang_tua');
  const [agree, setAgree] = useState(false);
  const [busy, setBusy] = useState(false);

  async function decide(decision: 'approve' | 'decline' | 'revoke') {
    setBusy(true);
    try {
      const body = decision === 'approve' ? { decision, guardian_name: name.trim(), relation } : { decision };
      const res = await api<{ status: Status }>(`/consent/guardian/${token}`, { method: 'POST', body });
      queryClient.setQueryData(['guardian', token], res.status);
    } catch (e) {
      if (e instanceof ApiError && [404, 409, 410].includes(e.status)) await status.refetch();
      else toast(t.failed);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-dvh items-start justify-center bg-sand-100 lg:px-20 lg:py-40">
      <main className="w-full max-w-640 overflow-hidden bg-cream lg:rounded-24 lg:shadow-panel">
        <div className="flex flex-wrap items-center gap-8 border-b border-sand-200 bg-white px-24 py-16">
          <LogoMark className="h-26 w-26" />
          <Wordmark className="text-17" />
          <span className="ml-auto text-12 font-semibold text-muted">{t.program}</span>
        </div>
        <div className="flex flex-col gap-18 px-24 py-28">
          <div className="flex flex-col gap-8">
            <div className="text-12 font-bold uppercase tracking-wide text-teal-600">{t.kicker}</div>
            <h1 className="m-0 text-24 font-extrabold leading-130">{t.title}</h1>
            <p className="m-0 text-15 leading-160 text-muted">{t.lead}</p>
          </div>

          {status.isPending && <p className="m-0 text-14 text-muted">{t.loading}</p>}
          {status.isError && <StateCard title={t.failed} body="" />}
          {status.data === 'invalid' && <StateCard title={t.invalidTitle} body={t.invalidBody} />}
          {status.data === 'expired' && <StateCard title={t.expiredTitle} body={t.expiredBody} />}
          {status.data === 'declined' && <StateCard title={t.declinedTitle} body={t.declinedBody} />}
          {status.data === 'revoked' && <StateCard title={t.revokedTitle} body={t.revokedBody} />}
          {status.data === 'approved' && (
            <>
              <StateCard title={t.approvedTitle} body={t.approvedBody} />
              <Button variant="outline" disabled={busy} onClick={() => decide('revoke')}>
                {t.revoke}
              </Button>
            </>
          )}

          {status.data === 'pending' && (
            <>
              <div className="flex flex-col gap-14 rounded-16 border border-sand-200 bg-white p-20">
                {t.terms.map((term) => (
                  <div key={term.title}>
                    <h2 className="m-0 text-15 font-bold">{term.title}</h2>
                    <p className="m-0 text-14 leading-160 text-muted">{term.body}</p>
                  </div>
                ))}
              </div>
              <div className="flex flex-col gap-6">
                <label htmlFor="p-name" className="text-14 font-semibold">
                  {t.nameLabel}
                </label>
                <input
                  id="p-name"
                  value={name}
                  maxLength={120}
                  autoComplete="name"
                  placeholder={t.namePlaceholder}
                  onChange={(e) => setName(e.target.value)}
                  className="h-50 rounded-14 border-1.5 border-sand-400 bg-white px-16 text-16"
                />
              </div>
              <div className="flex flex-col gap-6">
                <span className="text-14 font-semibold" id="p-rel">
                  {t.relationLabel}
                </span>
                <div className="flex gap-8" role="group" aria-labelledby="p-rel">
                  {t.relations.map((r) => {
                    const on = relation === r.value;
                    return (
                      <button
                        key={r.value}
                        type="button"
                        aria-pressed={on}
                        onClick={() => setRelation(r.value)}
                        className={`h-46 flex-1 rounded-12 border-1.5 text-14 font-bold ${on ? 'border-teal-600 bg-teal-600 text-white' : 'border-sand-400 bg-white text-navy'}`}
                      >
                        {r.label}
                      </button>
                    );
                  })}
                </div>
              </div>
              <button
                type="button"
                role="checkbox"
                aria-checked={agree}
                onClick={() => setAgree(!agree)}
                className="flex items-start gap-12 bg-transparent py-4 text-left"
              >
                <span className={`flex h-26 w-26 flex-none items-center justify-center rounded-8 border-2 border-teal-600 ${agree ? 'bg-teal-600' : 'bg-white'}`}>
                  {agree && <Icon name="check" className="h-16 w-16 stroke-white" strokeWidth={3} />}
                </span>
                <span className="text-14 leading-155">{t.agree}</span>
              </button>
              <Button disabled={!agree || !name.trim() || busy} onClick={() => decide('approve')}>
                {t.approve}
              </Button>
              <button type="button" disabled={busy} onClick={() => decide('decline')} className="h-44 bg-transparent text-14 font-semibold">
                {t.decline}
              </button>
            </>
          )}
          <div className="text-center text-12 leading-150 text-muted">{t.contact}</div>
        </div>
      </main>
    </div>
  );
}

// DESIGN-GAP: kartu status tidak ada di desain; diturunkan dari kartu ketentuan.
function StateCard({ title, body }: { title: string; body: string }) {
  return (
    <div role="status" className="flex flex-col gap-8 rounded-16 border border-sand-200 bg-white p-20">
      <h2 className="m-0 text-17 font-extrabold">{title}</h2>
      {body && <p className="m-0 text-14 leading-160 text-muted">{body}</p>}
    </div>
  );
}
