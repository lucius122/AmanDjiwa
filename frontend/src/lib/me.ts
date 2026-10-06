import { useQuery } from '@tanstack/react-query';
import { ApiError, api } from './api';
import { useSession } from './auth';
import type { Me } from './types';

export type Gate =
  | { state: 'loading' }
  | { state: 'anon' } // belum login
  | { state: 'needs_profile' } // login, belum onboarding (GET /me = 404)
  | { state: 'pending'; me: Me } // menunggu izin orang tua/wali
  | { state: 'active'; me: Me };

/** Posisi remaja di alur: landing → masuk → daftar → (menunggu wali) → app. */
export function useGate(pollMs?: number): Gate {
  const { session, loading } = useSession();
  const me = useQuery({
    queryKey: ['me', session?.user.id],
    queryFn: () => api<Me>('/me'),
    enabled: !!session,
    refetchInterval: pollMs,
    retry: (count, err) => !(err instanceof ApiError && err.status < 500) && count < 2,
  });
  if (loading) return { state: 'loading' };
  if (!session) return { state: 'anon' };
  if (me.data) return me.data.status === 'active' ? { state: 'active', me: me.data } : { state: 'pending', me: me.data };
  if (me.error instanceof ApiError && me.error.status === 404) return { state: 'needs_profile' };
  return { state: 'loading' }; // DESIGN-GAP: error jaringan → tetap memuat, query mencoba ulang
}

export const GATE_ROUTE: Record<Exclude<Gate['state'], 'loading'>, string> = {
  anon: '/masuk',
  needs_profile: '/daftar',
  pending: '/menunggu',
  active: '/ngobrol',
};
