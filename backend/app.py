from flask import Flask, request, jsonify
from flask_cors import CORS
from diana import SimpleLocalAI
import os

app = Flask(__name__)
CORS(app) # Mengizinkan Astro (frontend) mengakses API ini

from database.db_manager import (
    init_db, save_chat_message, get_chat_history, update_history_duration,
    get_all_intents, add_new_intent, clear_chat_history,
    delete_chat_message, toggle_chat_lock, get_setting, delete_intents_bulk,
    create_conversation, get_conversations, get_conversation_messages,
    delete_conversation, update_conversation_title
)
from services.ollama_service import ask_ollama, list_ollama_models

import subprocess

@app.route('/ollama/models', methods=['GET'])
def get_ollama_models():
    try:
        base_url = get_setting('ollama_api_url', 'http://localhost:11434')
        models_path = get_setting('ollama_models_path', '').strip()
        
        models = list_ollama_models(base_url=base_url, models_path=models_path)
        return jsonify({"models": models})
    except Exception as e:
        return jsonify({"models": [], "error": str(e)})

@app.route('/ollama/sync_models', methods=['POST'])
def sync_ollama_models():
    """Manual trigger untuk menghubungkan model dari folder kustom."""
    data = request.json
    models_path = data.get('path', '').strip()
    
    if not models_path:
        return jsonify({"success": False, "message": "Jalur folder tidak boleh kosong."})
        
    if not os.path.exists(models_path):
        return jsonify({"success": False, "message": "Folder tidak ditemukan di PC Anda."})
        
    # Langsung lakukan scan manual ke folder manifests (lewatkan API dulu agar cepat)
    from services.ollama_service import list_ollama_models
    models = list_ollama_models(base_url=None, models_path=models_path)
    
    if not models:
        return jsonify({"success": False, "message": "Tidak ditemukan model Ollama di folder tersebut. Pastikan folder berisi folder 'manifests'."})
        
    # Simpan jalur ini secara permanen
    from database.db_manager import update_setting
    update_setting('ollama_models_path', models_path)
    
    return jsonify({
        "success": True, 
        "message": f"Diana berhasil terhubung! Menemukan: {', '.join(models)}",
        "models": models
    })

@app.route('/ollama/run', methods=['POST'])
def run_ollama_model():
    data = request.json
    model_name = data.get('model_name')
    if not model_name:
        return jsonify({"success": False, "message": "Nama model tidak ditemukan."}), 400
    
    models_path = get_setting('ollama_models_path', '').strip()
    
    try:
        # Menyiapkan environment variable hanya jika ada custom path yang diisi
        env = os.environ.copy()
        if models_path:
            env["OLLAMA_MODELS"] = models_path
            cmd = f'start cmd /k "set OLLAMA_MODELS={models_path} && ollama run {model_name}"'
        else:
            # Jika kosong, gunakan default system
            cmd = f'start cmd /k "ollama run {model_name}"'
            
        subprocess.Popen(cmd, shell=True, env=env)
        return jsonify({"success": True, "message": f"Memulai {model_name} di terminal baru menggunakan lokasi default."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/settings/browse_folder', methods=['GET'])
def browse_folder():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder_path = filedialog.askdirectory()
        root.destroy()
        if folder_path:
            return jsonify({"success": True, "path": folder_path})
        return jsonify({"success": False, "message": "Batal memilih folder."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Inisialisasi Database
init_db()

# Inisialisasi AI
ai = SimpleLocalAI()

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '')
    conversation_id = data.get('conversation_id')
    
    if not user_input:
        return jsonify({"response": "Pesan kosong."}), 400
    
    # Auto-create conversation jika belum ada
    if not conversation_id:
        title = user_input[:40] + ('...' if len(user_input) > 40 else '')
        conversation_id = create_conversation(title)
    
    # Simpan pesan User ke DB
    save_chat_message("user", user_input, conversation_id)
    
    # Mendapatkan respon dari AI
    if hasattr(ai, 'base_url'):
        ai.base_url = get_setting('ollama_api_url', 'http://localhost:11434')
        
    response = ai.respond(user_input)
    
    # Simpan respon Bot ke DB
    save_chat_message("bot", response, conversation_id)
    
    return jsonify({
        "response": response,
        "user_name": ai.user_name,
        "bot_name": ai.name,
        "conversation_id": conversation_id
    })

# --- ADMIN PANEL ENDPOINTS ---

@app.route('/intents', methods=['GET'])
def get_intents():
    """Mengambil semua pengetahuan untuk Admin Panel."""
    data = get_all_intents()
    # Format agar mudah dibaca oleh tabel frontend
    formatted_data = []
    for pattern, responses in data.items():
        formatted_data.append({
            "pattern": pattern,
            "responses": responses
        })
    return jsonify({"intents": formatted_data})

@app.route('/intents/delete', methods=['POST'])
def delete_intent():
    """Menghapus pengetahuan tertentu."""
    data = request.json
    pattern = data.get('pattern')
    if not pattern:
        return jsonify({"success": False, "message": "Pola tidak ditemukan."}), 400
        
    from database.db_manager import DB_PATH
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM intents WHERE pattern = ?', (pattern,))
    conn.commit()
    conn.close()
    ai.load_knowledge() # Reload AI memory
    return jsonify({"success": True, "message": "Pengetahuan berhasil dihapus."})

@app.route('/intents/delete_bulk', methods=['POST'])
def delete_intents_bulk_api():
    """Menghapus banyak pengetahuan sekaligus."""
    data = request.json
    patterns = data.get('patterns', [])
    if not patterns:
        return jsonify({"success": False, "message": "Tidak ada data yang dipilih."}), 400
        
    success = delete_intents_bulk(patterns)
    if success:
        ai.load_knowledge() # Reload AI memory
        return jsonify({"success": True, "message": f"{len(patterns)} pengetahuan berhasil dihapus."})
    return jsonify({"success": False, "message": "Gagal menghapus data."}), 500

@app.route('/intents/upload', methods=['POST'])
def upload_intents():
    """Mengimpor banyak pengetahuan sekaligus melalui file CSV."""
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Tidak ada file yang diunggah."}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "Nama file kosong."}), 400
        
    if not file.filename.endswith('.csv'):
        return jsonify({"success": False, "message": "Hanya file .csv yang diperbolehkan."}), 400

    import csv
    import io
    
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.reader(stream)
    
    count = 0
    for row in csv_input:
        if len(row) >= 2:
            trigger = row[0].strip()
            # Ambil semua kolom setelah pemicu sebagai variasi respon
            responses = [r.strip() for r in row[1:] if r.strip()]
            
            if trigger and responses:
                # Jika pemicu sudah mengandung simbol regex (seperti | atau \b), gunakan langsung
                # Jika pemicu hanya kata biasa, bungkus dengan \b
                if any(c in trigger for c in ['|', '\\', '(', ')', '.*']):
                    pattern = trigger.lower()
                else:
                    pattern = f"\\b({trigger.lower()})\\b"
                
                add_new_intent(pattern, responses)
                count += 1
                
    ai.load_knowledge() # Reload AI agar data baru langsung aktif
    return jsonify({"success": True, "message": f"Berhasil mengimpor {count} pengetahuan baru!"})

@app.route('/analyze', methods=['POST'])
def analyze_file():
    """Menganalisis isi file .txt atau .pdf."""
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Tidak ada file yang diunggah."}), 400
        
    file = request.files['file']
    filename = file.filename
    content = ""
    
    try:
        if filename.endswith('.txt'):
            content = file.read().decode('utf-8')
        elif filename.endswith('.pdf'):
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                content += page.extract_text()
        else:
            return jsonify({"success": False, "message": "Format file tidak didukung (hanya .txt dan .pdf)."}), 400

        if not content.strip():
            return jsonify({"success": False, "message": "File kosong atau tidak terbaca."}), 400

        # ANALISIS SEDERHANA
        words = content.split()
        word_count = len(words)
        char_count = len(content)
        
        # Ekstrak 3 kalimat pertama sebagai ringkasan awal
        sentences = content.replace('\n', ' ').split('. ')
        summary = ". ".join(sentences[:3]) + ('.' if len(sentences) > 0 else '')

        # Cari kata-kata yang paling sering muncul (Kecuali kata sambung umum)
        stop_words = {'dan', 'yang', 'di', 'ke', 'dari', 'itu', 'ini', 'untuk', 'dengan', 'adalah'}
        word_freq = {}
        for w in words:
            w_clean = w.lower().strip(',.()[]{}')
            if len(w_clean) > 3 and w_clean not in stop_words:
                word_freq[w_clean] = word_freq.get(w_clean, 0) + 1
        
        # Ambil 5 kata kunci teratas
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        keyword_list = [k[0] for k in keywords]

        analysis_result = (
            f"📄 **Hasil Analisis File: {filename}**\n\n"
            f"📊 **Statistik:**\n"
            f"- Jumlah Kata: {word_count}\n"
            f"- Jumlah Karakter: {char_count}\n\n"
            f"🔑 **Kata Kunci Utama:**\n"
            f"- {', '.join(keyword_list)}\n\n"
            f"📝 **Ringkasan Singkat:**\n"
            f"{summary}..."
        )

        # --- FITUR BARU: AUTO-ABSORB KNOWLEDGE ---
        fallback_brain = get_setting('fallback_brain', 'ollama')
        gemini_api_key = get_setting('gemini_api_key', '')
        ollama_enabled = get_setting('ollama_enabled', 'true') == 'true'
        ollama_model = get_setting('ollama_model', '')
        
        absorbed_count = 0
        if content.strip() and ((fallback_brain == 'gemini' and gemini_api_key) or (fallback_brain == 'ollama' and ollama_enabled)):
            print(f"DEBUG: Diana sedang menyerap ilmu dari {filename} menggunakan {fallback_brain.capitalize()}...")
            
            # Kita ambil potongan teks saja agar tidak melebihi context window (misal 4000 karakter pertama)
            learning_context = content[:4000]
            
            learning_prompt = (
                f"Berikut adalah potongan konten dari file '{filename}':\n\n"
                f"{learning_context}\n\n"
                "Tugas Anda: Ekstrak 3-5 pengetahuan paling penting dari teks di atas. "
                "Format hasil harus TANYA: [pemicu singkat] JAWAB: [penjelasan formal]. "
                "Gunakan Bahasa Indonesia yang baku dan objektif. "
                "Jangan gunakan persona, gaya bahasa futuristik, atau bumbu percakapan. "
                "Jangan berikan pembukaan, langsung saja ke format TANYA dan JAWAB."
            )
            
            system_prompt = "Anda adalah sistem ekstraksi informasi profesional yang bertugas menyerap data dari dokumen secara akurat dan formal."
            
            res = None
            if fallback_brain == 'gemini' and gemini_api_key:
                from services.gemini_service import ask_gemini
                res = ask_gemini(learning_prompt, api_key=gemini_api_key, system=system_prompt)
            else:
                base_url = get_setting('ollama_api_url', 'http://localhost:11434')
                if not ollama_model:
                    from services.ollama_service import get_first_available_model
                    ollama_model = get_first_available_model(base_url)
                res = ask_ollama(learning_prompt, model=ollama_model, base_url=base_url, system=system_prompt)
            
            if res:
                import re
                # Log untuk debug (bisa dihapus nanti)
                from database.db_manager import DB_PATH
                with open(os.path.join(os.path.dirname(DB_PATH), 'learning_debug.log'), 'a', encoding='utf-8') as f:
                    f.write(f"\n--- {filename} ---\n{res}\n")

                # Mencari pola TANYA: ... JAWAB: ... (Lebih fleksibel)
                # Mencari blok yang diawali TANYA atau Pertanyaan, diikuti JAWAB atau Jawaban
                blocks = re.findall(r"(?:TANYA|Pertanyaan):?\s*(.*?)\s*(?:JAWAB|Jawaban):?\s*(.*?)(?=(?:TANYA|Pertanyaan)|$)", res, re.DOTALL | re.IGNORECASE)
                
                if not blocks:
                    # Coba fallback jika formatnya baris per baris tanpa label
                    # (Hanya jika Ollama bandel tidak pakai label)
                    pass

                for tanya, jawab in blocks:
                    t_clean = tanya.strip().replace("**", "").replace("*", "").replace("?", "")
                    j_clean = jawab.strip().replace("**", "").replace("*", "")
                    
                    if t_clean and j_clean:
                        # Gunakan pemicu yang lebih fleksibel (tidak harus pas persis di awal/akhir)
                        pattern = f"({t_clean.lower()})"
                        add_new_intent(pattern, [j_clean])
                        absorbed_count += 1
            else:
                analysis_result += f"\n\n⚠️ **Peringatan:** Diana tidak bisa menyerap ilmu secara permanen karena {fallback_brain.capitalize()} tidak merespon."
            
            if absorbed_count > 0:
                ai.load_knowledge() # Refresh AI memory
                analysis_result += f"\n\n✨ **Update Memori:** Diana telah berhasil menyerap {absorbed_count} poin pengetahuan baru dari dokumen ini ke dalam basis datanya secara permanen."
        
        # Simpan interaksi ini ke history agar tidak hilang
        save_chat_message("user", f"Menganalisis file: {filename}")
        save_chat_message("bot", analysis_result)

        return jsonify({
            "success": True, 
            "analysis": analysis_result
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Gagal menganalisis file: {str(e)}"}), 500

@app.route('/settings', methods=['GET'])
def get_settings():
    return jsonify({
        "history_days": get_setting('history_days', '7'),
        "ollama_model": get_setting('ollama_model', ''),
        "fallback_brain": get_setting('fallback_brain', 'ollama'),
        "gemini_api_key": get_setting('gemini_api_key', ''),
        "ollama_api_url": get_setting('ollama_api_url', 'http://localhost:11434'),
        "ollama_models_path": get_setting('ollama_models_path', '')
    })

@app.route('/settings', methods=['POST'])
def settings():
    data = request.json
    
    # Update Durasi History
    days = data.get('history_days')
    if days is not None:
        update_history_duration(days)
        
    # (Kepribadian sekarang dihardcode menjadi Jinx, tidak perlu diupdate)

    # Update Ollama/Gemini Model
    ollama_model = data.get('ollama_model')
    fallback_brain = data.get('fallback_brain')
    gemini_api_key = data.get('gemini_api_key')
    ollama_api_url = data.get('ollama_api_url')
    ollama_models_path = data.get('ollama_models_path')
    
    from database.db_manager import update_setting
    
    if ollama_model is not None:
        update_setting('ollama_model', ollama_model)
    if fallback_brain is not None:
        update_setting('fallback_brain', fallback_brain)
    if gemini_api_key is not None:
        update_setting('gemini_api_key', gemini_api_key)
    if ollama_api_url is not None:
        update_setting('ollama_api_url', ollama_api_url)
    if ollama_models_path is not None:
        update_setting('ollama_models_path', ollama_models_path)
        
    return jsonify({"success": True, "message": "Pengaturan berhasil diperbarui!"})

def simpan_ke_respon_diana(trigger, response):
    """Fungsi pembantu untuk menyimpan latihan baru."""
    add_new_intent(trigger, response)

@app.route('/train', methods=['POST'])
def train():
    data = request.json
    trigger = data.get('trigger', '')
    response = data.get('response', '')
    
    if not trigger or not response:
        return jsonify({"success": False, "message": "Pemicu dan respon tidak boleh kosong."}), 400
    
    try:
        simpan_ke_respon_diana(trigger, response)
        ai.load_knowledge() # Reload agar ilmu baru langsung aktif
        return jsonify({"success": True, "message": f"Berhasil melatih Diana untuk pemicu: '{trigger}'"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/history', methods=['GET'])
def history():
    """Mengambil riwayat percakapan."""
    chat_history = get_chat_history()
    return jsonify({"history": chat_history})

@app.route('/history/clear', methods=['POST'])
def clear_history():
    """Menghapus seluruh riwayat percakapan (kecuali yang dikunci)."""
    clear_chat_history()
    return jsonify({"success": True, "message": "Riwayat chat (yang tidak dikunci) telah dihapus."})

@app.route('/history/delete/<int:msg_id>', methods=['POST'])
def delete_history_item(msg_id):
    """Menghapus satu item riwayat chat."""
    delete_chat_message(msg_id)
    return jsonify({"success": True})

@app.route('/history/lock/<int:msg_id>', methods=['POST'])
def lock_history_item(msg_id):
    """Mengunci/membuka kunci item riwayat chat."""
    toggle_chat_lock(msg_id)
    return jsonify({"success": True})

# --- CONVERSATION ENDPOINTS ---

@app.route('/conversations', methods=['GET'])
def list_conversations():
    """Mengambil daftar semua percakapan."""
    convs = get_conversations()
    return jsonify({"conversations": convs})

@app.route('/conversations', methods=['POST'])
def new_conversation():
    """Membuat percakapan baru."""
    data = request.json or {}
    title = data.get('title', 'Percakapan Baru')
    conv_id = create_conversation(title)
    return jsonify({"success": True, "conversation_id": conv_id})

@app.route('/conversations/<int:conv_id>/messages', methods=['GET'])
def conversation_messages(conv_id):
    """Mengambil semua pesan dari percakapan tertentu."""
    messages = get_conversation_messages(conv_id)
    return jsonify({"messages": messages})

@app.route('/conversations/<int:conv_id>', methods=['DELETE'])
def remove_conversation(conv_id):
    """Menghapus percakapan."""
    delete_conversation(conv_id)
    return jsonify({"success": True})

# --- AUTO LEARNING ENDPOINTS ---
from services.auto_learner import start_learning, stop_learning, get_status

@app.route('/auto_learning/start', methods=['POST'])
def auto_learning_start():
    data = request.json
    minutes = int(data.get('minutes', 15))
    topic = data.get('topic', "").strip()
    model_name = data.get('model_name') # Bisa None
    success, message = start_learning(minutes, topic, model_name)
    
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400

@app.route('/auto_learning/stop', methods=['POST'])
def auto_learning_stop():
    success, message = stop_learning()
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400

@app.route('/full_ai/status', methods=['GET'])
def get_full_ai_status():
    mode = get_setting('full_ai_mode', 'off')
    return jsonify({"mode": mode})

@app.route('/full_ai/toggle', methods=['POST'])
def toggle_full_ai():
    data = request.json
    mode = data.get('mode', 'off') # 'off', 'ollama', 'gemini'
    from database.db_manager import update_setting
    update_setting('full_ai_mode', mode)
    return jsonify({"success": True, "mode": mode})

@app.route('/status', methods=['GET'])
def status_check():
    """Endpoint untuk mengecek apakah server aktif."""
    return jsonify({
        "status": "online", 
        "bot_name": ai.name,
        "message": "Server Diana AI Aktif",
        "settings": {
            "ollama_model": get_setting('ollama_model', ''),
            "full_ai_mode": get_setting('full_ai_mode', 'off')
        }
    }), 200

@app.route('/auto_learning/status', methods=['GET'])
def auto_learning_status():
    return jsonify(get_status())

if __name__ == '__main__':
    print("==========================================")
    print("       BACKEND DIANA AI AKTIF             ")
    print("  Alamat: http://127.0.0.1:5050           ")
    print("==========================================")
    # Menjalankan server di port 5050 (0.0.0.0 agar bisa diakses dari IP lokal mana pun)
    app.run(host='0.0.0.0', debug=True, port=5050)
