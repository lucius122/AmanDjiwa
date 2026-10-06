import type { ReactNode } from 'react';
import { copy } from '../lib/copy';
import { Icon } from './Icon';

interface Progress {
  step: number;
  total: number;
  onBack: () => void;
}

/** Bingkai onboarding: kartu di tengah pada layar lebar (≥ 900px), layar penuh di mobile. */
export function OnboardingFrame({ progress, children }: { progress?: Progress; children: ReactNode }) {
  return (
    <div className="flex min-h-dvh items-start justify-center bg-cream lg:bg-sand-100 lg:px-20 lg:py-40">
      <main className="flex min-h-dvh w-full max-w-460 flex-col bg-cream lg:min-h-640 lg:rounded-24 lg:shadow-panel">
        {progress && (
          <div className="flex items-center gap-6 px-12 pt-12">
            <button
              type="button"
              onClick={progress.onBack}
              aria-label={copy.login.back}
              className="flex h-44 w-44 items-center justify-center rounded-12 bg-transparent"
            >
              <Icon name="back" className="h-22 w-22 stroke-navy" strokeWidth={2} />
            </button>
            <div className="flex flex-1 gap-6" aria-hidden="true">
              {Array.from({ length: progress.total }, (_, i) => (
                <div
                  key={i}
                  className={`h-6 flex-1 rounded-3 transition-colors duration-300 ${i < progress.step ? 'bg-teal-500' : 'bg-sand-300'}`}
                />
              ))}
            </div>
            <div className="w-44 text-center text-12 font-bold text-muted">
              {progress.step}/{progress.total}
            </div>
          </div>
        )}
        {children}
      </main>
    </div>
  );
}
