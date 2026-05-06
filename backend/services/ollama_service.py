import requests
import json
import os


def list_ollama_models(base_url="http://localhost:11434", models_path=None):
    """
    Mengambil daftar model yang terinstal di Ollama lokal.
    Jika ada models_path, kita juga coba scan foldernya secara fisik sebagai backup.
    """
    all_models = []
    
    # 1. Coba lewat API resmi dulu (hanya jika base_url ada)
    if base_url:
        url = f"{base_url}/api/tags"
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                all_models = [m["name"] for m in data.get("models", [])]
        except:
            pass

    # 2. Jika ada path khusus, scan manual sebagai tambahan/backup
    if models_path and os.path.exists(models_path):
        manifest_dir = os.path.join(models_path, "manifests")
        if os.path.exists(manifest_dir):
            try:
                for root, dirs, files in os.walk(manifest_dir):
                    for file in files:
                        try:
                            rel_path = os.path.relpath(root, manifest_dir)
                            parts = rel_path.replace('\\', '/').split('/')
                            # Format path Ollama: registry/namespace/model
                            if len(parts) >= 3:
                                namespace = parts[1]
                                model_name = "/".join(parts[2:])
                                
                                if namespace == 'library':
                                    full_name = f"{model_name}:{file}"
                                else:
                                    full_name = f"{namespace}/{model_name}:{file}"
                                    
                                if full_name not in all_models:
                                    all_models.append(full_name)
                        except Exception:
                            pass
            except Exception as e:
                print(f"Error scanning manual folder: {e}")
                
    return all_models


def get_first_available_model(base_url="http://localhost:11434"):
    """
    Mendapatkan model pertama yang tersedia di Ollama secara otomatis.
    Sangat berguna agar kode tidak 'kaku' (hardcoded).
    Mengembalikan None jika tidak ada model sama sekali agar pemanggil bisa handle.
    """
    from database.db_manager import get_setting
    models_path = get_setting('ollama_models_path', '').strip()
    
    models = list_ollama_models(base_url, models_path=models_path)
    if models:
        return models[0]
    return None  # Tidak ada model yang tersedia


def ask_ollama(prompt, model=None, system=None, options=None, base_url="http://localhost:11434"):
    """
    Mengirim prompt ke API Ollama lokal.
    Jika model tidak diberikan, secara otomatis mengambil model pertama yang tersedia.
    """
    if not model:
        model = get_first_available_model(base_url)
    
    if not model:
        print("Ollama Error: Tidak ada model yang tersedia. Pastikan Ollama sudah dijalankan dan model sudah diunduh.")
        return None

    url = f"{base_url}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    if system:
        payload["system"] = system
    
    if options:
        payload["options"] = options

    try:
        response = requests.post(url, json=payload, timeout=None)
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "").strip()
        else:
            print(f"Ollama Error: {response.status_code} - {response.text[:200]}")
            return None
    except requests.exceptions.ConnectionError:
        print("Ollama Error: Tidak dapat terhubung ke Ollama. Pastikan Ollama sudah dijalankan.")
        return None
    except Exception as e:
        print(f"Ollama Error: {e}")
        return None


if __name__ == "__main__":
    # Test sederhana
    res = ask_ollama("Halo, siapa namamu?")
    print(f"Response: {res}")
