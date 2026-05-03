from flask import Flask, request, jsonify
from flask_cors import CORS
from powder import SimpleLocalAI
import os

app = Flask(__name__)
CORS(app) # Mengizinkan Astro (frontend) mengakses API ini

from database.db_manager import (
    init_db, save_chat_message, get_chat_history, update_history_duration,
    get_all_intents, add_new_intent
)

# Inisialisasi Database
init_db()

# Inisialisasi AI
ai = SimpleLocalAI()

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '')
    
    if not user_input:
        return jsonify({"response": "Pesan kosong."}), 400
    
    # Simpan pesan User ke DB
    save_chat_message("user", user_input)
    
    # Mendapatkan respon dari AI
    response = ai.respond(user_input)
    
    # Simpan respon Bot ke DB
    save_chat_message("bot", response)
    
    return jsonify({
        "response": response,
        "user_name": ai.user_name,
        "bot_name": ai.name
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
    ai.load_knowledge() # Reload AI
    return jsonify({"success": True, "message": "Pengetahuan berhasil dihapus."})

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
            response = row[1].strip()
            if trigger and response:
                # Bungkus pemicu dengan pola regex standar
                pattern = f"\\b({trigger.lower()})\\b"
                add_new_intent(pattern, response)
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

        # Simpan interaksi ini ke history agar tidak hilang
        save_chat_message("user", f"Menganalisis file: {filename}")
        save_chat_message("bot", analysis_result)

        return jsonify({
            "success": True, 
            "analysis": analysis_result
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Gagal menganalisis file: {str(e)}"}), 500

@app.route('/settings', methods=['POST'])
def settings():
    data = request.json
    
    # Update Durasi History
    days = data.get('history_days')
    if days is not None:
        update_history_duration(days)
        
    # Update Kepribadian
    personality = data.get('personality')
    if personality is not None:
        from database.db_manager import update_setting
        update_setting('personality', personality)
        
    return jsonify({"success": True, "message": "Pengaturan berhasil diperbarui!"})

def simpan_ke_respon_powder(trigger, response):
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
        simpan_ke_respon_powder(trigger, response)
        ai.load_knowledge() # Reload agar ilmu baru langsung aktif
        return jsonify({"success": True, "message": f"Berhasil melatih Powder untuk pemicu: '{trigger}'"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "active", "bot_name": ai.name})

if __name__ == '__main__':
    print("==========================================")
    print("      BACKEND POWDER AI AKTIF             ")
    print("  Alamat: http://127.0.0.1:5000           ")
    print("==========================================")
    # Menjalankan server di port 5000
    app.run(host='127.0.0.1', debug=True, port=5000)
