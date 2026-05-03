# 🛠️ Panduan Menjalankan Powder AI (Arsitektur Baru)

Selamat! Powder AI sekarang menggunakan struktur folder profesional yang lebih rapi dan kencang.

## 🚀 Cara Menjalankan
Cukup jalankan satu file utama di folder root:
```bash
python main.py
```

## 📂 Struktur Proyek
- `main.py`: Titik masuk utama aplikasi.
- `core/`: Berisi logika utama (AI Engine, Browser, Analyzer, Actions).
- `api/`: Berisi server Flask dan rute komunikasi.
- `database/`: Berisi manajemen database SQLite.
- `utils/`: Berisi fungsi pembantu (Text processing, Trainer).
- `frontend/`: Folder antarmuka Astro.

## 📦 Requirements
Pastikan Anda sudah menginstal library terbaru:
```bash
pip install -r docs/requirements.txt
```

---
**Sekarang semuanya sudah tertata rapi! Selamat menikmati Powder AI yang lebih profesional.**
