"""
Auto Learner Service — Optimized v2.0
======================================
Modul ini bertanggung jawab atas fitur "Latihan Mandiri" Diana.
Diana secara otomatis mencari pengetahuan baru dari model Ollama,
lalu menyimpannya ke database sebagai pola (intent) baru.

Optimasi dari v1:
- Generate langsung dalam Bahasa Indonesia (tanpa terjemahan) → hemat ~10 panggilan AI/batch
- Batch typo correction (1 panggilan) → hemat ~10 panggilan AI/batch
- Configurable batch_size, delay, max_variations
- Deduplikasi & variasi jawaban
- Session statistics tracking
- Thread-safe dengan Lock
"""

import threading
import time
import re
from database.db_manager import append_intent_response, get_setting, update_setting
from services.ollama_service import ask_ollama, get_first_available_model

# === STATE GLOBAL (Thread-Safe) ===
_lock = threading.Lock()
learning_thread = None
is_learning = False
end_time = 0
learned_items = []
active_model = ""

# Session stats — reset setiap sesi baru
session_stats = {
    "total_generated": 0,     # Total Q&A yang di-generate AI
    "total_saved": 0,         # Total yang berhasil disimpan
    "total_duplicates": 0,    # Total yang di-skip karena duplikat
    "total_errors": 0,        # Total error
    "batches_completed": 0,   # Total batch yang selesai
    "start_time": 0,          # Waktu mulai (unix timestamp)
    "items_per_minute": 0.0,  # Kecepatan belajar
}

# === CONFIGURABLE DEFAULTS ===
DEFAULT_BATCH_SIZE = 10
DEFAULT_DELAY = 1.0
DEFAULT_MAX_VARIATIONS = 5


def _batch_fix_typos(items, model, base_url):
    """Memperbaiki typo untuk batch Q&A sekaligus dalam 1 panggilan AI.
    
    Args:
        items: List of tuples [(tanya, jawab), ...]
        model: Nama model Ollama
        base_url: URL Ollama API
        
    Returns:
        List of tuples [(tanya_fixed, jawab_fixed), ...] 
    """
    if not items:
        return items
    
    # Bangun prompt batch
    lines = []
    for i, (t, j) in enumerate(items, 1):
        lines.append(f"{i}. T: {t}")
        lines.append(f"   J: {j}")
    
    batch_text = "\n".join(lines)
    
    prompt = (
        "Perbaiki typo dan ejaan dalam pasangan Tanya-Jawab berikut. "
        "Jangan ubah makna, hanya perbaiki ejaan agar baku. "
        "PENTING: Pertahankan format yang sama persis (nomor, T:, J:). "
        "Langsung berikan hasil perbaikan tanpa penjelasan apapun.\n\n"
        f"{batch_text}"
    )
    system = "Anda adalah spell-checker Bahasa Indonesia yang sangat akurat. Tugas Anda hanya memperbaiki ejaan."
    
    try:
        result = ask_ollama(prompt, model=model, base_url=base_url, system=system, 
                           options={"num_predict": 2000})
        if not result:
            return items  # Gagal → kembalikan asli
        
        # Parse hasil
        fixed_items = []
        pairs = re.findall(
            r'(\d+)\.\s*T:\s*(.*?)\s*J:\s*(.*?)(?=\d+\.\s*T:|$)', 
            result, re.DOTALL
        )
        
        if len(pairs) == len(items):
            for (_, t_fixed, j_fixed) in pairs:
                t_clean = t_fixed.strip().replace('"', '').replace("'", "").rstrip('.')
                j_clean = j_fixed.strip().replace('"', '').replace("'", "")
                if t_clean and j_clean:
                    fixed_items.append((t_clean, j_clean))
                else:
                    fixed_items.append(items[len(fixed_items)])  # Fallback ke asli
            return fixed_items
        
        # Jika parsing gagal, kembalikan asli
        return items
        
    except Exception as e:
        print(f"[Auto Learning] Batch typo fix gagal: {e}")
        return items


def _update_speed_stats():
    """Menghitung kecepatan belajar (items per menit)."""
    global session_stats
    if session_stats["start_time"] > 0:
        elapsed_minutes = (time.time() - session_stats["start_time"]) / 60
        if elapsed_minutes > 0:
            session_stats["items_per_minute"] = round(
                session_stats["total_saved"] / elapsed_minutes, 1
            )


def learning_loop(duration_minutes, model_name, topic="", batch_size=DEFAULT_BATCH_SIZE, 
                  delay_seconds=DEFAULT_DELAY, max_variations=DEFAULT_MAX_VARIATIONS):
    """Loop utama pembelajaran mandiri Diana.
    
    Optimasi v2: Generate langsung dalam Bahasa Indonesia,
    batch typo fix, configurable params, dedup + variasi jawaban.
    """
    global is_learning, end_time, learned_items, session_stats
    
    # Setup waktu
    if duration_minutes > 0:
        end_time = time.time() + (duration_minutes * 60)
        mode_text = f"{duration_minutes} menit"
    else:
        end_time = None
        mode_text = "Tanpa Batas Waktu (Manual Stop)"
    
    # Clamp batch_size ke range yang aman
    batch_size = max(3, min(batch_size, 20))
    
    topic_instruction = f"KHUSUS tentang topik '{topic}'" if topic else "seperti fakta sains, sejarah, budaya, atau teknologi"
    
    # === PROMPT v2: Langsung Bahasa Indonesia (tanpa perlu terjemahan) ===
    system_prompt = (
        f"Anda adalah sistem basis pengetahuan profesional. "
        f"Tugas Anda adalah menghasilkan pasangan pertanyaan dan jawaban {topic_instruction} "
        f"yang akurat dan bisa disimpan dalam database pengetahuan.\n\n"
        "ATURAN KETAT:\n"
        "- Gunakan Bahasa Indonesia yang BAKU dan formal.\n"
        "- Tulis pertanyaan seperti yang akan ditanyakan manusia biasa.\n"
        "- Jawab LANGSUNG dengan inti fakta, tanpa basa-basi atau pembuka.\n"
        "- Jangan gunakan kata 'saya', 'kamu', atau persona apapun.\n"
        "- Utamakan akurasi ilmiah dan sejarah.\n"
        "- Setiap pertanyaan harus UNIK dan BERBEDA satu sama lain.\n"
        "- Format: TANYA: [pertanyaan] JAWAB: [jawaban singkat dan padat]"
    )
    
    topic_msg = f" dengan fokus topik: {topic}" if topic else ""
    print(f"[Auto Learning v2] Memulai latihan selama {mode_text} | model: {model_name} | batch: {batch_size}{topic_msg}")
    
    batch_count = 0
    
    while is_learning:
        # Cek batas waktu
        if end_time and time.time() >= end_time:
            break
            
        try:
            batch_count += 1
            print(f"[Auto Learning] Batch #{batch_count} — Mencari {batch_size} pengetahuan baru...")
            
            # === STEP 1: Generate Q&A langsung dalam Bahasa Indonesia ===
            user_query = (
                f"Berikan {batch_size} pasangan pertanyaan dan jawaban yang berbeda-beda "
                f"tentang {topic if topic else 'pengetahuan umum yang bermanfaat'}. "
                "Pastikan setiap fakta AKURAT dan BERBEDA topiknya. "
                "Gunakan Bahasa Indonesia baku. "
                "Format setiap item: TANYA: [pertanyaan] JAWAB: [jawaban]. "
                "Pisahkan setiap item dengan baris baru. Langsung ke konten."
            )
            
            base_url = get_setting('ollama_api_url', 'http://localhost:11434')
            
            # Sesuaikan num_predict dengan batch_size
            predict_tokens = min(batch_size * 200, 4000)
            
            res = ask_ollama(
                user_query, model=model_name, system=system_prompt, 
                options={"num_predict": predict_tokens}, base_url=base_url
            )
            
            if not res:
                print("[Auto Learning] Tidak ada respons dari model, mencoba lagi...")
                session_stats["total_errors"] += 1
                time.sleep(delay_seconds * 2)
                continue
            
            # === STEP 2: Parse semua Q&A dari respons ===
            blocks = re.findall(
                r"(?:TANYA|Pertanyaan):?\s*(.*?)\s*(?:JAWAB|Jawaban):?\s*(.*?)(?=(?:TANYA|Pertanyaan)|$)", 
                res, re.DOTALL | re.IGNORECASE
            )
            
            if not blocks:
                print("[Auto Learning] Format respons tidak sesuai, mencoba lagi...")
                session_stats["total_errors"] += 1
                time.sleep(delay_seconds)
                continue
            
            # Bersihkan hasil parsing
            raw_items = []
            for tanya, jawab in blocks:
                t_clean = tanya.strip().replace("**", "").replace("*", "").strip('"').strip("'")
                j_clean = jawab.strip().replace("**", "").replace("*", "").strip('"').strip("'")
                
                # Filter: minimal 5 karakter untuk tanya dan jawab
                if len(t_clean) >= 5 and len(j_clean) >= 5:
                    raw_items.append((t_clean, j_clean))
            
            session_stats["total_generated"] += len(raw_items)
            
            if not raw_items:
                print("[Auto Learning] Tidak ada item valid dari batch ini.")
                time.sleep(delay_seconds)
                continue
            
            # === STEP 3: Batch Typo Fix (1 panggilan AI untuk semua) ===
            print(f"[Auto Learning] Memperbaiki ejaan {len(raw_items)} item (batch)...")
            fixed_items = _batch_fix_typos(raw_items, model_name, base_url)
            
            # === STEP 4: Simpan ke Database dengan Variasi ===
            saved_in_batch = 0
            dupes_in_batch = 0
            
            for t_fixed, j_fixed in fixed_items:
                if not is_learning:
                    break
                    
                # Gunakan append_intent_response untuk mendukung variasi jawaban
                # Pattern disimpan lowercase untuk konsistensi matching
                pattern = t_fixed.lower().strip()
                
                try:
                    append_intent_response(pattern, j_fixed, max_variations=max_variations)
                    
                    with _lock:
                        learned_items.append({"tanya": t_fixed, "jawab": j_fixed})
                    
                    saved_in_batch += 1
                    session_stats["total_saved"] += 1
                    update_setting('last_learned_topic', f"{t_fixed} | {j_fixed}")
                    print(f"[Auto Learning] ✓ TERSIMPAN: {t_fixed[:50]}...")
                    
                except Exception as e:
                    print(f"[Auto Learning] Gagal menyimpan: {e}")
                    session_stats["total_errors"] += 1
            
            session_stats["batches_completed"] += 1
            _update_speed_stats()
            
            print(f"[Auto Learning] Batch #{batch_count} selesai: {saved_in_batch} tersimpan, {dupes_in_batch} duplikat")
            
            # Delay antar batch
            time.sleep(delay_seconds)
            
        except Exception as e:
            print(f"[Auto Learning] ERROR: {e}")
            session_stats["total_errors"] += 1
            time.sleep(delay_seconds * 3)
            
    is_learning = False
    _update_speed_stats()
    print(f"[Auto Learning] Sesi selesai. Total: {session_stats['total_saved']} tersimpan, "
          f"{session_stats['total_duplicates']} duplikat, {session_stats['total_errors']} error, "
          f"kecepatan: {session_stats['items_per_minute']} items/menit")


def start_learning(minutes, topic="", model_name=None, batch_size=DEFAULT_BATCH_SIZE,
                   delay_seconds=DEFAULT_DELAY, max_variations=DEFAULT_MAX_VARIATIONS):
    """Memulai sesi latihan mandiri baru.
    
    Args:
        minutes: Durasi latihan (0 = tanpa batas)
        topic: Topik spesifik (opsional)
        model_name: Nama model Ollama (None = auto-detect)
        batch_size: Jumlah Q&A per batch (3-20, default 10)
        delay_seconds: Jeda antar batch dalam detik (0.5-10, default 1)
        max_variations: Maks variasi jawaban per pattern (1-10, default 5)
    
    Returns:
        Tuple (success: bool, message: str)
    """
    global learning_thread, is_learning, end_time, learned_items, active_model, session_stats
    
    # Cek apakah thread benar-benar masih hidup
    if is_learning and learning_thread and learning_thread.is_alive():
        return False, "Sudah ada sesi latihan yang berjalan."
    
    # Reset status tersangkut
    if is_learning:
        print("[Auto Learning] Deteksi status tersangkut, mereset...")
        is_learning = False
        
    # Resolve model
    base_url = get_setting('ollama_api_url', 'http://localhost:11434')
    model = model_name if model_name else get_setting('ollama_model', get_first_available_model(base_url))
    
    if not model:
        return False, "Tidak ada model Ollama yang tersedia. Pastikan Ollama sudah dijalankan."
    
    # Clamp parameters
    batch_size = max(3, min(int(batch_size), 20))
    delay_seconds = max(0.5, min(float(delay_seconds), 10.0))
    max_variations = max(1, min(int(max_variations), 10))
    
    # Reset state untuk sesi baru
    learned_items = []
    active_model = model
    session_stats = {
        "total_generated": 0,
        "total_saved": 0,
        "total_duplicates": 0,
        "total_errors": 0,
        "batches_completed": 0,
        "start_time": time.time(),
        "items_per_minute": 0.0,
    }
    
    is_learning = True
    learning_thread = threading.Thread(
        target=learning_loop, 
        args=(minutes, model, topic, batch_size, delay_seconds, max_variations), 
        daemon=True
    )
    learning_thread.start()
    
    topic_msg = f" tentang '{topic}'" if topic else ""
    return True, f"Sesi latihan dimulai selama {minutes} menit{topic_msg} menggunakan model {model} (batch: {batch_size})."


def stop_learning():
    """Menghentikan sesi latihan mandiri secara manual."""
    global is_learning, learning_thread
    if not is_learning:
        is_learning = False
        learning_thread = None
        return True, "Status latihan sudah dalam keadaan berhenti."
    
    is_learning = False
    learning_thread = None
    return True, "Sesi latihan telah dihentikan secara manual."


def get_status():
    """Mendapatkan status sesi latihan saat ini termasuk statistik performa."""
    global is_learning, end_time, learned_items, learning_thread, session_stats
    
    # Self-heal: cek apakah thread masih hidup
    if is_learning and (not learning_thread or not learning_thread.is_alive()):
        is_learning = False
    
    if is_learning:
        _update_speed_stats()
        
        if end_time is None:
            time_str = "Infinite"
        else:
            remaining_seconds = int(end_time - time.time())
            if remaining_seconds <= 0:
                is_learning = False
                return {
                    "is_learning": False, "status": "inactive", 
                    "learned_items": learned_items, "session_stats": session_stats
                }
            minutes, seconds = divmod(remaining_seconds, 60)
            time_str = f"{minutes:02d}:{seconds:02d}"

        return {
            "is_learning": True,
            "status": "active",
            "time_remaining": time_str,
            "model_name": active_model,
            "learned_items": learned_items,
            "session_stats": session_stats,
        }
    
    return {
        "is_learning": False, "status": "inactive", 
        "learned_items": learned_items, "session_stats": session_stats
    }
