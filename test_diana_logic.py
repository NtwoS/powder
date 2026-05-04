import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from diana import SimpleLocalAI

try:
    print("Inisialisasi Diana...")
    ai = SimpleLocalAI()
    print(f"Nama AI: {ai.name}")
    print(f"User: {ai.user_name}")
    
    print("Testing respond...")
    response = ai.respond("Halo")
    print(f"Diana: {response}")
    
    print("SUCCESS: Diana is online and working.")
except Exception as e:
    print(f"ERROR: Diana failed to start - {e}")
    import traceback
    traceback.print_exc()
