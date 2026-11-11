# Epson Resetter & Maintenance Utility

Utilitas desktop cross-platform berbasis Python dan Qt untuk membaca telemetri, merawat komponen cetak mekanis, dan mereset Waste Ink Pad Counter pada printer Epson L3110 Series melalui koneksi USB langsung tanpa driver khusus (driverless).

Program ini dikembangkan secara independen dan bersih (clean-room) untuk mendukung transparansi teknis, perawatan mandiri perangkat keras, dan keberlanjutan pemakaian printer.

---

## Fitur Utama

- Pembacaan Counter Waste Ink: Menampilkan poin dan persentase kapasitas penampung tinta pembuangan utama (Main Pad) serta borderless (Platen Pad).
- Reset Waste Ink Counter: Prosedur reset nilai counter dengan validasi keselamatan dan verifikasi pasca-restart perangkat.
- Pemeliharaan Head Cetak (Maintenance Suite):
  - Nozzle Check: Mencetak pola uji nozel untuk memeriksa kelancaran seluruh saluran warna dan hitam.
  - Head Cleaning: Membersihkan saluran head cetak melalui siklus pompa hisap standar.
  - Power Cleaning: Pembersihan intensif bertekanan tinggi untuk mengatasi nozel yang tersumbat berat, dilengkapi pengaman volume tinta dan ambang batas penampung limbah.
  - Print Head Alignment: Mencetak lembar evaluasi keselarasan serta menyimpan nilai kalibrasi posisi head cetak.
- Diagnostik Koneksi & Perangkat: Pengujian bertahap konektivitas USB fisik, negosiasi mode paket IEEE 1284.4, dan alokasi saluran perintah.
- Riwayat Perawatan (History Log): Pencatatan audit otomatis seluruh operasi pemeliharaan ke dalam basis data lokal SQLite dengan opsi ekspor ke format CSV dan JSON.
- Antarmuka Modern & Mode CLI: GUI berbasis tema gelap ergonomis dan responsif, serta dukungan baris perintah (CLI) untuk diagnostik cepat tanpa tampilan grafis.

---

## Kebutuhan Sistem

- Sistem Operasi: Linux (Arch, Ubuntu, Debian, Fedora, openSUSE, dll.) atau Windows 10 / Windows 11 (64-bit).
- Python: Versi 3.10 atau yang lebih baru.
- Pustaka Sistem: libusb-1.0 (standar pada distribusi Linux; disertakan pada Windows).
- Perangkat: Printer terhubung secara fisik melalui kabel USB ke komputer.

---

## Instalasi

1. Kloning repositori ini:
```bash
git clone https://github.com/USERNAME/epson-resetter.git
cd epson-resetter
```

2. Pasang dependensi pustaka:
```bash
pip install -r requirements.txt
```

Catatan Konfigurasi Linux (Akses Non-Root):
Agar aplikasi dapat berkomunikasi langsung dengan antarmuka USB tanpa memerlukan perintah sudo, pasang aturan udev berikut:
```bash
sudo cp scripts/99-epson-l3110.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

---

## Cara Penggunaan

### 1. Menjalankan Antarmuka Grafis (Desktop GUI)
```bash
python3 app/main.py
```

Navigasi menu aplikasi:
- Dashboard: Status koneksi printer, ringkasan kapasitas bantalan limbah, dan statistik cetak.
- Diagnostics: Pengujian otomatis kesiapan komunikasi perangkat.
- Waste Counter: Informasi rinci kapasitas dan tingkat kesehatan bantalan tinta.
- Reset Utility: Prosedur reset counter limbah tinta terverifikasi.
- Maintenance: Eksekusi Nozzle Check, Head Cleaning, Power Cleaning, dan Alignment.
- History: Catatan riwayat perawatan lokal dan ekspor data.

### 2. Menjalankan Mode Baris Perintah (CLI Headless)
- Membaca data counter dan informasi perangkat:
```bash
python3 app/main.py --counters
```

- Menjalankan uji diagnostik hardware:
```bash
python3 app/main.py --diagnostics
```

### 3. Prosedur Reset Waste Ink Pad Counter
1. Pastikan printer terhubung melalui kabel USB dan dalam kondisi menyala.
2. Buka tab Reset Utility pada aplikasi.
3. Lakukan pembersihan atau penggantian fisik bantalan spon penampung tinta di bagian belakang bawah printer agar tinta tidak meluap.
4. Centang persetujuan konfirmasi fisik spon, lalu tekan tombol reset.
5. Ketika lampu indikator pada tombol printer berkedip bersamaan (menandakan printer meminta reboot fisik), tekan tombol Power pada printer untuk mematikan perangkat.
6. Nyalakan kembali printer, kemudian klik konfirmasi pada aplikasi untuk menyelesaikan proses verifikasi counter.

---

## Pengujian Otomatis

Untuk memastikan seluruh logika program berfungsi dengan benar:
```bash
python3 -m unittest discover tests/unit
```

---

## Penafian (Disclaimer)

- Proyek Independen: Utilitas ini dikembangkan secara independen untuk tujuan interoperabilitas teknis dan hak perbaikan mandiri (Right to Repair). Proyek ini tidak memiliki afiliasi atau pengesahan resmi dari Seiko Epson Corporation.
- Merek Dagang: Nama "Epson" dan identifikasi model printer digunakan semata-mata untuk tujuan deskriptif kesesuaian perangkat (fair use).
- Tanggung Jawab Fisik Pengguna: Mereset nilai counter digital tidak membersihkan tinta cair fisik yang terserap pada bantalan spon di dalam printer. Pengguna bertanggung jawab penuh atas pemeriksaan dan penggantian fisik bantalan spon untuk mencegah kebocoran atau korsleting. Perangkat lunak ini disediakan apa adanya (AS IS) tanpa jaminan apa pun.

---

## Lisensi

Didistribusikan di bawah lisensi terbuka MIT License. Bebas digunakan, dipelajari, dan dikembangkan kembali.
