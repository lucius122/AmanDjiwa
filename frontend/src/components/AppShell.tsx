import { NavLink, Outlet } from 'react-router';
import { copy } from '../lib/copy';
import type { Me } from '../lib/types';
import { Avatar } from './Avatar';
import { Icon, type IconName } from './Icon';
import { LogoMark, Wordmark } from './Logo';

const NAV: { to: string; label: string; icon: IconName }[] = [
  { to: '/ngobrol', label: copy.nav.chat, icon: 'chat' },
  { to: '/jurnal', label: copy.nav.jurnal, icon: 'jurnal' },
  { to: '/aku', label: copy.nav.aku, icon: 'aku' },
];

/** Shell app remaja: sidebar di layar lebar (≥ 900px), bottom nav di mobile. */
export function AppShell({ me }: { me: Me }) {
  return (
    <div className="flex h-dvh min-h-480">
      <aside className="hidden w-240 flex-none flex-col gap-20 border-r border-sand-200 bg-white px-14 py-20 lg:flex">
        <div className="flex items-center gap-8 px-6">
          <LogoMark className="h-30 w-30" />
          <Wordmark className="text-18" />
        </div>
        <nav className="flex flex-col gap-4">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) =>
                `flex h-46 items-center gap-12 rounded-12 px-12 text-15 ${
                  isActive ? 'bg-teal-100 font-extrabold text-teal-600' : 'font-semibold text-muted'
                }`
              }
            >
              <Icon name={n.icon} className="h-22 w-22 stroke-current" />
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto flex flex-col gap-10">
          <div className="flex items-center gap-10 p-6">
            <Avatar index={me.avatar} size="sm" />
            <span className="flex flex-col">
              <span className="text-14 font-bold">{me.pseudonym}</span>
              <span className="text-12 text-muted">{me.kelurahan_name}</span>
            </span>
          </div>
          <div className="px-6 text-11 leading-150 text-muted">{copy.brand.notDiagnosis}</div>
        </div>
      </aside>
      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <Outlet context={me} />
        <nav className="grid h-64 flex-none grid-cols-3 border-t border-sand-200 bg-white lg:hidden">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) =>
                `group flex flex-col items-center justify-center gap-3 text-11 ${
                  isActive ? 'active font-extrabold text-teal-600' : 'font-semibold text-muted'
                }`
              }
            >
              <Icon name={n.icon} className="h-22 w-22 stroke-current group-[.active]:fill-teal-100" />
              {n.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  );
}
