import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from database.db_manager import get_all_intents

try:
    intents = get_all_intents()
    print(f"Jumlah pemicu di database: {len(intents)}")
    if len(intents) > 0:
        print("Contoh pemicu (3 teratas):")
        for i, pattern in enumerate(list(intents.keys())[:3]):
            print(f"{i+1}. {pattern}")
    else:
        print("DATABASE KOSONG!")
except Exception as e:
    print(f"Error: {e}")
