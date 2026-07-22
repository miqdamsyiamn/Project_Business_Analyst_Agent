# 📖 Panduan Lengkap - Business Analyst Agent

Panduan ini menjelaskan cara setup dan menjalankan **Business Analyst Agent** dari awal hingga bisa diakses secara publik.

---

## 📋 Daftar Isi

1. [Prasyarat](#-1-prasyarat)
2. [Clone Repository](#-2-clone-repository)
3. [Setup Virtual Environment](#-3-setup-virtual-environment)
4. [Install Dependencies](#-4-install-dependencies)
5. [Setup Database (MongoDB Atlas)](#-5-setup-database-mongodb-atlas)
6. [Setup Environment Variables (.env)](#-6-setup-environment-variables-env)
7. [Menjalankan Aplikasi](#-7-menjalankan-aplikasi)
8. [Dokumentasi API](#-8-dokumentasi-api)
9. [Cloudflare Tunnel (Akses Publik)](#-9-cloudflare-tunnel-akses-publik)
10. [Troubleshooting](#-10-troubleshooting)

---

## 🔧 1. Prasyarat

Pastikan kamu sudah menginstall:

| Software | Versi Minimum | Link Download |
|----------|---------------|---------------|
| **Python** | 3.10+ | [python.org/downloads](https://www.python.org/downloads/) |
| **Git** | 2.x | [git-scm.com](https://git-scm.com/) |
| **pip** | (bawaan Python) | — |

Cek versi:
```bash
python --version    # Python 3.10+
git --version       # Git 2.x
pip --version       # pip 21+
```

---

## 📥 2. Clone Repository

```bash
git clone https://github.com/USERNAME/BA-AgenticAI.git
cd BA-AgenticAI
```

> Ganti `USERNAME` dengan username GitHub kamu.

---

## 🐍 3. Setup Virtual Environment

### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

### Mac / Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

> ✅ Jika berhasil, akan muncul `(venv)` di awal terminal.
> ⚠️ Jalankan perintah aktivasi ini **setiap kali** buka terminal baru.

---

## 📦 4. Install Dependencies

```bash
pip install -r requirements.txt
```

Library yang diinstall:
| Library | Fungsi |
|---------|--------|
| `openai` | Client untuk komunikasi dengan LLM API (multi-provider) |
| `pymongo` | Driver MongoDB untuk Python |
| `python-dotenv` | Membaca variabel dari file `.env` |
| `gradio` | Web UI & API endpoint untuk mode serve |

---

## 🗄️ 5. Setup Database (MongoDB Atlas)

### 5.1 Buat Akun MongoDB Atlas (Gratis)

1. Kunjungi [mongodb.com/atlas](https://www.mongodb.com/atlas)
2. Klik **"Try Free"** dan buat akun
3. Pilih plan **M0 (Free/Shared)** — gratis selamanya

### 5.2 Buat Cluster

1. Setelah login, klik **"Build a Database"**
2. Pilih **Shared (Free)**
3. Pilih region terdekat (contoh: **Singapore** untuk Asia Tenggara)
4. Klik **"Create Cluster"**

### 5.3 Buat Database User

1. Di sidebar, masuk ke **Database Access**
2. Klik **"Add New Database User"**
3. Pilih **Password** authentication
4. Isi:
   - **Username**: `username_kamu`
   - **Password**: `password_kamu` (catat ini!)
5. Di **Built-in Role**, pilih **"Read and write to any database"**
6. Klik **"Add User"**

### 5.4 Whitelist IP Address

1. Di sidebar, masuk ke **Network Access**
2. Klik **"Add IP Address"**
3. Klik **"Allow Access from Anywhere"** (`0.0.0.0/0`) — atau masukkan IP spesifik untuk keamanan lebih
4. Klik **"Confirm"**

### 5.5 Dapatkan Connection String

1. Kembali ke **Database** (sidebar)
2. Klik **"Connect"** pada cluster kamu
3. Pilih **"Drivers"**
4. Copy connection string, formatnya seperti:
   ```
   mongodb+srv://username_kamu:password_kamu@cluster0.xxxxx.mongodb.net/
   ```
5. **Ganti `<password>`** dengan password yang kamu buat di langkah 5.3

### 5.6 Struktur Database

Aplikasi akan **otomatis membuat** database dan collection saat pertama kali dijalankan. Tidak perlu setup manual!

```
Database: BaAgent
│
├── 📁 projects              — Menyimpan informasi proyek
│   ├── project_id           (string, unik)
│   ├── project_name         (string)
│   ├── description          (string)
│   ├── status               (string: "in_progress" | "analyzed")
│   └── created_at           (ISO datetime)
│
├── 📁 business_analysis     — Menyimpan hasil analisis BA
│   ├── project_id           (string, unik)
│   ├── user_stories         (array of objects)
│   ├── functional_requirements    (array of strings)
│   ├── non_functional_requirements (array of strings)
│   ├── constraints          (array of strings)
│   ├── stakeholders         (array of strings)
│   ├── created_at           (ISO datetime)
│   └── agent                (string)
│
└── 📁 conversations         — Menyimpan histori percakapan
    ├── project_id           (string)
    ├── role                 (string: "user" | "agent")
    ├── message              (string)
    └── timestamp            (ISO datetime)
```

---

## 🔐 6. Setup Environment Variables (.env)

### 6.1 Salin Template

```bash
# Windows (CMD)
copy .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env

# Mac / Linux
cp .env.example .env
```

### 6.2 Isi Konfigurasi

Buka file `.env` dengan text editor, lalu isi sesuai provider LLM yang ingin dipakai.

**Pilih SATU provider** dan uncomment (hapus `#`) baris yang sesuai:

#### Opsi A: Groq (Gratis, Super Cepat) ⭐ Rekomendasi

```env
LLM_PROVIDER=groq
LLM_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
LLM_MODEL=llama-3.3-70b-versatile
LLM_BASE_URL=https://api.groq.com/openai/v1
```

> Dapatkan API key gratis di: [console.groq.com](https://console.groq.com/)

#### Opsi B: OpenRouter (Banyak Model Gratis)

```env
LLM_PROVIDER=openrouter
LLM_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxxxxxx
LLM_MODEL=meta-llama/llama-3.3-70b-instruct:free
LLM_BASE_URL=https://openrouter.ai/api/v1
```

> Dapatkan API key gratis di: [openrouter.ai/keys](https://openrouter.ai/keys)

#### Opsi C: Gemini (Google)

```env
LLM_PROVIDER=gemini
LLM_API_KEY=AIzaxxxxxxxxxxxxxxxxxxxxxxxx
LLM_MODEL=gemini-2.0-flash
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

> Dapatkan API key gratis di: [aistudio.google.com](https://aistudio.google.com/)

#### Opsi D: Qwen (DashScope)

```env
LLM_PROVIDER=qwen
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
LLM_MODEL=qwen-plus
LLM_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

> Dapatkan API key di: [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com/)

#### Opsi E: Custom (LLM OpenAI-Compatible Lainnya)

```env
LLM_PROVIDER=custom
LLM_API_KEY=isi_api_key_kamu
LLM_MODEL=nama-model
LLM_BASE_URL=https://api.example.com/v1
```

#### MongoDB (WAJIB diisi)

```env
MONGODB_URI=mongodb+srv://username:password@cluster.xxxxx.mongodb.net/
```

> ⚠️ **PENTING**: Jangan pernah commit file `.env` ke GitHub! File ini sudah masuk `.gitignore`.

---

## 🚀 7. Menjalankan Aplikasi

Aplikasi memiliki **2 mode**:

### Mode 1: CLI (Command Line Interface)

```bash
python main.py
```

Fitur mode CLI:
- Menu interaktif untuk buat/lanjutkan proyek
- Percakapan real-time dengan BA Agent di terminal
- Perintah yang tersedia:
  | Perintah | Fungsi |
  |----------|--------|
  | `/selesai` | Generate/update dokumen analisis bisnis |
  | `/beranda` | Kembali ke menu utama |
  | `/keluar` | Keluar dari program |

### Mode 2: Gradio Web UI + API (Untuk Deploy & Orchestrator)

```bash
python main.py --serve
```

Ini akan menjalankan:
- **Web UI** di `http://localhost:7860` — chat interface di browser
- **API endpoint** di `http://localhost:7860/api/analyze` — untuk dipanggil Orchestrator

> Mode ini wajib dipakai saat deploy ke Hugging Face Spaces atau saat ingin diakses via API.

---

## 📡 8. Dokumentasi API

### 8.1 API Chat (via Gradio)

Saat menjalankan `python main.py --serve`, Gradio otomatis menyediakan API endpoint.

#### Endpoint: POST `/api/analyze`

**Deskripsi**: Endpoint non-interaktif untuk dipanggil oleh Orchestrator Agent (#1). Langsung generate analisis tanpa percakapan bertahap.

**URL**: `http://localhost:7860/api/analyze`

**Request Body** (JSON):
```json
{
  "data": ["project_id_opsional", "deskripsi proyek kamu"]
}
```

| Parameter | Tipe | Wajib | Deskripsi |
|-----------|------|-------|-----------|
| `data[0]` | string | Opsional | Project ID (kosongkan `""` untuk auto-generate) |
| `data[1]` | string | ✅ Ya | Deskripsi proyek yang ingin dianalisis |

**Contoh Request**:
```bash
curl -X POST http://localhost:7860/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "data": ["proj_001", "Buat aplikasi pemesanan makanan untuk kantin kampus dengan fitur pembayaran digital"]
  }'
```

**Contoh Response** (Sukses):
```json
{
  "data": [
    {
      "status": "success",
      "project_id": "proj_001",
      "result": {
        "user_stories": [
          {
            "id": "US-001",
            "as_a": "mahasiswa",
            "i_want": "memesan makanan secara online dari kantin",
            "so_that": "saya tidak perlu mengantri lama di kantin"
          },
          {
            "id": "US-002",
            "as_a": "pemilik kantin",
            "i_want": "menerima pesanan secara digital",
            "so_that": "proses pemesanan lebih efisien"
          }
        ],
        "functional_requirements": [
          "Sistem registrasi dan login untuk mahasiswa dan pemilik kantin",
          "Fitur menampilkan daftar menu makanan beserta harga",
          "Fitur pemesanan makanan dengan keranjang belanja",
          "Integrasi pembayaran digital (e-wallet, QRIS)",
          "Notifikasi status pesanan real-time"
        ],
        "non_functional_requirements": [
          "Response time maksimal 2 detik",
          "Sistem mampu menangani 500 concurrent users",
          "Data pembayaran dienkripsi menggunakan standar PCI-DSS"
        ],
        "constraints": [
          "Budget pengembangan terbatas (project kampus)",
          "Deadline pengembangan 3 bulan"
        ],
        "stakeholders": [
          "Mahasiswa (pembeli)",
          "Pemilik kantin (penjual)",
          "Admin kampus",
          "Payment gateway provider"
        ],
        "project_id": "proj_001",
        "created_at": "2026-07-17T10:00:00+00:00",
        "agent": "business_analyst_agent_v1"
      }
    }
  ]
}
```

**Contoh Response** (Error):
```json
{
  "data": [
    {
      "status": "error",
      "message": "Deskripsi proyek tidak boleh kosong"
    }
  ]
}
```

### 8.2 API Chat (Interactive)

Gradio juga menyediakan endpoint chat untuk interaksi bertahap:

#### Endpoint: POST `/api/chat_respond`

**Deskripsi**: Endpoint interaktif — agent akan bertanya balik sebelum generate analisis.

**Request Body** (JSON):
```json
{
  "data": [
    "pesan dari user",
    [],
    "Nama Proyek",
    "project_id_opsional"
  ]
}
```

| Parameter | Tipe | Deskripsi |
|-----------|------|-----------|
| `data[0]` | string | Pesan dari user |
| `data[1]` | array | History chat (kosongkan `[]` untuk sesi baru) |
| `data[2]` | string | Nama proyek |
| `data[3]` | string | Project ID (kosongkan `""` untuk proyek baru) |

**Perintah Spesial**:
| Pesan | Fungsi |
|-------|--------|
| `/selesai` | Generate analisis berdasarkan percakapan yang sudah dilakukan |

### 8.3 Mengakses Dokumentasi API Otomatis

Gradio secara otomatis menyediakan halaman dokumentasi API interaktif:

```
http://localhost:7860/docs
```

Di halaman ini kamu bisa:
- Melihat semua endpoint yang tersedia
- Mencoba request langsung dari browser
- Melihat format request/response

---

## 🌐 9. Cloudflare Tunnel (Akses Publik)

**Ya, bisa!** Dengan Cloudflare Tunnel, kamu bisa membuat aplikasi yang berjalan di **localhost** bisa diakses secara **publik** melalui internet — tanpa perlu port forwarding, IP publik, atau VPS.

### 9.1 Apa itu Cloudflare Tunnel?

Cloudflare Tunnel membuat koneksi aman dari komputer kamu ke jaringan Cloudflare, sehingga siapapun bisa mengakses aplikasi lokal kamu via URL publik.

```
User di Internet → Cloudflare Edge → Tunnel → Laptop/PC Kamu (localhost:7860)
```

### 9.2 Cara Cepat (Tanpa Akun — Quick Tunnel)

Ini cara paling mudah untuk **testing** atau **demo cepat**:

#### Langkah 1: Download `cloudflared`

**Windows:**
```powershell
# Download via winget (Windows 10/11)
winget install --id Cloudflare.cloudflared

# Atau download manual dari:
# https://github.com/cloudflare/cloudflared/releases/latest
# Pilih: cloudflared-windows-amd64.exe
# Rename menjadi cloudflared.exe dan taruh di folder yang ada di PATH
```

**Mac:**
```bash
brew install cloudflared
```

**Linux:**
```bash
# Debian/Ubuntu
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# Atau download binary langsung
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/
```

#### Langkah 2: Jalankan Aplikasi (Terminal 1)

```bash
# Aktifkan venv dulu
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# Jalankan dalam mode serve
python main.py --serve
```

> Pastikan app sudah jalan di `http://localhost:7860`

#### Langkah 3: Buat Quick Tunnel (Terminal 2)

Buka terminal baru dan jalankan:

```bash
cloudflared tunnel --url http://localhost:7860
```

Output yang akan muncul:

```
2026-07-17T10:00:00Z INF +----------------------------+
2026-07-17T10:00:00Z INF |  Your quick Tunnel has been created!
2026-07-17T10:00:00Z INF +----------------------------+
2026-07-17T10:00:00Z INF |  https://random-name-here.trycloudflare.com
2026-07-17T10:00:00Z INF +----------------------------+
```

🎉 **Selesai!** URL `https://random-name-here.trycloudflare.com` bisa diakses siapapun di internet.

> ⚠️ Quick Tunnel menghasilkan URL **random** yang berubah setiap kali dijalankan ulang. Untuk URL permanen, gunakan Named Tunnel (lihat bagian 9.3).

### 9.3 Cara Permanen (Dengan Akun — Named Tunnel)

Untuk URL **permanen** dengan domain kustom:

#### Langkah 1: Buat Akun Cloudflare

1. Daftar di [dash.cloudflare.com](https://dash.cloudflare.com/) (gratis)
2. Opsional: tambahkan domain kamu ke Cloudflare (atau gunakan subdomain gratis)

#### Langkah 2: Login cloudflared

```bash
cloudflared tunnel login
```

Ini akan membuka browser untuk autentikasi. Pilih domain/zone yang ingin dipakai.

#### Langkah 3: Buat Named Tunnel

```bash
cloudflared tunnel create ba-agent
```

Output:
```
Created tunnel ba-agent with id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

#### Langkah 4: Buat Config File

Buat file `~/.cloudflared/config.yml`:

```yaml
tunnel: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  # Ganti dengan tunnel ID kamu
credentials-file: ~/.cloudflared/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.json

ingress:
  - hostname: ba-agent.domain-kamu.com  # Ganti dengan subdomain kamu
    service: http://localhost:7860
  - service: http_status:404
```

#### Langkah 5: Buat DNS Record

```bash
cloudflared tunnel route dns ba-agent ba-agent.domain-kamu.com
```

#### Langkah 6: Jalankan Tunnel

```bash
# Terminal 1: Jalankan app
python main.py --serve

# Terminal 2: Jalankan tunnel
cloudflared tunnel run ba-agent
```

🎉 Aplikasi kamu sekarang bisa diakses secara permanen di `https://ba-agent.domain-kamu.com`

### 9.4 Ringkasan Perbandingan

| Fitur | Quick Tunnel | Named Tunnel |
|-------|-------------|--------------|
| **Akun Cloudflare** | ❌ Tidak perlu | ✅ Perlu |
| **URL** | Random (berubah tiap kali) | Permanen (domain kustom) |
| **Setup** | 1 perintah | Beberapa langkah |
| **Cocok untuk** | Testing, demo cepat | Production, integrasi Orchestrator |
| **HTTPS** | ✅ Otomatis | ✅ Otomatis |
| **Biaya** | Gratis | Gratis (domain sendiri) |

### 9.5 Contoh Akses API via Cloudflare Tunnel

Setelah tunnel aktif, endpoint API bisa diakses dari mana saja:

```bash
# Ganti URL dengan URL tunnel kamu
curl -X POST https://random-name-here.trycloudflare.com/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "data": ["", "Buat sistem informasi perpustakaan digital"]
  }'
```

Ini artinya **Orchestrator Agent (#1)** atau agent lain bisa memanggil API ini dari server manapun di internet.

---

## ❓ 10. Troubleshooting

### Error: `LLM_API_KEY tidak ditemukan`
```
❌ Error: LLM_API_KEY tidak ditemukan di file .env
```
**Solusi**: Pastikan file `.env` sudah ada dan `LLM_API_KEY` sudah diisi. Cek juga tidak ada spasi di sekitar `=`.

---

### Error: `MONGODB_URI tidak ditemukan`
```
ValueError: MONGODB_URI tidak ditemukan di file .env
```
**Solusi**: Isi `MONGODB_URI` di file `.env` dengan connection string MongoDB Atlas kamu.

---

### Error: `ServerSelectionTimeoutError`
```
pymongo.errors.ServerSelectionTimeoutError: ...
```
**Solusi**:
1. Pastikan IP kamu sudah di-whitelist di MongoDB Atlas (Network Access)
2. Cek koneksi internet
3. Pastikan username/password di connection string benar

---

### Error: `Rate limit (429)`
```
⏳ Rate limit tercapai. Menunggu 10 detik...
```
**Solusi**: Ini normal — aplikasi otomatis retry. Jika sering terjadi:
- Gunakan provider yang lebih generous (Groq recommended)
- Tunggu beberapa menit sebelum mencoba lagi
- Upgrade ke tier berbayar jika perlu

---

### Error: `ModuleNotFoundError`
```
ModuleNotFoundError: No module named 'openai'
```
**Solusi**: Pastikan venv sudah aktif dan dependencies sudah diinstall:
```bash
venv\Scripts\activate           # Windows
source venv/bin/activate        # Mac/Linux
pip install -r requirements.txt
```

---

### Cloudflare Tunnel tidak bisa diakses
**Solusi**:
1. Pastikan app sudah running di `localhost:7860` sebelum menjalankan tunnel
2. Cek firewall tidak memblokir `cloudflared`
3. Untuk Quick Tunnel, pastikan port 7860 tidak dipakai aplikasi lain

---

### Gradio UI tidak muncul
**Solusi**: Pastikan menjalankan dengan flag `--serve`:
```bash
python main.py --serve    # ✅ benar
python main.py            # ❌ ini mode CLI, bukan web
```

---

## 📝 Catatan Penting

1. **Jangan commit `.env`** ke GitHub — file ini berisi kredensial sensitif
2. **Rotasi API key** secara berkala untuk keamanan
3. **Quick Tunnel** cocok untuk testing, gunakan **Named Tunnel** untuk production
4. Semua data tersimpan di **MongoDB Atlas** — bisa diakses dari mana saja
5. Hasil analisis juga disimpan sebagai **backup lokal** di folder `output/`

---

*Panduan ini dibuat untuk memudahkan siapapun menjalankan Business Analyst Agent. Jika ada pertanyaan, buat Issue di repository GitHub.*
