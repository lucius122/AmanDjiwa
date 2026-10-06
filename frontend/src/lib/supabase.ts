import { createClient, type SupabaseClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL;
const key = import.meta.env.VITE_SUPABASE_ANON_KEY;

// Supabase hanya untuk login remaja (CLAUDE.md §3). null = belum dikonfigurasi di .env.
export const supabase: SupabaseClient | null = url && key ? createClient(url, key) : null;
