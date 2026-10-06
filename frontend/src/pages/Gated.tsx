import { useState } from 'react';
import { Navigate, useOutletContext } from 'react-router';
import { AppShell } from '../components/AppShell';
import { GATE_ROUTE, useGate } from '../lib/me';
import type { Me } from '../lib/types';
import { Aku } from './Aku';
import { Chat } from './Chat';
import { Jurnal } from './Jurnal';

/** /mulai: arahkan ke langkah berikutnya sesuai status (dipakai tombol "Mulai ngobrol" & "Masuk"). */
const OAUTH_FAILED = { oauthFailed: true } as const;

export function Start() {
  const gate = useGate();
  // Login Google batal/gagal: Supabase kembali ke /mulai?error=… → pesan di halaman masuk.
  // Dibaca sekali saat mount: selama transisi ke /masuk komponen ini masih dirender ulang
  // dengan URL yang sudah berubah, dan Navigate kedua (tanpa state) akan menimpa yang pertama.
  const [oauthFailed] = useState(() => /[?&#]error=/.test(window.location.search + window.location.hash));
  if (oauthFailed) return <Navigate to="/masuk" replace state={OAUTH_FAILED} />;
  if (gate.state === 'loading') return null; // DESIGN-GAP: layar loading awal belum ada di desain
  return <Navigate to={GATE_ROUTE[gate.state]} replace />;
}

export function TeenApp() {
  const gate = useGate();
  if (gate.state === 'loading') return null;
  if (gate.state !== 'active') return <Navigate to={GATE_ROUTE[gate.state]} replace />;
  return <AppShell me={gate.me} />;
}

export function ChatRoute() {
  return <Chat me={useOutletContext<Me>()} />;
}

export function JurnalRoute() {
  return <Jurnal me={useOutletContext<Me>()} />;
}

export function AkuRoute() {
  return <Aku me={useOutletContext<Me>()} />;
}
