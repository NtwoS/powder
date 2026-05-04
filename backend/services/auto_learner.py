import threading
import time
from database.db_manager import add_new_intent, get_setting, update_setting
from services.ollama_service import ask_ollama

learning_thread = None
is_learning = False
end_time = 0
learned_items = []

def learning_loop(duration_minutes, model_name, topic=""):
    global is_learning, end_time, learned_items
    end_time = time.time() + (duration_minutes * 60)
    
    topic_instruction = f"KHUSUS tentang topik '{topic}'" if topic else "seperti fakta sains, sejarah, atau teknologi"
    
    # Prompt Generator dengan Gaya Diana (Pragmata)
    system_prompt = (
        f"Anda adalah Diana, asisten android futuristik yang sangat cerdas dan tenang. "
        f"Tugas Anda adalah merangkum satu pengetahuan fundamental tentang {topic_instruction} "
        f"untuk diintegrasikan ke dalam database masa depan.\n\n"
        "VARIASI GAYA (Pilih salah satu):\n"
        "1. ANALISIS DATA: 'Berdasarkan data yang saya kumpulkan, [Konsep] adalah...'\n"
        "2. PENGAMATAN: 'Dalam pengamatan saya, [Konsep] memiliki pola...'\n"
        "3. SINKRONISASI: 'Hasil sinkronisasi informasi menunjukkan bahwa [Konsep]...'\n\n"
        "ATURAN KETAT:\n"
        "- Jawaban harus ditulis secara TENANG, CERDAS, dan FUTURISTIK.\n"
        "- Gunakan Bahasa Indonesia yang sopan (gunakan 'Anda').\n"
        "- JANGAN gunakan gaya Jinx (jangan ada tawa atau ledakan).\n"
        "- Format harus tetap TANYA: [pertanyaan] dan JAWAB: [jawaban]."
    )

    # Prompt Validator
    validator_prompt = (
        "Anda adalah pemeriksa fakta (fact-checker) profesional. Tugas Anda adalah memvalidasi pasangan Pertanyaan dan Jawaban. "
        "Apakah pertanyaan tersebut logis? Apakah jawabannya benar secara faktual, formal, dan nyambung dengan pertanyaannya? "
        "Balas hanya dengan satu kata: 'VALID' jika benar dan masuk akal, atau 'INVALID' jika salah, ngawur, atau tidak logis. "
        "Jangan berikan penjelasan apa pun, hanya satu kata."
    )
    
    topic_msg = f" dengan fokus topik: {topic}" if topic else ""
    print(f"[Auto Learning] Memulai latihan mandiri secara PROFESIONAL selama {duration_minutes} menit dengan model {model_name}{topic_msg}.")
    
    while is_learning and time.time() < end_time:
        try:
            print("[Auto Learning] Mencari pengetahuan (Mode Cepat & Akurat)...")
            # Prompt yang menyuruh AI memvalidasi dirinya sendiri dalam satu langkah
            user_query = (
                f"Berikan 1 pengetahuan dasar tentang {topic if topic else 'hal bermanfaat'}. "
                "SYARAT: Pastikan fakta ini 100% akurat secara ilmiah/faktual. Jika Anda tidak yakin, berikan fakta lain yang lebih pasti. "
                "Format wajib TANYA: [pertanyaan] JAWAB: [jawaban]. Singkat saja!"
            )
            
            res = ask_ollama(user_query, model=model_name, system=system_prompt, options={"num_predict": 120})
            
            if res:
                res_upper = res.upper()
                if "TANYA:" in res_upper and "JAWAB:" in res_upper:
                    tanya_idx = res_upper.find("TANYA:")
                    jawab_idx = res_upper.find("JAWAB:")
                    
                    tanya = res[tanya_idx+6:jawab_idx].strip().replace("**", "").replace("*", "")
                    jawab = res[jawab_idx+6:].strip().replace("**", "").replace("*", "")
                    
                    if tanya and jawab:
                        # Langsung simpan tanpa validasi kedua (Ngebut Mode)
                        add_new_intent(tanya, jawab)
                        learned_items.append({"tanya": tanya, "jawab": jawab})
                        update_setting('last_learned_topic', f"{tanya} | {jawab}")
                        print(f"[Auto Learning] TERSIMPAN: {tanya[:50]}...")
                else:
                    print("[Auto Learning] Format tidak pas, mencoba lagi...")
            
            # Jeda minimal agar tidak spamming tapi tetap cepat
            time.sleep(1)
        except Exception as e:
            print(f"[Auto Learning] ERROR: {e}")
            time.sleep(5)
            
    is_learning = False
    print("[Auto Learning] Sesi latihan selesai.")

def start_learning(minutes, topic=""):
    global learning_thread, is_learning, end_time, learned_items
    
    if is_learning:
        return False, "Sudah ada sesi latihan yang berjalan."
        
    model = get_setting('ollama_model', 'qwen2:0.5b')
    learned_items = [] # Reset laporan untuk sesi baru
    is_learning = True
    learning_thread = threading.Thread(target=learning_loop, args=(minutes, model, topic), daemon=True)
    learning_thread.start()
    
    topic_msg = f" tentang '{topic}'" if topic else ""
    return True, f"Sesi latihan dimulai selama {minutes} menit{topic_msg}."

def stop_learning():
    global is_learning
    if not is_learning:
        return False, "Tidak ada sesi latihan yang sedang berjalan."
        
    is_learning = False
    return True, "Sesi latihan dihentikan paksa."

def get_status():
    global is_learning, end_time, learned_items
    if is_learning:
        remaining_seconds = int(end_time - time.time())
        if remaining_seconds <= 0:
            is_learning = False
            return {"status": "inactive", "learned_items": learned_items}
        
        minutes, seconds = divmod(remaining_seconds, 60)
        return {
            "status": "active",
            "time_remaining": f"{minutes:02d}:{seconds:02d}",
            "learned_items": learned_items
        }
    return {"status": "inactive", "learned_items": learned_items}
