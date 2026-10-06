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
# isi minimal: MESSAGE_ENC_KEY, JWT_SECRET (cara membuatnya ada di komentar .env.example),
# SUPABASE_URL + VITE_SUPABASE_URL + VITE_SUPABASE_ANON_KEY (Auth remaja)

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

Akun staf (password diminta lewat prompt, lalu pindai URI otpauth di aplikasi authenticator):

```bash
cd backend
uv run python -m app.cli create-staff --email nama@contoh.id --name "Kak Dimas P." --role pendamping --kelurahan Krobokan
#   --role: pendamping (wajib --kelurahan) | konselor | admin_kota
```

## Login remaja: kode OTP email & Google (Supabase)

Template email kode OTP ada di [supabase/templates/kode-masuk.html](supabase/templates/kode-masuk.html).
Pasang template itu, Site URL & Redirect URL, serta (kalau sudah diisi di `.env`) SMTP sendiri dan
login Google ke proyek Supabase dengan satu perintah:

```bash
cd backend
uv run python -m app.cli supabase-auth                         # dev: http://localhost:5173
uv run python -m app.cli supabase-auth --site-url https://domainmu   # produksi
```

Perintah meminta *personal access token* Supabase (supabase.com/dashboard/account/tokens). Token
tidak disimpan; cabut lagi setelah dipakai. Tanpa SMTP sendiri, Supabase hanya mengirim kode ke
email anggota tim proyek dan dibatasi beberapa email per jam.

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
4. Di dashboard Supabase → Authentication → URL Configuration: isi Site URL dan Redirect URL
   `https://domainmu/mulai`.
5. Cadangkan database tiap hari, mis. lewat cron di VPS:
   `docker compose exec -T postgres pg_dump -U amandjiwa amandjiwa | gzip > backup-$(date +%F).sql.gz`

Caddy menyajikan frontend, meneruskan `/api/*` ke backend, mengurus HTTPS otomatis, dan memasang
header keamanan (CSP, HSTS). Port Postgres/Redis hanya terbuka di `127.0.0.1`.

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
# AmanDjiwa
