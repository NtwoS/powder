import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Tambahkan path agar bisa import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.powder import SimpleLocalAI
from backend.database.db_manager import init_db, get_all_intents

class TestOllamaLearning(unittest.TestCase):
    def setUp(self):
        # Inisialisasi DB (akan menggunakan file powder.db yang ada atau buat baru)
        init_db()
        self.ai = SimpleLocalAI()

    @patch('backend.services.ollama_service.ask_ollama')
    def test_learning_process(self, mock_ask):
        # Setup mock agar Ollama mengembalikan jawaban tertentu
        test_input = "Apa itu Python?"
        test_response = "Python adalah bahasa pemrograman populer."
        mock_ask.return_value = test_response
        
        # Pastikan input belum ada di memori lokal
        # (Kita asumsikan ini input baru)
        
        # Jalankan respond
        response = self.ai.respond(test_input)
        
        # Verifikasi respons mengandung label belajar
        self.assertIn("Belajar dari Ollama", response)
        self.assertIn(test_response, response)
        
        # Verifikasi data tersimpan di database
        intents = get_all_intents()
        found = False
        for pattern, responses in intents.items():
            if test_input.lower() in pattern.lower():
                if test_response in responses:
                    found = True
                    break
        
        self.assertTrue(found, "Intent baru tidak ditemukan di database!")
        print("SUCCESS: Powder berhasil belajar dan menyimpan data ke database.")

if __name__ == "__main__":
    unittest.main()
