import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'diana.db')

def init_db():
    """Inisialisasi database dan buat tabel jika belum ada."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabel untuk menyimpan pemicu dan respon
    # Kita simpan respon dalam format JSON string karena satu pemicu bisa punya banyak variasi jawaban
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS intents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern TEXT UNIQUE NOT NULL,
            responses TEXT NOT NULL
        )
    ''')
    
    # Tabel untuk kosa kata (vocabulary) untuk typo correction
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vocabulary (
            word TEXT PRIMARY KEY
        )
    ''')
    
    # Tabel untuk riwayat chat
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_locked INTEGER DEFAULT 0
        )
    ''')
    
    # Migrasi: Tambahkan kolom is_locked dan session_id jika belum ada (untuk DB lama)
    try:
        cursor.execute('ALTER TABLE chat_history ADD COLUMN is_locked INTEGER DEFAULT 0')
    except: pass
    try:
        cursor.execute('ALTER TABLE chat_history ADD COLUMN session_id TEXT')
    except: pass
    
    # Tabel untuk pengaturan (seperti durasi simpan history)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    # Set default history duration (7 hari) jika belum ada
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('history_days', '7'))
    # Set default personality (ceria) jika belum ada
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('personality', 'ceria'))
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('ollama_api_url', 'http://localhost:11434'))
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('ollama_models_path', ''))
    # Set default Ollama settings
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('ollama_enabled', 'true'))
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('ollama_model', ''))  # Kosong = otomatis pilih model pertama yang tersedia
    
    # Set default Gemini settings
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('fallback_brain', 'ollama'))
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('gemini_api_key', ''))
    
    conn.commit()
    conn.close()

def get_setting(key, default=None):
    """Mengambil nilai pengaturan tertentu."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def update_setting(key, value):
    """Memperbarui atau menambah pengaturan baru."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit()
    conn.close()

def migrate_from_json(json_path):
    """Memindahkan data dari intents.json ke SQLite."""
    if not os.path.exists(json_path):
        return
        
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Migrasi Responses
    for pattern, responses in data.get("responses", {}).items():
        try:
            cursor.execute('INSERT OR REPLACE INTO intents (pattern, responses) VALUES (?, ?)', 
                           (pattern, json.dumps(responses)))
        except Exception as e:
            print(f"Gagal migrasi pola {pattern}: {e}")
            
    # Migrasi Vocabulary
    for word in data.get("vocabulary", []):
        try:
            cursor.execute('INSERT OR IGNORE INTO vocabulary (word) VALUES (?)', (word,))
        except: pass
        
    conn.commit()
    conn.close()
    print("Migrasi dari JSON ke SQLite berhasil!")

def get_all_intents():
    """Mengambil semua pola dan respon dari database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT pattern, responses FROM intents ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    
    # Ubah kembali string JSON menjadi list Python
    return {row[0]: json.loads(row[1]) for row in rows}

def get_vocabulary():
    """Mengambil semua kosa kata."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT word FROM vocabulary')
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def add_new_intent(pattern, response_data):
    """Menambahkan atau memperbarui pengetahuan baru."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Jika response_data adalah string tunggal, bungkus dalam list
    if isinstance(response_data, str):
        responses = [response_data]
    else:
        responses = response_data

    # Gunakan INSERT OR REPLACE untuk menimpa pengetahuan lama dengan yang baru
    cursor.execute('INSERT OR REPLACE INTO intents (pattern, responses) VALUES (?, ?)', 
                   (pattern, json.dumps(responses)))
        
    # Tambahkan kosa kata baru ke vocabulary
    words = pattern.replace('\\b', '').replace('(', '').replace(')', '').replace('|', ' ').split()
    for word in words:
        if len(word) > 1:
            cursor.execute('INSERT OR IGNORE INTO vocabulary (word) VALUES (?)', (word.lower(),))
            
    conn.commit()
    conn.close()

def delete_intents_bulk(patterns):
    """Menghapus banyak pola sekaligus."""
    if not patterns:
        return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Gunakan query parameter berkelompok
    placeholders = ','.join(['?'] * len(patterns))
    cursor.execute(f'DELETE FROM intents WHERE pattern IN ({placeholders})', patterns)
    conn.commit()
    conn.close()
    return True

def save_chat_message(sender, message):
    """Menyimpan pesan chat ke database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO chat_history (sender, message) VALUES (?, ?)', (sender, message))
    conn.commit()
    conn.close()
    # Panggil cleanup setiap kali ada pesan baru untuk menjaga kebersihan
    delete_old_history()

def get_chat_history():
    """Mengambil riwayat chat yang masih berlaku."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, sender, message, timestamp, is_locked FROM chat_history ORDER BY timestamp ASC')
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "sender": row[1], "message": row[2], "time": row[3], "is_locked": row[4]} for row in rows]

def delete_old_history():
    """Menghapus history yang sudah melewati batas hari yang ditentukan."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ambil durasi dari settings
    cursor.execute('SELECT value FROM settings WHERE key = "history_days"')
    days = cursor.fetchone()
    days = int(days[0]) if days else 7
    
    # Hapus data yang lebih tua dari X hari
    cursor.execute(f"DELETE FROM chat_history WHERE timestamp <= datetime('now', '-{days} day')")
    
    conn.commit()
    conn.close()

def update_history_duration(days):
    """Mengubah durasi penyimpanan history."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE settings SET value = ? WHERE key = "history_days"', (str(days),))
    conn.commit()
    conn.close()
    return f"Durasi history berhasil diubah menjadi {days} hari."

def clear_chat_history():
    """Menghapus seluruh riwayat chat (kecuali yang dikunci)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM chat_history WHERE is_locked = 0')
    conn.commit()
    conn.close()
    return True

def delete_chat_message(msg_id):
    """Menghapus satu pesan spesifik."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM chat_history WHERE id = ? AND is_locked = 0', (msg_id,))
    conn.commit()
    conn.close()
    return True

def toggle_chat_lock(msg_id):
    """Mengunci atau membuka kunci pesan."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE chat_history SET is_locked = 1 - is_locked WHERE id = ?', (msg_id,))
    conn.commit()
    conn.close()
    return True
