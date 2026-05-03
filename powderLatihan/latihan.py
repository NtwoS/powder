import os
import json

def simpan_ke_respon_powder(pemicu, respon):
    pemicu = pemicu.strip().lower()
    respon = respon.strip()
    
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'intents.json')
    
    # Baca file JSON saat ini
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = {"responses": {}, "default_responses": [], "vocabulary": []}
        
    # Buat pola regex sederhana
    pattern = f"\\b({pemicu})\\b"
    
    # Tambahkan ke dictionary responses
    if pattern not in data["responses"]:
        data["responses"][pattern] = []
    
    if respon not in data["responses"][pattern]:
        data["responses"][pattern].append(respon)
        
    # Tambahkan kata-kata ke vocabulary jika belum ada
    words = pemicu.split()
    for word in words:
        if word not in data.get("vocabulary", []):
            data["vocabulary"].append(word)
            
    # Simpan kembali ke file JSON dengan format rapi
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
def mulai_latihan(ai_name):
    print("\n" + "="*45)
    print(f"   MODE LATIHAN {ai_name.upper()} AKTIF   ")
    print("="*45)
    print("Ketik 'selesai' untuk keluar dari mode latihan.\n")
    
    while True:
        pemicu = input("Anda (Pemicu/Pertanyaan): ")
        if pemicu.lower() == 'selesai':
            print("Keluar dari mode latihan.")
            break
            
        if not pemicu.strip():
            continue
            
        respon = input(f"{ai_name} (Respon): ")
        if respon.lower() == 'selesai':
            break
            
        try:
            simpan_ke_respon_powder(pemicu, respon)
            print(f"-> Berhasil! Mulai sekarang jika Anda mengetik '{pemicu}', {ai_name} akan merespon.\n")
        except Exception as e:
            print(f"-> Gagal menyimpan: {e}\n")
