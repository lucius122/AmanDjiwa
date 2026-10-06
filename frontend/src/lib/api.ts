export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

// Token staf di sessionStorage: hilang saat tab ditutup (perangkat kelurahan sering dipakai bersama).
export const staffToken = {
  get: () => sessionStorage.getItem('amandjiwa_staff'),
  set: (t: string) => sessionStorage.setItem('amandjiwa_staff', t),
  clear: () => sessionStorage.removeItem('amandjiwa_staff'),
};

/** Panggil backend. Default membawa token sesi Supabase remaja; `auth: 'staff'` untuk dasbor staf;
 * `auth: false` untuk endpoint publik (landing tidak ikut memuat Supabase). */
export async function api<T>(
  path: string,
  init: { method?: string; body?: unknown; auth?: boolean | 'staff' } = {},
): Promise<T> {
  let token: string | undefined;
  if (init.auth === 'staff') {
    token = staffToken.get() ?? undefined;
  } else if (init.auth !== false) {
    const { supabase } = await import('./supabase');
    token = supabase ? (await supabase.auth.getSession()).data.session?.access_token : undefined;
  }
  const res = await fetch(`${import.meta.env.VITE_API_URL}${path}`, {
    method: init.method ?? 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: init.body === undefined ? undefined : JSON.stringify(init.body),
  });
  if (!res.ok) {
    const detail: unknown = await res.json().catch(() => null);
    const message =
      detail && typeof detail === 'object' && 'detail' in detail && typeof detail.detail === 'string'
        ? detail.detail
        : res.statusText;
    throw new ApiError(res.status, message);
  }
  return (res.status === 204 ? undefined : await res.json()) as T;
}

export const staffApi = <T,>(path: string, init: { method?: string; body?: unknown } = {}) =>
  api<T>(path, { ...init, auth: 'staff' });
