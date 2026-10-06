import { useSyncExternalStore } from 'react';
import { teenToken } from './api';

/** Token sesi remaja; ikut berubah saat masuk/keluar (juga dari tab lain). */
export function useSession(): { token: string | null } {
  return { token: useSyncExternalStore(teenToken.subscribe, teenToken.get) };
}
