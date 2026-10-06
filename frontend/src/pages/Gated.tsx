import { Navigate, useOutletContext } from 'react-router';
import { AppShell } from '../components/AppShell';
import { GATE_ROUTE, useGate } from '../lib/me';
import type { Me } from '../lib/types';
import { Aku } from './Aku';
import { Chat } from './Chat';
import { Jurnal } from './Jurnal';

/** /mulai: arahkan ke langkah berikutnya sesuai status (dipakai tombol "Mulai ngobrol" & "Masuk"). */
export function Start() {
  const gate = useGate();
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
