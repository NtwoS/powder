import datetime
import subprocess
import json
import os
import urllib.request
import urllib.parse
import random

def get_time():
    now = datetime.datetime.now()
    return f"Waktu sekarang menunjukkan jam {now.strftime('%H:%M')}."

def open_calculator():
    try:
        # Menjalankan aplikasi kalkulator bawaan Windows
        subprocess.Popen('calc')
        return "Baik, saya telah membuka aplikasi kalkulator untukmu."
    except Exception as e:
        return f"Maaf, saya gagal membuka kalkulator: {e}"

def save_name(name):
    # Menyimpan nama ke user_profile.json
    profile_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'user_profile.json')
    try:
        # Normalisasi nama (kapital di depan)
        name = name.strip().title()
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump({"user_name": name}, f, indent=2)
        return f"Baiklah, saya akan mengingat namamu. Senang bertemu denganmu, {name}!"
    except Exception as e:
        return f"Maaf, saya gagal menyimpan namamu: {e}"

def get_user_profile():
    profile_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'user_profile.json')
    try:
        if os.path.exists(profile_path):
            with open(profile_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {"user_name": ""}

def search_wikipedia(query):
    # Mencari ringkasan dari Wikipedia Bahasa Indonesia
    # Menghapus kata sandang atau awalan jika terbawa regex
    query = query.strip().replace(" ", "_")
    url = f"https://id.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
    
    # Wikimedia API mewajibkan User-Agent agar tidak kena blokir (Error 403)
    headers = {
        'User-Agent': 'PowderAI/1.0 (Local-Python-Bot)'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if "extract" in data:
                return f"\n--- Wikipedia ---\n{data['extract']}\n"
            else:
                return "Maaf, saya tidak menemukan informasi tersebut di Wikipedia."
    except Exception as e:
        # Debugging sederhana jika error berlanjut
        return f"Maaf, saya gagal terhubung ke Wikipedia. Pastikan internet aktif. (Error: {str(e)})"

def play_game():
    # Game Tebak Angka sederhana
    angka_rahasia = random.randint(1, 100)
    percobaan = 0
    print("\n" + "="*45)
    print("   GAME TEBAK ANGKA (1 - 100)   ")
    print("="*45)
    print("Ketik 'menyerah' untuk berhenti.\n")
    
    while True:
        tebakan = input("Tebakanmu: ")
        if tebakan.lower() == 'menyerah':
            return f"Sayang sekali! Angka rahasianya adalah {angka_rahasia}."
            
        try:
            tebakan = int(tebakan)
            percobaan += 1
            if tebakan < angka_rahasia:
                print("Terlalu rendah! Coba lagi.")
            elif tebakan > angka_rahasia:
                print("Terlalu tinggi! Coba lagi.")
            else:
                return f"SELAMAT! Kamu berhasil menebak angka {angka_rahasia} dalam {percobaan} percobaan."
        except ValueError:
            print("Masukkan angka yang valid ya!")

# Pemetaan antara teks aksi di JSON dengan fungsi Python asli
ACTION_MAP = {
    "get_time": get_time,
    "open_calculator": open_calculator,
    "save_name": save_name,
    "search_wikipedia": search_wikipedia,
    "play_game": play_game
}

def load_data():
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'intents.json')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception:
        # Fallback kosong jika gagal membaca file
        return {"responses": {}, "default_responses": [], "vocabulary": []}

def get_responses(bot_name):
    data = load_data()
    responses = {}
    
    # Memproses dictionary dari JSON dan mengganti variabel {bot_name}
    for pattern, answers in data.get("responses", {}).items():
        processed_answers = []
        for ans in answers:
            if isinstance(ans, str):
                ans = ans.replace("{bot_name}", bot_name)
            processed_answers.append(ans)
        responses[pattern] = processed_answers
        
    return responses, data.get("default_responses", [])

def get_vocabulary():
    data = load_data()
    return data.get("vocabulary", [])
