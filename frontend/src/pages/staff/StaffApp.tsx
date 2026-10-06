import { useQuery, useQueryClient, type UseQueryResult } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { Navigate, NavLink, Outlet, useNavigate, useOutletContext } from 'react-router';
import { Icon, type IconName } from '../../components/Icon';
import { LogoMark, Wordmark } from '../../components/Logo';
import { ApiError, staffApi, staffToken } from '../../lib/api';
import { copy } from '../../lib/copy';
import type { CaseRow, Staff, StaffSettings } from '../../lib/types';

const t = copy.staff;
const POLL_MS = 15_000;
export const DEFAULT_SETTINGS: StaffSettings = { notif_red: true, sound: false, compact: true };

export interface StaffCtx {
  me: Staff;
  settings: StaffSettings;
  active: UseQueryResult<CaseRow[]>;
  arrived: Set<string>; // kasus yang masuk selama dasbor terbuka → label "BARU MASUK"
  now: Date;
}

export const useStaff = () => useOutletContext<StaffCtx>();
export const ACTIVE_QUERY = ['cases', 'active'] as const;

const NAV: { to: string; key: keyof typeof t.nav; icon: IconName }[] = [
  { to: '/staf', key: 'antrian', icon: 'list' },
  { to: '/staf/riwayat', key: 'riwayat', icon: 'hist' },
  { to: '/staf/jadwal', key: 'jadwal', icon: 'cal' },
  { to: '/staf/pengaturan', key: 'pengaturan', icon: 'gear' },
];

const initials = (name: string) =>
  name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

/** Bunyi peringatan singkat (WebAudio, tanpa file suara). */
function beep() {
  const ctx = new AudioContext();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.frequency.value = 880;
  gain.gain.value = 0.1;
  osc.connect(gain).connect(ctx.destination);
  osc.onended = () => void ctx.close();
  osc.start();
  osc.stop(ctx.currentTime + 0.4);
}

export function StaffApp() {
  const token = staffToken.get();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const me = useQuery({ queryKey: ['staff-me'], queryFn: () => staffApi<Staff>('/auth/staff/me'), enabled: !!token });
  const settingsQ = useQuery({
    queryKey: ['staff-settings'],
    queryFn: () => staffApi<StaffSettings>('/auth/staff/settings'),
    enabled: !!token,
  });
  const settings = settingsQ.data ?? DEFAULT_SETTINGS;
  const scoped = me.data && me.data.role !== 'admin_kota';
  const active = useQuery({
    queryKey: ACTIVE_QUERY,
    queryFn: () => staffApi<CaseRow[]>('/cases?status=baru&status=ditangani'),
    enabled: !!scoped,
    refetchInterval: POLL_MS,
  });
  const [now, setNow] = useState(() => new Date());
  const [arrived, setArrived] = useState<Set<string>>(() => new Set());
  const seen = useRef<Map<string, CaseRow['level']> | null>(null);

  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 30_000);
    return () => window.clearInterval(id);
  }, []);

  // Kasus baru / naik ke merah sejak poll terakhir → label, notifikasi browser, bunyi.
  useEffect(() => {
    const rows = active.data;
    if (!rows) return;
    const prev = seen.current;
    seen.current = new Map(rows.map((r) => [r.id, r.level]));
    if (!prev) return; // muatan pertama: bukan "baru masuk"
    const fresh = rows.filter((r) => !prev.has(r.id));
    if (fresh.length) setArrived((s) => new Set([...s, ...fresh.map((r) => r.id)]));
    const red = rows.filter((r) => r.level === 'merah' && r.status === 'baru' && prev.get(r.id) !== 'merah');
    if (!red.length) return;
    if (settings.notif_red && 'Notification' in window && Notification.permission === 'granted') {
      new Notification(copy.staffSettings.notifyTitle, { body: copy.staffSettings.notifyBody(red[0].kelurahan) });
    }
    if (settings.sound) beep();
  }, [active.data, settings.notif_red, settings.sound]);

  useEffect(() => {
    if (settings.notif_red && 'Notification' in window && Notification.permission === 'default') {
      void Notification.requestPermission();
    }
  }, [settings.notif_red]);

  const unauthorized = [me.error, active.error].some((e) => e instanceof ApiError && e.status === 401);
  useEffect(() => {
    if (!unauthorized) return;
    staffToken.clear();
    queryClient.clear();
    navigate('/staf/masuk', { replace: true });
  }, [unauthorized, navigate, queryClient]);

  if (!token) return <Navigate to="/staf/masuk" replace />;
  if (!me.data) return null;
  // ponytail: admin_kota diarahkan ke dasbor kota (M5).
  if (me.data.role === 'admin_kota') return <Navigate to="/kota" replace />;

  const name = me.data.display_name ?? '';
  const kel = me.data.kelurahan_name ?? '';
  const konselor = me.data.role === 'konselor';
  const newCount = active.data?.filter((r) => r.status === 'baru').length ?? 0;
  const logout = () => {
    staffToken.clear();
    queryClient.clear();
    navigate('/staf/masuk', { replace: true });
  };

  return (
    <div className="flex h-dvh min-h-480 bg-cream">
      <aside className="hidden w-236 flex-none flex-col border-r border-sand-200 bg-white px-14 py-20 xl:flex">
        <div className="flex items-center gap-8 px-6 pb-20">
          <LogoMark className="h-30 w-30" />
          <div className="flex flex-col">
            <Wordmark className="text-18" />
            <span className="text-11 font-semibold text-muted">{t.roleLabel[me.data.role]}</span>
          </div>
        </div>
        <nav className="flex flex-col gap-4">
          {NAV.map((n) => (
            <NavLink
              key={n.key}
              to={n.to}
              end
              className={({ isActive }) =>
                `flex h-44 items-center gap-12 rounded-12 px-12 text-14 ${isActive ? 'bg-teal-100 font-extrabold text-teal-800' : 'font-semibold text-navy'}`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon name={n.icon} className={`h-20 w-20 ${isActive ? 'stroke-teal-800' : 'stroke-navy'}`} />
                  {t.nav[n.key]}
                  {n.key === 'antrian' && newCount > 0 && (
                    <span className="ml-auto flex h-22 min-w-24 items-center justify-center rounded-full bg-teal-600 px-7 text-12 text-white">
                      {newCount}
                    </span>
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto flex flex-col gap-12">
          <div className="rounded-12 bg-cream p-12 text-12 leading-150 text-muted-strong">
            {konselor ? t.scopeSideKonselor : t.scopeSide(kel)}
          </div>
          <div className="flex items-center gap-10 p-6">
            <span className="flex h-40 w-40 flex-none items-center justify-center rounded-full bg-lavender-100 text-14 font-extrabold text-lavender-600">
              {initials(name)}
            </span>
            <span className="flex min-w-0 flex-col">
              <span className="text-14 font-bold">{name}</span>
              <span className="text-12 text-muted">
                {t.roleLabel[me.data.role]}
                {konselor ? '' : ` · ${kel}`}
              </span>
            </span>
          </div>
          {/* DESIGN-GAP: tombol keluar tidak ada di desain. */}
          <button type="button" onClick={logout} className="h-36 rounded-10 text-left text-13 font-bold text-muted hover:text-navy">
            <span className="px-6">{t.logout}</span>
          </button>
        </div>
      </aside>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <div className="flex flex-none flex-col border-b border-sand-200 bg-white xl:hidden">
          <div className="flex items-center justify-between gap-8 px-16 pb-6 pt-10 text-12 text-muted-strong">
            <span>{konselor ? t.scopeTopKonselor(name) : t.scopeTop(name, kel)}</span>
            <button type="button" onClick={logout} className="h-28 flex-none font-bold text-muted">
              {t.logout}
            </button>
          </div>
          <nav className="flex gap-4 overflow-x-auto px-10 pb-8">
            {NAV.map((n) => (
              <NavLink
                key={n.key}
                to={n.to}
                end
                className={({ isActive }) =>
                  `flex h-40 flex-none items-center gap-6 rounded-10 px-12 text-13 ${isActive ? 'bg-teal-100 font-extrabold text-teal-800' : 'font-semibold text-navy'}`
                }
              >
                {t.nav[n.key]}
                {n.key === 'antrian' && newCount > 0 && (
                  <span className="flex h-20 min-w-20 items-center justify-center rounded-full bg-teal-600 px-6 text-11 text-white">
                    {newCount}
                  </span>
                )}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="flex min-h-0 flex-1">
          <Outlet context={{ me: me.data, settings, active, arrived, now } satisfies StaffCtx} />
        </div>
      </div>
    </div>
  );
}
