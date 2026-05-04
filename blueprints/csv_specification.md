# Spesifikasi File CSV Pengetahuan Diana AI

Untuk mengimpor pengetahuan baru ke dalam "Otak Diana", Anda harus menggunakan format CSV yang sesuai agar Diana dapat memiliki variasi jawaban dan kepribadian yang kaya.

## Struktur File (Wajib 4 Kolom)
File CSV tidak boleh memiliki header (baris judul) dan harus mengikuti urutan kolom berikut:

| Kolom | Nama | Deskripsi | Contoh |
| :--- | :--- | :--- | :--- |
| 1 | **Trigger** | Kata kunci atau pola Regex yang memicu respon. | `halo|hai|helo` atau `siapa penemu listrik` |
| 2 | **Response_1** | Variasi jawaban pertama (Utama). | `Halo. Sinkronisasi selesai. Ada yang bisa saya bantu?` |
| 3 | **Response_2** | Variasi jawaban kedua. | `Koneksi stabil. Sistem saya siap melayani Anda.` |
| 4 | **Response_3** | Variasi jawaban ketiga. | `Data diterima. Senang bertemu kembali dengan Anda.` |

## Aturan Penulisan
1. **Pemisah**: Gunakan koma (`,`) sebagai pemisah antar kolom.
2. **Tanda Petik**: Jika teks Anda mengandung koma, teks tersebut **wajib** diapit tanda petik ganda (`"`). Contoh: `"Tentu, ini datanya"`.
3. **Regex**: Anda bisa menggunakan simbol regex seperti `|` (atau), `\b` (batas kata), atau `.*` (apapun) di kolom Trigger untuk membuat pemicu yang lebih fleksibel.
4. **Variasi**: Semakin berbeda gaya bahasa antar Response_1, 2, dan 3, Diana akan terasa semakin alami dan tidak membosankan.

## Rekomendasi Konten (Layer 2-3)
Untuk membuat Diana terasa relevan dengan konteks Indonesia, masukkan topik-topik berikut:
- **Budaya:** Sejarah Kerajaan di Sulawesi, Tradisi Toraja, Legenda lokal.
- **Kuliner:** Resep Coto Makassar, asal-usul Rendang, tips memasak nasi kuning.
- **Teknologi:** Berita startup Indonesia, perkembangan Palapa Ring, keamanan siber lokal.

## Cara Mengimpor
1. Gunakan **Master Prompt** di `blueprints/master_prompt.md` untuk meminta data dari AI lain.
2. Simpan hasilnya sebagai file `.csv` (Pastikan encoding-nya UTF-8).
3. Buka Dashboard Diana -> Menu **Otak Diana** -> Klik **Import CSV**.
4. Diana akan secara otomatis me-reload memorinya.
