# 📖 Panduan Setup Diana AI

## Tata Cara Menjalankan Diana di Device Baru

---

## 🔧 Software yang HARUS Diinstal

### 1. Python (Versi 3.10+)
- **Download**: https://www.python.org/downloads/
- **PENTING**: Saat install, centang ✅ **"Add Python to PATH"**
- Cek instalasi: buka CMD, ketik `python --version`

### 2. Node.js (Versi 18+)
- **Download**: https://nodejs.org/ (pilih versi LTS)
- Cek instalasi: buka CMD, ketik `node --version`

### 3. Git (Opsional, untuk clone dari GitHub)
- **Download**: https://git-scm.com/downloads
- Cek instalasi: buka CMD, ketik `git --version`

---

## 📥 Cara Download Project

### Opsi A: Clone dari GitHub
```bash
git clone https://github.com/NtwoS/powder.git
cd powder
```

### Opsi B: Download ZIP
1. Buka https://github.com/NtwoS/powder
2. Klik tombol hijau **"Code"** → **"Download ZIP"**
3. Extract ke folder pilihan Anda

---

## 🚀 Cara Menjalankan Diana

### Langkah 1: Buka folder project
Buka folder tempat Anda menyimpan Diana AI (contoh: `D:\DianaAI\`)

### Langkah 2: Double-klik `run_diana.bat`
Script ini akan otomatis:
- ✅ Cek Python & Node.js terinstall
- ✅ Install semua Python dependencies (`pip install`)
- ✅ Install semua Frontend dependencies (`npm install`)
- ✅ Jalankan Backend (port 5050)
- ✅ Jalankan Frontend (port 4321)
- ✅ Monitor status Diana setiap 15 detik

### Langkah 3: Buka browser
Pergi ke: **http://localhost:4321**

---

## 🛑 Cara Mematikan Diana

Double-klik **`stop_diana.bat`** — otomatis menghentikan semua proses.

---

## 📂 Struktur Folder Project

```
DianaAI/
├── run_diana.bat          ← Jalankan Diana
├── stop_diana.bat         ← Matikan Diana
├── requirements.txt       ← Daftar library Python
│
├── backend/               ← Otak Diana (Python Flask)
│   ├── app.py             ← Server API utama
│   ├── diana.py           ← Logika AI & personality Diana
│   ├── data/
│   │   └── diana.db       ← Database pengetahuan (SQLite)
│   ├── database/
│   │   └── db_manager.py  ← Pengelola database
│   ├── respon/
│   │   └── respon_diana.py ← Respons & kepribadian bawaan
│   └── services/
│       ├── ollama_service.py      ← Koneksi ke Ollama (AI lokal)
│       ├── gemini_service.py      ← Koneksi ke Google Gemini
│       └── translation_service.py ← Layanan terjemahan
│
├── frontend/              ← Tampilan Web (Astro)
│   ├── src/
│   │   ├── pages/         ← Halaman web
│   │   └── styles/        ← CSS styling
│   └── package.json       ← Daftar library Node.js
│
├── blueprints/            ← Panduan pengembangan Diana
└── docs/                  ← Dokumentasi (folder ini)
```

---

## ⚙️ Konfigurasi Opsional

### Menggunakan AI Lokal (Ollama)
1. **Download Ollama**: https://ollama.ai
2. Install dan jalankan Ollama
3. Download model: `ollama pull llama3.2` (atau model lain)
4. Diana akan otomatis mendeteksi model Ollama yang tersedia

### Menggunakan Google Gemini
1. Dapatkan API key dari: https://aistudio.google.com/apikey
2. Buka Diana → Settings → masukkan Gemini API Key
3. Pilih "Gemini" sebagai Fallback Brain

---

## 🔍 Troubleshooting

### "python tidak ditemukan"
→ Install Python dan pastikan centang "Add to PATH" saat install

### "npm tidak ditemukan" / "astro tidak ditemukan"
→ Install Node.js dari https://nodejs.org/

### Diana tidak merespon / timeout
→ Pastikan backend berjalan (cek jendela CMD "Diana AI - Backend")
→ Buka http://127.0.0.1:5050/status di browser untuk cek

### Port 5050 sudah dipakai
→ Jalankan `stop_diana.bat` dulu, lalu `run_diana.bat` lagi

### Database error / Diana lupa semua
→ Hapus file `backend/data/diana.db` — akan dibuat ulang otomatis

---

## 📋 Daftar Library Python (requirements.txt)

| Library | Fungsi |
|---------|--------|
| flask | Server API backend |
| flask-cors | Izinkan akses dari frontend |
| scikit-learn | Pencocokan semantik (TF-IDF) |
| deep-translator | Terjemahan online |
| requests | HTTP requests ke Ollama/Gemini |
| duckduckgo-search | Pencarian web |
| google-generativeai | Google Gemini API |

---

## 📝 Catatan Penting

- **Database** (`diana.db`) menyimpan semua pengetahuan Diana. 
  Jika Anda pindah device, copy file ini agar Diana tetap ingat.
- **`user_profile.json`** menyimpan nama pengguna.
- Semua path sudah menggunakan relative path, jadi bisa 
  dijalankan dari folder mana saja tanpa perlu edit kode.
