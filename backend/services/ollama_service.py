import requests
import json

def ask_ollama(prompt, model="llama3", system=None, options=None):
    """
    Mengirim prompt ke API Ollama lokal.
    """
    url = "http://localhost:11434/api/generate"
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
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "").strip()
        else:
            print(f"Ollama Error: {response.status_code}")
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
