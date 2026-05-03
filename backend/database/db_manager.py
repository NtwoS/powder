import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'powder.db')

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
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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
    cursor.execute('SELECT pattern, responses FROM intents')
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

def add_new_intent(pattern, response_text):
    """Menambahkan atau memperbarui pengetahuan baru."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Cek apakah pola sudah ada
    cursor.execute('SELECT responses FROM intents WHERE pattern = ?', (pattern,))
    row = cursor.fetchone()
    
    if row:
        # Jika sudah ada, tambahkan ke list respon yang ada
        responses = json.loads(row[0])
        if response_text not in responses:
            responses.append(response_text)
        cursor.execute('UPDATE intents SET responses = ? WHERE pattern = ?', 
                       (json.dumps(responses), pattern))
    else:
        # Jika baru, buat entri baru
        cursor.execute('INSERT INTO intents (pattern, responses) VALUES (?, ?)', 
                       (pattern, json.dumps([response_text])))
        
    # Tambahkan kosa kata baru ke vocabulary
    words = pattern.replace('\\b', '').replace('(', '').replace(')', '').replace('|', ' ').split()
    for word in words:
        if len(word) > 1:
            cursor.execute('INSERT OR IGNORE INTO vocabulary (word) VALUES (?)', (word.lower(),))
            
    conn.commit()
    conn.close()

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
    cursor.execute('SELECT sender, message, timestamp FROM chat_history ORDER BY timestamp ASC')
    rows = cursor.fetchall()
    conn.close()
    return [{"sender": row[0], "message": row[1], "time": row[2]} for row in rows]

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
