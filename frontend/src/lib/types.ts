// Cermin skema backend (app/dialog, app/api/chat.py, app/api/me.py).
export type Sender = 'remaja' | 'bot' | 'pendamping';
export type MessageKind = 'text' | 'crisis_card';

export interface Hotline {
  id: string;
  label: string;
  number: string;
  note: string;
}

export interface CrisisCard {
  title: string;
  body: string;
  call_label: string;
  connect_label: string;
  connect_sub: string;
  footer: string;
}

export interface ScreeningQuestion {
  instrument: 'phq9' | 'gad7';
  item: number;
  n: number;
  total: number;
  text: string;
  options: string[];
}

export interface BotMessage {
  sender: Sender;
  kind: MessageKind;
  text: string;
}

export interface ChatTurn {
  messages: BotMessage[];
  card: CrisisCard | null;
  hotlines: Hotline[];
  offer_connect: boolean;
  connected: boolean;
  screening: ScreeningQuestion | null;
  followup_offer: boolean;
  client_action: 'open_napas' | 'open_help' | null;
}

export interface HistoryItem {
  id: string;
  sender: Sender;
  kind: MessageKind;
  text: string;
  created_at: string;
  author: string | null; // nama pendamping untuk sender=pendamping
}

export interface History {
  messages: HistoryItem[];
  card: CrisisCard;
  hotlines: Hotline[];
  connected: boolean;
  screening: ScreeningQuestion | null;
  followup_offer: boolean;
}

export interface Me {
  pseudonym: string;
  avatar: number;
  kelurahan_id: number;
  kelurahan_name: string;
  birth_year: number;
  status: 'pending_guardian' | 'active' | 'disabled';
}

export type EmotionKey = 'senang' | 'sedih' | 'cemas' | 'marah' | 'malu_bersalah' | 'netral';

export interface JournalEntry {
  entry_date: string; // YYYY-MM-DD (WIB)
  emotion: EmotionKey;
  intensity: number; // 1–5
  note: string | null;
}

export interface JournalSave {
  entry: JournalEntry;
  help: boolean; // catatan menunjukkan bahaya → buka "Butuh bantuan sekarang?"
}

export type ChatAction = 'answer' | 'skip' | 'stop' | 'continue' | 'connect';

export interface TelegramLink {
  code: string;
  bot_username: string;
  deep_link: string;
  expires_in: number;
}

// ---------- dasbor staf (app/api/auth.py, app/api/cases.py) ----------
export type Role = 'remaja' | 'pendamping' | 'konselor' | 'admin_kota';
export type RiskLevel = 'kuning' | 'oranye' | 'merah'; // hijau tidak pernah jadi kasus
export type CaseStatus = 'baru' | 'ditangani' | 'selesai' | 'dirujuk';

export interface Staff {
  role: Role;
  display_name: string | null;
  kelurahan_id: number | null;
  kelurahan_name: string | null;
}

export interface StaffToken extends Staff {
  access_token: string;
}

export interface StaffSettings {
  notif_red: boolean;
  sound: boolean;
  compact: boolean;
}

export interface CaseRow {
  id: string;
  pseudonym: string;
  kelurahan: string;
  level: RiskLevel;
  status: CaseStatus;
  detected_at: string;
}

export interface CaseNote {
  id: string;
  text: string;
  author: string | null;
  created_at: string;
}

export interface ScreeningScore {
  total: number | null; // null = "Belum lengkap"
  severity: 'minimal' | 'ringan' | 'sedang' | 'sedang_berat' | 'berat' | null;
}

export interface CaseDetail extends CaseRow {
  age: number | null;
  referred_to: string | null;
  trajectory: (number | null)[]; // 14 hari, −2..+2
  trajectory_from: string; // YYYY-MM-DD
  dominant: { emotion: EmotionKey; days: number }[];
  phq9: ScreeningScore;
  gad7: ScreeningScore;
  markers: string[];
  notes: CaseNote[];
}

export interface TriggerMessages {
  messages: { text: string; created_at: string }[];
  accessed_at: string;
  accessed_by: string | null;
}

export interface FollowUp {
  id: string;
  title: string;
  scheduled_at: string;
  ends_at: string | null;
  case_id: string | null;
}

// ---------- dasbor kota (app/api/dashboard.py) — hanya agregat; null = disembunyikan (k < 10) ----------
export type FullRiskLevel = 'hijau' | RiskLevel;

export interface CityKpis {
  active_users: number;
  active_users_change_pct: number | null;
  sessions: number;
  handled_15m_pct: number | null;
  referrals: number;
}

export interface KelurahanStat {
  id: number;
  name: string;
  users: number | null;
  risk_pct: number | null;
  levels: Record<FullRiskLevel, number> | null;
}

export interface CityAggregate {
  start: string;
  end: string;
  min_cell: number;
  demo: boolean;
  kpis: CityKpis | null;
  kelurahan: KelurahanStat[];
  trend: { week: string; pct: Record<EmotionKey, number> | null }[];
  topics: { key: string; label: string; pct: number }[];
}

// ---------- kelola akun staf (app/api/admin.py) ----------
export interface StaffAccount {
  id: string;
  display_name: string | null;
  email: string | null;
  role: Exclude<Role, 'remaja'>;
  kelurahan_id: number | null;
  kelurahan_name: string | null;
  status: 'active' | 'disabled';
  needs_setup: boolean;
  created_at: string;
}

export interface StaffWithPassword {
  account: StaffAccount;
  temp_password: string;
}
