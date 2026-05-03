# Powder AI - Project Context & Documentation

## Deskripsi Proyek
Powder AI adalah asisten virtual (AI) sederhana berbasis lokal yang ditulis menggunakan bahasa pemrograman Python. Proyek ini berevolusi dari sebuah *chatbot* murni berbasis aturan (Rule-Based) menjadi sistem AI Hibrida (Campuran) yang menggabungkan kecepatan Rule-Based dengan kecerdasan Large Language Model (LLM) melalui integrasi Ollama.

## Arsitektur & Fitur Utama

1. **Rule-Based System (`powder.py`)**
   Sistem utama memproses input pengguna dan mencocokkannya dengan pola Regex. Jika ada kecocokan, AI akan mengembalikan jawaban secara instan (atau memanggil fungsi aksi).

2. **Deteksi & Koreksi Typo**
   Sistem memisahkan kalimat pengguna menjadi kata-kata, lalu menggunakan library bawaan Python `difflib` (`get_close_matches`) untuk mencocokkan input dengan daftar kosa kata (vocabulary) dengan toleransi kemiripan 70%. Hal ini membuat AI kebal terhadap kesalahan ketik (typo).

3. **Pemisahan Data (`respon/respon_powder.py`)**
   Semua data *knowledge* (pengetahuan), daftar respons (Regex), dan kosa kata dipisah ke dalam folder `respon`. File ini menyediakan fungsi `get_responses` dan `get_vocabulary`.

4. **Aksi Sistem (System Actions)**
   Powder memiliki kemampuan mengeksekusi aksi di luar chat, seperti:
   - `get_time()`: Menjawab waktu terkini menggunakan modul `datetime`.
   - `open_calculator()`: Membuka aplikasi kalkulator bawaan Windows menggunakan `subprocess.Popen('calc')`.

5. **Mode Latihan Dinamis (`powderLatihan/latihan.py`)**
   Jika pengguna mengetik **"waktunya latihan powder"**, program masuk ke mode *Training*. AI akan meminta "Pemicu" dan "Respon". Skrip akan membuka file `respon_powder.py` dan memodifikasi *source code*-nya secara otomatis untuk menyisipkan regex dan respons baru, lalu me-reload modul (`importlib.reload`) sehingga otak AI terbarui seketika tanpa harus di-restart.

6. **Fallback ke LLM Ollama (Qwen2 0.5b)**
   Jika *Rule-Based System* tidak menemukan jawaban atas pertanyaan pengguna, `powder.py` tidak menyerah. Sistem akan membuat HTTP Request lokal (`urllib.request`) ke API Ollama di `http://localhost:11434/api/generate` untuk meminta jawaban dari model `qwen2:0.5b`. Jika sukses, jawaban Ollama akan diteruskan ke pengguna. Jika Ollama mati atau belum diinstal, program kembali menggunakan default responses.

7. **Auto-Installer (`install_ollama.bat`)**
   Mengingat spesifikasi laptop yang terbatas (RAM 8GB), proyek ini menyertakan skrip `.bat` otomatis yang mengunduh `OllamaSetup.exe`, mengonfigurasi *Environment Variable* `OLLAMA_MODELS` ke folder lokal `modelAI` (di Drive non-C), menginstal Ollama secara *silent*, menyalakan *service*, dan otomatis mengunduh model `qwen2:0.5b` (model super ringan ~350MB).

## Struktur File
```text
powderAI/
├── powder.py                  (File utama/Loop utama program)
├── install_ollama.bat         (Skrip instalasi otomatis Ollama)
├── respon/
│   └── respon_powder.py       (Penyimpanan pola regex, jawaban, dan aksi)
├── powderLatihan/
│   └── latihan.py             (Mesin modifikasi kode otomatis untuk mode latihan)
├── modelAI/                   (Folder penyimpanan model LLM Ollama - dibuat otomatis)
└── skils/
    └── project_context.md     (File ini - Catatan perkembangan dan dokumentasi AI)
```

## Cara Menjalankan
Buka terminal/CMD di dalam direktori `powderAI` dan ketik:
```bash
python powder.py
```

## Catatan Tambahan Untuk AI Berikutnya
Jika Anda (Model AI) membaca file ini di masa depan, pahami bahwa Anda sedang membantu mengelola **Powder AI**. Harap sesuaikan bantuan Anda dengan struktur di atas. Jangan menginstal dependensi (pip) kecuali sangat dibutuhkan, karena filosofi proyek ini adalah menggunakan sebisa mungkin modul bawaan standar Python (seperti `difflib`, `urllib`, `re`) agar tetap "Sederhana dan Ringan".
