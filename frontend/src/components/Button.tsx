import type { ButtonHTMLAttributes } from 'react';

// Varian tombol yang berulang di desain (h52, radius 14).
const VARIANTS = {
  primary: 'h-52 rounded-14 bg-teal-600 text-16 font-bold text-white hover:bg-teal-700 disabled:bg-teal-disabled',
  dark: 'h-52 rounded-14 bg-navy text-16 font-bold text-white',
  outline: 'h-52 rounded-14 border-1.5 border-sand-400 bg-white text-15 font-semibold hover:border-navy',
  link: 'h-44 bg-transparent text-13 font-bold text-teal-600',
} as const;

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof VARIANTS;
}

export function Button({ variant = 'primary', className = '', type = 'button', ...rest }: Props) {
  return <button type={type} className={`${VARIANTS[variant]} ${className}`} {...rest} />;
}
