import type { Session } from '@supabase/supabase-js';
import { useEffect, useState } from 'react';
import { supabase } from './supabase';

/** Sesi Supabase remaja; ikut berubah saat login/logout. */
export function useSession(): { session: Session | null; loading: boolean } {
  const [state, setState] = useState({ session: null as Session | null, loading: supabase !== null });
  useEffect(() => {
    if (!supabase) return;
    void supabase.auth.getSession().then(({ data }) => setState({ session: data.session, loading: false }));
    const { data } = supabase.auth.onAuthStateChange((_event, session) =>
      setState({ session, loading: false }),
    );
    return () => data.subscription.unsubscribe();
  }, []);
  return state;
}
