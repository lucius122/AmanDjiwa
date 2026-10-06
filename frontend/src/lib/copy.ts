// Semua teks UI remaja (CLAUDE.md §10). Sumber: design/_unpacked/template.html.
// Yang tidak ada di desain ditandai DESIGN-GAP.

export const copy = {
  brand: {
    aman: 'Aman',
    djiwa: 'Djiwa',
    notDiagnosis: 'AmanDjiwa bukan alat diagnosis.',
    botUrl: 'https://t.me/AmanDjiwa_bot',
    botHandle: '@AmanDjiwa_bot', // handle asli dari BotFather (desain: @AmanDjiwaBot)
  },

  login: {
    back: 'Kembali',
    title: 'Hai! Yuk masuk dulu',
    lead: 'Email cuma dipakai buat login. Nggak bakal ditampilkan ke siapa pun.',
    emailLabel: 'Email kamu',
    emailPlaceholder: 'nama@email.com',
    emailError: 'Cek lagi ya, formatnya belum kayak email.',
    // DESIGN-GAP: email + password (keputusan 2026-10-06), desain memakai kode OTP + Google.
    titleRegister: 'Hai! Yuk bikin akun dulu',
    passwordLabel: 'Password',
    passwordHint: 'Minimal 8 karakter',
    passwordShort: 'Password minimal 8 karakter ya.',
    confirmLabel: 'Ulangi password',
    confirmMismatch: 'Password-nya belum sama.',
    submitLogin: 'Masuk',
    submitRegister: 'Buat akun',
    toRegister: 'Belum punya akun?',
    toRegisterLink: 'Daftar',
    toLogin: 'Sudah punya akun?',
    toLoginLink: 'Masuk',
    forgot: 'Lupa password?',
    failed: 'Lagi ada gangguan. Coba lagi sebentar ya.',
  },

  // DESIGN-GAP: lupa & atur ulang password (tidak ada di desain).
  forgot: {
    title: 'Lupa password?',
    lead: 'Tulis email akunmu. Kalau terdaftar, kami kirim tautan untuk bikin password baru.',
    submit: 'Kirim tautan',
    sent: (email: string) => `Kalau ${email} terdaftar, tautannya sudah dikirim. Cek juga folder spam ya.`,
    back: 'Kembali ke halaman masuk',
  },

  reset: {
    title: 'Bikin password baru',
    lead: 'Pakai password yang belum pernah kamu pakai di aplikasi lain.',
    submit: 'Simpan password',
    invalid: 'Tautan sudah tidak berlaku. Minta tautan baru ya.',
    done: 'Password baru tersimpan',
  },

  nav: { chat: 'Ngobrol', jurnal: 'Jurnal', aku: 'Aku' },

  chat: {
    name: 'Djiwa',
    online: 'Online',
    typing: 'lagi ngetik…',
    typingLong: 'Djiwa lagi ngetik…',
    help: 'Butuh bantuan sekarang',
    // DESIGN-GAP: popup wajib isi jurnal sebelum chat (keputusan 2026-10-06) tidak ada di desain.
    journalGate: 'Isi jurnal hari ini dulu ya, habis itu kita lanjut ngobrol. Cuma sekali sehari kok.',
    telegram: 'Telegram',
    today: 'Hari ini',
    inputLabel: 'Tulis pesan',
    inputPlaceholder: 'Tulis pesan… (coba: lagi cemas)',
    send: 'Kirim',
    chips: ['Lagi capek', 'Cemas', 'Cek perasaanku', 'Latihan napas', 'Mau cerita aja'],
    chipScreening: 'Cek perasaanku',
    chipScreeningText: 'Cek perasaanku dong (skrining)',
    chipBreathing: 'Latihan napas',
    question: (n: number, total: number) => `Pertanyaan ${n} dari ${total}`,
    skip: 'Lewati dulu',
    stop: 'Berhenti & ngobrol biasa',
    pendamping: (name?: string | null) => `${name || 'Kakak pendamping'} · pendamping`, // desain: "Kak Dimas · pendamping"
    connected: 'Pendamping sudah dikabari',
    // DESIGN-GAP: tombol lanjut skrining & tawaran pendamping di luar kartu krisis.
    followupContinue: 'Lanjut',
    followupStop: 'Berhenti',
    connectOffer: 'Hubungkan aku ke pendamping',
    sendFailed: 'Pesanmu belum terkirim. Coba lagi ya.',
    loadFailed: 'Obrolan belum bisa dimuat.',
    retry: 'Coba lagi',
    hotlineUnverified: 'Nomor layanan sedang diverifikasi. Untuk sekarang, minta dihubungkan ke pendamping ya.',
  },

  help: {
    title: 'Butuh bantuan sekarang?',
    lead: 'Pilih yang paling nyaman buat kamu.',
    pendampingLabel: 'Chat kakak pendamping',
    pendampingTitle: (kel: string) => `Kelurahan ${kel}`,
    close: 'Tutup',
  },

  telegram: {
    title: 'Lanjut di Telegram',
    lead: 'Buka bot Djiwa di Telegram, lalu kirim kode ini supaya obrolanmu nyambung.',
    open: 'Buka Telegram',
    // DESIGN-GAP
    loading: '······',
    failed: 'Kode belum bisa dibuat. Coba lagi sebentar ya.',
  },

  breathing: {
    title: 'Napas 4-7-8',
    phases: { Tarik: 'Tarik 4', Tahan: 'Tahan 7', Buang: 'Buang 8' },
    seconds: (n: number) => `${n} detik`,
    done: 'Selesai',
    doneSub: 'Kerja bagus!',
    hint: 'Ikuti lingkarannya. Kalau pusing, napas biasa aja dulu ya.',
    round: (n: number) => `Putaran ${n} dari 4`,
    pause: 'Jeda',
    resume: 'Lanjut',
    again: 'Ulangi',
  },

  landing: {
    skip: 'Lewati ke konten utama', // aksesibilitas (tidak terlihat sampai difokus)
    nav: { how: 'Cara kerja', privacy: 'Privasi', help: 'Bantuan darurat', login: 'Masuk' },
    badge: 'Untuk remaja Semarang, 13–19 tahun',
    title: 'Cerita aja, kamu nggak sendirian',
    lead: 'Djiwa siap dengerin kapan aja. Nggak ada yang nge-judge, dan kamu bisa pakai nama samaran.',
    cta: 'Mulai ngobrol',
    telegram: 'Lewat Telegram',
    heroAlt: 'Remaja tersenyum tenang sambil memegang HP dan ngobrol dengan Djiwa',
    howTitle: 'Cara kerjanya',
    steps: [
      { n: '01', title: 'Ngobrol', body: 'Ceritain apa aja ke Djiwa. Lewat web atau Telegram.' },
      { n: '02', title: 'Kenali perasaanmu', body: 'Djiwa bantu kamu kasih nama ke yang kamu rasain.' },
      { n: '03', title: 'Terhubung dengan pendamping', body: 'Kalau kamu butuh, kakak pendamping di kelurahanmu siap bantu.' },
    ],
    privacyTitle: 'Privasimu aman',
    privacy: [
      { title: 'Nama samaran', body: 'Nggak perlu nama asli atau foto.' },
      { title: 'Data terenkripsi', body: 'Obrolanmu disimpan dengan aman.' },
      { title: 'Hapus kapan aja', body: 'Datamu, kamu yang pegang kendali.' },
    ],
    notDiagnosisBold: 'AmanDjiwa bukan alat diagnosis.',
    notDiagnosisRest:
      ' Djiwa bantu kamu mengenali perasaan lebih awal. Untuk diagnosis, tetap perlu psikolog atau tenaga kesehatan. Kami bisa bantu hubungkan.',
    helpTitle: 'Butuh bantuan sekarang?',
    helpLead: 'Kamu bisa langsung hubungi salah satu ini. Gratis.',
    hotlineLoadFailed: 'Nomor bantuan belum bisa dimuat. Muat ulang halaman ya.', // DESIGN-GAP
    // DESIGN-GAP: nomor belum diverifikasi (hotlines.yaml masih TODO_VERIFY)
    hotlineUnverified:
      'Nomor layanan sedang diverifikasi. Sementara itu, kamu bisa mulai ngobrol dan minta dihubungkan ke kakak pendamping.',
    // Tambahan yang disetujui 2026-10-05: CTA penutup sebelum footer.
    closingTitle: 'Siap mulai cerita?',
    closingBody: 'Pakai nama samaran, gratis, dan kamu bisa berhenti kapan aja.',
    tagline: 'Bagian dari program Semarang Smart City.',
    supportedBy: 'Didukung oleh',
    partners: ['Karang Taruna Semarang Barat', 'Universitas Semarang'], // teks sampai ada file logo resmi
    privacyPolicy: 'Kebijakan privasi',
    contact: 'Kontak',
  },

  register: {
    welcome: (nick: string) => `Selamat datang, ${nick}!`,
    failed: 'Lagi ada gangguan. Coba lagi sebentar ya.', // DESIGN-GAP
    profileTitle: 'Kamu mau dipanggil apa?',
    profileLead: 'Pakai nama samaran aja. Nggak perlu nama asli.',
    nickLabel: 'Nama samaran',
    nickPlaceholder: 'Contoh: Bintang Senja',
    nickError: 'Pakai nama samaran aja, tanpa email atau nomor HP.', // DESIGN-GAP (validasi)
    random: 'Acak',
    randomFirst: ['Bintang', 'Langit', 'Awan', 'Pelangi', 'Embun', 'Ombak', 'Senja', 'Bulan'],
    randomSecond: ['Senja', 'Biru', 'Teduh', 'Pagi', 'Kecil', 'Tenang', 'Jingga'],
    avatarLabel: 'Pilih avatar',
    avatarNames: ['Bintang', 'Bulan', 'Matahari', 'Daun', 'Awan', 'Hati', 'Musik', 'Ombak'],
    kelLabel: 'Kelurahan',
    kelSuffix: '· Semarang Barat',
    kelPlaceholder: 'Pilih kelurahan',
    kelSheetTitle: 'Pilih kelurahan',
    kelSheetSub: 'Kecamatan Semarang Barat',
    yearLabel: 'Tahun lahir',
    next: 'Lanjut',
    consentTitle: 'Sebelum mulai, ini janji kami',
    consent: [
      { title: 'Yang kami simpan', body: 'Nama samaran, kelurahan, tahun lahir, obrolan, dan jurnal emosimu.' },
      { title: 'Siapa yang bisa lihat', body: 'Cuma kamu. Pemkot hanya lihat angka total, tanpa nama.' },
      {
        title: 'Demi keselamatanmu',
        body: 'Kalau ada pesan yang menunjukkan kamu dalam bahaya, kakak pendamping akan membacanya untuk bantu kamu.',
      },
      { title: 'Kamu bisa berhenti', body: 'Hapus akun dan semua datamu kapan aja.' },
    ],
    agree: 'Aku sudah baca dan paham.',
    agreeSubmit: 'Aku setuju',
    guardianTitle: 'Satu langkah lagi',
    guardianLead: 'Karena kamu belum 18 tahun, kami perlu izin orang tua atau wali kamu dulu.',
    guardianEmailLabel: 'Email orang tua / wali',
    guardianEmailPlaceholder: 'email.ortu@email.com',
    guardianEmailError: 'Cek lagi ya, formatnya belum kayak email.',
    guardianInfoTitle: 'Yang orang tuamu terima',
    guardianInfo1: 'Email berisi penjelasan AmanDjiwa dan tombol persetujuan.',
    guardianInfo2Bold: 'Mereka nggak bisa baca obrolanmu',
    guardianInfo2Rest: ', dan nggak lihat nama samaranmu.',
    guardianSubmit: 'Kirim permintaan izin',
  },

  waiting: {
    illustrationAlt: 'Remaja duduk santai sementara amplop surat terbang ke orang tuanya',
    title: 'Menunggu persetujuan orang tua',
    bodyBefore: 'Kami sudah kirim email ke ',
    bodyAfter: '. Begitu disetujui, kamu langsung bisa ngobrol sama Djiwa.',
    bodyNoEmail: 'Kami sudah kirim email ke orang tua atau walimu. Begitu disetujui, kamu langsung bisa ngobrol sama Djiwa.', // DESIGN-GAP (setelah muat ulang)
    sent: 'Email terkirim',
    resend: 'Kirim ulang email',
    resent: (email: string) => `Email dikirim ulang ke ${email}`,
    change: 'Ganti email orang tua',
    emergency: 'Butuh bantuan sekarang? Layanan darurat tetap bisa kamu hubungi: ',
    approved: 'Orang tua sudah menyetujui. Selamat datang!',
  },

  // Halaman orang tua: bahasa formal ("Anda"), sesuai desain.
  guardian: {
    program: 'Program Semarang Smart City',
    kicker: 'Persetujuan Orang Tua / Wali',
    title: 'Permohonan izin penggunaan layanan AmanDjiwa',
    lead: 'Bapak/Ibu yang kami hormati, putra/putri Anda telah mendaftar di AmanDjiwa dan memerlukan persetujuan Anda untuk melanjutkan.',
    terms: [
      { title: 'Tentang layanan', body: 'AmanDjiwa adalah layanan skrining dini kesehatan mental bagi remaja Kota Semarang. Layanan ini bukan alat diagnosis medis.' },
      { title: 'Data yang dikumpulkan', body: 'Nama samaran, kelurahan, tahun lahir, isi percakapan, dan jurnal emosi. Seluruh data disimpan terenkripsi.' },
      { title: 'Kerahasiaan', body: 'Isi percakapan tidak dibagikan kepada orang tua maupun pihak sekolah. Pemerintah Kota hanya menerima data agregat tanpa identitas.' },
      {
        title: 'Penanganan risiko tinggi',
        body: 'Apabila terdeteksi pesan berisiko tinggi, pendamping sebaya atau konselor terlatih akan membaca pesan tersebut dan menindaklanjuti demi keselamatan anak. Setiap akses tercatat.',
      },
      { title: 'Hak Anda', body: 'Anda dapat mencabut persetujuan sewaktu-waktu melalui tautan di email ini.' },
    ],
    nameLabel: 'Nama lengkap orang tua / wali',
    namePlaceholder: 'Nama lengkap',
    relationLabel: 'Hubungan dengan anak',
    relations: [
      { value: 'orang_tua', label: 'Orang tua' },
      { value: 'wali', label: 'Wali' },
    ],
    agree:
      'Saya telah membaca dan memahami ketentuan di atas, serta menyetujui putra/putri saya menggunakan layanan AmanDjiwa.',
    approve: 'Berikan persetujuan',
    decline: 'Tidak setuju',
    contact: 'Pertanyaan? Hubungi tim AmanDjiwa di [ kontak ]', // TODO_VERIFY: kontak tim
    // DESIGN-GAP: state di bawah tidak ada di desain.
    loading: 'Memuat…',
    failed: 'Terjadi gangguan. Silakan coba lagi.',
    invalidTitle: 'Tautan tidak valid',
    invalidBody: 'Pastikan Anda membuka tautan dari email terbaru AmanDjiwa.',
    expiredTitle: 'Tautan sudah kedaluwarsa',
    expiredBody: 'Silakan minta putra/putri Anda mengirim ulang permintaan izin dari aplikasi.',
    approvedTitle: 'Persetujuan sudah diberikan',
    approvedBody:
      'Terima kasih. Putra/putri Anda sekarang dapat menggunakan AmanDjiwa. Anda dapat mencabut persetujuan ini kapan saja melalui tautan yang sama.',
    revoke: 'Cabut persetujuan',
    revokedTitle: 'Persetujuan sudah dicabut',
    revokedBody: 'Putra/putri Anda tidak dapat menggunakan layanan sampai ada persetujuan baru.',
    declinedTitle: 'Persetujuan tidak diberikan',
    declinedBody: 'Terima kasih atas tanggapan Anda. Putra/putri Anda belum dapat menggunakan layanan ini.',
  },

  jurnal: {
    title: 'Hari ini kamu ngerasa apa?',
    emotionsLabel: 'Emosi hari ini',
    // Urutan & nama sesuai desain; kunci = label model (Emotion di backend).
    emotions: {
      senang: 'Senang',
      sedih: 'Sedih',
      cemas: 'Cemas',
      marah: 'Marah',
      malu_bersalah: 'Malu',
      netral: 'Biasa aja',
    },
    intensityLabel: 'Seberapa kuat rasanya?',
    intensity: ['Sedikit', 'Agak', 'Lumayan', 'Kuat', 'Banget'],
    intensityMin: 'Sedikit',
    intensityMax: 'Banget',
    noteLabel: 'Mau nulis sesuatu?',
    noteOptional: '(opsional)',
    notePlaceholder: 'Apa yang bikin kamu ngerasa gini?',
    save: 'Simpan jurnal',
    update: 'Perbarui jurnal',
    saved: 'Jurnal hari ini tersimpan',
    historyTitle: '14 hari terakhir',
    notFilled: 'Belum diisi',
    insightCemas: 'Belakangan kamu lebih sering ngerasa cemas. Itu wajar. Mau coba latihan napas?',
    insightTop: (name: string) => `Belakangan kamu paling sering ngerasa ${name.toLowerCase()}. Terus isi jurnal ya.`,
    insightEmpty: 'Isi jurnal tiap hari ya, nanti polanya kelihatan di sini.', // DESIGN-GAP (belum ada entri)
    exercisesTitle: 'Latihan buat kamu',
    breathingTitle: 'Napas 4-7-8',
    breathingBody: 'Tarik 4 detik, tahan 7, buang 8. Bantu tenangin badan.',
    breathingTime: '± 1 menit',
    groundingBadge: '5·4·3',
    groundingTitle: 'Grounding 5-4-3-2-1',
    groundingBody: 'Kenali sekelilingmu pakai 5 indra. Pas buat saat panik.',
    groundingTime: '± 3 menit',
    saveFailed: 'Jurnal belum tersimpan. Coba lagi ya.', // DESIGN-GAP
    loadFailed: 'Jurnal belum bisa dimuat.', // DESIGN-GAP
  },

  grounding: {
    title: 'Grounding 5-4-3-2-1',
    lead: 'Pelan-pelan aja. Sebutin dalam hati, lalu tekan Lanjut.',
    steps: [
      { n: 5, title: 'Hal yang bisa kamu lihat', example: 'Lampu, jendela, sepatu…' },
      { n: 4, title: 'Hal yang bisa kamu sentuh', example: 'Kain baju, meja…' },
      { n: 3, title: 'Suara yang bisa kamu dengar', example: 'Kipas angin, motor lewat…' },
      { n: 2, title: 'Bau yang bisa kamu cium', example: 'Sabun, teh…' },
      { n: 1, title: 'Rasa yang bisa kamu kecap', example: 'Air putih, permen…' },
    ],
    next: 'Lanjut',
    done: 'Selesai',
    finished: 'Mantap, kamu udah selesai grounding',
  },

  aku: {
    age: (n: number) => `${n} tahun`,
    privacyTitle: 'Privasimu',
    privacyBody:
      'Obrolan dan jurnalmu cuma bisa kamu lihat. Pesan yang menunjukkan kamu dalam bahaya akan dibaca kakak pendamping, dan setiap aksesnya tercatat.',
    telegram: 'Sambungkan ke Telegram',
    help: 'Butuh bantuan sekarang',
    delete: 'Hapus semua dataku',
    logout: 'Keluar',
    loggedOut: 'Kamu sudah keluar',
  },

  deleteSheet: {
    title: 'Hapus semua datamu?',
    body: 'Obrolan, jurnal, dan profilmu akan dihapus permanen. Ini nggak bisa dibatalkan.',
    confirm: 'Ya, hapus semua',
    cancel: 'Batal',
    done: 'Semua datamu sudah dihapus',
    failed: 'Datamu belum terhapus. Coba lagi ya.', // DESIGN-GAP
  },

  // ---------- dasbor staf (pendamping / konselor) ----------
  staffLogin: {
    // DESIGN-GAP: halaman login staf tidak ada di desain; diturunkan dari langkah login remaja.
    title: 'Masuk dasbor staf',
    lead: 'Khusus pendamping dan konselor AmanDjiwa.',
    email: 'Email',
    password: 'Kata sandi',
    submit: 'Lanjut',
    totpLabel: 'Kode autentikator',
    totpLead: 'Buka aplikasi autentikator lalu masukkan 6 digit kodenya.',
    totpSubmit: 'Masuk',
    failed: 'Belum bisa masuk. Coba lagi.',
    // Login pertama (akun dibuat/di-reset admin kota): pasang authenticator + password baru.
    setupTitle: 'Atur akunmu dulu',
    setupLead: 'Ini login pertamamu. Pasang aplikasi authenticator di HP, lalu buat password baru.',
    setupKeyLabel: 'Kunci penyiapan',
    setupKeyHelp:
      'Di aplikasi authenticator (Google Authenticator, Aegis, atau Microsoft Authenticator) pilih "Masukkan kunci penyiapan", lalu ketik kunci ini. Jenis: berbasis waktu.',
    setupOpenApp: 'Buka di aplikasi authenticator (HP)',
    newPassword: 'Password baru',
    newPasswordHint: 'Minimal 12 karakter, beda dari password sementara.',
    confirmPassword: 'Ulangi password baru',
    passwordShort: 'Password baru minimal 12 karakter.',
    passwordMismatch: 'Password baru belum sama.',
    setupCode: 'Kode 6 digit dari aplikasi',
    setupSubmit: 'Simpan & masuk',
  },

  staff: {
    roleLabel: { pendamping: 'Pendamping', konselor: 'Konselor', admin_kota: 'Dinkes Kota', remaja: '' },
    nav: { antrian: 'Antrian kasus', riwayat: 'Riwayat', jadwal: 'Jadwal', pengaturan: 'Pengaturan' },
    scopeSide: (kel: string) => `Kamu hanya melihat kasus di Kelurahan ${kel}.`,
    scopeTop: (name: string, kel: string) => `${name} · hanya kasus Kelurahan ${kel}`,
    // DESIGN-GAP: varian konselor (lintas kelurahan, hanya oranye/merah).
    scopeSideKonselor: 'Kamu melihat kasus oranye dan merah di semua kelurahan.',
    scopeTopKonselor: (name: string) => `${name} · kasus oranye & merah semua kelurahan`,
    logout: 'Keluar', // DESIGN-GAP
    queueTitle: 'Antrian kasus',
    historyTitle: 'Riwayat kasus',
    tabs: { semua: 'Semua', baru: 'Baru', ditangani: 'Sedang ditangani' },
    newBadge: 'BARU MASUK',
    priority: (since: string) => `${since} sejak terdeteksi · prioritas`,
    empty: 'Tidak ada kasus di sini.',
    loadFailed: 'Antrian belum bisa dimuat.', // DESIGN-GAP
    retry: 'Coba lagi', // DESIGN-GAP
    pickCase: 'Pilih kasus di antrian untuk melihat detailnya.', // DESIGN-GAP
    risk: { merah: 'Merah', oranye: 'Oranye', kuning: 'Kuning' },
    riskPrefix: 'Risiko',
    status: { baru: 'Baru', ditangani: 'Sedang ditangani', selesai: 'Selesai', dirujuk: 'Dirujuk' },
  },

  caseDetail: {
    back: 'Kembali',
    subline: (kel: string, age: number | null, at: string, since: string) =>
      `${kel}${age ? ` · ${age} tahun` : ''} · terdeteksi ${at} (${since})`,
    trajectory: 'Lintasan emosi 14 hari',
    trajectorySource: 'jurnal + obrolan',
    trajectoryAxis: '↑ positif · ↓ negatif',
    trajectoryEmpty: 'Belum ada data emosi.', // DESIGN-GAP
    dominant: 'Emosi dominan',
    dominantDays: (name: string, days: number) => `${name} · ${days} hari`,
    severity: {
      minimal: 'Minimal',
      ringan: 'Ringan',
      sedang: 'Sedang',
      sedang_berat: 'Sedang-berat',
      berat: 'Berat',
    },
    incomplete: 'Belum lengkap',
    markers: 'Penanda yang terdeteksi',
    snippets: 'Cuplikan pesan pemicu',
    accessLogged: (name: string, at: string) => `Akses tercatat · ${name}, ${at}`,
    showSnippets: 'Tampilkan cuplikan pesan', // DESIGN-GAP: "Tampilan ringkas" menyembunyikan cuplikan
    showSnippetsNote: 'Membuka cuplikan akan tercatat.', // DESIGN-GAP
    snippetsEmpty: 'Kasus ini terdeteksi dari jurnal atau skrining. Isinya tetap privat.', // DESIGN-GAP
    snippetsFooter: 'Hanya pesan yang memicu deteksi yang ditampilkan. Obrolan lain tetap privat.',
    notes: 'Catatan tindak lanjut',
    notePlaceholder: 'Tulis apa yang sudah dilakukan dan rencana berikutnya…',
    saveNote: 'Simpan catatan',
    contacted: 'Sudah dihubungi',
    markDone: 'Tandai selesai',
    refer: 'Rujuk ke Puskesmas/Psikolog',
    referredTo: (dest: string) => `Dirujuk ke ${dest}`,
    toastNote: 'Catatan disimpan',
    toastContacted: 'Status: sedang ditangani',
    toastDone: 'Kasus ditandai selesai',
    toastReferred: (dest: string) => `Rujukan ke ${dest} dicatat`, // lihat referSheet.lead
    actionFailed: 'Belum tersimpan. Coba lagi.', // DESIGN-GAP
    loadFailed: 'Detail kasus belum bisa dimuat.', // DESIGN-GAP
  },

  referSheet: {
    title: (name: string) => `Rujuk ${name}`,
    // DESIGN-GAP (disengaja): desain menulis "Ringkasan kasus … akan dikirim", padahal pengiriman
    // otomatis belum ada (protokol & persetujuan remaja belum diputuskan tim). Pendamping tidak boleh
    // mengira tujuan rujukan sudah dikabari.
    lead: 'Pilih tujuan rujukan. Rujukan dicatat di kasus ini; untuk sekarang hubungi tujuannya langsung.',
    // TODO_VERIFY: daftar tujuan rujukan resmi per kelurahan (dari desain, belum diverifikasi).
    targets: [
      { label: 'Puskesmas Krobokan', sub: 'Poli jiwa · Senin–Sabtu' },
      { label: 'Psikolog mitra USM', sub: 'Konseling gratis untuk remaja' },
      { label: 'Konselor BK sekolah', sub: 'Dengan persetujuan remaja' },
    ],
  },

  schedule: {
    title: 'Jadwal tindak lanjut',
    empty: 'Belum ada jadwal.', // DESIGN-GAP
    // DESIGN-GAP: form tambah jadwal (desain hanya menampilkan daftar).
    add: 'Tambah jadwal',
    titleLabel: 'Kegiatan',
    titlePlaceholder: 'Mis. Ketemu Awan Teduh · balai RW 03',
    date: 'Tanggal',
    start: 'Mulai',
    end: 'Selesai (opsional)',
    save: 'Simpan jadwal',
    saved: 'Jadwal disimpan',
    remove: (title: string) => `Hapus jadwal ${title}`, // DESIGN-GAP
    removed: 'Jadwal dihapus',
    failed: 'Jadwal belum tersimpan. Coba lagi.',
  },

  staffSettings: {
    title: 'Pengaturan',
    items: {
      notif_red: { title: 'Notifikasi kasus merah', body: 'Kirim push notif saat ada kasus risiko merah baru.' },
      sound: { title: 'Bunyi peringatan', body: 'Putar suara saat kasus merah masuk.' },
      compact: { title: 'Tampilan ringkas', body: 'Sembunyikan cuplikan pesan sampai diklik.' },
    },
    // DESIGN-GAP: isi notifikasi browser (tanpa nama samaran, cukup kelurahan).
    notifyTitle: 'Kasus merah baru',
    notifyBody: (kel: string) => `Ada kasus risiko merah baru di ${kel}. Buka antrian.`,
    failed: 'Pengaturan belum tersimpan.', // DESIGN-GAP
  },

  // ---------- kelola akun staf (admin kota). DESIGN-GAP: tidak ada di desain. ----------
  kotaNav: { summary: 'Ringkasan', accounts: 'Akun staf' },
  staffAdmin: {
    title: 'Akun staf',
    lead: 'Tambah akun pendamping, konselor, atau admin kota. Staf baru memasang authenticator dan membuat password sendiri saat login pertama.',
    addTitle: 'Tambah akun',
    name: 'Nama tampil',
    namePlaceholder: 'Mis. Kak Rina',
    email: 'Email kerja',
    role: 'Peran',
    roles: { pendamping: 'Pendamping', konselor: 'Konselor', admin_kota: 'Admin kota' },
    kelurahan: 'Kelurahan',
    kelurahanPick: 'Pilih kelurahan',
    add: 'Tambah akun',
    tempTitle: (name: string) => `Password sementara untuk ${name}`,
    tempBody:
      'Berikan langsung ke orangnya (jangan lewat grup). Password ini hanya ditampilkan sekali. Saat login pertama di /staf/masuk, staf wajib menggantinya dan memasang authenticator.',
    copy: 'Salin',
    copied: 'Password disalin',
    close: 'Sudah dicatat',
    listTitle: 'Daftar akun',
    active: 'Aktif',
    disabled: 'Nonaktif',
    needsSetup: 'Belum login pertama',
    disable: 'Nonaktifkan',
    enable: 'Aktifkan',
    reset: 'Reset',
    resetConfirm: (name: string) =>
      `Reset akun ${name}? Password lama dan authenticator-nya tidak berlaku lagi; ${name} harus login pertama ulang.`,
    created: 'Akun dibuat',
    failed: 'Belum berhasil. Coba lagi.',
    loadFailed: 'Daftar akun belum bisa dimuat.',
  },

  // ---------- dasbor kota (hanya agregat) ----------
  kota: {
    subtitle: 'Dasbor Kota · Kec. Semarang Barat',
    title: 'Ringkasan kesehatan mental remaja',
    ranges: [
      { label: '4 minggu', weeks: 4 },
      { label: '8 minggu', weeks: 8 },
      { label: '3 bulan', weeks: 13 },
    ],
    exportPdf: 'Ekspor policy brief (PDF)',
    notice: (k: number) => `Data agregat anonim. Kelurahan dengan < ${k} pengguna disembunyikan.`,
    noticeSub: 'Tidak ada isi chat atau identitas individu.',
    noticeDemo: 'Semua angka adalah data contoh.', // hanya saat DEMO_MODE (seed sintetis)
    kpi: {
      active: 'Pengguna aktif',
      activeChange: (p: number) => `${p >= 0 ? '+' : ''}${p}% dari periode sebelumnya`,
      activeNoPrev: 'Periode sebelumnya belum cukup data', // DESIGN-GAP
      sessions: 'Sesi',
      sessionsNote: (avg: string) => `Rata-rata ${avg} sesi per pengguna`,
      handled: 'Kasus tertangani < 15 menit',
      handledNote: 'Target 90%',
      referrals: 'Jumlah rujukan',
      referralsNote: 'Puskesmas & psikolog',
      hidden: (k: number) => `Belum cukup data (< ${k} pengguna)`, // DESIGN-GAP
    },
    mapTitle: 'Proporsi risiko per kelurahan',
    mapSub: '% pengguna level oranye + merah',
    modes: { peta: 'Peta', tabel: 'Tabel' },
    hidden: 'Disembunyikan',
    tileAria: (name: string, pct: number | null) => `${name}: ${pct === null ? 'disembunyikan' : `${pct}% berisiko`}`,
    tableKel: 'Kelurahan',
    tableUsers: 'Pengguna',
    tableRisk: 'Berisiko',
    fewUsers: (k: number) => `< ${k}`,
    selUsers: (u: string) => `${u} pengguna`,
    selRisk: (label: string) => `${label} berisiko`,
    showAll: 'Tampilkan semua',
    legend: ['< 7%', '7–10%', '11–14%', '≥ 15%'],
    distTitle: 'Distribusi level risiko',
    distSub: 'urut dari merah tertinggi',
    levels: { hijau: 'Hijau', kuning: 'Kuning', oranye: 'Oranye', merah: 'Merah' },
    distTip: (name: string, l: Record<'hijau' | 'kuning' | 'oranye' | 'merah', number>) =>
      `${name}: hijau ${l.hijau}%, kuning ${l.kuning}%, oranye ${l.oranye}%, merah ${l.merah}%`,
    distEmpty: 'Belum ada kelurahan dengan ≥ 10 pengguna.', // DESIGN-GAP
    trendTitle: 'Tren emosi mingguan',
    trendSub: '% entri jurnal per emosi',
    week: (w: string) => `Minggu ${w}`,
    weekHidden: (k: number) => `Data minggu ini disembunyikan (< ${k} pengguna).`, // DESIGN-GAP
    topicsTitle: 'Topik pemicu teratas',
    topicsSub: 'klasifikasi otomatis',
    topicsEmpty: (k: number) => `Belum cukup data (< ${k} pengguna).`, // DESIGN-GAP
    loadFailed: 'Data dasbor belum bisa dimuat.', // DESIGN-GAP
    retry: 'Coba lagi',
  },
} as const;
