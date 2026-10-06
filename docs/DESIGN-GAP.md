# Daftar DESIGN-GAP

Layar, keadaan, atau teks yang **tidak ada di `design/`** sehingga diturunkan sendiri dari komponen
yang sudah ada (CLAUDE.md §2). Mohon direview desainer/tim. Dibuat otomatis dari komentar
`DESIGN-GAP` di kode (06-10-2026); perbarui dengan:

```bash
git grep -n DESIGN-GAP -- backend/app frontend/src
```

## `backend/app/config/emails.yaml`

| Baris | Catatan |
|---|---|
| 1 | isi email ke orang tua tidak ada di design/. Diturunkan dari halaman |
| 22 | tidak ada di desain. TODO_VERIFY: review tim. ---------- |

## `backend/app/config/response_bank.yaml`

| Baris | Catatan |
|---|---|
| 3 | . TODO_VERIFY: SEMUA teks wajib divalidasi psikolog sebelum rilis. |
| 8 | tidak ada di desain. |
| 25 | variasi kedua tidak ada di desain. |
| 30 | balasan "sedih" tidak ada di desain. |
| 51 | tidak ada di desain. |
| 59 | desain hanya punya versi pendamping; versi konselor (lintas kelurahan). |

## `backend/app/config/screening.yaml`

| Baris | Catatan |
|---|---|
| 2 | item lain ditulis dengan gaya bahasa yang sama (adaptasi PHQ-9 / GAD-7). |
| 27 | tawaran lanjut (alur bertahap, keputusan 2026-10-05) tidak ada di desain. |

## `backend/app/config/telegram.yaml`

| Baris | Catatan |
|---|---|
| 1 | tidak ada desain Telegram; diturunkan dari copy web. |
| 16 | + TODO_VERIFY. Bisa dimatikan: /pengingat |

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
| 29 | state error & belum dikonfigurasi tidak ada di desain. |
| 57 | tombol lanjut skrining & tawaran pendamping di luar kartu krisis. |
| 79 | (lihat kode di baris ini) |
| 123 | (lihat kode di baris ini) |
| 124 | nomor belum diverifikasi (hotlines.yaml masih TODO_VERIFY) |
| 139 | (lihat kode di baris ini) |
| 144 | validasi) |
| 186 | setelah muat ulang) |
| 223 | state di bawah tidak ada di desain. |
| 266 | belum ada entri) |
| 275 | (lihat kode di baris ini) |
| 276 | (lihat kode di baris ini) |
| 312 | (lihat kode di baris ini) |
| 317 | halaman login staf tidak ada di desain; diturunkan dari langkah login remaja. |
| 334 | varian konselor (lintas kelurahan, hanya oranye/merah). |
| 337 | (lihat kode di baris ini) |
| 344 | (lihat kode di baris ini) |
| 345 | (lihat kode di baris ini) |
| 346 | (lihat kode di baris ini) |
| 359 | (lihat kode di baris ini) |
| 373 | "Tampilan ringkas" menyembunyikan cuplikan |
| 374 | (lihat kode di baris ini) |
| 375 | (lihat kode di baris ini) |
| 388 | (lihat kode di baris ini) |
| 389 | (lihat kode di baris ini) |
| 394 | disengaja): desain menulis "Ringkasan kasus … akan dikirim", padahal pengiriman |
| 408 | (lihat kode di baris ini) |
| 409 | form tambah jadwal (desain hanya menampilkan daftar). |
| 418 | (lihat kode di baris ini) |
| 430 | isi notifikasi browser (tanpa nama samaran, cukup kelurahan). |
| 433 | (lihat kode di baris ini) |
| 452 | (lihat kode di baris ini) |
| 459 | (lihat kode di baris ini) |
| 479 | (lihat kode di baris ini) |
| 483 | (lihat kode di baris ini) |
| 486 | (lihat kode di baris ini) |
| 487 | (lihat kode di baris ini) |

## `frontend/src/lib/me.ts`

| Baris | Catatan |
|---|---|
| 27 | error jaringan → tetap memuat, query mencoba ulang |

## `frontend/src/pages/Chat.tsx`

| Baris | Catatan |
|---|---|
| 84 | (lihat kode di baris ini) |
| 145 | state gagal memuat tidak ada di desain |
| 170 | tawaran pendamping di luar kartu krisis memakai gaya chip. |

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
| 61 | peringatan konfigurasi untuk lingkungan dev |

## `frontend/src/pages/kota/Kota.tsx`

| Baris | Catatan |
|---|---|
| 124 | tombol keluar tidak ada di desain. |
| 174 | state gagal memuat. |

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
| 18 | login staf (email + kata sandi → TOTP) tidak ada di desain; diturunkan dari login remaja. |
