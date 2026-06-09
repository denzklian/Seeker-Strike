# Seeker Strike

**OSINT + Social Engineering Tracking Tool**

Track GPS location, capture front camera photos, and collect device information via legitimate-looking phishing links.

---

## Daftar Isi

- [Fitur](#fitur)
- [Cara Kerja Singkat](#cara-kerja-singkat)
- [Instalasi — Windows](#instalasi--windows)
- [Instalasi — Termux (Android)](#instalasi--termux-android)
- [Cara Pakai — Windows](#cara-pakai--windows)
- [Cara Pakai — Termux (Android)](#cara-pakai--termux-android)
- [Daftar Template](#daftar-template)
- [Metode Tunnel](#metode-tunnel)
- [Dashboard](#dashboard)
- [Telegram Bot Setup](#telegram-bot-setup)
- [File .env](#file-env)
- [Troubleshooting](#troubleshooting)
- [Struktur Project](#struktur-project)
- [Keamanan & Etika](#keamanan--etika)
- [Credits](#credits)

---

## Fitur

### Tracking & Capture
| Fitur | Keterangan |
|---|---|
| **GPS Tracking** | Koordinat real-time dari device target (jika izin lokasi diberikan) |
| **IP Geolocation** | Estimasi lokasi berdasarkan IP address (fallback kalau GPS tidak diizinkan) |
| **Kamera Depan** | Ambil foto dari kamera depan target (perlu izin kamera) |
| **Clipboard** | Rekam isi clipboard target |
| **Device Info** | OS, browser, CPU, RAM, GPU, resolusi layar, baterai, status VPN/proxy |

### Dashboard
- Live map interaktif (Leaflet + OpenStreetMap)
- Auto-refresh setiap 3 detik
- Detail per target: GPS, foto, device info, clipboard, IP
- Responsive — bisa dibuka dari HP
- Tidak perlu koneksi internet (file lokal)

### Notifikasi
- **Telegram Bot** — setiap data target masuk langsung dikirim ke Telegram kamu
- **Webhook** — bisa kirim ke webhook custom (Discord, Slack, dll)

### Tunnel (Agar Link Bisa Diakses Target)
- **Cloudflare Tunnel** — gratis, tanpa warning page, URL anonymous, paling recommended
- **SSH localhost.run** — gratis, tanpa install, tapi kadang down
- **ngrok + Cloudflare Worker** — bypass halaman warning ngrok

---

## Cara Kerja Singkat

```
Kamu buat link phishing → Target klik link →
Browsernya kirim data (GPS, kamera, device) balik ke server kamu →
Server kamu simpan data + kirim notif ke Telegram →
Kamu pantau hasilnya di Dashboard
```

---

## Instalasi — Windows

### Cara Otomatis (Recommended)

Tinggal double-click `SEEKER_STRIKE.bat`. Script akan otomatis:

1. **Cek semua dependensi** — PHP, Python, OpenSSH, cloudflared, ngrok
2. **Install yang belum ada** — pakai `winget` (tanpa klik apa-apa)
3. **Install Python modules** — `requests`, `packaging`, `psutil`
4. **Jalankan tool** — langsung ke menu

### Cara Manual

Kalau mau install sendiri satu-satu:

1. **Install PHP 8.4**
   ```powershell
   winget install -e --id PHP.PHP.8.4
   ```

2. **Install Python 3.12**
   ```powershell
   winget install -e --id Python.Python.3.12
   ```

3. **Install Python modules**
   ```powershell
   pip install requests packaging psutil
   ```

4. **Install OpenSSH Client** (untuk tunnel SSH)
   ```
   Settings > Apps > Optional Features > Add a feature > OpenSSH Client
   ```

5. **Install cloudflared** (untuk Cloudflare Tunnel)
   ```powershell
   winget install -e --id Cloudflare.cloudflared
   ```

6. **Download ngrok** (untuk ngrok + CF Worker)
   - Download dari https://ngrok.com/download
   - Extract `ngrok.exe` ke folder project ini

7. **Clone project**
   ```powershell
   git clone https://github.com/denzklian/Seeker-Strike.git
   cd Seeker-Strike
   ```

8. **Jalankan**
   ```powershell
   .\SEEKER_STRIKE.bat
   ```

---

## Instalasi — Termux (Android)

> **PENTING:** Download Termux dari **F-Droid** (bukan Play Store), karena versi Play Store sudah outdated.

1. **Update Termux**
   ```bash
   pkg update && pkg upgrade -y
   ```

2. **Install dependensi**
   ```bash
   pkg install python php openssh curl git -y
   ```

3. **Install Python packages**
   ```bash
   pip install requests packaging psutil
   ```

4. **Clone project**
   ```bash
   git clone https://github.com/denzklian/Seeker-Strike.git
   cd Seeker-Strike
   ```

5. **Jalankan**
   ```bash
   bash seeker_strike.sh
   ```

   Script akan otomatis:
   - Cek dan install dependensi yang kurang
   - Tanya hapus database lama
   - Tampilkan menu pilih template
   - Matikan proses di port 8080 kalau ada
   - Start PHP server + seeker.py

---

## Cara Pakai — Windows

Jalankan `SEEKER_STRIKE.bat`, lalu ikuti langkah-langkah:

### 1. Hapus Database Lama?
```
Hapus riwayat database lama? [Y/N] (biar kga error: y):
```
Pilih `Y` kalau mau bersihin data dari session sebelumnya.

### 2. Telegram Bot Token (Opsional)
```
Mau isi bot token dan chat ID Telegram?
Format: bot_token:chat_id
Contoh: 1234567890:ABCdef...:123456789
```
Kalau kamu belum setup bot, lihat [Telegram Bot Setup](#telegram-bot-setup). Kosongkan kalau gak mau pakai Telegram.

Token akan disimpan otomatis ke file `.env`.

### 3. Pilih Template
```
 [0] NearYou
 [1] Google Drive
 [2] WhatsApp
 [3] WhatsApp Redirect
 [4] Telegram
 [5] Zoom
 [6] Google ReCaptcha
 [7] Custom OG Tags
 [8] Instagram
 [9] YouTube Age Verify
[10] E-commerce
[11] Package Delivery

Pilih template [0-11] (Default: 0):
```
Ini menentukan tampilan halaman yang akan dilihat target. Pilih yang paling sesuai dengan skenario social engineering kamu.

### 4. Metode Pengiriman Data
```
 [1] Bot Telegram aja   (notif via Telegram)
 [2] Dashboard aja      (pantau via browser)
 [3] Keduanya           (Telegram + Dashboard)

Pilih [1-3] (Default: 3):
```
- **Bot Telegram aja**: Hanya kirim notifikasi ke Telegram. Dashboard tidak dibuka otomatis.
- **Dashboard aja**: Hanya dashboard yang terbuka. Tidak kirim ke Telegram.
- **Keduanya**: Telegram + Dashboard (recommended).

### 5. Pilih Metode Tunnel
```
 [1] SSH  localhost.run        (no warning, tanpa install)
 [2] Cloudflare Tunnel         (no warning, anonymous URL)
 [3] ngrok + CF Worker         (auto bypass warning page)

Pilih [1-3] (Default: 2):
```
Ini menentukan bagaimana link phishing kamu bisa diakses oleh target dari internet. Lihat penjelasan di [Metode Tunnel](#metode-tunnel).

Saat tunnel dimulai:
- Jendela tunnel akan muncul di taskbar
- Seeker.py akan berjalan dan menunggu URL tunnel
- Kamu akan ditanya: **"Mau URL di-shorten dulu? (Y/n)"** — biar link makin pendek dan tidak mencurigakan

### 6. Kirim Link ke Target

Setelah URL keluar (original atau sudah di-shorten), kirim ke target via chat/email.

### 7. Pantau Hasil

- Kalau pilih dashboard: akan terbuka otomatis di browser
- Kalau pilih Telegram: setiap kali target buka link, kamu dapat notif

---

## Cara Pakai — Termux (Android)

Jalankan `bash seeker_strike.sh`, lalu:

### 1. Hapus Database Lama?
Sama seperti Windows — pilih `y` biar kga ada yg error.

### 2. Pilih Template
Sama seperti Windows — 12 pilihan template.

### 3. Tunnel Manual

Di Termux, tunnel dilakukan secara **manual** karena tidak bisa auto-start tunnel di background. Script akan menampilkan panduan:

```
PILIH METODE TUNNEL:
 [1] SSH localhost.run
 [2] SSH serveo.net
 [3] Paste URL manual
```

**Untuk [1] / [2], caranya:**

1. Di Termux, buka session baru (swipe dari kiri > New session)
2. Ketik perintah yang ditampilkan, contoh:
   ```bash
   ssh -o StrictHostKeyChecking=no -R 80:127.0.0.1:8080 nokey@localhost.run
   ```
3. Tunggu sampai muncul URL (contoh: `https://xxxxx.lhr.life`)
4. Copy URL tersebut
5. Kembali ke session pertama, paste URL-nya

**Untuk [2] serveo.net:**
```bash
ssh -R 80:127.0.0.1:8080 serveo.net
```
> **NOTE:** URL dari serveo.net **tidak bisa di-shorten** (karena serveo block shortener). Script akan otomatis skip shorten + kasih warning.

**Untuk [3] Paste URL manual:**
Kalau kamu sudah punya tunnel sendiri (ngrok, Cloudflare tunnel dari PC lain, dll), tinggal paste URL-nya.

### 4. Shorten URL?

Setelah masukkan URL, script akan tanya:
```
Mau URL di-shorten dulu? (Y/n)
```
Kalau `Y` — coba shorten pakai TinyURL, is.gd, v.gd, dll.

### 5. Mulai Tracking

Seeker.py jalan → target yang buka link akan datanya masuk ke:
- `db/results.csv` dan `db/results.json`
- `db/captures/` untuk foto kamera
- Telegram (kalau token bot di-set)

---

## Daftar Template

| Index | Nama Template | Deskripsi |
|---|---|---|
| 0 | **NearYou** | Halaman dating app "people near you" |
| 1 | **Google Drive** | Halaman download file dari Google Drive |
| 2 | **WhatsApp** | Tampilan chat WhatsApp |
| 3 | **WhatsApp Redirect** | WhatsApp + redirect setelah klik |
| 4 | **Telegram** | Tampilan chat/file Telegram |
| 5 | **Zoom** | Halaman join meeting Zoom |
| 6 | **Google ReCaptcha** | Halaman verifikasi "I'm not a robot" |
| 7 | **Custom OG Tags** | Link preview custom (thumbnail, judul, deskripsi) |
| 8 | **Instagram** | Halaman login Instagram |
| 9 | **YouTube Age Verify** | Halaman verifikasi umur YouTube |
| 10 | **E-commerce** | Halaman produk/toko online |
| 11 | **Package Delivery** | Halaman tracking paket pengiriman |

---

## Metode Tunnel

### 1. Cloudflare Tunnel (Windows — Recommended)
```
✅ Gratis
✅ Tidak ada halaman warning
✅ URL random anonymous (tidak ada nama/email kamu di URL)
✅ Tanpa batasan bandwidth
✅ Paling stabil
❌ Hanya bisa dari Windows (perlu cloudflared)
```

Cara kerja: `cloudflared tunnel --url http://127.0.0.1:8080` bikin tunnel dari server lokal kamu ke domain `*.trycloudflare.com` yang random.

### 2. SSH localhost.run (Windows + Termux)
```
✅ Gratis
✅ Tidak ada warning page
✅ Tanpa install tambahan
❌ Kadang down / timeout
❌ URL panjang dan random
❌ Tidak bisa custom domain
```

Cara kerja: SSH reverse tunnel. Akses port 8080 lokal kamu diteruskan ke `localhost.run`.

### 3. ngrok + Cloudflare Worker (Windows)
```
✅ Bypass halaman warning ngrok
✅ URL pendek dan rapi
❌ Perlu Cloudflare account (gratis)
❌ Perlu ngrok account (gratis)
```

Cara kerja:
1. **ngrok** — expose port 8080 ke internet (tapi ada halaman warning)
2. **Cloudflare Worker** — duduk di depan ngrok sebagai reverse proxy, hapus halaman warning, ganti URL

Saat kamu pilih opsi ini, script akan:
1. Cek apakah ngrok sudah terinstall. Kalau belum, auto-download.
2. Cek apakah ngrok sudah login (auth token). Kalau belum, minta token.
3. Start ngrok tunnel.
4. Deploy Cloudflare Worker yang proxy ke ngrok URL.
5. Hasil akhirnya: URL CF Worker yang bersih tanpa warning.

---

## Dashboard

Dashboard bisa dibuka lewat:
- **Otomatis** — kalau pilih "Bot Telegram aja" = tidak terbuka, kalau pilih "Dashboard aja" atau "Keduanya" = terbuka otomatis
- **File langsung** — double click `dashboard.html`

### Fitur Dashboard:
- **Peta interaktif** — marker merah untuk GPS, marker oranye untuk IP fallback
- **Tabel target** — list semua target dengan timestamp
- **Klik target** — lihat detail: GPS coordinate, Google Maps link, foto kamera, device info, clipboard
- **Auto-refresh 3 detik** — data terbaru selalu muncul tanpa reload manual
- **Mobile responsive** — bisa pantau dari HP

> **NOTE:** Dashboard adalah file HTML statis. Tidak perlu di-hosting. Cukup buka langsung atau dari localhost.

---

## Telegram Bot Setup

### Cara Buat Bot Telegram:

1. Buka Telegram, cari **@BotFather**
2. Kirim `/newbot`
3. Ikuti instruksi (kasih nama bot, kasih username bot)
4. BotFather akan kasih **token**, contoh: `123456789:ABCdefGHIjklmnopQRStuv`
5. **COPY token ini**

### Cara Dapat Chat ID:

1. Buka browser, masuk ke:
   ```
   https://api.telegram.org/bot<TOKEN_KAMU>/getUpdates
   ```
   (ganti `<TOKEN_KAMU>` dengan token dari step 4)
2. Kirim pesan apa aja ke bot kamu di Telegram
3. Refresh halaman browser tadi
4. Cari `"chat":{"id":123456789` — itu chat ID kamu

### Cara Set Token di Seeker Strike:

Formatnya: `bot_token:chat_id` (dipisah pakai titik dua)

**Windows:**
- Saat `SEEKER_STRIKE.bat` jalan, nanti ditanya. Tinggal paste format tadi.
- Atau edit manual file `.env`:
  ```
  TELEGRAM=123456789:ABCdefGHIjklmnopQRStuv:123456789
  ```

**Termux:**
- Edit file `.env`:
  ```bash
  nano .env
  ```
- Di bagian `TELEGRAM=`, isi dengan format `bot_token:chat_id`

### Jenis Notifikasi Telegram:
| Event | Notifikasi |
|---|---|
| Target buka link | Device info (OS, browser, IP, CPU, RAM, GPU) |
| Target izinkan GPS | Koordinat + akurasi + Google Maps link |
| Target izinkan kamera | Foto kamera depan (gambar) |
| Target clipboard | Isi clipboard |
| GPS error/fallback | Notif error + IP geolocation |

---

## File .env

File `.env` menyimpan semua konfigurasi. Copy dari `.env.example`:

```bash
cp .env.example .env
```

### Isi File:

```ini
# Port web server (default: 8080)
PORT=8080

# Template default (0-11)
# Kalau dikosongkan, akan ditanya saat startup
TEMPLATE=1

# Kamera depan (on/off)
CAMERA=on

# Debug mode — disable HTTPS redirect (0/1)
# Hanya untuk testing lokal, JANGAN nyalakan di production
DEBUG_HTTP=0

# Telegram (format: bot_token:chat_id)
TELEGRAM=123456789:ABCdefGHIjklmnopQRStuv:123456789

# Webhook URL (untuk Discord / webhook custom)
WEBHOOK=https://discord.com/api/webhooks/...

# Cloudflare API Token (untuk ngrok + CF Worker)
CF_API_TOKEN=your_cloudflare_api_token

# Custom template settings (tergantung template)
TITLE=Judul halaman
IMAGE=https://example.com/gambar.jpg
REDIRECT=https://situs-tujuan.com
DESC=Deskripsi halaman
SITENAME=Nama situs
```

---

## Troubleshooting

### Port 8080 Already in Use

Error: `Address already in use` atau `port 8080 is already in use`.

**Windows:**
```powershell
# Lihat proses yang make port 8080
netstat -ano | findstr :8080

# Kill prosesnya (ganti <PID> dengan nomor PID)
taskkill /F /PID <PID>
```

**Termux:**
```bash
fuser -k 8080/tcp
```

Atau tutup paksa semua proses lama:
```bash
killall php python3 ssh 2>/dev/null
```

### cloudflared Not Found

**Windows:**
```powershell
winget install -e --id Cloudflare.cloudflared
```

### Ngrok Warning Page Still Shows

Kalau pilih opsi 3 (ngrok + CF Worker) tapi masih muncul halaman warning, berarti CF Worker belum ter-deploy dengan benar.

Solusi:
```bash
python deploy_cf.py
```

### PHP Not Found

**Windows:**
```powershell
winget install -e --id PHP.PHP.8.4
```

Tutup dan buka ulang cmd.exe setelah install.

**Termux:**
```bash
pkg install php -y
```

### Kamera Tidak Berfungsi

Syarat kamera bekerja:
1. Target pakai browser modern (Chrome, Firefox, Safari, Edge)
2. Target mengizinkan akses kamera (ada popup izin)
3. Website diakses via **HTTPS** (semua tunnel otomatis HTTPS)

Kalau target klik "Block" di popup kamera, kamera tidak akan mengambil foto.

### GPS Tidak Akurat / Tidak Muncul

1. Target harus **mengizinkan akses lokasi** di browser
2. Kalau target reject, script fallback ke **IP geolocation** (estimasi kasar)
3. IP geolocation hanya bisa estimasi sampai level kota/negara, bukan koordinat presisi
4. Kalau target pakai VPN, IP geolocation akan salah

Di dashboard:
- **Marker merah** = GPS akurat (target izinin)
- **Marker oranye** = IP fallback (target gak izinin GPS)

### Dashboard Tidak Update

1. Buka DevTools browser (F12), refresh dashboard (Ctrl+F5)
2. Kalau error `seeker_results is not defined` → cek file `db/results.js` ada
3. Kalau data kosong → pastikan PHP server jalan dan tunnel aktif
4. Coba buka dashboard lewat `http://127.0.0.1:8080/dashboard.html`

### Telegram Bot Tidak Kirim Notif

1. Cek format token di `.env` udah benar: `bot_token:chat_id` (dipisah `:`)
2. Cek bot token masih valid — coba buka `https://api.telegram.org/bot<TOKEN>/getMe`
3. Cek chat ID benar — kirim pesan ke bot, lalu cek `getUpdates`
4. Cek koneksi internet

---

## Struktur Project

```
Seeker-Strike/
├── SEEKER_STRIKE.bat       # Windows launcher (auto-install + menu)
├── seeker_strike.sh         # Termux launcher
├── seeker.py                # Main Python script
├── cf_setup.py              # Cloudflare Worker + ngrok setup
├── deploy_cf.py             # Deploy Cloudflare Worker
├── cloudflare-worker.js     # CF Worker code
├── url_shortener.py         # URL shortener (TinyURL, is.gd, dll)
├── telegram_api.py          # Telegram bot sender
├── utils.py                 # Utility functions
├── dashboard.html           # Live monitoring dashboard
├── requirements.txt         # Python dependencies
├── .env.example             # Template konfigurasi
├── .env                     # Konfigurasi kamu (jangan di-commit!)
│
├── php/                     # PHP server handlers
│   ├── info.php             # Device info collector
│   ├── result_handler.php   # GPS/location handler
│   ├── camera.php           # Camera capture handler
│   ├── error.php            # Error handler
│   ├── clear.php            # Clear data handler
│   └── clipboard_handler.php
│
├── js/                      # JavaScript (client-side)
│   └── location.js          # GPS + camera + clipboard JS
│
├── template/                # Phishing templates (12 buah)
│   ├── templates.json       # Template registry
│   ├── nearyou/
│   ├── gdrive/
│   ├── whatsapp/
│   ├── whatsapp_redirect/
│   ├── telegram/
│   ├── zoom/
│   ├── captcha/
│   ├── custom_og_tags/
│   ├── instagram/
│   ├── youtube/
│   ├── ecommerce/
│   └── package/
│
├── db/                      # Database & logs
│   ├── results.json         # Semua data (JSON)
│   ├── results.csv          # Data tabular (CSV)
│   ├── results.js           # Data untuk dashboard (JS)
│   └── captures/            # Foto kamera target
│
└── README.md                # File ini
```

---

## Keamanan & Etika

### BOLEH Digunakan Untuk:
- ✅ Belajar OSINT dan cybersecurity
- ✅ Penetration testing yang SUDAH dapat izin tertulis
- ✅ Security research
- ✅ CTF (Capture The Flag) competition
- ✅ Demo / edukasi keamanan

### DILARANG Digunakan Untuk:
- ❌ Melacak / stalking orang tanpa izin
- ❌ Mencuri data pribadi
- ❌ Aktivitas ilegal atau melanggar hukum
- ❌ Phishing untuk kejahatan
- ❌ Melanggar privasi orang lain

> **DISCLAIMER:** Penulis TIDAK bertanggung jawab atas penyalahgunaan tool ini. Semua risiko ditanggung oleh pengguna. Gunakan dengan etika dan sesuai hukum yang berlaku. Illegal use is strictly prohibited.

---

## Credits
- thewhiteh4t && Aditya && d3nz
- Original Seeker: [thewhiteh4t/seeker](https://github.com/thewhiteh4t/seeker)
- Cloudflare Workers: [workers.cloudflare.com](https://workers.cloudflare.com)
- Ngrok: [ngrok.com](https://ngrok.com)
- Leaflet Maps: [leafletjs.com](https://leafletjs.com)
- Tailwind CSS: [tailwindcss.com](https://tailwindcss.com)

---

## WhatsApp Channel/Tiktok denz 
- WhatsApp Channel: https://whatsapp.com/channel/0029VbCPZlNF1YlLNJXx6V0b
- tiktok: tiktok.com/@cpl_denz
---


##report bugs/errors 
- https://wa.me/6285218441692
- denz25980@gmail.com


---


## Changelog

### v2.0 — Current
- 12 templates phishing (NearYou, GDrive, WhatsApp, WhatsApp Redirect, Telegram, Zoom, Captcha, Custom OG, Instagram, YouTube, E-commerce, Package)
- Auto-install semua dependensi di Windows (PHP, Python, OpenSSH, cloudflared, ngrok)
- Windows launcher (`SEEKER_STRIKE.bat`) dengan menu interaktif
- Termux launcher (`seeker_strike.sh`) dengan dependency check
- Tiga opsi tunnel: Cloudflare Tunnel, SSH localhost.run, ngrok + CF Worker
- Termux support: tunnel manual (SSH localhost.run / serveo.net / paste URL)
- URL shortener dengan konfirmasi Y/n (TinyURL, is.gd, v.gd, chilp.it, cleanuri, 1pt.co, da.gd)
- Serveo.net auto-detection — skip shorten + warning
- Telegram Bot: kirim device info, GPS, foto kamera, clipboard
- Webhook support (Discord, custom)
- Dashboard mobile responsive, auto-refresh 3 detik
- IP geolocation fallback (ip-api.com)
- VPN/Proxy detection
- Auto-kill port 8080 saat restart
- Cross-platform: Windows + Termux (Android)
- Ngrok auto-download + auth token check (3 lokasi config)

