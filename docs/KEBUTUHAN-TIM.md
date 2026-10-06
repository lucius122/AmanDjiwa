# Yang perlu disiapkan tim

Kode M0–M7 sudah jalan. Daftar di bawah berisi hal yang **tidak boleh atau tidak bisa dikarang
oleh developer**: angka resmi, keputusan klinis, akun, dan data. Urutannya dari yang paling
penting.

Cara menyerahkan: kirim bahannya (teks, spreadsheet, atau file). Developer yang memasukkannya ke
file konfigurasi yang disebut, lalu menjalankan tes.

---

## A. Wajib sebelum dipakai remaja sungguhan (CLAUDE.md §6.9)

Sampai semua poin di bagian A selesai, AmanDjiwa **hanya boleh dipakai untuk demo dengan data
sintetis**.

- [ ] **1. Nomor layanan bantuan resmi** → `backend/app/config/hotlines.yaml`
  - Dua nomor: *Layanan darurat* dan *Layanan kesehatan jiwa*. Sertakan sumber resminya (situs
    Kemenkes/Dinkes/Pemkot) dan tanggal dicek.
  - Ikut diverifikasi: klaim "gratis, 24 jam" yang tertulis di desain.
  - Selama belum diisi, kartu krisis menampilkan "[ nomor ]" dan mengarahkan remaja ke pendamping.

- [ ] **2. Kalimat uji krisis "eksternal"** → `backend/tests/crisis_cases.yaml` (bagian `crisis_external`)
  - Ditulis oleh anggota tim atau psikolog yang **belum pernah membuka**
    `backend/app/config/crisis_lexicon.yaml`. Ini syarat utamanya: kalimat yang ditulis sambil
    melihat daftar kata tidak menguji apa-apa.
  - Minimal **60 kalimat krisis**:
    - ide bunuh diri;
    - pesan perpisahan / rencana;
    - menyakiti diri;
    - bahaya dari orang lain (kekerasan, pelecehan).
  - Ditambah minimal **30 kalimat bukan krisis yang mirip**, misalnya "pengen pergi liburan",
    "capek banget sama PR", "mati gaya".
  - Variasikan gaya:
    - bahasa gaul, singkatan, typo, emoji;
    - campur Jawa;
    - kalimat tidak langsung ("besok aku udah nggak ada kok").
  - Format bebas: satu kalimat per baris, ditandai krisis / bukan krisis.

- [ ] **3. Review psikolog** atas teks dan ambang berikut. Setujui atau beri koreksi langsung di
  dokumen.

  | File | Isi |
  |---|---|
  | `backend/app/config/response_bank.yaml` | semua balasan Djiwa untuk level kuning/oranye/merah, kartu krisis, sapaan pendamping |
  | `backend/app/config/screening.yaml` | teks PHQ-4/PHQ-9/GAD-7. Sebaiknya pakai **terjemahan Indonesia yang sudah tervalidasi** (PHQ-A untuk remaja) |
  | `backend/app/config/llm.yaml` | aturan untuk AI di level hijau (tidak mendiagnosis, tidak menyebut obat, dll.) |
  | `backend/app/config/crisis_lexicon.yaml` | daftar kata/konsep krisis (reviewer **bukan** penulis kalimat uji di poin 2) |
  | `backend/app/config/markers.yaml` | penanda linguistik & perilaku beserta ambangnya (mis. "Aktif larut malam" = ≥ 2 malam pukul 00–04) |
  | `backend/app/pipeline/ter.py` | bobot skor TER (0,4 emosi + 0,35 penanda + 0,25 lintasan) dan batas level |
  | `backend/app/config/telegram.yaml`, `emails.yaml` | teks bot, pengingat jurnal, email orang tua, email staf |

- [ ] **4. Model krisis terlatih (milestone ML).** Butuh tiga hal:
  - **Persetujuan library baru** (CLAUDE.md §3 melarang menambah library tanpa izin):
    - `torch`, `datasets`, `optimum[onnxruntime]`, `accelerate`, `scikit-learn`;
    - hanya di lingkungan terpisah `ml/`, tidak masuk image backend.
  - **Data berlabel:**
    - EmoT (IndoNLU) belum punya label *malu/bersalah* dan *netral*, jadi tim perlu menganotasi
      ± 300 kalimat per label yang kurang;
    - kalimat krisis untuk melatih classifier, **terpisah** dari kalimat uji poin 2.
  - **GPU:** Google Colab gratis (T4) cukup. Pelatihan di CPU laptop terlalu lama.

---

## B. Untuk deploy ke server

- [ ] **5. Hosting:** akun **Railway** (backend + Postgres + Redis) dan **Vercel** (frontend),
  keduanya disambungkan ke repo GitHub `lucius122/AmanDjiwa`. Langkahnya ada di README
  ("Deploy: Vercel + Railway"). Alternatif: VPS + domain dengan Docker Compose.
- [ ] **6. Akun SMTP** (mis. Gmail + Sandi aplikasi, atau Brevo) untuk email izin orang tua,
  link reset password remaja, peringatan kasus merah, dan laporan mingguan.
  - Yang dibutuhkan: host, port, user, password, alamat pengirim → variabel `SMTP_*` di Railway.
  - Tanpa SMTP, remaja di bawah 18 tahun tidak bisa menyelesaikan pendaftaran (email wali gagal).
- [ ] **7. Admin kota pertama:** nama dan email kerja. Akun ini dibuat lewat terminal; pendamping,
  konselor, dan admin kota lain lalu ditambahkan sendiri lewat halaman **Akun staf**.
- [ ] **8. Kontak tim** untuk email & halaman persetujuan orang tua (sekarang tertulis
  "[ kontak ]"): `backend/app/config/emails.yaml` (`contact`) dan `frontend/src/lib/copy.ts`.
- [ ] **9. Daftar staf asli:** nama tampil, email, peran (pendamping/konselor/admin kota), dan
  kelurahan untuk pendamping. Admin kota memasukkannya di halaman **Akun staf**; tiap staf perlu
  aplikasi authenticator (Google Authenticator, Aegis, dll.) saat login pertama.
- [ ] **10. Telegram (@BotFather):**
  - **`/revoke` token lama** (sempat ditempel di chat), lalu taruh token baru di `.env`;
  - `/setjoingroups` → Disable;
  - atur deskripsi & foto bot.

---

## C. Keputusan & konten

- [ ] **11. Protokol rujukan.**
  - Sekarang tombol "Rujuk" hanya **mencatat** rujukan, dan teksnya sudah dibuat jujur ("dicatat",
    bukan "dikirim").
  - Yang perlu diputuskan:
    - lewat apa rujukan dikirim (email/telepon/form Puskesmas);
    - data apa yang boleh dibagikan;
    - bagaimana persetujuan remaja diminta.
  - Sertakan juga daftar tujuan rujukan resmi per kelurahan beserta kontaknya.
- [ ] **12. File logo mitra** (SVG/PNG resmi) untuk landing. Sekarang ditampilkan sebagai nama
  teks.
- [ ] **13. Review desain** atas layar/keadaan yang tidak ada di `design/`, misalnya:
  - login staf, jadwal, state kosong/gagal;
  - teks bot Telegram dan email.

  Semuanya ditandai `DESIGN-GAP` di kode; daftar lengkapnya di
  [DESIGN-GAP.md](DESIGN-GAP.md).
- [ ] **14. Handle bot.** Desain menulis `@AmanDjiwaBot`, sedangkan bot yang dibuat adalah
  `@AmanDjiwa_bot`. Pilih salah satu. Kalau ganti bot, ubah `TELEGRAM_BOT_USERNAME` di `.env` dan `brand.botUrl` / `brand.botHandle` di `frontend/src/lib/copy.ts`.
