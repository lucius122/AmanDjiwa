import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react';

const ToastContext = createContext<(text: string) => void>(() => {});

export function useToast() {
  return useContext(ToastContext);
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [text, setText] = useState<string | null>(null);
  const timer = useRef<number>();
  const show = useCallback((t: string) => {
    window.clearTimeout(timer.current);
    setText(t);
    timer.current = window.setTimeout(() => setText(null), 2800);
  }, []);
  return (
    <ToastContext.Provider value={show}>
      {children}
      {text && (
        <div
          role="status"
          className="fixed inset-x-16 bottom-88 z-60 mx-auto w-fit animate-in-25 rounded-14 bg-navy px-18 py-12 text-14 font-semibold text-white shadow-toast"
        >
          {text}
        </div>
      )}
    </ToastContext.Provider>
  );
}
