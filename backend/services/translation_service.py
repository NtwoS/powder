import socket
import logging
import os
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TranslationService")

# Global variables for offline translator
argos_installed = False
tried_init = False

# Cache untuk internet check (hemat 2 detik per panggilan)
_internet_cache = {"status": None, "last_check": 0}
_INTERNET_CACHE_TTL = 60  # Cache selama 60 detik

def check_internet():
    """Mengecek apakah ada koneksi internet (dengan cache 60 detik)."""
    now = time.time()
    if now - _internet_cache["last_check"] < _INTERNET_CACHE_TTL and _internet_cache["status"] is not None:
        return _internet_cache["status"]
    
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=1.5)
        _internet_cache["status"] = True
    except (OSError, socket.timeout):
        _internet_cache["status"] = False
    
    _internet_cache["last_check"] = now
    return _internet_cache["status"]

def init_offline_translator():
    """Inisialisasi Argos Translate (Offline)."""
    global argos_installed, tried_init
    if tried_init:
        return
    
    tried_init = True
    try:
        import argostranslate.package
        import argostranslate.translate
        
        from_code = "en"
        to_code = "id"
        
        # Pastikan index package terupdate jika kosong
        # Ini butuh internet sekali saja
        installed_languages = argostranslate.translate.get_installed_languages()
        from_lang = list(filter(lambda x: x.code == from_code, installed_languages))
        to_lang = list(filter(lambda x: x.code == to_code, installed_languages))
        
        if not from_lang or not to_lang:
            if check_internet():
                logger.info("Model offline EN-ID tidak ditemukan. Mengunduh...")
                argostranslate.package.update_package_index()
                available_packages = argostranslate.package.get_available_packages()
                package_to_install = next(
                    filter(
                        lambda x: x.from_code == from_code and x.to_code == to_code,
                        available_packages
                    ), None
                )
                if package_to_install:
                    argostranslate.package.install_from_path(package_to_install.download())
                    logger.info("Instalasi model Argos selesai.")
                    argos_installed = True
                else:
                    logger.error("Model EN-ID tidak tersedia di index Argos.")
            else:
                logger.warning("Mode Offline butuh download model pertama kali, tapi tidak ada internet.")
        else:
            argos_installed = True
            logger.info("Argos Translate Offline Siap.")
            
    except Exception as e:
        logger.error(f"Gagal inisialisasi Argos Translate: {e}")
        argos_installed = False

def translate(text, target_lang='id', source_lang='en'):
    """Fungsi utama terjemahan dengan auto-switch online/offline."""
    if not text or len(text.strip()) < 3:
        return text

    # 1. Coba Online (Deep Translator)
    if check_internet():
        try:
            from deep_translator import GoogleTranslator
            # logger.info("Menggunakan Deep Translator (Online)...")
            translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
            if translated:
                return translated
        except Exception as e:
            logger.warning(f"Deep Translator gagal: {e}. Beralih ke offline...")

    # 2. Coba Offline (Argos Translate)
    global argos_installed
    if not argos_installed:
        init_offline_translator()
    
    if argos_installed:
        try:
            import argostranslate.translate
            # logger.info("Menggunakan Argos Translate (Offline)...")
            return argostranslate.translate.translate(text, source_lang, target_lang)
        except Exception as e:
            logger.error(f"Argos Translate gagal: {e}")
    
    return text # Kembalikan teks asli jika semua gagal

def is_english(text):
    """Heuristik sederhana untuk mendeteksi apakah teks kemungkinan besar bahasa Inggris."""
    if not text: return False
    
    en_words = {'the', 'and', 'is', 'are', 'was', 'were', 'that', 'this', 'with', 'from', 'have', 'has', 'not', 'for', 'but'}
    id_words = {'yang', 'dan', 'adalah', 'itu', 'ini', 'dengan', 'dari', 'tidak', 'untuk', 'tapi', 'ada', 'sudah', 'telah'}
    
    words = text.lower().split()
    en_score = sum(1 for w in words if w in en_words)
    id_score = sum(1 for w in words if w in id_words)
    
    # Jika banyak kata Inggris dan sedikit kata Indonesia
    return en_score > id_score or (en_score > 0 and id_score == 0)
