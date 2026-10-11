# KATARINA Attendance — Android PWA Pilot v0.1

**Status:** kode pilot 1 perusahaan, **belum sistem absensi produksi**, belum diinstal dan diuji di Android fisik, tidak memiliki pelacakan lokasi kontinu. Tidak untuk onboarding data karyawan sungguhan sebelum audit keamanan, kebijakan privasi dan persetujuan internal.

## Fitur yang dapat dijalankan

- Admin: membuat beberapa lokasi kantor/cabang, masing-masing dengan koordinat dan radius 20–1.000 m; membuat akun karyawan dan mengaitkan ke lokasi.
- Karyawan: login dengan password, meminta izin kamera depan dan geolocation, mengambil foto langsung, absen Masuk/Pulang. GPS harus berakurasi <=75 m dan jarak perangkat <= radius lokasi resmi dari database. Server menentukan waktu dan memvalidasi aturan.
- Rekap: admin melihat 500 catatan terbaru, karyawan 100 miliknya sendiri, unduh CSV. Foto JPEG disimpan privat (bukan static file URL); GPS dan foto hanya diambil saat tombol absen digunakan.
- Idempotency untuk submit berulang, urutan IN/OUT, session cookie HttpOnly/SameSite Strict, password hashing PBKDF2, input validasi foto dengan Pillow, CSV formula injection mitigation.
- PWA memiliki manifest/ikon/service worker, berpeluang diinstal melalui **Chrome Android** apabila dilayani oleh HTTPS dan persyaratan browser terpenuhi.

## Instalasi lokal untuk menguji, bukan publik

Gunakan Python 3.11+ dan lingkungan virtual. Di folder proyek:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m app.manage add-admin --username owner --name "Admin Usaha"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Buka `http://localhost:8000` **pada mesin yang menjalankan server**. Masuk sebagai admin, buat lokasi kerja dan akun karyawan. Karyawan masuk dengan akun masing-masing. Tidak ada akun default/password bawaan yang ditanam dalam paket.

Untuk menguji dari Android, pasang reverse proxy HTTPS yang benar (TLS valid, host/domain yang Anda kuasai) dan atur `KATARINA_FORCE_HTTPS=1`. `uvicorn` hanya listen di localhost, bukan di internet. Periksa izin kamera/lokasi; GPS via Chrome Android memerlukan secure context. Jangan membuka port 8000 secara publik.

Konfigurasi via variabel lingkungan: `KATARINA_ATTENDANCE_DB` (jalur database SQLite), `KATARINA_ATTENDANCE_PHOTOS` (direktori foto privat), `KATARINA_ATTENDANCE_TZ` (default Asia/Jakarta), `KATARINA_FORCE_HTTPS` (set 1 bila di balik TLS proxy). Jangan menyimpan `private/`, file SQLite, dan foto di GitHub atau directory yang diekspos web. Backup database dan foto secara terenkripsi.

## Pengujian

```bash
pip install pytest httpx
pytest -q
```

Skenario otomatis meliputi role admin/karyawan, validasi radius, akurasi GPS, validasi foto, urutan absen, anti-duplikat, keamanan akses foto, CSV dan logout. **Test kamera GPS real hardware** tidak digantikan oleh automated API test.

## Tidak tersedia di versi ini

1. **Shift jadwal 08.00–04.00, cuti, lembur, payroll, penggajian, rekap per hari, dan koreksi admin dengan audit trail** — perlu fase berikutnya.
2. **Multi-company tenant**, pengenalan wajah, deteksi spoofing lokasi, anti-fake-GPS, liveness — belum ada. Foto + GPS tidak menjamin pekerja berada di titik yang diklaim.
3. Otomatisasi retensi/hapus foto, ekspor data subjek, audit aktivitas admin, rate-limiting login (perlu reverse proxy), backup/recovery, uji beban, HTTPS/VPS hardening, verifikasi pada Android nyata — **harus beres sebelum dipakai pelanggan**.
4. Offline absen: bila jaringan mati, **tidak mengklaim absensi berhasil**; user perlu menghubungi pengelola untuk koreksi manual.

### Rekomendasi roadmap

HPP Studio dan jasa kustomisasi tetap menjadi fokus penjualan pertama. Setelah checkout dan pengiriman HPP benar-benar berfungsi, lakukan pengujian Attendance pilot pada 2 Android dan 1 lokasi fiktif, lalu implementasi shift lintas tanggal, kebijakan foto/retensi, koreksi+audit log, login hardening, dan penagihan SaaS berdasarkan biaya hosting/foto nyata.
