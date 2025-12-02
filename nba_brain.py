import pandas as pd
import numpy as np
import pickle
import requests
from sklearn.linear_model import RidgeClassifier
from sklearn.preprocessing import StandardScaler
import os

def build_brain():
    print("🧠 STARTING BRAIN SURGERY...")

    # --- 1. DOWNLOAD DATA ---
    print("⬇️  Downloading stats history...")
    url = "https://drive.google.com/uc?export=download&id=1YyNpERG0jqPlpxZvvELaNcMHTiKVpfWe"
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        with open("nba_games.csv", "wb") as f:
            f.write(r.content)
        print("✅ Data downloaded.")
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return

    # --- 2. PROCESS DATA ---
    print("⚙️  Processing rolling averages (this takes a moment)...")
    df = pd.read_csv("nba_games.csv", parse_dates=["date"])
    df = df.sort_values("date")
    
    # Fix team names
    code_map = {"NOH":"NOP", "CHO":"CHA", "BRK":"BKN", "PHO":"PHX"}
    df.replace(code_map, inplace=True)
    
    # Clean columns
    cols_drop = ["mp.1", "mp_opp.1", "index_opp"]
    df = df.drop(columns=[c for c in cols_drop if c in df.columns])
    
    # Create Target (Did they win the NEXT game?)
    df["target"] = df.groupby("team")["won"].shift(-1).fillna(0).astype(int)
    
    # Rolling Averages (The "Sniper" Logic)
    numeric = df.select_dtypes(include=[np.number])
    cols = [c for c in numeric.columns if c not in ["season", "target", "won"]]
    r10 = df.groupby("team")[cols].rolling(10, min_periods=1).mean().reset_index(0, drop=True)
    r10.columns = [f"{c}_R10" for c in r10.columns]
    
    df = pd.concat([df, r10], axis=1).fillna(0)
    
    # Save the processed data for the App to use
    df.to_csv("nba_games_rolled.csv", index=False)
    print("✅ Stats processed and saved.")

    # --- 3. TRAIN MODEL ---
    print("💪 Training the ML Model...")
    features = [c for c in df.columns if "_R10" in c]
    X = df[features]
    y = df["target"]
    
    scaler = StandardScaler()
    X_sc = scaler.fit_transform(X)
    
    model = RidgeClassifier()
    model.fit(X_sc, y)
    
    # Save the Brain
    pkg = {"model": model, "scaler": scaler, "features": features}
    with open("nba_brain.pkl", "wb") as f:
        pickle.dump(pkg, f)
    
    print("✅ BRAIN SUCCESSFULLY BUILT! You can now run the app.")

if __name__ == "__main__":
    build_brain()
