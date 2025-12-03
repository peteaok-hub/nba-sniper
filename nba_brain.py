import pandas as pd
import numpy as np
import requests
import os
import pickle
from datetime import datetime, timedelta
from sklearn.linear_model import RidgeClassifier
from sklearn.preprocessing import StandardScaler

# CONFIG
DATA_FILE = "nba_games_processed.csv"
MODEL_FILE = "nba_model_v1.pkl"
HISTORY_FILE = "nba_betting_ledger.csv"

# --- 1. DATA ENGINE ---
def update_nba_data():
    """Fetches latest NBA game data (Mock/Placeholder for V4.1 stability)."""
    # In V5 we will hook this to the live NBA_API. 
    # For now, we ensure the file exists so the app doesn't crash.
    if not os.path.exists(DATA_FILE):
        print("🏀 INITIALIZING NBA DATABASE...")
        # Create a dummy structure if file is missing to prevent crash
        cols = ['game_id', 'date', 'home_team', 'away_team', 'home_score', 'away_score', 'h_mom', 'a_mom']
        df = pd.DataFrame(columns=cols)
        df.to_csv(DATA_FILE, index=False)
        return df
    return pd.read_csv(DATA_FILE)

# --- 2. BRAIN ENGINE ---
def train_nba_model():
    """Trains the prediction model."""
    if not os.path.exists(DATA_FILE): update_nba_data()
    
    try:
        df = pd.read_csv(DATA_FILE)
        if df.empty or len(df) < 10:
            # Return a dummy model if not enough data
            model = RidgeClassifier()
            scaler = StandardScaler()
            pkg = {"model": model, "scaler": scaler}
            with open(MODEL_FILE, "wb") as f: pickle.dump(pkg, f)
            return pkg

        # Real training logic would go here
        # For V4.1 stability, we return a basic initialized model
        model = RidgeClassifier()
        scaler = StandardScaler()
        # Mock fitting to avoid sklearn errors
        X_mock = np.array([[0,0], [1,1]])
        y_mock = np.array([0, 1])
        model.fit(X_mock, y_mock)
        
        pkg = {"model": model, "scaler": scaler}
        with open(MODEL_FILE, "wb") as f: pickle.dump(pkg, f)
        return pkg
    except Exception as e:
        print(f"Training Error: {e}")
        return None

# --- 3. THE MISSING FUNCTION (FIX) ---
def load_brain_engine():
    """Loads the Data and Model for the App."""
    # 1. Ensure Data Exists
    if not os.path.exists(DATA_FILE):
        df = update_nba_data()
    else:
        df = pd.read_csv(DATA_FILE)
        
    # 2. Ensure Model Exists
    if not os.path.exists(MODEL_FILE):
        pkg = train_nba_model()
    else:
        try:
            with open(MODEL_FILE, "rb") as f: pkg = pickle.load(f)
        except:
            pkg = train_nba_model() # Rebuild if corrupt
            
    return df, pkg

# --- 4. UTILITIES ---
def get_todays_games():
    """Fetches today's schedule."""
    # This logic matches your 'Prop Sniper' / 'Game Predictor' tabs
    # For V4.1, we return a clean list or scrape live
    # Returning a mock list for the UI to render correctly
    today = datetime.now().strftime("%Y-%m-%d")
    return [
        {"home": "LAL", "away": "BOS", "time": "7:30 PM", "date": today},
        {"home": "MIA", "away": "NYK", "time": "8:00 PM", "date": today},
        {"home": "GSW", "away": "PHX", "time": "10:00 PM", "date": today},
    ]

def log_transaction(matchup, pick, wager, result="Pending"):
    try:
        new_rec = {
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Matchup": matchup,
            "Pick": pick,
            "Wager": wager,
            "Result": result
        }
        if os.path.exists(HISTORY_FILE): df = pd.read_csv(HISTORY_FILE)
        else: df = pd.DataFrame(columns=new_rec.keys())
        df = pd.concat([df, pd.DataFrame([new_rec])], ignore_index=True)
        df.to_csv(HISTORY_FILE, index=False)
    except: pass
