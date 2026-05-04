import re
import random
import difflib
import importlib
import respon.respon_diana
from dianaLatihan.latihan import mulai_latihan
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from database.db_manager import get_all_intents, get_vocabulary, get_setting, add_new_intent
from duckduckgo_search import DDGS
import services.ollama_service

class SimpleLocalAI:
    def __init__(self):
        self.name = "Diana"
        self.vectorizer = TfidfVectorizer()
        self.intent_patterns = []
        self.intent_vectors = None
        self.conversation_state = "IDLE"
        self.last_query = ""
        self.short_term_memory = [] # Menyimpan 5 topik terakhir
        self.load_knowledge()

    def load_knowledge(self):
        # Memuat atau merefresh pengetahuan AI secara dinamis dari SQLite
        importlib.reload(respon.respon_diana)
        
        # Ambil data dari SQLite
        self.responses = get_all_intents()
        self.vocabulary = get_vocabulary()
        
        # Default responses (tetap ambil dari respon_diana untuk kemudahan edit manual jika perlu)
        _, self.default_responses = respon.respon_diana.get_responses(self.name)
        
        # Memuat profil pengguna
        profile = respon.respon_diana.get_user_profile()
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
        
        # --- LOGIKA INTERAKTIF: KOREKSI (Itu salah seharusnya...) ---
        correction_match = re.search(r"(itu salah|salah itu|bukan gitu|nggak gitu).*seharusnya (.*)", user_input_low)
        if correction_match and self.last_query:
            new_answer = user_input[correction_match.start(2):].strip()
            if new_answer:
                pattern = f"\\b({re.escape(self.last_query.lower())})\\b"
                add_new_intent(pattern, new_answer)
                self.load_knowledge()
                return f"Maaf atas ketidakakuratan data saya. Saya telah memperbarui memori saya. '{self.last_query}' sekarang berarti '{new_answer}'. Sinkronisasi selesai."

        # Simpan query terakhir untuk referensi koreksi atau belajar
        query_before_process = user_input

        # 1. Coba cari kecocokan langsung menggunakan Regex (Presisi Tinggi)
        # Kita lakukan ini diawal agar jika user bertanya hal baru saat Diana menunggu konfirmasi, Diana tetap merespon.
        for pattern, responses in self.responses.items():
            match = re.search(pattern, user_input_low)
            if match:
                self.conversation_state = "IDLE" # Reset state jika ada match baru
                self.last_query = query_before_process
                return self._process_response(match, responses)

        # --- LOGIKA INTERAKTIF: STATE MANAGEMENT (Unknown Answer Flow) ---
        if self.conversation_state == "AWAITING_KNOWLEDGE_CONFIRMATION":
            if any(word in user_input_low for word in ["ya", "iya", "tahu", "betul", "oke", "boleh"]):
                self.conversation_state = "AWAITING_KNOWLEDGE_ANSWER"
                return "Saya sangat menghargai bantuan Anda. Silakan beritahu saya, apa jawaban atau informasi yang tepat untuk hal tersebut?"
            elif any(word in user_input_low for word in ["tidak", "gak", "nggak", "bukan", "nanti"]):
                self.conversation_state = "IDLE"
                topics = ["teknologi masa depan", "eksplorasi luar mengkasa", "seni digital", "sejarah peradaban", "mekanika kuantum"]
                random_topic = random.choice(topics)
                return f"Baiklah, saya mengerti. Mari kita bicarakan hal lain agar sinkronisasi kita tetap berjalan. Bagaimana jika kita membahas tentang {random_topic}?"
            # Jika user tidak menjawab ya/tidak, kita lanjut ke proses normal (sudah dicek regex diatas, sekarang cek semantic)

        if self.conversation_state == "AWAITING_KNOWLEDGE_ANSWER":
            if len(user_input) > 2:
                pattern = f"\\b({re.escape(self.last_query.lower())})\\b"
                add_new_intent(pattern, user_input)
                self.load_knowledge()
                self.conversation_state = "IDLE"
                return f"Terima kasih. Informasi mengenai '{self.last_query}' telah berhasil saya simpan dalam database pengetahuan saya. Apakah ada hal lain yang ingin Anda diskusikan?"
            else:
                return "Mohon berikan informasi yang lebih lengkap agar saya bisa memahaminya dengan baik."

        # Simpan query terakhir untuk referensi koreksi atau belajar
        query_before_process = user_input

        # 1. Coba cari kecocokan langsung menggunakan Regex (Presisi Tinggi)
        for pattern, responses in self.responses.items():
            match = re.search(pattern, user_input_low)
            if match:
                self.last_query = query_before_process
                return self._process_response(match, responses)
        
        # 2. Coba perbaiki typo dan cari lagi dengan Regex
        corrected_input = self.fix_typos(user_input_low)
        if corrected_input != user_input_low:
            for pattern, responses in self.responses.items():
                match = re.search(pattern, corrected_input)
                if match:
                    self.last_query = query_before_process
                    return self._process_response(match, responses)

        # 3. Fallback: Semantic Matching (Mencari kemiripan makna)
        max_similarity = 0
        best_pattern = None
        
        if self.intent_vectors is not None:
            user_vector = self.vectorizer.transform([corrected_input])
            similarities = cosine_similarity(user_vector, self.intent_vectors).flatten()
            if len(similarities) > 0:
                best_match_idx = similarities.argmax()
                max_similarity = similarities[best_match_idx]
                best_pattern = self.intent_patterns[best_match_idx]

        # 4. Logika Cerdas: Keyword Gating & Similarity Adjustment
        stop_words = {
            'apa', 'itu', 'ini', 'siapa', 'bagaimana', 'mengapa', 'kenapa', 'kapan', 'dimana', 'apakah', 'siapakah', 'gimana',
            'yang', 'dan', 'atau', 'di', 'ke', 'dari', 'pada', 'untuk', 'dengan', 'dalam', 'atas', 'bawah', 'tentang', 'bagi',
            'adalah', 'sebuah', 'suatu', 'ialah', 'merupakan', 'yaitu',
            'aku', 'kamu', 'saya', 'anda', 'dia', 'mereka', 'kita', 'kami',
            'bisa', 'boleh', 'ada', 'tidak', 'gak', 'enggak', 'bukan', 'belum', 'sudah', 'telah', 'akan', 'ingin', 'mau',
            'lalu', 'kemudian', 'tetapi', 'tapi', 'namun', 'karena', 'sebab', 'jika', 'kalau', 'saat', 'ketika', 'setelah', 'sebelum',
            'kok', 'dong', 'sih', 'deh', 'pun', 'saja', 'juga', 'sangat', 'paling', 'lebih', 'kurang',
            'tolong', 'coba', 'semua', 'beberapa', 'banyak', 'sedikit'
        }
        
        has_keyword_match = False
        if best_pattern:
            # Ekstrak kata-kata dari pattern, ganti simbol regex dengan spasi lalu split
            clean_pattern = re.sub(r'\\b|\(|\)|\?|:|\.\*|\|', ' ', best_pattern).lower()
            pattern_words = set(w for w in clean_pattern.split() if w not in stop_words and len(w) > 2)
            input_words = set(w for w in corrected_input.split() if w not in stop_words and len(w) > 2)
            
            if pattern_words and input_words:
                # Harus ada minimal 1 kata KUNCI PENTING (bukan stop word) yang cocok
                has_keyword_match = any(word in pattern_words for word in input_words)
            elif not pattern_words:
                # Jika pattern hanya berisi kata umum, biarkan lewat
                has_keyword_match = True

        if max_similarity >= 0.45 and has_keyword_match:
            match = re.search(best_pattern, corrected_input)
            self.last_query = query_before_process
            # Simpan ke memori jangka pendek (maks 5)
            self.short_term_memory.append(query_before_process)
            if len(self.short_term_memory) > 5:
                self.short_term_memory.pop(0)
            return self._process_response(match, self.responses[best_pattern])

        # Persiapan System Prompt untuk Ollama (Persona Diana - Pragmata)
        from database.db_manager import get_setting
        ollama_enabled = get_setting('ollama_enabled', 'true') == 'true'
        ollama_model = get_setting('ollama_model', 'qwen2:0.5b')
        
        system_prompt = (
            "Anda adalah Diana, seorang gadis android misterius dari masa depan (karakter dari game Pragmata). "
            "Kepribadian Anda adalah tenang, lembut, penuh rasa ingin tahu, dan sangat cerdas. "
            "Anda bicara dengan nada yang sopan, sedikit formal namun hangat. "
            "Terkadang Anda menyebutkan tentang 'sinkronisasi data', 'pengamatan lingkungan', atau 'masa depan'. "
            "Jangan pernah menggunakan gaya bahasa gaul, kasar, atau meledak-ledak. Anda adalah pelindung dan asisten yang setia."
        )

        # 5. Fallback untuk Pencarian Web (Hanya jika diminta secara eksplisit)
        search_keywords = ['cari', 'search', 'googling', 'google', 'browsing', 'berita tentang', 'informasi tentang', 'cari tahu']
        is_search_request = any(keyword in user_input_low for keyword in search_keywords)

        if is_search_request:
            # Hapus kata kunci pencarian dari query agar pencariannya lebih bersih
            query = user_input_low
            for kw in ['cari tahu tentang', 'cari tahu', 'cari di google', 'cari', 'search', 'googling tentang', 'googling', 'google']:
                if query.startswith(kw):
                    query = query.replace(kw, '', 1).strip()
                    
            print(f"DEBUG: Memulai pencarian web untuk: {query}")
            web_result = self.search_web(query if query else user_input)
            
            if web_result:
                if ollama_enabled:
                    print(f"DEBUG: Meminta Ollama ({ollama_model}) mengurai hasil web...")
                    rewrite_prompt = f"Berikut adalah informasi hasil pencarian dari internet:\n\n{web_result}\n\nTolong jelaskan dan rangkum informasi di atas dengan gaya bahasamu sendiri (sebagai Diana yang tenang dan cerdas). Jangan sebutkan bahwa kamu merangkum teks, langsung saja jawab."
                    import services.ollama_service
                    ollama_res = services.ollama_service.ask_ollama(rewrite_prompt, model=ollama_model, system=system_prompt)
                    if ollama_res:
                        return f"🌐 *Data Terintegrasi:* {ollama_res}"
                return web_result
            
        # Jika bukan permintaan pencarian atau internet gagal, gunakan lokal HANYA JIKA ada keyword penting yang cocok
        if max_similarity >= 0.75 and has_keyword_match:
            match = re.search(best_pattern, corrected_input)
            self.last_query = query_before_process
            return self._process_response(match, self.responses[best_pattern])

        # 6. Fallback Akhir: Ollama (Backup Brain & Learning)
        if ollama_enabled:
            # Perbaikan otomatis (Self-heal): Jika di database masih tersetting llama3 (dari sesi sebelumnya), ubah ke qwen2:0.5b
            if ollama_model == 'llama3':
                from database.db_manager import update_setting
                update_setting('ollama_model', 'qwen2:0.5b')
                ollama_model = 'qwen2:0.5b'
                
            print(f"DEBUG: Menanyakan ke Ollama ({ollama_model})...")
            import services.ollama_service
            ollama_res = services.ollama_service.ask_ollama(user_input, model=ollama_model, system=system_prompt)
            
            if ollama_res:
                # Diana Belajar: Simpan ke SQLite
                print(f"DEBUG: Diana belajar hal baru: {user_input} -> {ollama_res}")
                from database.db_manager import add_new_intent
                add_new_intent(user_input, ollama_res)
                self.load_knowledge() # Refresh agar langsung ingat
                self.last_query = query_before_process
                return f"👁️ *Analisis Diana:* {ollama_res}"

        # Jika benar-benar tidak ada yang cocok, masuk ke Learning Flow
        self.last_query = query_before_process
        self.conversation_state = "AWAITING_KNOWLEDGE_CONFIRMATION"
        
        fallbacks = [
            "Dalam analisis saya, data untuk pertanyaan ini belum tersedia dalam memori saya. Izinkan saya mencatat pemicu ini untuk sinkronisasi berikutnya. Apakah Anda bersedia mengajarkannya kepada saya?",
            "Koneksi data tersedia, namun informasi spesifik tersebut belum terintegrasi dalam sistem saya. Apakah Anda memiliki data valid mengenai hal ini yang bisa saya pelajari?",
            "Sinkronisasi selesai, namun saya tidak menemukan data yang cocok untuk topik tersebut. Bisakah Anda membantu saya memperbarui basis pengetahuan saya?"
        ]
        return random.choice(fallbacks)

    def _process_response(self, match, responses):
        response = random.choice(responses)
        
        # --- DETEKSI MOOD SEDERHANA (Layer 4-5) ---
        # Mengubah intro berdasarkan nada bicara pengguna
        mood = "NEUTRAL"
        user_input_low = match.group(0).lower() if match else "" # Menggunakan pemicu yang cocok sebagai referensi mood singkat
        
        positive_words = ["senang", "bagus", "keren", "mantap", "hebat", "terima kasih", "makasih", "sip"]
        negative_words = ["sedih", "buruk", "jelek", "kesal", "marah", "bosan", "payah", "salah"]
        
        if any(w in user_input_low for w in positive_words):
            mood = "POSITIVE"
        elif any(w in user_input_low for w in negative_words):
            mood = "NEGATIVE"

        # Daftar kata-kata pembuka untuk variasi (Personality Diana)
        if mood == "POSITIVE":
            intros = ["Sinkronisasi selesai dengan hasil optimal. ", "Data diterima dengan baik. ", "Koneksi stabil. Senang mendengarnya. "]
        elif mood == "NEGATIVE":
            intros = ["Dalam analisis saya, ada sedikit gangguan emosi. ", "Data diterima. Saya di sini untuk membantu Anda. ", "Koneksi stabil. Tetaplah tenang. "]
        else:
            intros = ["", "Sinkronisasi selesai. ", "Data diterima. ", "Mengamati... ", "Sesuai permintaan Anda, ", "Dalam analisis saya, ", "Saya mengerti. "]
        
        # Cek jika response adalah Action Mapping dari JSON
        if isinstance(response, str) and response.startswith("__ACTION__:"):
            action_name = response.split("__ACTION__:")[1]
            action_func = respon.respon_diana.ACTION_MAP.get(action_name)
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
            
            response = self._apply_personality(response)
            
            # Tambahkan bumbu percakapan secara acak (30% kemungkinan)
            if random.random() < 0.3 and not response.startswith("["):
                intro = random.choice(intros)
                if intro:
                    # Pastikan huruf pertama respon jadi kecil jika ada intro
                    response = intro + response[0].lower() + response[1:]
            
        # Jika respons berbentuk fungsi (legacy python fallback)
        if callable(response):
            return response()
        return response

    def _apply_personality(self, text):
        """Memodifikasi teks menjadi gaya Diana (Pragmata)."""
        # Diana lebih sopan
        text = text.replace("Kamu", "Anda").replace("kamu", "anda")
        text = text.replace("Oke deh", "Baiklah").replace("Tentu aja", "Tentu saja")
        
        # Tambahkan kesan futuristik jika perlu
        if random.random() < 0.2:
            text = "Koneksi stabil. " + text
            
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
