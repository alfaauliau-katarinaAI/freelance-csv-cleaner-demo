# KATARINA Attendance — Spesifikasi MVP Android (foto + titik kerja)

**Status terbaru 11 Oktober 2026: prototipe MVP single-company telah dibuat dan sembilan tes API lulus; source di [products/attendance-pilot](../products/attendance-pilot). Belum ada backend produksi, uji Android nyata, HTTPS publik, audit keamanan, atau checkout komersial.**

## Sasaran dan posisi produk

Aplikasi absen untuk UMKM dengan 3–30 karyawan: kedai kopi, laundry, toko, kos, restoran, bengkel, dan unit usaha dengan shift termasuk lintas tengah malam. Fokus kemudahan pemakaian, biaya rendah, foto saat absen, verifikasi geofence serta rekap otomatis.

## Teknologi tahap pertama

Progressive Web App (PWA) **HTTPS**: dapat dipasang dari Chrome Android ke layar utama dengan manifest dan ikon; tidak mengharuskan publikasi Play Store. Gunakan camera capture/getUserMedia untuk selfie dan Geolocation API dengan izin pengguna. PWA tetap memerlukan backend aman agar pencatatan tidak mudah dimanipulasi. APK/Play Store lewat Capacitor menjadi tahap berikutnya setelah pilot dan pengujian di perangkat.

## Alur karyawan

1. Login dengan kredensial perusahaan; hanya karyawan aktif.
2. Buka halaman *Absen Masuk* atau *Absen Pulang*; izinkan GPS dan kamera saat digunakan.
3. Perangkat mengambil koordinat, nilai akurasi (meter), dan selfie langsung dari kamera; tidak menerima unggahan galeri sebagai foto kehadiran standar.
4. Aplikasi menunjukkan titik kerja resmi, estimasi jarak, akurasi GPS, dan batas area mis. radius **100 m (nilai awal yang dapat disetel oleh admin)**.
5. Kirim foto + koordinat + presisi + ID lokasi + jenis aksi. Server mengecek geofence, autentikasi, aturan shift, anti-duplikasi dan menyimpan waktu server.
6. Tampilkan status **Berhasil** hanya setelah server mengesahkan; jika lokasi tidak cocok, GPS kurang akurat, kamera ditolak, atau jaringan gagal, tampilkan alasan jelas serta jalur permintaan koreksi admin, bukan absensi sukses palsu.

## Admin

- Pengelolaan perusahaan, cabang, daftar staf, peran dan perizinan.
- Atur lokasi kerja dari koordinat peta, radius, jam kerja, toleransi terlambat, shift 22:00–06:00, hari libur/cuti.
- Dasbor harian: hadir, terlambat, tidak hadir, jam masuk/pulang, foto, akurasi, status lokasi.
- Koreksi dengan alasan wajib dan **audit log** siapa, kapan, sebelum/sesudah.
- Ekspor CSV/XLSX periode dan rekap keterlambatan.
- Tanpa pelacakan lokasi secara terus-menerus; koordinat hanya diminta saat aksi absen.

## Kontrol fraud & keandalan

- **Semua aturan geofence diverifikasi ulang di server** (haversine) menggunakan koordinat lokasi resmi dari database, jangan percaya jarak yang dihitung frontend.
- GPS mudah dimanipulasi/mengandung error. Foto + GPS tidak menjamin kehadiran nyata. Untuk kasus berisiko tinggi, pertimbangkan liveness/device integrity dan verifikasi manual supervisor sebagai modul berikutnya.
- Tolak atau beri status 'perlu tinjauan' saat akurasi melewati ambang konfigurasi, posisi terlalu jauh, atau sinyal palsu terindikasi.
- Timestamp server, aturan urutan check-in/out, idempotency token, rate limit dan session-expiry.
- Multi-tenant isolation: data cabang/perusahaan tidak bisa dibaca tenant lain; foto privat dengan URL akses terbatas, bukan public bucket.
- Tidak memproses foto/koordinat tanpa penjelasan tujuan, kebijakan retensi, dan dasar pemrosesan yang sesuai; pastikan hak akses dan penghapusan data. Hindari *face recognition* otomatis pada MVP sampai kesiapan privasi, biaya dan akurasi dinilai.

## Entitas backend minimum

- organizations(id, name, settings)
- work_sites(id, org_id, name, lat, lng, radius_m)
- employees(id, org_id, site_id, auth_user_id, active)
- shifts(id, org_id, start_time, end_time, timezone)
- shift_assignments(id, employee_id, shift_id, work_date)
- attendance_events(id, org_id, employee_id, site_id, action, server_time, lat, lng, accuracy_m, distance_m, photo_object_key, status, idempotency_key)
- audit_logs(id, org_id, actor_id, record_id, change_reason, before, after, server_time)

## Rencana uji penerimaan MVP

- [ ] Pasang di 2 perangkat Android (Chrome); ikon dan shortcut berfungsi.
- [ ] Kamera live berfungsi, izin kamera ditolak memiliki pesan benar, file galeri tidak disamarkan sebagai selfie live.
- [ ] GPS radius di dalam/di luar dan akurasi buruk disimulasikan; server menolak posisi di luar area.
- [ ] Aksi absen dua kali cepat tidak menghasilkan dua record.
- [ ] Shift lintas hari (mis. 22:00–06:00) tercatat pada tanggal kerja yang benar.
- [ ] Karyawan hanya melihat catatan sendiri; admin cabang hanya cabangnya; tenant lain tidak bisa mengakses.
- [ ] Jaringan hilang: tidak memalsukan status berhasil, memberi pilihan coba ulang/permintaan koreksi.
- [ ] Laporan mencocokkan event tersimpan dan penyuntingan tercatat pada log.

## Strategi komersial awal

Harga **masih hipotesis**, diputuskan setelah biaya penyimpanan foto, hosting, support dan bukti kebutuhan pelanggan. Sasaran pilot 1–3 outlet sebelum paket bulanan diputuskan. Nilai jual harus melampaui fitur GPS/selfie standar yang sudah dimiliki beberapa pesaing. Potensi pembeda: satu aplikasi sederhana yang menyatukan jadwal shift lintas tengah malam, absensi foto-lokasi, ekspor gaji untuk UMKM dan dukungan lokal.

## Dev progress 11 Oktober 2026

- Backend FastAPI + SQLite (pilot satu perusahaan), login per pengguna, validasi GPS radius per titik kerja, validasi JPEG/PNG, foto privat, timestamp server, idempotency, kontrol urutan IN/OUT dan ekspor CSV telah diimplementasikan.
- PWA manifest, ikon yang dihasilkan saat startup, offline cache asset dan pengambilan selfie dengan kamera telah ditambahkan.
- Uji lokal API: **9 lulus**. Pengujian Chrome Android fisik **belum** dilakukan.
- Belum ada shift lintas tengah malam, payroll, multi-tenant, retensi otomatis, rate limit login, atau deployment HTTPS; ini masih backlog sebelum digunakan karyawan asli.
