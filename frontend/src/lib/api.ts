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

// Sesi remaja (email+password, 7 hari) di localStorage. Komponen berlangganan lewat useSession().
// Storage bisa diblokir (mode privat) → anggap belum login, jangan crash.
const TEEN_KEY = 'amandjiwa_teen';
const listeners = new Set<() => void>();
const notify = () => listeners.forEach((l) => l());
export const teenToken = {
  get: (): string | null => {
    try {
      return localStorage.getItem(TEEN_KEY);
    } catch {
      return null;
    }
  },
  set: (t: string) => {
    try {
      localStorage.setItem(TEEN_KEY, t);
    } catch {
      /* tetap jalan untuk sesi ini saja tidak mungkin tanpa storage; abaikan */
    }
    notify();
  },
  clear: () => {
    try {
      localStorage.removeItem(TEEN_KEY);
    } catch {
      /* abaikan */
    }
    notify();
  },
  subscribe: (l: () => void) => {
    listeners.add(l);
    window.addEventListener('storage', l); // keluar di tab lain = keluar juga di sini
    return () => {
      listeners.delete(l);
      window.removeEventListener('storage', l);
    };
  },
};

/** Panggil backend. Default membawa token sesi remaja; `auth: 'staff'` untuk dasbor staf;
 * `auth: false` untuk endpoint publik (landing, daftar, masuk). */
export async function api<T>(
  path: string,
  init: { method?: string; body?: unknown; auth?: boolean | 'staff' } = {},
): Promise<T> {
  const token = init.auth === 'staff' ? staffToken.get() : init.auth === false ? null : teenToken.get();
  const res = await fetch(`${import.meta.env.VITE_API_URL}${path}`, {
    method: init.method ?? 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: init.body === undefined ? undefined : JSON.stringify(init.body),
  });
  if (res.status === 401 && token && init.auth !== 'staff' && init.auth !== false) {
    teenToken.clear(); // sesi kedaluwarsa / akun dihapus → kembali ke halaman masuk
  }
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
