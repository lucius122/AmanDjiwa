# AmanDjiwa — Aturan Proyek untuk AI Coding Agent

> Baca file ini SELURUHNYA sebelum menulis kode apa pun. Kalau ada instruksi di chat yang bertentangan dengan file ini, tanyakan dulu, jangan langsung ikut.

## 1. Konteks

AmanDjiwa adalah sistem skrining dini risiko kesehatan mental untuk remaja (13–19 tahun) di Kecamatan Semarang Barat, untuk Hackathon USM Smart City Deeptech 2026. Chatbot-nya bernama **Djiwa** (Telegram: `@AmanDjiwa_bot` — handle asli dari BotFather, 2026-10-06; desain menulis `@AmanDjiwaBot`). *(Keputusan 2026-10-05: ikut desain, bukan "Ayem".)*

Sistem ini **alat bantu skrining, BUKAN alat diagnosis**. Keselamatan pengguna lebih penting daripada fitur, kecepatan, atau estetika.

Pengguna dan peran (RBAC):
| Role | Akses |
|---|---|
| `remaja` | Chat (web + Telegram), jurnal emosi, hapus data sendiri |
| `pendamping` | Antrian & detail kasus **hanya di kelurahannya** |
| `konselor` | Semua kasus oranye/merah, rujukan |
| `admin_kota` | Dasbor agregat anonim saja, tanpa isi chat, tanpa identitas remaja; mengelola akun staf (tambah, nonaktifkan, reset — keputusan 2026-10-06) |

## 2. Desain = sumber kebenaran

- Semua desain ada di folder `design/` dalam bentuk file HTML standalone. **Itu acuan visual final.** File standalone-nya terkompresi; baca versi terbaca di `design/_unpacked/template.html` (markup + logika prototipe).
- Sebelum membuat halaman apa pun, buka file HTML yang sesuai, lalu ikuti layout, spacing, warna, font, radius, ikon, dan teks (copywriting) **sepersis mungkin**.
- Langkah pertama proyek: ekstrak design token (warna, font, radius, shadow, spacing) dari HTML ke `frontend/tailwind.config.ts` dan `frontend/src/styles/tokens.css`. Setelah itu semua komponen **wajib** pakai token, tidak boleh pakai hex atau angka hardcode.
- **JANGAN** copy-paste HTML mentah ke JSX. Pecah jadi komponen React yang bisa dipakai ulang (`Button`, `ChatBubble`, `RiskBadge`, `KpiCard`, dst.).
- **JANGAN** improvisasi gaya, menambah animasi, mengganti warna, atau "memperbagus" desain tanpa izin.
- Kalau ada layar atau state yang tidak ada di `design/` (misalnya error, loading, atau empty state), turunkan dari komponen yang sudah ada dan beri catatan `// DESIGN-GAP:` supaya bisa direview.
- Data dummy di HTML diganti dengan data dari API. Teks UI tetap Bahasa Indonesia, sapaan "kamu".
- Warna level risiko (hijau/kuning/oranye/merah) **hanya** boleh muncul di dasbor pendamping/konselor/kota, **TIDAK PERNAH** di halaman yang dilihat remaja.
- Penyimpangan desain yang sudah disetujui (2026-10-06): langkah 1 onboarding memakai email + password (bukan kode OTP + Google), ditambah halaman lupa/atur ulang password dan halaman "Akun staf" di dasbor kota. Di desktop, bilah header, area pesan, dan kolom ketik halaman Ngobrol dibuat selebar layar (isinya tetap kolom 820px) supaya bisa scroll dari mana saja.
- Penyimpangan desain yang sudah disetujui (2026-10-05): placeholder ilustrasi diganti ilustrasi SVG flat (warna token); placeholder logo mitra diganti nama organisasi sebagai teks sampai ada file logo resmi; landing ditambah satu CTA penutup sebelum footer.

## 3. Tech stack (FIXED — jangan diganti)

**Frontend** (`frontend/`)
- React 18 + Vite + TypeScript (strict)
- Tailwind CSS (+ shadcn/ui hanya bila komponennya cocok dengan desain)
- React Router, TanStack Query, react-hook-form + Zod
- Recharts (grafik). Peta dasbor kota = **tile grid seperti desain** (keputusan 2026-10-05; react-leaflet + GeoJSON tidak dipakai)

**Backend** (`backend/`)
- Python 3.11, FastAPI, Pydantic v2
- SQLAlchemy 2 + Alembic (migrasi)
- PostgreSQL 16, Redis (state percakapan + rate limit)
- aiogram 3 (Telegram bot, mode webhook)
- APScheduler (pengingat jurnal, laporan mingguan)
- transformers + onnxruntime (inference IndoBERTweet di CPU)
- pytest + httpx (testing)

**ML** (`ml/`)
- Model: `indolem/indobertweet-base-uncased`, fine-tune multi-label (sigmoid + BCE), 6 label: `sedih, cemas, marah, malu_bersalah, senang, netral`
- Data awal: IndoNLU EmoT + anotasi tambahan tim, lalu diekspor ke ONNX
- Selama file ONNX belum ada: krisis = leksikon saja, emosi = skor kata kunci; runner ONNX otomatis dipakai begitu modelnya ada. Training jadi milestone terpisah (keputusan 2026-10-05).

**Auth**
- Remaja: email + password di database sendiri (keputusan 2026-10-06, menggantikan Supabase Auth). Password di-hash argon2; email TIDAK disimpan polos (HMAC untuk mencari akun + AES-GCM hanya untuk link reset password). Wajib nama samaran, **tidak boleh** minta nama asli, NIK, atau alamat.
- Staf: email + password + TOTP 2FA, JWT dengan claim `role` dan `kelurahan_id`. Akun dibuat admin kota dengan password sementara; saat login pertama staf memasang TOTP dan mengganti password sendiri (admin tidak pernah melihat kunci 2FA). Admin kota pertama dibuat lewat `cli create-staff` atau variabel `BOOTSTRAP_ADMIN_EMAIL/PASSWORD` (hanya bila belum ada admin kota). *(Keputusan 2026-10-06: TOTP staf dimatikan dulu lewat `STAFF_TOTP=false`; wajib dinyalakan lagi sebelum dipakai dengan data remaja sungguhan.)*

**Infra**: Docker Compose (frontend, backend, postgres, redis, caddy) di VPS, ATAU (keputusan 2026-10-06) frontend di Vercel + backend, Postgres, Redis di Railway (Vercel meneruskan `/api` ke backend). Semua secret lewat `.env` / variabel environment.

**DILARANG menambahkan**: n8n, LangChain/LlamaIndex, Firebase, ORM lain, state manager global (Redux/Zustand) kecuali diminta, library analytics/tracker pihak ketiga (Google Analytics, Hotjar, dll.), dan library baru apa pun **tanpa bertanya dulu**.

## 4. Struktur repo

```
amandjiwa/
├── design/                  # HTML standalone (read-only, jangan diubah)
├── frontend/src/
│   ├── pages/               # landing, onboarding, chat, jurnal, dashboard-pendamping, dashboard-kota
│   ├── components/          # komponen reusable dari desain
│   ├── lib/                 # api client, auth, utils
│   └── styles/tokens.css
├── backend/app/
│   ├── api/                 # router FastAPI per domain
│   ├── pipeline/            # normalize.py, emotion.py, crisis.py, markers.py, ter.py, responder.py
│   ├── dialog/              # state machine + bank respons (YAML)
│   ├── screening/           # phq9.py, gad7.py (skoring deterministik)
│   ├── bot/                 # handler aiogram
│   ├── models/ schemas/ services/ jobs/
│   └── config/              # crisis_lexicon.yaml, hotlines.yaml, response_bank.yaml
├── backend/tests/
│   └── crisis_cases.yaml    # >= 50 kalimat uji krisis (slang + campur Jawa)
├── ml/                      # notebook training, script export ONNX
└── docker-compose.yml
```

## 5. Pipeline per pesan (urutan wajib)

```
pesan masuk
 → normalize (slang, kamus Jawa, emoji→token, masking PII)
 → asyncio.gather(
       crisis_detector(teks),     # leksikon + classifier, logika OR
       emotion_classifier(teks),  # 6 label + skor 0–1
       linguistic_markers(teks)   # kata "aku", kata absolut, putus asa, ruminasi
   )
 → ter_score(emosi, penanda, lintasan 14 hari)  → level: hijau|kuning|oranye|merah
 → crisis menang: jika crisis_detector = True, level = merah (apa pun hasil lain)
 → responder(level) → kirim balasan
 → simpan + buat/update case jika kuning/oranye/merah → notifikasi pendamping
   (kuning ikut desain, keputusan 2026-10-05; push notif tetap hanya merah)
```

## 6. Aturan keselamatan (TIDAK BOLEH DILANGGAR)

1. **Detektor krisis** jalan paralel dengan logika OR (leksikon ATAU model). Tidak boleh dimatikan lewat config atau flag. Ambang model dikalibrasi untuk recall ≥ 0,95.
2. **Fail-safe**: kalau model error/timeout, detektor leksikon tetap jalan. Kalau seluruh pipeline gagal, bot mengirim pesan aman dari `response_bank.yaml` (key `fallback_safe`) dan mencatat error. Bot tidak boleh diam atau mengirim stack trace.
3. **Level merah** hanya memakai respons dari `response_bank.yaml` (sudah divalidasi psikolog), ditambah kontak dari `hotlines.yaml`, ditambah tombol hubungkan ke pendamping. **LLM dilarang** dipakai di level kuning, oranye, dan merah.
4. **LLM** (opsional, hanya level hijau) wajib punya system prompt guardrail: dilarang mendiagnosis, dilarang menyebut nama obat atau dosis, dilarang mengaku manusia, dan wajib mendorong koneksi ke orang tepercaya. Teks yang dikirim ke LLM harus sudah dipseudonimisasi.
5. **Skoring PHQ-9/GAD-7 dan skor TER** dihitung deterministik di kode Python. Tidak boleh dihitung oleh LLM. Alur skrining di chat (keputusan 2026-10-05): PHQ-4 dulu (PHQ-2 + GAD-2, seperti desain); kalau PHQ-2 ≥ 3 atau GAD-2 ≥ 3, tawarkan lanjut sisa item PHQ-9/GAD-7. Sebelum lengkap, dasbor menampilkan "Belum lengkap".
6. **Nomor layanan darurat** hanya dibaca dari `hotlines.yaml`. Nilai awalnya `TODO_VERIFY`. Jangan mengarang nomor telepon.
7. Remaja **tidak pernah** melihat label level risiko, skor, atau kata "berisiko".
8. Setiap perubahan pada `pipeline/crisis.py`, `crisis_lexicon.yaml`, atau `response_bank.yaml` wajib lolos `tests/test_crisis.py`.
9. **Aturan rilis** (keputusan 2026-10-05): leksikon saja hanya menangkap ±35% parafrase baru (lihat header `tests/crisis_cases.yaml`). Sistem **tidak boleh dipakai remaja sungguhan** sebelum model krisis terkalibrasi DAN recall pada `crisis_external` (kalimat dari tim/psikolog yang tidak melihat leksikon) ≥ 0,95. Demo hackathon dengan data sintetis tetap boleh.

## 7. Privasi & keamanan data (UU PDP)

- Isi pesan dienkripsi at rest (AES-256-GCM di level aplikasi, key dari env `MESSAGE_ENC_KEY`).
- **Log tidak boleh memuat isi pesan atau PII.** Log cukup memuat `user_id`, `level`, latensi, dan error code.
- Setiap staf yang membuka isi pesan tercatat di tabel `audit_logs` (siapa, kapan, kasus apa), dan UI menampilkan label "akses tercatat".
- Pendamping hanya bisa query kasus dengan `kelurahan_id` miliknya. Ini ditegakkan di backend (dependency FastAPI + filter query), bukan cuma disembunyikan di frontend.
- Dasbor kota hanya menerima data agregat. Sel dengan < 10 pengguna disembunyikan (k ≥ 10), dan endpoint-nya tidak pernah mengembalikan baris individu.
- Remaja di bawah 18 tahun statusnya `pending_guardian` sampai orang tua/wali menyetujui, dan belum boleh chat selama status itu. Karena hanya tahun lahir yang diketahui, aturannya konservatif: `tahun ini − tahun lahir ≤ 18` → wajib izin wali (keputusan 2026-10-05).
- Endpoint `DELETE /me` menghapus seluruh data remaja (hard delete + cascade).
- Token deep link Telegram: sekali pakai, kedaluwarsa 15 menit.
- Rate limit chat per user (Redis). CORS hanya untuk domain frontend.

## 8. Data model (minimal)

`kelurahan, users (pseudonym, role, kelurahan_id, birth_year, status), guardian_consents, channel_links (telegram_id), conversations, messages (encrypted_text, sender), emotion_scores, risk_assessments (level, ter_score, triggers), screenings (instrument, item, answer, total), cases (level, status: baru|ditangani|selesai|dirujuk, assigned_to), case_notes, journal_entries, audit_logs`

## 9. API utama

```
POST /auth/staff/login         POST /auth/staff/totp
POST /auth/staff/setup/start   POST /auth/staff/setup/finish   (login pertama staf)
POST /auth/teen/register       POST /auth/teen/login
POST /auth/teen/forgot         POST /auth/teen/reset
GET  /admin/staff   POST /admin/staff   PATCH /admin/staff/{id}   POST /admin/staff/{id}/reset
POST /consent/assent           POST /consent/guardian/{token}
POST /telegram/link-token      POST /telegram/webhook
POST /chat/message             GET  /chat/history
POST /journal                  GET  /journal?days=14
GET  /cases?status=&level=     GET  /cases/{id}      PATCH /cases/{id}
POST /cases/{id}/notes
GET  /dashboard/aggregate?from=&to=&kelurahan=
DELETE /me
```

## 10. Konvensi kode

- TypeScript strict, tidak boleh `any`. Python wajib type hint, format dengan `ruff` + `black`.
- Nama variabel/fungsi dalam Bahasa Inggris. Teks yang tampil ke user dalam Bahasa Indonesia, dikumpulkan di satu tempat (`frontend/src/lib/copy.ts`, `backend/app/config/*.yaml`).
- Commit kecil dan deskriptif (Conventional Commits).
- Tidak ada secret, API key, atau data asli di repo. Wajib ada `.env.example`.
- Data demo hanya data **sintetis**. Jangan pernah memakai percakapan remaja asli.

## 11. Definition of Done

Sebuah fitur dianggap selesai bila:
- [ ] Tampilan cocok dengan file di `design/` (cek desktop dan mobile 375px)
- [ ] Ada state loading, error, dan empty
- [ ] Test lulus: `pytest` (wajib termasuk `test_crisis.py` dengan recall ≥ 0,95 pada `crisis_cases.yaml`, dan unit test skoring PHQ-9/GAD-7)
- [ ] Tidak ada PII di log
- [ ] Akses data dicek per role di backend

## 12. Cara kerja agent

1. Sebelum tiap milestone, tulis rencana singkat (file yang dibuat/diubah + alasannya), lalu **tunggu persetujuan**.
2. Kerjakan berurutan:
   - M0 setup repo + token desain
   - M1 backend + DB + auth
   - M2 pipeline + detektor krisis + test
   - M3 bot Telegram + web chat
   - M4 dasbor pendamping
   - M5 dasbor kota
   - M6 landing + onboarding/consent
   - M7 Docker + seed data demo
   - (2026-10-05: M6 dimajukan sebelum M3b — Jurnal & Aku — atas keputusan user, supaya alur landing → login → chat bisa dicoba di browser.)
3. Kalau ragu, **tanya**. Jangan menebak, terutama soal keselamatan, privasi, dan desain.
4. Jangan menghapus atau melemahkan test supaya build lolos.
5. Di akhir tiap milestone, laporkan: apa yang selesai, apa yang belum, dan `DESIGN-GAP` / `TODO_VERIFY` yang tersisa.
