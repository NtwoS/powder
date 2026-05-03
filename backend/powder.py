import re
import random
import difflib
import importlib
import respon.respon_powder
from powderLatihan.latihan import mulai_latihan
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from database.db_manager import get_all_intents, get_vocabulary
from duckduckgo_search import DDGS

class SimpleLocalAI:
    def __init__(self):
        self.name = "Powder"
        self.vectorizer = TfidfVectorizer()
        self.intent_patterns = []
        self.intent_vectors = None
        self.load_knowledge()

    def load_knowledge(self):
        # Memuat atau merefresh pengetahuan AI secara dinamis dari SQLite
        importlib.reload(respon.respon_powder)
        
        # Ambil data dari SQLite
        self.responses = get_all_intents()
        self.vocabulary = get_vocabulary()
        
        # Default responses (tetap ambil dari respon_powder untuk kemudahan edit manual jika perlu)
        _, self.default_responses = respon.respon_powder.get_responses(self.name)
        
        # Memuat profil pengguna
        profile = respon.respon_powder.get_user_profile()
        self.user_name = profile.get("user_name", "")
        
        # Inisialisasi Semantic Matcher
        self.init_semantic_matcher()

    def init_semantic_matcher(self):
        # Membersihkan pola regex agar bisa diolah secara semantik
        self.intent_patterns = list(self.responses.keys())
        cleaned_patterns = []
        for pattern in self.intent_patterns:
            # Hapus simbol regex umum untuk mendapatkan teks "mentah"
            clean = re.sub(r'\\b|\(|\)|\?|:|\.\*', '', pattern)
            clean = clean.replace('|', ' ')
            cleaned_patterns.append(clean.lower())
        
        if cleaned_patterns:
            self.intent_vectors = self.vectorizer.fit_transform(cleaned_patterns)

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

    def search_web(self, query):
        """Mencari informasi di internet menggunakan DuckDuckGo."""
        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=3)
                if not results:
                    return None
                
                response_text = f"🌐 **HASIL PENCARIAN WEB**\n"
                response_text += f"---------------------------\n\n"
                
                for i, r in enumerate(results, 1):
                    # Bersihkan teks agar tidak terlalu panjang
                    body = r['body'][:250] + "..." if len(r['body']) > 250 else r['body']
                    response_text += f"📍 **{r['title']}**\n"
                    response_text += f"{body}\n"
                    response_text += f"🔗 [Baca Selengkapnya]({r['href']})\n\n"
                    if i < len(results):
                        response_text += f"---\n\n"
                
                response_text += "Semoga informasi ini membantu! 😊"
                return response_text
        except Exception as e:
            print(f"Error browsing: {e}")
            return None

    def respond(self, user_input):
        user_input_low = user_input.lower()
        
        # 1. Coba cari kecocokan langsung menggunakan Regex (Presisi Tinggi)
        for pattern, responses in self.responses.items():
            match = re.search(pattern, user_input_low)
            if match:
                return self._process_response(match, responses)
        
        # 2. Coba perbaiki typo dan cari lagi dengan Regex
        corrected_input = self.fix_typos(user_input_low)
        if corrected_input != user_input_low:
            for pattern, responses in self.responses.items():
                match = re.search(pattern, corrected_input)
                if match:
                    return self._process_response(match, responses)

        # 3. Fallback: Semantic Matching (Mencari kemiripan makna)
        max_similarity = 0
        best_pattern = None
        
        if self.intent_vectors is not None:
            user_vector = self.vectorizer.transform([corrected_input])
            similarities = cosine_similarity(user_vector, self.intent_vectors).flatten()
            best_match_idx = similarities.argmax()
            max_similarity = similarities[best_match_idx]
            best_pattern = self.intent_patterns[best_match_idx]

        # 4. Logika Cerdas: Kapan harus Browsing vs Pakai Database Lokal
        question_words = ['siapa', 'apa', 'mengapa', 'kenapa', 'bagaimana', 'dimana', 'kapan', 'berapa', 'ceo', 'harga', 'berita', 'saham']
        is_question = any(word in user_input_low for word in question_words)

        # Jika kemiripan sangat tinggi (> 0.8), pakai database lokal (Pasti benar)
        # Tapi jika itu pertanyaan dan tidak ada konteks 'jam', coba browsing dulu
        if max_similarity >= 0.8:
            is_time_intent = 'jam' in best_pattern or 'waktu' in best_pattern
            if is_time_intent and is_question and 'jam' not in user_input_low and 'pukul' not in user_input_low:
                # Ini kemungkinan salah sasaran (misal: "berapa harga" dikira "jam berapa")
                web_result = self.search_web(user_input)
                if web_result: return web_result
            
            match = re.search(best_pattern, corrected_input)
            return self._process_response(match, self.responses[best_pattern])
            
        # Jika kemiripan sedang atau ini pertanyaan umum
        if is_question or max_similarity < 0.8:
            web_result = self.search_web(user_input)
            if web_result:
                return web_result
            
            # Jika internet gagal, gunakan lokal jika masih masuk akal
            if max_similarity >= 0.4:
                match = re.search(best_pattern, corrected_input)
                return self._process_response(match, self.responses[best_pattern])

        # Jika benar-benar tidak ada yang cocok, gunakan default response
        return random.choice(self.default_responses)

    def _process_response(self, match, responses):
        response = random.choice(responses)
        
        # Daftar kata-kata pembuka untuk variasi (Personality)
        intros = [
            "", # Kosong agar tidak selalu muncul
            "",
            "Tentu, ",
            "Baiklah, ",
            "Menurut saya, ",
            "Hmm, ",
            "Oh, ",
            "Oke, ",
            "Wah, ",
        ]
        
        # Cek jika response adalah Action Mapping dari JSON
        if isinstance(response, str) and response.startswith("__ACTION__:"):
            action_name = response.split("__ACTION__:")[1]
            action_func = respon.respon_powder.ACTION_MAP.get(action_name)
            if callable(action_func):
                # Jika ada group yang ditangkap regex, kirim sebagai argumen
                if match and match.groups():
                    res = action_func(match.group(1))
                    if action_name == "save_name":
                        self.load_knowledge() # Reload agar nama baru langsung aktif
                    return res
                return action_func()
                
        # Ganti placeholder jika ada
        if isinstance(response, str):
            import datetime
            now = datetime.datetime.now()
            if now.hour < 11:
                waktu = "pagi"
            elif now.hour < 15:
                waktu = "siang"
            elif now.hour < 19:
                waktu = "sore"
            else:
                waktu = "malam"

            name_display = self.user_name if self.user_name else "Teman"
            response = response.replace("{user_name}", name_display)
            response = response.replace("{waktu}", waktu)
            response = response.replace("{bot_name}", self.name)
            
            # Terapkan Kepribadian (Personality)
            from database.db_manager import get_setting
            personality = get_setting('personality', 'ceria')
            response = self._apply_personality(response, personality)
            
            # Tambahkan bumbu percakapan secara acak (20% kemungkinan)
            if random.random() < 0.2 and not response.startswith("[") and personality != 'profesional':
                intro = random.choice(intros)
                if intro:
                    # Pastikan huruf pertama respon jadi kecil jika ada intro
                    response = intro + response[0].lower() + response[1:]
            
        # Jika respons berbentuk fungsi (legacy python fallback)
        if callable(response):
            return response()
        return response

    def _apply_personality(self, text, personality):
        """Memodifikasi teks berdasarkan kepribadian yang aktif."""
        if personality == 'ceria':
            emojis = ["😊", "✨", "🙌", "👋", "🌟"]
            # Tambahkan emoji di akhir jika belum ada
            if not any(char in text for char in emojis):
                text += " " + random.choice(emojis)
            return text
            
        elif personality == 'profesional':
            # Hilangkan emoji jika ada dan buat lebih formal (kapital awal)
            text = text.replace("😊", "").replace("✨", "").strip()
            return text[0].upper() + text[1:] if text else text
            
        elif personality == 'santai':
            text = text.replace("Anda", "Kamu").replace("anda", "kamu")
            if random.random() < 0.3:
                text = "Sip, " + text[0].lower() + text[1:]
            return text + " 😎"
            
        return text

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
                
            response = ai.respond(user_input)
            print(f"{ai.name}: {response}")
            
        except KeyboardInterrupt:
            print(f"\n\n{ai.name}: Program dihentikan paksa. Sampai jumpa!")
            break
        except Exception as e:
            print(f"\n{ai.name}: Terjadi kesalahan - {e}")

if __name__ == "__main__":
    main()
