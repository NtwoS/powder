# 🛠️ Panduan Menjalankan Diana AI (Arsitektur Baru)

Selamat! Diana AI sekarang menggunakan struktur folder profesional yang lebih rapi dan kencang.

## 🚀 Cara Menjalankan
Cukup jalankan satu file utama di folder root:
```bash
run_diana.bat
```

## 📂 Struktur Proyek
- `run_diana.bat`: Launcher utama untuk menyalakan Backend dan Frontend sekaligus.
- `backend/`: Berisi logika utama (Diana Engine, API, Database, Services).
- `frontend/`: Folder antarmuka modern berbasis Astro.
- `database/`: Berisi manajemen database SQLite (diana.db).
- `blueprints/`: Panduan kepribadian dan spesifikasi data Diana.

## 📦 Requirements
Pastikan Anda sudah menginstal library terbaru:
```bash
pip install -r requirements.txt
cd frontend && npm install
```

---
**Sekarang semuanya sudah tertata rapi! Selamat menikmati Diana AI yang lebih cerdas dan elegan.**
