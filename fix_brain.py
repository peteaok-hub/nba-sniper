import nba_brain as brain
import time

print("🧠 NBA SNIPER: BRAIN SURGERY")
try:
    pkg = brain.train_nba_model()
    if pkg:
        print("[3/3] Saving Neural Pathways (nba_model_v1.pkl)... DONE.")
    else:
        print("[!] Training Failed.")
except Exception as e:
    print(f"[!] CRITICAL FAILURE: {e}")