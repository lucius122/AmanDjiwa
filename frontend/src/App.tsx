import { lazy, Suspense, type ComponentType } from 'react';
import { Navigate, Route, Routes } from 'react-router';
import { Landing } from './pages/Landing';

// Landing dimuat langsung (halaman pertama pengunjung). Halaman lain — yang butuh
// Zod — dipecah jadi chunk terpisah supaya landing ringan di jaringan seluler.
function page<K extends string>(load: () => Promise<Record<K, ComponentType>>, name: K) {
  return lazy(async () => ({ default: (await load())[name] }));
}
const Start = page(() => import('./pages/Gated'), 'Start');
const TeenApp = page(() => import('./pages/Gated'), 'TeenApp');
const ChatRoute = page(() => import('./pages/Gated'), 'ChatRoute');
const Login = page(() => import('./pages/Login'), 'Login');
const Register = page(() => import('./pages/Register'), 'Register');
const ForgotPassword = page(() => import('./pages/PasswordReset'), 'ForgotPassword');
const ResetPassword = page(() => import('./pages/PasswordReset'), 'ResetPassword');
const Waiting = page(() => import('./pages/Waiting'), 'Waiting');
const GuardianApproval = page(() => import('./pages/GuardianApproval'), 'GuardianApproval');
const JurnalRoute = page(() => import('./pages/Gated'), 'JurnalRoute');
const AkuRoute = page(() => import('./pages/Gated'), 'AkuRoute');
// Dasbor staf: chunk terpisah, tidak pernah dimuat di perangkat remaja.
const StaffLogin = page(() => import('./pages/staff/StaffLogin'), 'StaffLogin');
const StaffApp = page(() => import('./pages/staff/StaffApp'), 'StaffApp');
const Antrian = page(() => import('./pages/staff/Queue'), 'Antrian');
const Riwayat = page(() => import('./pages/staff/Queue'), 'Riwayat');
const Schedule = page(() => import('./pages/staff/Schedule'), 'Schedule');
const StaffSettings = page(() => import('./pages/staff/Settings'), 'Settings');
const Kota = page(() => import('./pages/kota/Kota'), 'Kota');
const KotaLayout = page(() => import('./pages/kota/KotaLayout'), 'KotaLayout');
const StaffAccounts = page(() => import('./pages/kota/StaffAccounts'), 'StaffAccounts');

export default function App() {
  return (
    <Suspense fallback={null}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/mulai" element={<Start />} />
        <Route path="/masuk" element={<Login />} />
        <Route path="/daftar" element={<Register />} />
        <Route path="/lupa-password" element={<ForgotPassword />} />
        <Route path="/reset-password/:token" element={<ResetPassword />} />
        <Route path="/menunggu" element={<Waiting />} />
        <Route path="/persetujuan-wali/:token" element={<GuardianApproval />} />
        <Route element={<TeenApp />}>
          <Route path="/ngobrol" element={<ChatRoute />} />
          <Route path="/jurnal" element={<JurnalRoute />} />
          <Route path="/aku" element={<AkuRoute />} />
        </Route>
        <Route path="/staf/masuk" element={<StaffLogin />} />
        <Route path="/staf" element={<StaffApp />}>
          <Route index element={<Antrian />} />
          <Route path="riwayat" element={<Riwayat />} />
          <Route path="jadwal" element={<Schedule />} />
          <Route path="pengaturan" element={<StaffSettings />} />
        </Route>
        <Route path="/kota" element={<KotaLayout />}>
          <Route index element={<Kota />} />
          <Route path="akun" element={<StaffAccounts />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
