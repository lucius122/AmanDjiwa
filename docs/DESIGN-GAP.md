# Daftar DESIGN-GAP

Layar, keadaan, atau teks yang **tidak ada di `design/`** sehingga diturunkan sendiri dari komponen
yang sudah ada (CLAUDE.md §2). Mohon direview desainer/tim. Dibuat otomatis dari komentar
`DESIGN-GAP` di kode (06-10-2026); perbarui dengan:

```bash
grep -rn DESIGN-GAP backend/app frontend/src
```

## `backend/app/config/emails.yaml`

| Baris | Catatan |
|---|---|
| 1 | isi email ke orang tua tidak ada di design/. Diturunkan dari halaman |
| 22 | tidak ada di desain. TODO_VERIFY: review tim. ---------- |
| 46 | tidak ada di desain. TODO_VERIFY: review tim. ---------- |

## `backend/app/config/response_bank.yaml`

| Baris | Catatan |
|---|---|
| 3 | . TODO_VERIFY: SEMUA teks wajib divalidasi psikolog sebelum rilis. |
| 8 | tidak ada di desain. |
| 25 | variasi kedua tidak ada di desain. |
| 30 | balasan "sedih" tidak ada di desain. |
| 51 | tidak ada di desain. |
| 59 | desain hanya punya versi pendamping; versi konselor (lintas kelurahan). |
| 63 | tidak ada di desain. |

## `backend/app/config/screening.yaml`

| Baris | Catatan |
|---|---|
| 2 | item lain ditulis dengan gaya bahasa yang sama (adaptasi PHQ-9 / GAD-7). |
| 27 | tawaran lanjut (alur bertahap, keputusan 2026-10-05) tidak ada di desain. |

## `backend/app/config/telegram.yaml`

| Baris | Catatan |
|---|---|
| 1 | tidak ada desain Telegram; diturunkan dari copy web. |
| 18 | + TODO_VERIFY. Bisa dimatikan: /pengingat |

## `frontend/src/components/ScreeningCard.tsx`

| Baris | Catatan |
|---|---|
| 57 | tawaran lanjut skrining (alur bertahap) tidak ada di desain; memakai gaya kartu skrining. |

## `frontend/src/components/TelegramSheet.tsx`

| Baris | Catatan |
|---|---|
| 26 | state loading & gagal tidak ada di desain |

## `frontend/src/lib/copy.ts`

| Baris | Catatan |
|---|---|
| 2 | . |
| 20 | email + password (keputusan 2026-10-06), desain memakai kode OTP + Google. |
| 37 | lupa & atur ulang password (tidak ada di desain). |
| 76 | tombol lanjut skrining & tawaran pendamping di luar kartu krisis. |
| 98 | (lihat kode di baris ini) |
| 142 | (lihat kode di baris ini) |
| 143 | nomor belum diverifikasi (hotlines.yaml masih TODO_VERIFY) |
| 158 | (lihat kode di baris ini) |
| 163 | validasi) |
| 205 | setelah muat ulang) |
| 242 | state di bawah tidak ada di desain. |
| 285 | belum ada entri) |
| 294 | (lihat kode di baris ini) |
| 295 | (lihat kode di baris ini) |
| 331 | (lihat kode di baris ini) |
| 336 | halaman login staf tidak ada di desain; diturunkan dari langkah login remaja. |
| 367 | varian konselor (lintas kelurahan, hanya oranye/merah). |
| 370 | (lihat kode di baris ini) |
| 377 | (lihat kode di baris ini) |
| 378 | (lihat kode di baris ini) |
| 379 | (lihat kode di baris ini) |
| 392 | (lihat kode di baris ini) |
| 406 | "Tampilan ringkas" menyembunyikan cuplikan |
| 407 | (lihat kode di baris ini) |
| 408 | (lihat kode di baris ini) |
| 421 | (lihat kode di baris ini) |
| 422 | (lihat kode di baris ini) |
| 427 | disengaja): desain menulis "Ringkasan kasus … akan dikirim", padahal pengiriman |
| 441 | (lihat kode di baris ini) |
| 442 | form tambah jadwal (desain hanya menampilkan daftar). |
| 451 | (lihat kode di baris ini) |
| 463 | isi notifikasi browser (tanpa nama samaran, cukup kelurahan). |
| 466 | (lihat kode di baris ini) |
| 469 | tidak ada di desain. ---------- |
| 519 | (lihat kode di baris ini) |
| 526 | (lihat kode di baris ini) |
| 546 | (lihat kode di baris ini) |
| 550 | (lihat kode di baris ini) |
| 553 | (lihat kode di baris ini) |
| 554 | (lihat kode di baris ini) |

## `frontend/src/lib/me.ts`

| Baris | Catatan |
|---|---|
| 26 | error jaringan → tetap memuat, query mencoba ulang |

## `frontend/src/pages/Chat.tsx`

| Baris | Catatan |
|---|---|
| 86 | (lihat kode di baris ini) |
| 147 | state gagal memuat tidak ada di desain |
| 172 | tawaran pendamping di luar kartu krisis memakai gaya chip. |

## `frontend/src/pages/Gated.tsx`

| Baris | Catatan |
|---|---|
| 12 | layar loading awal belum ada di desain |

## `frontend/src/pages/GuardianApproval.tsx`

| Baris | Catatan |
|---|---|
| 151 | kartu status tidak ada di desain; diturunkan dari kartu ketentuan. |

## `frontend/src/pages/Jurnal.tsx`

| Baris | Catatan |
|---|---|
| 69 | desain jurnal tidak punya kartu krisis; catatan berbahaya membuka sheet Bantuan |

## `frontend/src/pages/Landing.tsx`

| Baris | Catatan |
|---|---|
| 186 | ruang dipesan saat memuat supaya layout tidak loncat |
| 221 | halaman kebijakan privasi & kontak tim belum ada; sementara ke bagian terkait |

## `frontend/src/pages/Login.tsx`

| Baris | Catatan |
|---|---|
| 22 | desain memakai kode OTP email + Google; bingkai, judul, dan teks pembuka tetap. |

## `frontend/src/pages/PasswordReset.tsx`

| Baris | Catatan |
|---|---|
| 11 | lupa & atur ulang password tidak ada di desain; gaya diturunkan dari langkah masuk. |

## `frontend/src/pages/kota/Kota.tsx`

| Baris | Catatan |
|---|---|
| 129 | state gagal memuat. |

## `frontend/src/pages/kota/KotaLayout.tsx`

| Baris | Catatan |
|---|---|
| 21 | . |

## `frontend/src/pages/kota/StaffAccounts.tsx`

| Baris | Catatan |
|---|---|
| 9 | kelola akun staf tidak ada di desain; gaya diturunkan dari kartu & tombol dasbor kota. |

## `frontend/src/pages/staff/CaseDetail.tsx`

| Baris | Catatan |
|---|---|
| 90 | state gagal memuat detail. |
| 126 | lintasan kosong (belum ada jurnal/obrolan). |

## `frontend/src/pages/staff/Queue.tsx`

| Baris | Catatan |
|---|---|
| 128 | state gagal memuat antrian. |
| 143 | layar lebar tanpa kasus sama sekali. |

## `frontend/src/pages/staff/Schedule.tsx`

| Baris | Catatan |
|---|---|
| 80 | hapus jadwal tidak ada di desain. |
| 96 | form tambah jadwal (desain hanya menampilkan daftar); gaya dari kartu Catatan. |

## `frontend/src/pages/staff/StaffApp.tsx`

| Baris | Catatan |
|---|---|
| 176 | tombol keluar tidak ada di desain. |

## `frontend/src/pages/staff/StaffLogin.tsx`

| Baris | Catatan |
|---|---|
| 25 | login staf (email + kata sandi → TOTP) tidak ada di desain; diturunkan dari login remaja. |
