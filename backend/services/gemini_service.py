import google.generativeai as genai
import os

def ask_gemini(prompt, api_key, model="gemini-2.5-pro", system=None):
    """
    Mengirim prompt ke API Gemini.
    """
    if not api_key:
        print("Gemini Error: API Key tidak ditemukan.")
        return None
        
    try:
        genai.configure(api_key=api_key)
        
        # Inisialisasi model
        generation_config = {
          "temperature": 0.7,
          "top_p": 0.95,
          "top_k": 64,
          "max_output_tokens": 8192,
        }
        
        # System instruction hanya disupport oleh gemini-1.5-pro atau gemini-1.5-flash terbaru
        if system:
             model_instance = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
                system_instruction=system
            )
        else:
             model_instance = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
            )
            
        response = model_instance.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"Gemini Error: {e}")
        return None

if __name__ == "__main__":
    # Test sederhana
    print("Gemini Service Ready.")
