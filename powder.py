import re
import random
import difflib
import importlib
import respon.respon_powder
from powderLatihan.latihan import mulai_latihan

class SimpleLocalAI:
    def __init__(self):
        self.name = "Powder"
        self.load_knowledge()

    def load_knowledge(self):
        # Memuat atau merefresh pengetahuan AI secara dinamis
        importlib.reload(respon.respon_powder)
        self.responses, self.default_responses = respon.respon_powder.get_responses(self.name)
        self.vocabulary = respon.respon_powder.get_vocabulary()
        # Memuat profil pengguna
        profile = respon.respon_powder.get_user_profile()
        self.user_name = profile.get("user_name", "")

    def fix_typos(self, text):
        words = text.split()
        fixed_words = []
        for word in words:
            # Mencari kata terdekat dari vocabulary dengan tingkat kemiripan minimum 70%
            matches = difflib.get_close_matches(word, self.vocabulary, n=1, cutoff=0.7)
            if matches:
                fixed_words.append(matches[0])
            else:
                fixed_words.append(word)
        return " ".join(fixed_words)

    def respond(self, user_input):
        user_input_low = user_input.lower()
        
        # 1. Coba cari kecocokan langsung dari input asli (PENTING untuk pencarian seperti Wikipedia)
        for pattern, responses in self.responses.items():
            match = re.search(pattern, user_input_low)
            if match:
                return self._process_response(match, responses)
        
        # 2. Jika tidak ada yang cocok, baru coba perbaiki typo
        corrected_input = self.fix_typos(user_input_low)
        
        # Jika input setelah diperbaiki berbeda, coba cari lagi
        if corrected_input != user_input_low:
            for pattern, responses in self.responses.items():
                match = re.search(pattern, corrected_input)
                if match:
                    return self._process_response(match, responses)
                
        # Jika benar-benar tidak ada yang cocok, gunakan default response
        return random.choice(self.default_responses)

    def _process_response(self, match, responses):
        response = random.choice(responses)
        
        # Cek jika response adalah Action Mapping dari JSON
        if isinstance(response, str) and response.startswith("__ACTION__:"):
            action_name = response.split("__ACTION__:")[1]
            action_func = respon.respon_powder.ACTION_MAP.get(action_name)
            if callable(action_func):
                # Jika ada group yang ditangkap regex (seperti nama atau query wiki), kirim sebagai argumen
                if match.groups():
                    res = action_func(match.group(1))
                    if action_name == "save_name":
                        self.load_knowledge() # Reload agar nama baru langsung aktif
                    return res
                return action_func()
                
        # Ganti placeholder jika ada
        if isinstance(response, str):
            name_display = self.user_name if self.user_name else "Teman"
            response = response.replace("{user_name}", name_display)
            
        # Jika respons berbentuk fungsi (legacy python fallback)
        if callable(response):
            return response()
        return response
                
        # Jika tidak ada yang cocok, gunakan default response
        return random.choice(self.default_responses)

def main():
    ai = SimpleLocalAI()
    print("="*45)
    name_greet = f" {ai.user_name}" if ai.user_name else ""
    print(f"      Selamat datang kembali{name_greet}!      ")
    print(f"      Saya {ai.name}, asistenmu.           ")
    print("="*45)
    print("Ketik 'keluar', 'exit', atau 'quit' untuk mengakhiri percakapan.\n")
    
    while True:
        try:
            user_input = input("Anda: ")
            if user_input.lower() in ['keluar', 'exit', 'quit']:
                print(f"\n{ai.name}: Sampai jumpa lagi! Semoga harimu menyenangkan.")
                break
                
            if not user_input.strip():
                continue
                
            if user_input.lower() == 'waktunya latihan powder':
                mulai_latihan(ai.name)
                ai.load_knowledge()  # Reload respon baru secara real-time
                print("="*45)
                continue
                
            response = ai.respond(user_input)
            print(f"{ai.name}: {response}")
            
        except KeyboardInterrupt:
            # Mengatasi error saat pengguna menekan Ctrl+C
            print(f"\n\n{ai.name}: Program dihentikan paksa. Sampai jumpa!")
            break
        except Exception as e:
            print(f"\n{ai.name}: Terjadi kesalahan - {e}")

if __name__ == "__main__":
    main()
