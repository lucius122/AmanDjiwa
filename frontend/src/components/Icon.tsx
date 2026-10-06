// Path ikon dari prototipe (objek `I` dan ikon inline di design/). viewBox 24×24, garis.
export const ICONS = {
  chat: 'M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z',
  jurnal: 'M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3zM9 9h6M9 13h4',
  aku: 'M12 4a4 4 0 1 1 0 8 4 4 0 0 1 0-8zM4 21c0-4 3.6-7 8-7s8 3 8 7',
  heart:
    'M12 21s-7.5-4.6-9.6-9.2C.9 8.4 3 4.5 6.7 4.5c2.1 0 3.6 1.1 4.3 2.4.7-1.3 2.2-2.4 4.3-2.4 3.7 0 5.8 3.9 4.3 7.3C19.5 16.4 12 21 12 21z',
  phone: 'M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2',
  telegram: 'M21 4L3 11l6 2 2 6 3-4 5 4z',
  send: 'M4 12l16-8-6 16-3-7-7-1z',
  close: 'M6 6l12 12M18 6L6 18',
  back: 'M15 6l-6 6 6 6',
  next: 'M5 12h14M13 6l6 6-6 6',
  emo: 'M12 3a9 9 0 1 1 0 18 9 9 0 0 1 0-18zM8.5 14.5s1.3 1.8 3.5 1.8 3.5-1.8 3.5-1.8M9 9.5h.01M15 9.5h.01',
  shield: 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6zM9 12l2 2 4-4',
  lock: 'M5 11h14v10H5zM8 11V7a4 4 0 0 1 8 0v4',
  trash: 'M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3',
  info: 'M12 3a9 9 0 1 1 0 18 9 9 0 0 1 0-18zM12 11v5M12 8h.01',
  list: 'M4 6h16M4 12h16M4 18h10',
  eye: 'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12zM12 9a3 3 0 1 1 0 6 3 3 0 0 1 0-6z',
  check: 'M5 12l5 5 9-10',
  chevronDown: 'M6 9l6 6 6-6',
  chevronRight: 'M9 6l6 6-6 6',
  people:
    'M9 5a3 3 0 1 1 0 6 3 3 0 0 1 0-6zM3 19c0-3 2.7-5 6-5s6 2 6 5M17 6.6a2.4 2.4 0 1 1 0 4.8 2.4 2.4 0 0 1 0-4.8zM17.5 14c2.3.2 3.5 1.8 3.5 4',
  // dasbor staf
  hist: 'M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5M12 7v5l3 2',
  cal: 'M3.5 5h17v15h-17zM3.5 10h17M8 3v4M16 3v4',
  gear: 'M12 9a3 3 0 1 1 0 6 3 3 0 0 1 0-6zM12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1',
  timer: 'M12 5a8 8 0 1 1 0 16 8 8 0 0 1 0-16zM12 9v4l2 2M10 2h4',
  download: 'M12 4v11M7 10l5 5 5-5M5 20h14',
  shieldPlain: 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z',
  lockSmall: 'M7 11h10a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-6a2 2 0 0 1 2-2zM8 11V7a4 4 0 0 1 8 0v4',
} as const;

export type IconName = keyof typeof ICONS;

interface Props {
  name: IconName;
  className?: string; // ukuran (w-*/h-*) & warna garis (stroke-*)
  strokeWidth?: number;
  fill?: string;
}

export function Icon({ name, className, strokeWidth = 1.8, fill = 'none' }: Props) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill={fill}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d={ICONS[name]} />
    </svg>
  );
}
