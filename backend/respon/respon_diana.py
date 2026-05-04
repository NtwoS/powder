import datetime
import json
import os

# Database sederhana untuk profil (jika belum ada di SQLite)
USER_PROFILE_PATH = "data/user_profile.json"

def get_responses(bot_name):
    # Pengetahuan dasar statis Diana
    responses = {
        r"halo|hai|helo": ["Halo. Sistem saya mendeteksi kehadiran Anda. Ada yang bisa saya bantu?", "Halo. Senang bertemu kembali dengan Anda."],
        r"siapa namamu|nama kamu siapa": [f"Identitas saya adalah {bot_name}, asisten virtual futuristik Anda."],
        r"apa kabar|gimana kabarnya": ["Status sistem saya optimal. Bagaimana dengan kondisi Anda saat ini?"],
        r"\b(apa yang kamu pelajari|pelajaran terakhir|belajar apa|baru belajar apa)\b": ["__ACTION__:get_last_learned"]
    }
    default_responses = [
        "Maaf, sinkronisasi data saya belum mencakup informasi tersebut. Bisa Anda jelaskan kembali?",
        "Saya masih mengumpulkan data untuk topik ini. Bisakah Anda memberikan penjelasan lebih lanjut?"
    ]
    return responses, default_responses

def get_user_profile():
    if os.path.exists(USER_PROFILE_PATH):
        with open(USER_PROFILE_PATH, 'r') as f:
            return json.load(f)
    return {"user_name": "Pengguna"}

# Action Map untuk fungsi khusus
def get_time(*args):
    now = datetime.datetime.now()
    return f"Sekarang jam {now.strftime('%H:%M')}."

def save_name(name):
    profile = {"user_name": name}
    os.makedirs("data", exist_ok=True)
    with open(USER_PROFILE_PATH, 'w') as f:
        json.dump(profile, f)
    return f"Baik, saya akan panggil Anda {name}."

def get_last_learned(*args):
    from database.db_manager import get_setting
    last_topic = get_setting('last_learned_topic')
    if last_topic:
        # last_topic formatnya: Tanya | Jawab
        return f"Data pengetahuan terbaru yang berhasil saya integrasikan adalah sebagai berikut:\n\n{last_topic}\n\nSinkronisasi selesai."
    else:
        return "Database pengetahuan saya belum menerima input baru untuk saat ini."

ACTION_MAP = {
    "get_time": get_time,
    "save_name": save_name,
    "get_last_learned": get_last_learned
}
