// Format waktu dasbor staf, selalu WIB (sama dengan backend). Pola teks dari prototipe di design/.
const TZ = 'Asia/Jakarta';
const fmt = (d: Date, opts: Intl.DateTimeFormatOptions) =>
  new Intl.DateTimeFormat('id-ID', { ...opts, timeZone: TZ }).format(d);
const ymd = (d: Date) => new Intl.DateTimeFormat('en-CA', { timeZone: TZ }).format(d);

/** "09:28" (id-ID memakai titik; antrian di desain memakai titik dua). */
export const clock = (d: Date) => fmt(d, { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).replace('.', ':');

/** "16.00" — gaya jam di halaman Jadwal. */
export const clockDot = (d: Date) => clock(d).replace(':', '.');

/** "5 Okt" */
export const dayMonth = (d: Date) => fmt(d, { day: 'numeric', month: 'short' });

/** "RAB" */
export const weekdayShort = (d: Date) => fmt(d, { weekday: 'short' }).slice(0, 3).toUpperCase();

/** "Senin, 5 Okt · 09:40" */
export const headerClock = (now: Date) => `${fmt(now, { weekday: 'long' })}, ${dayMonth(now)} · ${clock(now)}`;

/** "09:28" hari ini, "Kemarin 21:10", lainnya "3 Okt 10:12". */
export function timeLabel(d: Date, now: Date): string {
  const yesterday = new Date(now.getTime() - 86_400_000);
  if (ymd(d) === ymd(now)) return clock(d);
  if (ymd(d) === ymd(yesterday)) return `Kemarin ${clock(d)}`;
  return `${dayMonth(d)} ${clock(d)}`;
}

/** "baru saja" / "12 mnt" / "3 jam" / "2 hari" */
export function since(d: Date, now: Date): string {
  const min = Math.floor((now.getTime() - d.getTime()) / 60_000);
  if (min < 1) return 'baru saja';
  if (min < 60) return `${min} mnt`;
  if (min < 1440) return `${Math.floor(min / 60)} jam`;
  return `${Math.floor(min / 1440)} hari`;
}

/** Tanggal WIB YYYY-MM-DD + jam HH:MM → Date (untuk form Jadwal). */
export const fromWib = (date: string, time: string) => new Date(`${date}T${time}:00+07:00`);

export const todayWib = () => ymd(new Date());

const DAY_MS = 86_400_000;

/** Tanggal saja (YYYY-MM-DD, WIB) → Date di tengah hari WIB, aman untuk diformat. */
export const wibDate = (ymd: string) => new Date(`${ymd}T12:00:00+07:00`);

/** `weeks` minggu terakhir (mulai Senin) sampai hari ini, sebagai tanggal WIB. */
export function lastWeeks(weeks: number): { from: string; to: string } {
  const to = todayWib();
  const d = new Date(`${to}T00:00:00Z`);
  const back = ((d.getUTCDay() + 6) % 7) + (weeks - 1) * 7;
  return { from: new Date(d.getTime() - back * DAY_MS).toISOString().slice(0, 10), to };
}
