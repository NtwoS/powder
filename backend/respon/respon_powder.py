import datetime
import json
import os

# Database sederhana untuk profil (jika belum ada di SQLite)
USER_PROFILE_PATH = "data/user_profile.json"

def get_responses(bot_name):
    # Pengetahuan dasar statis
    responses = {
        r"halo|hai|helo": ["Halo! Saya {bot_name}, ada yang bisa saya bantu?", "Hai! Senang bertemu Anda."],
        r"siapa namamu|nama kamu siapa": [f"Nama saya {bot_name}, asisten virtual Anda."],
        r"apa kabar|gimana kabarnya": ["Saya baik, terima kasih! Bagaimana dengan Anda?"],
    }
    default_responses = [
        "Maaf, saya tidak mengerti. Bisa ulangi?",
        "Saya masih belajar, bisa beritahu saya apa maksud Anda?"
    ]
    return responses, default_responses

def get_user_profile():
    if os.path.exists(USER_PROFILE_PATH):
        with open(USER_PROFILE_PATH, 'r') as f:
            return json.load(f)
    return {"user_name": "Pengguna"}

# Action Map untuk fungsi khusus
def get_time():
    now = datetime.datetime.now()
    return f"Sekarang jam {now.strftime('%H:%M')}."

def save_name(name):
    profile = {"user_name": name}
    os.makedirs("data", exist_ok=True)
    with open(USER_PROFILE_PATH, 'w') as f:
        json.dump(profile, f)
    return f"Baik, saya akan panggil Anda {name}."

ACTION_MAP = {
    "get_time": get_time,
    "save_name": save_name
}
