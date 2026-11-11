# Epson EcoTank L3110 Resetter & Maintenance Utility

Aplikasi desktop independen berbasis Python dan Qt untuk membaca telemetri, merawat komponen cetak mekanis, dan melakukan reset Waste Ink Pad Counter pada printer Epson EcoTank L3110 Series secara langsung melalui jalur USB (driverless).

Program ini dikembangkan berdasarkan hasil rekayasa balik (reverse-engineering) perangkat keras fisik tanpa bergantung pada perangkat lunak komersial pihak ketiga atau driver proprietary tambahan.

---

## Daftar Isi
- 1. Tentang Program
- 2. Fitur Utama
- 3. Techstack Program
- 4. Arsitektur dan Protokol Komunikasi
- 5. Kebutuhan Sistem
- 6. Instalasi
  - 6.1 Instalasi di Linux (Arch Linux, Ubuntu, Debian, Fedora)
  - 6.2 Konfigurasi Akses Non-Root Linux (Udev Rules)
  - 6.3 Instalasi di Windows 10/11
- 7. Cara Penggunaan
  - 7.1 Mode Antarmuka Grafis (Desktop GUI)
  - 7.2 Mode Baris Perintah (CLI Headless)
  - 7.3 Prosedur Reset Waste Ink Pad
  - 7.4 Prosedur Pemeliharaan Printer (Maintenance)
- 8. Gerbang Keselamatan (Safety Gates)
- 9. Struktur Direktori Proyek
- 10. Pengujian Otomatis
- 11. Penafian Tanggung Jawab (Disclaimer)
- 12. Lisensi

---

## 1. Tentang Program

Printer inkjet multifungsi Epson EcoTank L3110 mengandalkan bantalan spon pembuangan tinta (Waste Ink Pad) untuk menampung residu tinta saat proses pembersihan head otomatis dan pencetakan tanpa batas (borderless). Firmware printer mencatat volume pembuangan ini dalam bentuk hitungan poin akumulatif (Waste Ink Counter). Ketika counter mencapai ambang batas batas aman kapasitas spon, printer akan memasuki status Service Required dan mengunci operasional pencetakan dengan indikator lampu berkedip.

Kebanyakan utilitas servis yang beredar di internet memiliki beberapa kelemahan serius:
- Hanya dapat beroperasi pada arsitektur sistem operasi tertentu (khusus Windows lama).
- Seringkali disisipi adware, keylogger, atau program berbahaya (malware).
- Menggunakan skema lisensi berbayar per-reset atau sistem aktivasi yang memberatkan.
- Tidak memiliki dokumentasi teknis yang transparan dan tidak mengindahkan aspek keselamatan fisik perangkat.

Proyek ini dibuat untuk menyediakan alternatif yang transparan, modern, aman, cross-platform, dan berbasis kode sumber terbuka (open-source). Aplikasi dapat beroperasi secara langsung pada sistem operasi Linux maupun Windows dengan memanfaatkan jalur akses USB berkecepatan tinggi tanpa memerlukan instalasi driver printer khusus.

---

## 2. Fitur Utama

- Komunikasi USB Driverless: Mengakses antarmuka USB secara langsung melalui libusb-1.0 tanpa dependensi wrapper tambahan. Pada sistem Linux, aplikasi otomatis melepas (detach) driver kernel usblp selama transaksi berlangsung dan memasangnya kembali (attach) secara transparan setelah selesai.
- Pembacaan Counter Akurat: Mengurai register telemetri biner 73-byte dari firmware printer untuk menampilkan data:
  - Main Waste Ink Pad Counter (Poin penggunaan dan persentase kapasitas).
  - Platen / Borderless Waste Ink Pad Counter (Poin penggunaan dan persentase kapasitas).
  - Status Tingkat Kesehatan Keseluruhan (Overall Pad Health Level).
- Statistik Lifetime Print Engine: Membaca riwayat akumulatif pencetakan langsung dari memori EEPROM printer:
  - Total halaman tercetak (Total Pages Printed).
  - Distribusi cetak warna vs monokrom (Color vs Monochrome Split).
  - Jumlah total proses pemindaian (Scan Count).
- Diagnostik Multi-Titik Otomatis: Pemeriksaan 5 tahapan komunikasi perangkat keras mencakup: koneksi fisik USB, validasi deskriptor IEEE 1284, negosiasi D4 Mode, alokasi soket EPSON-CTRL, dan pembacaan blok telemetri.
- Reset Counter Terverifikasi dengan Gerbang Keselamatan (Safety Gates):
  - Validasi model printer untuk mencegah salah eksekusi.
  - Dokumentasi pembacaan awal (pre-reset snapshot) ke database audit.
  - Konfirmasi fisik penggantian atau pembersihan bantalan spon oleh pengguna.
  - Verifikasi otomatis pasca-reset (post-reset verification) untuk memastikan nilai counter benar-benar telah berkurang.
- Universal Printer Maintenance Suite:
  - Nozzle Check: Mengirim instruksi cetak pola uji nozel untuk memeriksa nozel warna dan hitam tanpa mengalami macet kertas.
  - Head Cleaning: Menjalankan siklus hisap pompa tinta standar untuk melancarkan saluran head cetak yang tersumbat.
  - Power Cleaning (Ink Flush): Pembersihan intensif bertekanan tinggi dengan perlindungan ganda (validasi visual volume tangki tinta minimal 30% dan pembatasan kapasitas pad maksimal 85%).
  - Print Head Alignment: Mencetak lembar evaluasi keselarasan head cetak serta menyimpan offset kalibrasi numerik langsung ke register firmware.
- Antarmuka Modern Minimalis (Modern Minimalist GUI): Tampilan berbasis tema gelap ergonomis dengan sidebar navigasi responsif, visual gauge indikator kapasitas, modal instruksi restart yang informatif, dan arsitektur multi-thread agar aplikasi tidak macet saat berkomunikasi dengan USB.
- Pencatatan Riwayat Lokal (Audit History): Menyimpan seluruh log operasi perawatan dan diagnostik ke dalam database tersemat SQLite dengan mode Write-Ahead Logging (WAL) serta kemampuan ekspor ke format JSON dan CSV.

---

## 3. Techstack Program

Program ini dibangun menggunakan tumpukan teknologi modern, efisien, dan bebas ketergantungan yang tidak perlu:

- Bahasa Pemrograman: Python 3 (kompatibel dengan Python 3.10 hingga Python 3.14).
- Antarmuka Pengguna (GUI): PyQt6 (didukung pula oleh PySide6 melalui abstraksi dinamis).
- Lapisan Komunikasi USB: libusb-1.0 dihubungkan melalui modul standar Python ctypes (menghilangkan kebutuhan library eksternal seperti pyusb).
- Basis Data: SQLite terintegrasi (standar library sqlite3) dengan mode WAL.
- Pemaketan Distribusi (Packaging): PyInstaller untuk menghasilkan biner standalone portable pada Linux dan Windows.
- Kerangka Pengujian (Testing Framework): Modul standar unittest untuk pengujian unit fungsional dan pengujian integrasi hardware fisik langsung.

---

## 4. Arsitektur dan Protokol Komunikasi

Aplikasi ini mengimplementasikan tumpukan protokol komunikasi printer multi-lapis:

1. Lapisan USB Fisik:
   - Vendor ID (VID): 0x04B8 (Seiko Epson Corp.)
   - Product ID (PID): 0x1142 (L3110 Series)
   - Interface Index: Interface 1 (Printer Class 0x07, Subclass 0x01, Protocol 0x02 Bidirectional)
   - Endpoint: Bulk OUT 0x04 dan Bulk IN 0x83.
2. Lapisan Protokol IEEE 1284.4 (Dot4):
   - Mengalokasikan saluran logis melalui enkapsulasi paket 6-byte header biner (PSID, SSID, Length, Credit, Control).
   - Memiliki mekanisme perlindungan sliding-window header validation untuk mencegah desinkronisasi akibat transmisi teks status asinkron (@BDC ST2) dari printer.
3. Lapisan Protokol EPSON-CTRL (Soket 2):
   - Beroperasi menggunakan kata kerja (verb) 2 karakter ASCII dengan prefiks panjang 16-bit little-endian (contoh: vi untuk versi firmware, di untuk identifikasi perangkat, cd untuk data counter, rw untuk tulis-baca register).
4. Lapisan ESC/P-R Kanonikal (Universal Maintenance):
   - Dieksekusi melalui mode REMOTE1 dengan struktur paket kanonikal yang divalidasi dari driver resmi Seiko Epson (libescpr.so).
   - Seluruh perintah diakhiri dengan instruksi wajib Job End (RemoteJE: b"JE\x01\x00\x00") dan Form Feed (0x0C) untuk memastikan motor mekanik menyelesaikan siklus cetak dan hisap secara tuntas.

---

## 5. Kebutuhan Sistem

- Sistem Operasi:
  - Linux: Arch Linux, Ubuntu (20.04+), Debian (11+), Fedora (36+), atau distribusi modern lainnya.
  - Windows: Windows 10 atau Windows 11 (arsitektur 64-bit).
- Dependensi Sistem:
  - Pustaka libusb-1.0 (tersedia secara default pada sebagian besar distribusi Linux; pada Windows disertakan melalui pustaka biner libusb).
- Perangkat Keras:
  - Printer Epson EcoTank L3110 terhubung melalui kabel USB fisik (koneksi Wi-Fi/jaringan tidak didukung).
  - Port USB 2.0 atau USB 3.0 yang stabil.

---

## 6. Instalasi

### 6.1 Instalasi di Linux

1. Pasang dependensi sistem (contoh untuk Arch Linux):
```bash
sudo pacman -S python python-pip libusb
```

Untuk Ubuntu / Debian:
```bash
sudo apt update
sudo apt install python3 python3-pip libusb-1.0-0
```

2. Kloning repositori ini:
```bash
git clone https://github.com/username/epson-resetter.git
cd epson-resetter
```

3. Pasang dependensi Python:
```bash
pip install -r requirements.txt
```

Atau menggunakan virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 6.2 Konfigurasi Akses Non-Root Linux (Udev Rules)

Secara default, perangkat USB printer pada Linux memiliki izin akses terbatas (root/lp). Agar aplikasi dapat beroperasi penuh tanpa perintah sudo, pasang berkas aturan udev:

1. Salin berkas udev rule ke direktori sistem:
```bash
sudo cp scripts/99-epson-l3110.rules /etc/udev/rules.d/
```

2. Muat ulang aturan udev:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

3. Pastikan pengguna Anda terdaftar dalam grup `lp` dan `plugdev`:
```bash
sudo usermod -aG lp $USER
```

### 6.3 Instalasi di Windows 10/11

1. Pastikan Python 3.10+ telah terpasang dan dicentang opsi "Add Python to PATH".
2. Kloning repositori atau unduh berkas ZIP proyek, lalu buka terminal PowerShell pada folder proyek.
3. Pasang dependensi:
```powershell
pip install -r requirements.txt
```
4. Pastikan printer terhubung ke komputer dan driver standar printer telah dikenali oleh Device Manager.

---

## 7. Cara Penggunaan

### 7.1 Mode Antarmuka Grafis (Desktop GUI)

Jalankan perintah berikut pada terminal:
```bash
python3 app/main.py
```

Antarmuka memiliki 6 panel utama pada sidebar navigasi:
- Dashboard: Ringkasan cepat status koneksi perangkat, indikator persentase bantalan limbah, statistik cetak seumur hidup, dan tombol pintas.
- Diagnostics: Pengujian otomatis 5 tahap komunikasi perangkat keras secara komprehensif.
- Waste Counter: Tampilan telemetri terperinci kapasitas Main Pad dan Platen Pad disertai status kondisi normal, peringatan, atau kritis.
- Reset Utility: Panel prosedur reset counter dengan gerbang keselamatan multi-lapis.
- Maintenance: Pusat pemeliharaan mekanis printer mencakup Nozzle Check, Head Cleaning, Power Cleaning, dan Print Head Alignment.
- History: Log audit seluruh aktivitas diagnostik dan pemeliharaan sebelumnya dengan tombol ekspor JSON dan CSV.

### 7.2 Mode Baris Perintah (CLI Headless)

Aplikasi menyediakan fungsionalitas CLI untuk kebutuhan otomasi server atau diagnostik cepat tanpa GUI:

- Melakukan diagnostik hardware lengkap:
```bash
python3 app/main.py --diagnostics
```

- Membaca telemetri counter dan statistik printer:
```bash
python3 app/main.py --counters
```

- Menjalankan dengan pencatatan log debug terperinci:
```bash
python3 app/main.py --debug
```

### 7.3 Prosedur Reset Waste Ink Pad

Prosedur reset counter pada printer fisik harus dilakukan dengan urutan berikut:

1. Hubungkan printer ke komputer menggunakan kabel USB fisik dan hidupkan printer.
2. Buka aplikasi dan pastikan badge status pada status bar menunjukkan status Connected.
3. Buka tab Reset Utility.
4. Periksa nilai counter awal yang ditampilkan pada kartu telemetri.
5. Lakukan penggantian fisik atau pencucian bantalan spon pembuangan tinta di bagian belakang bawah printer.
6. Centang kotak persetujuan konfirmasi fisik spon: "Saya menyatakan telah membersihkan/mengganti bantalan spon fisik...".
7. Klik tombol Jalankan Reset Terverifikasi.
8. Setelah instruksi reset diterima oleh firmware printer, kedua lampu merah pada tombol printer akan berkedip/menyala secara bersamaan. Ini adalah indikator normal dari firmware yang menandakan printer meminta restart.
9. Tekan tombol POWER fisik pada printer untuk mematikan perangkat. Tunggu hingga seluruh lampu mati total.
10. Tekan tombol POWER kembali untuk menghidupkan printer.
11. Klik tombol OK pada dialog instruksi aplikasi. Aplikasi akan memverifikasi ulang bahwa nilai counter di dalam EEPROM telah berkurang menjadi 0.

### 7.4 Prosedur Pemeliharaan Printer (Maintenance)

- Nozzle Check: Masukkan 1 lembar kertas A4 ke penampung kertas printer, buka tab Maintenance, lalu klik Cetak Pola Uji. Printer akan mencetak kisi-kisi nozel hitam dan tangga warna untuk memeriksa ada tidaknya garis yang putus.
- Head Cleaning: Jika hasil cetak bergaris, klik tombol Head Cleaning. Printer akan menjalankan siklus hisap pompa tinta selama 1 hingga 2 menit. Jangan mematikan printer selama proses berlangsung.
- Power Cleaning: Digunakan hanya jika pembersihan standar tidak mampu mengatasi nozel macet parah. Fitur ini memerlukan konfirmasi visual bahwa seluruh tabung tinta terisi minimal 30% dan kapasitas waste pad berada di bawah 85%.
- Head Alignment: Digunakan jika hasil cetakan teks terlihat berbayang atau tidak lurus. Klik tombol Cetak Lembar Uji untuk mencetak lembar evaluasi nomor pola, lalu masukkan nomor pola yang paling lurus pada aplikasi dan klik Terapkan Kalibrasi.

---

## 8. Gerbang Keselamatan (Safety Gates)

Mereset counter adalah instruksi manipulasi register digital. Hal tersebut tidak membersihkan fisik tinta cair yang tertampung di spon. Mengabaikan spon fisik dapat menyebabkan tinta limbah meluap keluar membanjiri meja kerja atau menyebabkan korsleting mekanik printer.

Aplikasi ini menerapkan kebijakan keselamatan berlapis:
1. Validasi Model Hardware: Perintah reset diblokir jika perangkat yang terhubung bukan Epson L3110 (VID 0x04B8 PID 0x1142).
2. Snapshot Audit Pre-Reset: Data awal dicatat permanen ke basis data audit lokal sebelum instruksi reset dikirim.
3. Konfirmasi Eksplisit: Tombol eksekusi reset terkunci sampai pengguna mencentang konfirmasi kesadaran fisik spon secara sadar.
4. Pencegahan Overflow Power Cleaning: Power Cleaning otomatis diblokir jika kapasitas pad saat itu telah melampaui 85%.
5. Verifikasi Post-Reset: Jika pembacaan counter setelah proses restart tidak membuktikan penurunan angka poin, operasi ditandai sebagai FAILED dan pengguna akan diberitahu bahwa reset belum berhasil di tingkat hardware.

---

## 9. Struktur Direktori Proyek

```text
epson-resetter/
|-- app/
|   |-- bootstrap.py            # Dependency injection container & service initialization
|   |-- main.py                 # Titik masuk utama aplikasi (GUI & CLI parser)
|   |-- core/                   # Konstanta, pengecualian kustom, dan logger
|   |   |-- constants.py        # Kode opcode, paket kanonikal ESC/P-R, dan threshold
|   |   |-- exceptions.py       # Hierarki exception terstruktur
|   |   \-- logger.py           # Konfigurasi structured rotating file logger
|   |-- models/                 # Model data typed (PrinterInfo, Counter, Record)
|   |-- database/               # Lapisan persistensi data SQLite
|   |   |-- connection.py       # Manajemen koneksi database thread-safe
|   |   \-- repository.py       # Operasi CRUD riwayat pemeliharaan
|   |-- communication/          # Lapisan protokol komunikasi hardware
|   |   |-- usb_interface.py    # Interface abstrak backend USB
|   |   |-- libusb_backend.py   # Driverless USB backend via ctypes libusb-1.0
|   |   |-- dot4_protocol.py    # Mesin multiplexing IEEE 1284.4 & sliding resync
|   |   \-- epson_ctrl_transport.py # Transpor perintah tingkat tinggi EPSON-CTRL
|   |-- services/               # Lapisan logika bisnis
|   |   |-- device_manager.py   # Monitoring koneksi USB latar belakang
|   |   |-- printer_service.py  # Ekstraksi informasi perangkat dan halaman
|   |   |-- counter_service.py  # Kalkulasi dan pembacaan Waste Pad Counter
|   |   |-- diagnostics_service.py # Pipeline diagnostik 5 titik
|   |   |-- reset_service.py    # Eksekusi reset counter dengan safety gate
|   |   \-- maintenance_service.py # Pengendali Nozzle Check, Cleaning, dan Alignment
|   \-- ui/                     # Komponen antarmuka pengguna Qt
|       |-- qt_compat.py        # Abstraksi pemilihan PyQt6 atau PySide6
|       |-- main_window.py      # Jendela utama aplikasi dengan QStackedWidget
|       |-- components.py       # Komponen kartu kustom, indikator, dan modal
|       |-- dashboard_view.py   # Tampilan beranda dan ringkasan
|       |-- diagnostics_view.py # Tampilan eksekusi diagnostik
|       |-- counter_view.py     # Tampilan telemetri counter
|       |-- reset_view.py       # Tampilan instruksi reset terverifikasi
|       |-- maintenance_view.py # Tampilan utilitas pemeliharaan
|       \-- history_view.py     # Tampilan audit log riwayat
|-- docs/                       # Dokumentasi arsitektur dan spesifikasi
|-- research/                   # Catatan rekayasa balik protokol & penangkapan paket
|   \-- protocol-notes.md       # Dokumentasi rinci struktur byte kanonikal
|-- scripts/                    # Skrip otomasi pembangun paket dan aturan udev
|   |-- 99-epson-l3110.rules    # Aturan udev untuk akses non-root pada Linux
|   \-- build-linux.sh          # Skrip kompilasi biner standalone Linux
|-- tests/                      # Rangkaian pengujian otomatis
|   |-- unit/                   # Pengujian logika modul independen
|   |   |-- test_database.py
|   |   |-- test_dot4.py
|   |   |-- test_maintenance.py
|   |   |-- test_protocol_parser.py
|   |   \-- test_safety_gates.py
|   \-- hardware/               # Pengujian integrasi langsung dengan unit fisik L3110
|       \-- test_hardware_integration.py
|-- pyproject.toml              # Konfigurasi build dan metadata paket
|-- requirements.txt            # Daftar pustaka minimal
\-- README.md                   # Dokumentasi teknis proyek
```

---

## 10. Pengujian Otomatis

Aplikasi ini dilengkapi dengan rangkaian pengujian unit lengkap yang dapat dijalankan secara terisolasi tanpa membutuhkan koneksi fisik perangkat, serta rangkaian pengujian integrasi hardware langsung.

Menjalankan seluruh unit test logika perangkat lunak:
```bash
python3 -m unittest discover tests/unit
```

Menjalankan pengujian integrasi hardware pada unit Epson L3110 fisik:
```bash
python3 -m unittest tests/hardware/test_hardware_integration.py
```

Menjalankan seluruh rangkaian tes sekaligus:
```bash
python3 -m unittest discover tests
```

---

## 11. Penafian Tanggung Jawab (Disclaimer)

1. Proyek Independen: Perangkat lunak ini dikembangkan secara independen oleh komunitas open-source untuk tujuan interoperabilitas teknis dan pelestarian perangkat keras (Right to Repair). Proyek ini tidak berafiliasi, disponsori, disahkan, atau memiliki hubungan resmi apapun dengan Seiko Epson Corporation maupun anak perusahaannya.
2. Merek Dagang: "Epson", "EcoTank", "L3110", dan nama model terkait adalah merek dagang terdaftar milik Seiko Epson Corporation. Penggunaan nama-nama tersebut di dalam proyek ini semata-mata bersifat deskriptif untuk tujuan identifikasi kompatibilitas perangkat keras (fair use).
3. Penggunaan Risiko Sendiri (As-Is): Perangkat lunak ini didistribusikan dengan itikad baik tanpa jaminan dalam bentuk apapun, baik tersurat maupun tersirat, termasuk namun tidak terbatas pada jaminan kelayakan untuk diperdagangkan atau kesesuaian untuk tujuan tertentu.
4. Tanggung Jawab Fisik Pengguna: Mereset Waste Ink Pad Counter secara digital tanpa melakukan pemeriksaan, pembersihan, atau penggantian bantalan spon penampung tinta fisik di dalam printer dapat menyebabkan cairan tinta meluap (spill), merusak komponen internal printer, mencemari area sekitar, atau menimbulkan risiko hubungan arus pendek. Pengguna bertanggung jawab penuh atas segala konsekuensi fisik, mekanis, maupun elektrik yang timbul akibat penggunaan aplikasi ini.

---

## 12. Lisensi

Proyek ini didistribusikan di bawah ketentuan lisensi MIT License.

Hak Cipta (c) 2026 Pengembang Epson Resetter & Maintenance Utility.

Izin dengan ini diberikan, bebas biaya, kepada siapa saja yang memperoleh salinan perangkat lunak ini dan berkas dokumentasi terkait, untuk memperlakukan perangkat lunak ini tanpa batasan, termasuk tanpa batasan hak untuk menggunakan, menyalin, memodifikasi, menggabungkan, mempublikasikan, mendistribusikan, mensublisensikan, dan/atau menjual salinan perangkat lunak, dengan tunduk pada ketentuan lisensi standar yang berlaku.
