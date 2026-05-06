import threading
import time
import re
from database.db_manager import add_new_intent, get_setting, update_setting
from services.ollama_service import ask_ollama, get_first_available_model
import services.translation_service as translator

learning_thread = None
is_learning = False
end_time = 0
learned_items = []
active_model = ""

def fix_typos(text, model, base_url):
    """Menggunakan AI untuk memperbaiki typo dalam teks Bahasa Indonesia."""
    prompt = f"Perbaiki typo atau kesalahan ejaan dalam kalimat Bahasa Indonesia berikut agar menjadi baku dan benar. Jangan berikan penjelasan, langsung berikan hasil perbaikannya saja:\n\n'{text}'"
    system = "Anda adalah sistem pemeriksa ejaan (spell checker) Bahasa Indonesia yang sangat akurat."
    try:
        corrected = ask_ollama(prompt, model=model, base_url=base_url, system=system)
        if corrected and len(corrected.strip()) > 0:
            # Bersihkan jika AI memberikan tanda kutip atau embel-embel
            return corrected.strip().replace('"', '').replace("'", "")
    except:
        pass
    return text

def learning_loop(duration_minutes, model_name, topic=""):
    global is_learning, end_time, learned_items
    
    # Jika duration_minutes <= 0, maka dianggap tanpa batas waktu (Infinite Mode)
    if duration_minutes > 0:
        end_time = time.time() + (duration_minutes * 60)
        mode_text = f"{duration_minutes} menit"
    else:
        end_time = None
        mode_text = "Tanpa Batas Waktu (Manual Stop)"
    
    topic_instruction = f"KHUSUS tentang topik '{topic}'" if topic else "seperti fakta sains, sejarah, atau teknologi"
    
    # Prompt Generator Formal & Objektif (English-First for better quality)
    system_prompt = (
        f"You are a professional knowledge extraction system. "
        f"Your task is to provide fundamental facts about {topic_instruction} "
        f"to be stored in a knowledge database.\n\n"
        "STYLE GUIDELINES:\n"
        "- Use ONLY English (to ensure maximum accuracy and natural phrasing).\n"
        "- Write questions as a NATURAL HUMAN would ask them.\n"
        "- Provide ONLY the core factual answer. NO introductory phrases (like 'Known as', 'Usually described as', etc).\n"
        "- Start the answer DIRECTLY with the subject or the fact itself.\n"
        "- Avoid first-person pronouns, meta-commentary, and futuristic persona elements.\n"
        "- Be as concise and professional as an encyclopedia entry.\n\n"
        "STRICT RULES:\n"
        "- Prioritize scientific or historical accuracy.\n"
        "- Format per item: TANYA: [natural question] JAWAB: [concise direct answer]."
    )

    # Prompt Validator
    validator_prompt = (
        "Anda adalah pemeriksa fakta (fact-checker) profesional. Tugas Anda adalah memvalidasi pasangan Pertanyaan dan Jawaban. "
        "Apakah pertanyaan tersebut logis? Apakah jawabannya benar secara faktual, formal, dan nyambung dengan pertanyaannya? "
        "Balas hanya dengan satu kata: 'VALID' jika benar dan masuk akal, atau 'INVALID' jika salah, ngawur, atau tidak logis. "
        "Jangan berikan penjelasan apa pun, hanya satu kata."
    )
    
    topic_msg = f" dengan fokus topik: {topic}" if topic else ""
    print(f"[Auto Learning] Memulai latihan mandiri secara PROFESIONAL selama {mode_text} dengan model {model_name}{topic_msg}.")
    
    while is_learning:
        # Cek batas waktu jika bukan mode infinite
        if end_time and time.time() >= end_time:
            break
            
        try:
            print("[Auto Learning] Mencari pengetahuan (Mode Turbo Batch)...")
            # English User Query for better model response
            user_query = (
                f"Provide 5 different fundamental facts about {topic if topic else 'useful general knowledge'}. "
                "REQUIREMENT: Facts must be 100% accurate. Write questions like a curious human. "
                "Format: TANYA: [question] JAWAB: [answer]. "
                "Separate each item with a newline. Go straight to the content."
            )
            
            base_url = get_setting('ollama_api_url', 'http://localhost:11434')
            res = ask_ollama(user_query, model=model_name, system=system_prompt, options={"num_predict": 1000}, base_url=base_url)
            
            if res:
                # Menggunakan Regex untuk menangkap semua blok TANYA dan JAWAB
                blocks = re.findall(r"(?:TANYA|Pertanyaan):?\s*(.*?)\s*(?:JAWAB|Jawaban):?\s*(.*?)(?=(?:TANYA|Pertanyaan)|$)", res, re.DOTALL | re.IGNORECASE)
                
                if blocks:
                    for tanya, jawab in blocks:
                        t_clean = tanya.strip().replace("**", "").replace("*", "")
                        j_clean = jawab.strip().replace("**", "").replace("*", "")
                        
                        if t_clean and j_clean:
                            # Terjemahkan ke Indonesia sebelum disimpan agar hasil di tabel "Otak" luwes
                            print(f"[Auto Learning] Menerjemahkan & Memperbaiki: {t_clean[:30]}...")
                            t_id = translator.translate(t_clean, target_lang='id', source_lang='en')
                            j_id = translator.translate(j_clean, target_lang='id', source_lang='en')
                            
                            # Koreksi Typo otomatis (Self-Correction)
                            base_url = get_setting('ollama_api_url', 'http://localhost:11434')
                            t_id = fix_typos(t_id, model_name, base_url)
                            j_id = fix_typos(j_id, model_name, base_url)
                            
                            add_new_intent(t_id, j_id)
                            learned_items.append({"tanya": t_id, "jawab": j_id})
                            update_setting('last_learned_topic', f"{t_id} | {j_id}")
                            print(f"[Auto Learning] TERSIMPAN: {t_id[:50]}...")
                else:
                    print("[Auto Learning] Format tidak pas atau tidak ada data, mencoba lagi...")
            
            # Jeda minimal agar tidak spamming tapi tetap cepat
            time.sleep(1)
        except Exception as e:
            print(f"[Auto Learning] ERROR: {e}")
            time.sleep(5)
            
    is_learning = False
    print("[Auto Learning] Sesi latihan selesai.")

def start_learning(minutes, topic="", model_name=None):
    global learning_thread, is_learning, end_time, learned_items, active_model
    
    # Cek apakah thread benar-benar masih hidup
    if is_learning and learning_thread and learning_thread.is_alive():
        return False, "Sudah ada sesi latihan yang berjalan."
    
    # Jika is_learning True tapi thread sudah mati, reset status
    if is_learning:
        print("[Auto Learning] Deteksi status tersangkut, mereset status...")
        is_learning = False
        
    # Gunakan model yang dikirim dari UI, atau ambil dari setting. 
    # Jika keduanya tidak ada/salah, ambil model pertama yang tersedia di PC.
    base_url = get_setting('ollama_api_url', 'http://localhost:11434')
    model = model_name if model_name else get_setting('ollama_model', get_first_available_model(base_url))
    
    learned_items = [] # Reset laporan untuk sesi baru
    active_model = model
    is_learning = True
    learning_thread = threading.Thread(target=learning_loop, args=(minutes, model, topic), daemon=True)
    learning_thread.start()
    
    topic_msg = f" tentang '{topic}'" if topic else ""
    return True, f"Sesi latihan dimulai selama {minutes} menit{topic_msg} menggunakan model {model}."

def stop_learning():
    global is_learning, learning_thread
    if not is_learning:
        # Jika is_learning False tapi thread masih ada, bersihkan tetap
        is_learning = False
        learning_thread = None
        return True, "Status latihan sudah dalam keadaan berhenti."
    
    is_learning = False
    learning_thread = None
    return True, "Sesi latihan telah dihentikan secara manual."

def get_status():
    global is_learning, end_time, learned_items, learning_thread
    
    # Cek apakah thread benar-benar masih hidup jika is_learning True
    if is_learning and (not learning_thread or not learning_thread.is_alive()):
        is_learning = False
    
    if is_learning:
        if end_time is None:
            time_str = "Infinite"
        else:
            remaining_seconds = int(end_time - time.time())
            if remaining_seconds <= 0:
                is_learning = False
                return {"is_learning": False, "status": "inactive", "learned_items": learned_items}
            
            minutes, seconds = divmod(remaining_seconds, 60)
            time_str = f"{minutes:02d}:{seconds:02d}"

        return {
            "is_learning": True,
            "status": "active",
            "time_remaining": time_str,
            "model_name": active_model,
            "learned_items": learned_items
        }
    return {"is_learning": False, "status": "inactive", "learned_items": learned_items}
