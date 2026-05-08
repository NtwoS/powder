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
            conversation_id INTEGER,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_locked INTEGER DEFAULT 0,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
    ''')
    
    # Tabel untuk conversations (sesi percakapan)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL DEFAULT 'Percakapan Baru',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Migrasi: Tambahkan kolom jika belum ada (untuk DB lama)
    try:
        cursor.execute('ALTER TABLE chat_history ADD COLUMN is_locked INTEGER DEFAULT 0')
    except: pass
    try:
        cursor.execute('ALTER TABLE chat_history ADD COLUMN conversation_id INTEGER')
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
    
    # Set default Full AI Mode (off)
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('full_ai_mode', 'off'))
    
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

def get_settings_batch(keys_with_defaults):
    """Mengambil banyak pengaturan sekaligus dalam satu koneksi DB.
    keys_with_defaults: dict seperti {'key1': 'default1', 'key2': 'default2'}
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    placeholders = ','.join(['?'] * len(keys_with_defaults))
    cursor.execute(f'SELECT key, value FROM settings WHERE key IN ({placeholders})', list(keys_with_defaults.keys()))
    rows = cursor.fetchall()
    conn.close()
    result = dict(keys_with_defaults)  # Start with defaults
    for key, value in rows:
        result[key] = value
    return result

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

_message_counter = 0

def save_chat_message(sender, message, conversation_id=None):
    """Menyimpan pesan chat ke database."""
    global _message_counter
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO chat_history (sender, message, conversation_id) VALUES (?, ?, ?)', (sender, message, conversation_id))
    # Update timestamp conversation
    if conversation_id:
        cursor.execute('UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (conversation_id,))
    conn.commit()
    conn.close()
    _message_counter += 1
    if _message_counter >= 50:
        _message_counter = 0
        delete_old_history()

# === CONVERSATION FUNCTIONS ===

def create_conversation(title='Percakapan Baru'):
    """Membuat conversation baru dan mengembalikan ID-nya."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO conversations (title) VALUES (?)', (title,))
    conv_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return conv_id

def get_conversations():
    """Mengambil daftar semua conversations, terbaru dulu."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "created_at": r[2], "updated_at": r[3]} for r in rows]

def get_conversation_messages(conv_id):
    """Mengambil semua pesan dari conversation tertentu."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, sender, message, timestamp FROM chat_history WHERE conversation_id = ? ORDER BY timestamp ASC', (conv_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "sender": r[1], "message": r[2], "time": r[3]} for r in rows]

def delete_conversation(conv_id):
    """Menghapus conversation dan semua pesannya."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM chat_history WHERE conversation_id = ?', (conv_id,))
    cursor.execute('DELETE FROM conversations WHERE id = ?', (conv_id,))
    conn.commit()
    conn.close()
    return True

def update_conversation_title(conv_id, title):
    """Memperbarui judul conversation."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE conversations SET title = ? WHERE id = ?', (title, conv_id))
    conn.commit()
    conn.close()
    return True

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
