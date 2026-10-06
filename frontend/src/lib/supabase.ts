import { createClient, type SupabaseClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL;
const key = import.meta.env.VITE_SUPABASE_ANON_KEY;

// Supabase hanya untuk login remaja (CLAUDE.md §3). null = belum dikonfigurasi di .env.
// PKCE: setelah login Google token tidak pernah muncul di URL / riwayat browser (HP dipakai bersama).
export const supabase: SupabaseClient | null = url && key ? createClient(url, key, { auth: { flowType: 'pkce' } }) : null;

/** Provider login yang aktif di proyek Supabase (endpoint publik /auth/v1/settings). */
export async function providerEnabled(provider: 'google'): Promise<boolean> {
  if (!url || !key) return false;
  try {
    const res = await fetch(`${url}/auth/v1/settings`, { headers: { apikey: key } });
    const body = (await res.json()) as { external?: Record<string, boolean> };
    return body.external?.[provider] === true;
  } catch {
    return false;
  }
}
