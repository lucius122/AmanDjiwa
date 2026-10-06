# AmanDjiwa

Sistem **skrining dini** risiko kesehatan mental untuk remaja 13–19 tahun di Kecamatan Semarang
Barat (Hackathon USM Smart City Deeptech 2026). Remaja ngobrol dengan **Djiwa** (web atau
Telegram [@AmanDjiwa_bot](https://t.me/AmanDjiwa_bot)) dan mengisi jurnal emosi. Pesan berisiko
diteruskan ke pendamping kelurahan, dan pemerintah kota hanya melihat data agregat anonim.

> **Bukan alat diagnosis.** Sistem ini **belum boleh dipakai remaja sungguhan** sampai model krisis
> terkalibrasi dan recall pada kalimat uji eksternal ≥ 0,95 (CLAUDE.md §6.9). Untuk demo, pakai
> data sintetis (`seed-demo`). Yang masih perlu disiapkan tim ada di
> [docs/KEBUTUHAN-TIM.md](docs/KEBUTUHAN-TIM.md).

Aturan proyek (keselamatan, privasi, desain, stack) ada di [CLAUDE.md](CLAUDE.md). Baca itu dulu
sebelum mengubah kode.

## Isi

| Bagian | Untuk siapa | Rute |
|---|---|---|
| Landing, daftar, izin wali | publik / remaja / orang tua | `/`, `/masuk`, `/daftar`, `/persetujuan-wali/:token` |
| Ngobrol, Jurnal, Aku | remaja | `/ngobrol`, `/jurnal`, `/aku` |
| Dasbor pendamping & konselor | staf | `/staf/masuk`, `/staf` (antrian, riwayat, jadwal, pengaturan) |
| Dasbor kota (agregat, k ≥ 10) | admin kota | `/kota` |
| Bot Telegram | remaja | @AmanDjiwa_bot (tautkan dari menu Aku) |

### Tampilan pemantauan (staf)

Semua tangkapan layar memakai data **sintetis** (`seed-demo`).

| Peran | Yang dipantau | Layar |
|---|---|---|
| Pendamping | antrian kasus kelurahannya (merah & baru di atas), detail kasus, cuplikan pesan pemicu (akses tercatat), catatan, rujukan | [antrian & detail](docs/screenshots/02-pendamping-antrian.png) · [riwayat](docs/screenshots/03-pendamping-riwayat.png) · [jadwal](docs/screenshots/04-pendamping-jadwal.png) · [pengaturan](docs/screenshots/05-pendamping-pengaturan.png) · [HP](docs/screenshots/06-pendamping-hp.png) |
| Konselor | kasus oranye & merah di semua kelurahan | [antrian](docs/screenshots/07-konselor-antrian.png) |
| Admin kota | hanya agregat (k ≥ 10): KPI, peta risiko per kelurahan, distribusi level, tren emosi, topik pemicu | [peta](docs/screenshots/08-kota-peta.png) · [tabel](docs/screenshots/09-kota-tabel.png) |

Login staf: [email + kata sandi + kode authenticator](docs/screenshots/01-login-staf.png).

Alur per pesan: normalisasi → (detektor krisis ‖ emosi ‖ penanda linguistik) → skor TER →
level hijau/kuning/oranye/merah (krisis selalu merah) → balasan → kasus + notifikasi pendamping.
Detail di CLAUDE.md §5–§6.

```
backend/   FastAPI, SQLAlchemy + Alembic, pipeline, bot aiogram, jobs APScheduler, tes pytest
frontend/  React + Vite + Tailwind (token desain di src/styles/tokens.css)
design/    prototipe HTML = acuan visual (read-only)
ml/models/ tempat model ONNX (kosong = detektor leksikon + skor kata kunci)
```

## Menjalankan di laptop (dev)

Butuh: Docker, [uv](https://docs.astral.sh/uv/), Node 22.

```bash
cp .env.example .env
# isi minimal: MESSAGE_ENC_KEY, JWT_SECRET (cara membuatnya ada di komentar .env.example)

docker compose up -d                      # Postgres :5433, Redis, Mailpit (email dev: http://localhost:8025)

cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --port 8000   # API + tugas terjadwal
uv run python -m app.bot.polling          # (opsional, terminal lain) bot Telegram mode polling

cd ../frontend
npm install
npm run dev                               # http://localhost:5173
```

## Akun

- **Remaja** mendaftar sendiri di `/masuk` dengan email + password. Email tidak disimpan polos
  (hash untuk mencari akun + terenkripsi untuk link reset). Lupa password → link lewat email
  backend (di laptop masuk Mailpit, http://localhost:8025).
- **Staf** dibuat oleh admin kota di dasbor kota → **Akun staf**. Akun baru mendapat password
  sementara (tampil sekali); saat login pertama di `/staf/masuk` staf memasang aplikasi
  authenticator dan membuat password sendiri. Admin juga bisa menonaktifkan dan mereset akun.
- **Admin kota pertama** dibuat lewat terminal (password diminta lewat prompt, lalu pindai URI
  otpauth di aplikasi authenticator):

  ```bash
  cd backend
  uv run python -m app.cli create-staff --email nama@contoh.id --name "Dinkes Kota" --role admin_kota
  ```

## Demo hackathon (data sintetis)

```bash
# .env: DEMO_MODE=true   (JANGAN di server yang dipakai remaja sungguhan)
cd backend
uv run python -m app.cli seed-demo    # ± 340 remaja sintetis + 6 kasus contoh dari desain + 3 akun staf demo
uv run python -m app.cli reset-demo   # hapus HANYA data demo
```

`seed-demo` mencetak email, password, dan URI TOTP untuk akun pendamping, konselor, dan admin
kota demo. Untuk presentasi tanpa aplikasi authenticator, ambil kode 6 digitnya lewat:

```bash
uv run python -m app.cli kode-demo pendamping   # atau: konselor | admin_kota (hanya akun demo-…)
```

## Deploy ke VPS (Docker Compose + Caddy)

1. Arahkan DNS domain ke VPS, lalu salin repo dan `.env`.
2. Di `.env`: `SITE_ADDRESS=domainmu`, `FRONTEND_ORIGIN=https://domainmu`, `POSTGRES_PASSWORD` yang
   kuat, SMTP asli (`DOCKER_SMTP_HOST`, `DOCKER_SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`,
   `SMTP_FROM`), `DEMO_MODE=false`.
3. Jalankan:
   ```bash
   docker compose --profile app up -d --build
   docker compose exec backend python -m app.cli telegram-webhook   # daftarkan webhook bot (HTTPS)
   ```
4. Cadangkan database tiap hari, mis. lewat cron di VPS:
   `docker compose exec -T postgres pg_dump -U amandjiwa amandjiwa | gzip > backup-$(date +%F).sql.gz`

Caddy menyajikan frontend, meneruskan `/api/*` ke backend, mengurus HTTPS otomatis, dan memasang
header keamanan (CSP, HSTS). Port Postgres/Redis hanya terbuka di `127.0.0.1`.

## Deploy: Vercel (frontend) + Railway (backend)

Vercel hanya menyajikan frontend; backend butuh proses yang selalu menyala (bot, peringatan kasus
merah, Postgres, Redis), jadi ditaruh di Railway. Vercel meneruskan `/api/*` ke Railway, sehingga
browser hanya bicara ke satu domain (tanpa CORS).

**Railway** (railway.com → New Project → Deploy from GitHub repo):
1. Tambah layanan **PostgreSQL** dan **Redis** di proyek yang sama.
2. Layanan backend: *Root Directory* `backend` (memakai `backend/Dockerfile` + `railway.json`).
   Migrasi jalan otomatis saat start.
3. Variables backend:
   - `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`, `REDIS_URL` = `${{Redis.REDIS_URL}}`
   - `MESSAGE_ENC_KEY`, `JWT_SECRET` (buat baru, jangan pakai milik laptop)
   - `FRONTEND_ORIGIN` = URL Vercel (mis. `https://amandjiwa.vercel.app`)
   - Email izin wali, reset password, dan peringatan merah: Railway paket Hobby/Trial
     **memblokir SMTP keluar**, jadi pakai `BREVO_API_KEY` (API HTTPS Brevo, gratis 300 email/hari)
     + `SMTP_FROM` = alamat yang sudah diverifikasi di Brevo (Senders). SMTP biasa (`SMTP_HOST`,
     `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`) hanya jalan di Railway Pro atau VPS.
   - `PORT` = `8000` (supaya port aplikasi pasti sama dengan target port domain)
   - admin kota pertama: `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD` (sementara, ≥ 12
     karakter), opsional `BOOTSTRAP_ADMIN_NAME`. Dibuat otomatis saat start **hanya kalau belum ada
     admin kota**; hapus kedua variabel setelah admin berhasil login pertama.
   - opsional: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `NVIDIA_API_KEY`
4. Settings → Networking → **Generate Domain** dengan target port **8000**, catat domainnya.
   Cek: Deploy Logs harus berisi `Uvicorn running on http://0.0.0.0:8000` dan
   `https://<domain>/health` menjawab `{"status":"ok"}`. Jawaban 502 "Application failed to
   respond" = aplikasi berhenti saat start (lihat Deploy Logs) atau target port tidak sama.
5. Login pertama admin kota: buka `https://<domain-vercel>/staf/masuk`, masuk dengan
   `BOOTSTRAP_ADMIN_EMAIL` + `BOOTSTRAP_ADMIN_PASSWORD`, lalu hapus kedua variabel itu di Railway.
   Staf lain ditambahkan dari menu **Akun staf**. Kode authenticator staf sedang dimatikan
   (`STAFF_TOTP=false`, default); dengan `STAFF_TOTP=true` login pertama meminta pasang
   authenticator + password baru.
6. Daftarkan webhook bot Telegram. Perintah ini harus jalan **di dalam** container backend
   (database Railway memakai jaringan privat), mis. lewat Railway CLI:
   ```bash
   railway link              # pilih proyek & layanan backend
   railway ssh               # shell di dalam container
   python -m app.cli telegram-webhook --url https://<domain-railway>/telegram/webhook
   ```
   Setelah webhook terdaftar, jangan jalankan bot mode polling di laptop dengan token yang sama
   (Telegram hanya mengirim ke satu tempat).

**Vercel** (vercel.com → Add New Project → repo ini):
1. *Root Directory* `frontend` (framework Vite terdeteksi; build & header keamanan dari
   `frontend/vercel.json`).
2. Environment variable: `VITE_API_URL` = `/api`.
3. Di `frontend/vercel.json`, ganti `GANTI-DENGAN-DOMAIN-RAILWAY.up.railway.app` dengan domain
   Railway dari langkah 4, commit, lalu deploy.

## Tugas terjadwal

Tugas ini berjalan di proses API (`RUN_JOBS=true`). Kalau ada beberapa proses, kunci
Redis/baris mencegah kiriman ganda.

| Tugas | Jadwal (WIB) | Isi |
|---|---|---|
| Peringatan kasus merah | tiap menit | email ke pendamping kelurahan + konselor; tanpa identitas/isi pesan; bisa dimatikan di Pengaturan |
| Pengingat jurnal | 19.00 | Telegram, hanya remaja yang menautkan akun & belum isi jurnal; dimatikan dengan `/pengingat` |
| Laporan mingguan | Senin 07.00 | email agregat 7 hari ke admin kota (aturan k ≥ 10 berlaku) |

## Tes & pengecekan

```bash
cd backend && uv run pytest            # termasuk test_crisis.py (wajib lolos untuk perubahan krisis)
cd backend && uv run ruff check . && uv run black --check .
cd frontend && npm run check:tokens && npm run build   # check:tokens = larang warna/ukuran hardcode
```

Tes memakai database `amandjiwa_test` di Postgres yang sama. Buat sekali:

```bash
docker compose exec postgres createdb -U amandjiwa amandjiwa_test
```
