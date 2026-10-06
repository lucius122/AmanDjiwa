import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Button } from '../../components/Button';
import { useToast } from '../../components/Toast';
import { ApiError, api, staffApi } from '../../lib/api';
import { copy } from '../../lib/copy';
import type { StaffAccount, StaffWithPassword } from '../../lib/types';

// DESIGN-GAP: kelola akun staf tidak ada di desain; gaya diturunkan dari kartu & tombol dasbor kota.
const t = copy.staffAdmin;
const CARD = 'flex min-w-0 flex-col rounded-16 border border-sand-200 bg-white p-20';
const FIELD = 'h-48 rounded-12 border-1.5 border-sand-400 bg-cream px-14 text-15';
const ROLES = ['pendamping', 'konselor', 'admin_kota'] as const;
type StaffRole = (typeof ROLES)[number];
const LIST = ['admin-staff'] as const;

export function StaffAccounts() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const list = useQuery({ queryKey: LIST, queryFn: () => staffApi<StaffAccount[]>('/admin/staff') });
  const kelurahan = useQuery({
    queryKey: ['kelurahan'],
    queryFn: () => api<{ id: number; name: string }[]>('/kelurahan', { auth: false }),
    staleTime: Infinity,
  });
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<StaffRole>('pendamping');
  const [kel, setKel] = useState<number | null>(null);
  const [shown, setShown] = useState<StaffWithPassword | null>(null); // password sementara, sekali tampil

  const fail = (e: unknown) => toast(e instanceof ApiError && [409, 422].includes(e.status) ? e.message : t.failed);
  const reveal = (r: StaffWithPassword) => {
    setShown(r);
    void queryClient.invalidateQueries({ queryKey: LIST });
  };
  const create = useMutation({
    mutationFn: () =>
      staffApi<StaffWithPassword>('/admin/staff', {
        method: 'POST',
        body: { display_name: name.trim(), email: email.trim(), role, kelurahan_id: role === 'pendamping' ? kel : null },
      }),
    onSuccess: (r) => {
      reveal(r);
      setName('');
      setEmail('');
      toast(t.created);
    },
    onError: fail,
  });
  const setStatus = useMutation({
    mutationFn: (a: StaffAccount) =>
      staffApi<StaffAccount>(`/admin/staff/${a.id}`, {
        method: 'PATCH',
        body: { status: a.status === 'active' ? 'disabled' : 'active' },
      }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: LIST }),
    onError: fail,
  });
  const reset = useMutation({
    mutationFn: (a: StaffAccount) => staffApi<StaffWithPassword>(`/admin/staff/${a.id}/reset`, { method: 'POST' }),
    onSuccess: reveal,
    onError: fail,
  });

  const ready = name.trim() !== '' && email.includes('@') && (role !== 'pendamping' || kel !== null);
  const busy = create.isPending || setStatus.isPending || reset.isPending;

  async function copyPassword(p: string) {
    try {
      await navigator.clipboard.writeText(p);
      toast(t.copied);
    } catch {
      /* clipboard diblokir: admin tetap bisa menyalin manual */
    }
  }

  return (
    <main className="mx-auto flex max-w-1100 flex-col gap-16 p-20">
      <div className="flex flex-col gap-6">
        <h1 className="m-0 text-fluid-24 font-extrabold tracking-tight">{t.title}</h1>
        <p className="m-0 max-w-720 text-14 leading-150 text-muted">{t.lead}</p>
      </div>

      {shown && (
        <section role="status" className="flex flex-col gap-10 rounded-16 border-1.5 border-teal-600 bg-teal-50 p-20">
          <h2 className="m-0 text-16 font-extrabold">{t.tempTitle(shown.account.display_name ?? shown.account.email ?? '')}</h2>
          <div className="flex flex-wrap items-center gap-10">
            <code className="select-all rounded-10 bg-white px-14 py-10 text-20 font-extrabold tracking-wide">
              {shown.temp_password}
            </code>
            <button
              type="button"
              onClick={() => void copyPassword(shown.temp_password)}
              className="h-40 rounded-10 border-1.5 border-sand-400 bg-white px-14 text-13 font-bold"
            >
              {t.copy}
            </button>
          </div>
          <p className="m-0 text-13 leading-150 text-muted-strong">{t.tempBody}</p>
          <button type="button" onClick={() => setShown(null)} className="h-40 self-start text-13 font-bold text-teal-600">
            {t.close}
          </button>
        </section>
      )}

      <section className={`${CARD} gap-14`}>
        <h2 className="m-0 text-16 font-extrabold">{t.addTitle}</h2>
        <div className="grid grid-cols-fit-170 gap-10">
          <label className="flex flex-col gap-6 text-13 font-semibold">
            {t.name}
            <input value={name} maxLength={64} placeholder={t.namePlaceholder} onChange={(e) => setName(e.target.value)} className={FIELD} />
          </label>
          <label className="flex flex-col gap-6 text-13 font-semibold">
            {t.email}
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={FIELD} />
          </label>
          <label className="flex flex-col gap-6 text-13 font-semibold">
            {t.role}
            <select value={role} onChange={(e) => setRole(e.target.value as StaffRole)} className={FIELD}>
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {t.roles[r]}
                </option>
              ))}
            </select>
          </label>
          {role === 'pendamping' && (
            <label className="flex flex-col gap-6 text-13 font-semibold">
              {t.kelurahan}
              <select value={kel ?? ''} onChange={(e) => setKel(e.target.value ? Number(e.target.value) : null)} className={FIELD}>
                <option value="">{t.kelurahanPick}</option>
                {kelurahan.data?.map((k) => (
                  <option key={k.id} value={k.id}>
                    {k.name}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
        <Button disabled={!ready || busy} onClick={() => create.mutate()} className="self-start px-20">
          {t.add}
        </Button>
      </section>

      <section className={`${CARD} gap-6 p-12`}>
        <h2 className="m-0 px-8 pb-6 pt-8 text-16 font-extrabold">{t.listTitle}</h2>
        {list.isError && <p className="m-0 px-8 text-14 text-muted">{t.loadFailed}</p>}
        {list.data?.map((a) => (
          <div key={a.id} className="flex flex-wrap items-center gap-x-12 gap-y-8 rounded-12 px-8 py-10 hover:bg-cream">
            <div className="flex min-w-0 flex-shrink flex-grow basis-220 flex-col gap-2">
              <span className="flex flex-wrap items-center gap-8 text-15 font-bold">
                {a.display_name}
                {a.needs_setup && (
                  <span className="rounded-6 bg-butter-100 px-6 py-2 text-11 font-bold text-butter-700">{t.needsSetup}</span>
                )}
              </span>
              <span className="break-all text-13 text-muted">
                {a.email} · {t.roles[a.role]}
                {a.kelurahan_name ? ` · ${a.kelurahan_name}` : ''}
              </span>
            </div>
            <span
              className={`rounded-8 px-8 py-4 text-12 font-bold ${a.status === 'active' ? 'bg-teal-100 text-teal-800' : 'bg-sand-100 text-muted'}`}
            >
              {a.status === 'active' ? t.active : t.disabled}
            </span>
            <button
              type="button"
              disabled={busy}
              onClick={() => setStatus.mutate(a)}
              className="h-40 rounded-10 border-1.5 border-sand-400 bg-white px-12 text-13 font-bold"
            >
              {a.status === 'active' ? t.disable : t.enable}
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => window.confirm(t.resetConfirm(a.display_name ?? '')) && reset.mutate(a)}
              className="h-40 rounded-10 border-1.5 border-navy bg-white px-12 text-13 font-bold"
            >
              {t.reset}
            </button>
          </div>
        ))}
      </section>
    </main>
  );
}
