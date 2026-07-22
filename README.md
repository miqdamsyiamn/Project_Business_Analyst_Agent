# 🤖 Agent #2 — Business Analyst Agent

Bagian dari project **AI Software Development Team** — sistem multi-agent yang mensimulasikan tim pengembangan software secara otomatis menggunakan AI.

---

## 🏗️ Gambaran Besar Project

Project ini terdiri dari **21 Agent AI** yang masing-masing dikerjakan oleh satu orang. Semua agent bekerja dalam satu pipeline besar yang dikoordinasikan oleh **Orchestrator Agent (#1)**.

```
User Input
    ↓
Orchestrator Agent #1  ← menghubungkan semua 21 agent via API
    ↓
Agent #2 → Agent #3 → Agent #4 → ... → Agent #21
```

Daftar seluruh agent dalam project besar ini:

| No | Agent | Tanggung Jawab |
|----|-------|----------------|
| 1 | Orchestrator Agent | Mengelola workflow dan koordinasi antar-agent |
| **2** | **Business Analyst Agent** | **Analisis kebutuhan bisnis dan user story ← BAGIAN INI** |
| 3 | Product Manager Agent | Menentukan roadmap, MVP, dan prioritas fitur |
| 4 | Project Planner Agent | Menyusun sprint, timeline, dan task |
| 5 | System Analyst Agent | Menyusun SRS dan analisis sistem |
| 6 | Software Architect Agent | Mendesain arsitektur aplikasi |
| 7 | Database Designer Agent | Mendesain ERD, skema database, dan migrasi |
| 8 | UI Designer Agent | Mendesain wireframe dan antarmuka |
| 9 | UX Designer Agent | Mendesain alur penggunaan dan pengalaman pengguna |
| 10 | API Designer Agent | Mendesain kontrak API (OpenAPI/Swagger) |
| 11 | Backend Developer Agent | Mengembangkan backend dan business logic |
| 12 | Frontend Developer Agent | Mengembangkan antarmuka web |
| 13 | Mobile Developer Agent | Mengembangkan aplikasi mobile |
| 14 | AI Engineer Agent | Mengembangkan fitur AI, RAG, dan integrasi LLM |
| 15 | DevOps Agent | Deployment, Docker, CI/CD, dan monitoring |
| 16 | Unit Testing Agent | Menulis unit test |
| 17 | Integration Testing Agent | Menguji integrasi antar-komponen |
| 18 | Security Agent | Audit keamanan aplikasi |
| 19 | Code Reviewer Agent | Review kode, refactoring, dan optimasi |
| 20 | Documentation Agent | Menulis dokumentasi teknis dan pengguna |
| 21 | Presentation Agent | Menyiapkan PPT, demo, dan presentasi |

---

## 📌 Deskripsi Agent #2

Business Analyst Agent bertugas sebagai analis kebutuhan bisnis. Agent ini menerima deskripsi proyek dari user atau Orchestrator, lalu menghasilkan dokumen analisis kebutuhan yang terstruktur dalam format JSON — yang kemudian akan dibaca oleh agent-agent lain seperti Product Manager Agent (#3) dan System Analyst Agent (#5).

**Posisi dalam pipeline:**

```
User Input / Orchestrator Agent #1
    ↓
[Agent #2 — Business Analyst]  ← kamu di sini
    ↓
Simpan ke MongoDB Atlas (collection: business_analysis)
    ↓
Agent #3 (Product Manager) & Agent #5 (System Analyst)
```

---

## 🛠️ Tech Stack

| Komponen | Teknologi |
|----------|-----------|
| **Language** | Python 3.10+ |
| **LLM API** | Google Gemini API (model: gemini-1.5-flash) |
| **Database** | MongoDB Atlas |
| **DB Name** | `BaAgent` |
| **Collections** | `projects`, `business_analysis`, `conversations` |
| **Deploy** | Hugging Face Spaces |
| **Framework** | ❌ tidak pakai framework (manual) |

---

## 🗄️ Database MongoDB Atlas

### Nama Database
```
BaAgent
```

### Collections


```
BaAgent
│
├── 📁 projects
│   └── Menyimpan informasi dasar proyek yang diinput user
│       Field: project_id, project_name, description, status, created_at
│
├── 📁 business_analysis
│   └── Menyimpan hasil analisis kebutuhan bisnis dari agent ini
│       Field: project_id, user_stories, functional_requirements,
│              non_functional_requirements, constraints, stakeholders, created_at
│
└── 📁 conversations
    └── Menyimpan histori percakapan antara user dan agent
        Field: project_id, role, message, timestamp
```

### Struktur Dokumen `conversations`
```json
{
  "_id": "ObjectId(...)",
  "project_id": "proj_001",
  "role": "user",
  "message": "Buat aplikasi pemesanan makanan untuk kantin kampus",
  "timestamp": "2026-07-08T10:00:00Z"
}
```

> `role` bisa berisi `"user"` (pesan dari user) atau `"agent"` (response dari BA Agent)

### Struktur Dokumen `projects`
```json
{
  "_id": "ObjectId(...)",
  "project_id": "proj_001",
  "project_name": "App Toko Online",
  "description": "Aplikasi pemesanan makanan untuk kantin kampus",
  "status": "in_progress",
  "created_at": "2026-07-08T10:00:00Z"
}
```

### Struktur Dokumen `business_analysis`
```json
{
  "_id": "ObjectId(...)",
  "project_id": "proj_001",
  "user_stories": [
    {
      "id": "US-001",
      "as_a": "pelanggan",
      "i_want": "memesan makanan secara online",
      "so_that": "saya tidak perlu antri di kantin"
    }
  ],
  "functional_requirements": [
    "User dapat mendaftar dan login",
    "User dapat melihat menu makanan",
    "User dapat melakukan pemesanan"
  ],
  "non_functional_requirements": [
    "Aplikasi harus bisa diakses dari mobile",
    "Response time tidak lebih dari 2 detik"
  ],
  "constraints": [
    "Budget terbatas",
    "Deadline 3 bulan"
  ],
  "stakeholders": [
    "Mahasiswa (pembeli)",
    "Pemilik kantin (penjual)",
    "Admin kampus"
  ],
  "created_at": "2026-07-08T10:00:00Z",
  "agent": "business_analyst_agent_v1"
}
```

---

## 📤 Output yang Dihasilkan

Agent ini menghasilkan 2 output:

1. **MongoDB Atlas** — disimpan di collection `business_analysis` (utama)
2. **File lokal** `output/business_analysis.json` — sebagai backup

---

## 📁 Struktur Folder

```
business-analyst-agent/
│
├── main.py              ← file utama, jalankan ini
├── prompt.py            ← system prompt untuk Gemini
├── database.py          ← koneksi dan operasi MongoDB
├── .env                 ← kredensial (JANGAN di-share atau di-commit!)
├── .env.example         ← contoh format .env
├── requirements.txt     ← daftar library yang dibutuhkan
├── README.md            ← file ini
│
└── output/
    └── business_analysis.json   ← backup lokal hasil agent
```

---

## ⚙️ Cara Menjalankan (Lokal)

### 1. Pastikan Python sudah terinstall

```bash
python --version
# Output yang diharapkan: Python 3.10 ke atas
```

### 2. Buat dan aktifkan Virtual Environment (venv)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac / Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

> Kalau berhasil, nama `(venv)` akan muncul di awal terminal kamu.
> Jalankan perintah ini setiap kali buka terminal baru sebelum menjalankan project.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup kredensial di file `.env`

Salin file `.env.example` menjadi `.env`:

```bash
cp .env.example .env
```

Isi file `.env` dengan kredensial kamu:

```
GEMINI_API_KEY=isi_gemini_api_key_kamu
MONGODB_URI=isi_mongodb_connection_string_kamu
```

Cara dapat kredensial:
- **Gemini API Key** → daftar di [aistudio.google.com](https://aistudio.google.com) → gratis
- **MongoDB URI** → daftar di [mongodb.com/atlas](https://mongodb.com/atlas) → gratis, pilih DB: `BaAgent`

> ⚠️ Jangan pernah share atau commit file `.env` ke GitHub!
> ⚠️ Pastikan folder `venv/` sudah masuk `.gitignore`!

### 5. Jalankan agent

```bash
python main.py
```

Agent akan meminta input deskripsi proyek, lalu menyimpan hasilnya ke MongoDB dan file lokal.

### 6. Nonaktifkan venv setelah selesai

```bash
deactivate
```

---

## 📦 Dependencies

File `requirements.txt`:
```
google-generativeai
pymongo
python-dotenv
```

Install sekaligus (pastikan venv sudah aktif):

```bash
pip install -r requirements.txt
```

---

## 🚀 Deploy ke Hugging Face Spaces

Agent ini di-deploy di **Hugging Face Spaces** agar bisa diakses oleh Orchestrator Agent (#1) dan agent lain via HTTP request.

### Langkah Deploy

1. Daftar di [huggingface.co](https://huggingface.co) jika belum punya akun
2. Buat Space baru → pilih **Gradio** atau **Docker** sebagai SDK
3. Upload semua file project ke Space
4. Tambahkan kredensial di **Settings → Repository Secrets**:
   ```
   GEMINI_API_KEY = isi_gemini_api_key_kamu
   MONGODB_URI    = isi_mongodb_connection_string_kamu
   ```
5. Agent akan otomatis jalan dan punya URL publik:
   ```
   https://huggingface.co/spaces/username/ba-agent
   ```

### Endpoint yang Tersedia (setelah deploy)

```
POST https://username-ba-agent.hf.space/analyze

Body (JSON):
{
  "project_id": "proj_001",
  "description": "Buat app toko online untuk kantin kampus"
}

Response (JSON):
{
  "status": "success",
  "project_id": "proj_001",
  "result": { ... hasil analisis ... }
}
```

---

## 🔗 Hubungan dengan Agent Lain

| Agent | Hubungan | Keterangan |
|-------|----------|------------|
| **#1 Orchestrator** | Memanggil agent ini | Orchestrator yang memulai dan menghubungkan semua 21 agent |
| **#3 Product Manager** | Membaca output agent ini | Menggunakan user stories untuk buat roadmap |
| **#5 System Analyst** | Membaca output agent ini | Menggunakan functional req untuk buat SRS |
| **#6 Software Architect** | Membaca output agent ini | Menggunakan constraints untuk desain arsitektur |

---

## 📋 Tanggung Jawab Agent Ini

- [x] Menerima deskripsi proyek dari user atau Orchestrator
- [x] Mengidentifikasi stakeholder yang terlibat
- [x] Menghasilkan user stories dalam format standar
- [x] Mendefinisikan functional requirements
- [x] Mendefinisikan non-functional requirements
- [x] Mencatat constraints proyek
- [x] Menyimpan hasil ke MongoDB Atlas (collection: `business_analysis`)
- [x] Menyimpan backup lokal ke `output/business_analysis.json`

---

## 👤 Pengembang

| Nama | NIM | Agent |
|------|-----|-------|
| *(isi nama kamu)* | *(isi NIM kamu)* | #2 Business Analyst Agent |

---

## 📝 Catatan untuk Tim

- Hasil analisis disimpan di **MongoDB Atlas** DB `BaAgent`, collection `business_analysis` — agent lain cukup query dengan `project_id` yang sama.
- Struktur JSON adalah **kontrak data** — jangan diubah tanpa koordinasi dengan tim.
- Kalau ada perubahan struktur, update juga README ini.
- `GEMINI_API_KEY` dan `MONGODB_URI` disimpan di file `.env` (lokal) dan **Hugging Face Secrets** (saat deploy) — tidak boleh di-commit ke Git.
- Pastikan `.env` sudah masuk `.gitignore`.
