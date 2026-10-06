import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Navigate, NavLink, Outlet, useNavigate } from 'react-router';
import { LogoMark, Wordmark } from '../../components/Logo';
import { ApiError, staffApi, staffToken } from '../../lib/api';
import { copy } from '../../lib/copy';
import type { Staff } from '../../lib/types';

const initials = (name: string) =>
  name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

const NAV = [
  { to: '/kota', label: copy.kotaNav.summary },
  { to: '/kota/akun', label: copy.kotaNav.accounts },
];

/** Bingkai dasbor kota: hanya admin kota. Header dari desain; menu "Akun staf" & Keluar = DESIGN-GAP. */
export function KotaLayout() {
  const token = staffToken.get();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const me = useQuery({ queryKey: ['staff-me'], queryFn: () => staffApi<Staff>('/auth/staff/me'), enabled: !!token });

  if (!token || (me.error instanceof ApiError && me.error.status === 401)) {
    staffToken.clear();
    return <Navigate to="/staf/masuk" replace />;
  }
  if (!me.data) return null;
  if (me.data.role !== 'admin_kota') return <Navigate to="/staf" replace />;

  const name = me.data.display_name ?? copy.staff.roleLabel.admin_kota;
  const logout = () => {
    staffToken.clear();
    queryClient.clear();
    navigate('/staf/masuk', { replace: true });
  };

  return (
    <div className="min-h-dvh bg-cream">
      <header className="border-b border-sand-200 bg-white">
        <div className="mx-auto flex min-h-64 max-w-1440 flex-wrap items-center gap-x-12 gap-y-10 px-20 py-8">
          <LogoMark className="h-28 w-28" />
          <Wordmark className="text-18" />
          <span className="text-14 font-semibold text-muted">{copy.kota.subtitle}</span>
          <nav className="flex gap-4 rounded-12 bg-sand-100 p-3 print:hidden">
            {NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end
                className={({ isActive }) =>
                  `flex h-34 items-center rounded-9 px-12 text-13 font-bold text-navy ${isActive ? 'bg-white' : 'bg-transparent'}`
                }
              >
                {n.label}
              </NavLink>
            ))}
          </nav>
          <span className="ml-auto flex items-center gap-8 text-13 font-semibold">
            <span className="flex h-34 w-34 items-center justify-center rounded-full bg-sky-100 text-12 font-extrabold">
              {initials(name)}
            </span>
            {name}
            <button type="button" onClick={logout} className="ml-8 h-34 px-6 font-bold text-muted hover:text-navy print:hidden">
              {copy.staff.logout}
            </button>
          </span>
        </div>
      </header>
      <Outlet />
    </div>
  );
}
