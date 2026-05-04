# Diana AI - Project Context & Documentation

## Deskripsi Proyek
Diana AI (sebelumnya Powder AI) adalah asisten virtual (AI) hibrida berbasis lokal yang menggabungkan kecepatan pemrosesan berbasis aturan (Regex) dengan kecerdasan Large Language Model (LLM) melalui integrasi Ollama. Diana dirancang dengan persona gadis android futuristik dari masa depan (terinspirasi dari Pragmata) yang tenang, cerdas, dan suportif.

## Arsitektur & Fitur Utama

1. **Sistem Hibrida (`diana.py`)**
   Sistem memproses input pengguna melalui beberapa lapisan:
   - **Regex Precision**: Pencocokan pola yang sangat akurat.
   - **Semantic Matching**: Menggunakan TF-IDF & Cosine Similarity untuk memahami maksud meskipun kata-katanya berbeda.
   - **Ollama Fallback**: Jika data lokal tidak ditemukan, Diana bertanya kepada "otak cadangan" (Ollama Qwen2).

2. **Pembelajaran Interaktif (Interactive Learning)**
   Diana memiliki kemampuan belajar secara langsung:
   - **Koreksi**: Pengguna bisa mengoreksi jawaban Diana secara instan.
   - **Inquiry**: Jika tidak tahu, Diana bertanya kepada pengguna dan menyinkronkan data baru ke memori permanennya.

3. **Deteksi & Koreksi Typo**
   Menggunakan `difflib` untuk memastikan input pengguna tetap dipahami meskipun terjadi kesalahan pengetikan ringan (toleransi 70%).

4. **Database SQLite (`database/diana.db`)**
   Semua pengetahuan, riwayat percakapan, dan pengaturan disimpan dalam database SQLite profesional, menggantikan sistem file JSON/Python statis sebelumnya.

5. **Antarmuka Modern (Astro Frontend)**
   Dashboard berbasis web yang elegan dengan fitur:
   - Chatting real-time.
   - Manajemen Otak (Intents Management).
   - Skill & Tugas (Latihan Mandiri & Keuangan).
   - Pengaturan Model Ollama & Auto-Learning.

6. **Web Search Integration**
   Diana dapat mencari informasi terkini di internet menggunakan DuckDuckGo Search API.

## Struktur Proyek
```text
powderAI/ (Root Folder)
├── diana.py                    (Logika inti AI)
├── run_diana.bat               (Launcher utama)
├── backend/
│   ├── app.py                  (Server API Flask)
│   ├── database/               (Manajemen SQLite)
│   ├── services/               (Ollama & Auto-Learning service)
│   └── respon/                 (Data respon dasar & profil)
├── frontend/                   (Antarmuka web modern)
├── blueprints/                 (Panduan persona & spesifikasi data)
└── docs/                       (Dokumentasi & Setup Guide)
```

## Cara Menjalankan
Cukup jalankan file `run_diana.bat` di root directory. Sistem akan menyalakan Backend dan Frontend secara otomatis.

## Filosofi
Diana AI dibangun untuk menjadi asisten yang "Sederhana, Ringan, dan Belajar". Fokus utamanya adalah pada interaksi yang bermakna dan pertumbuhan pengetahuan yang didorong oleh pengguna.
