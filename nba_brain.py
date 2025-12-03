# NBA SNIPER INTELLIGENCE ENGINE V5.1 (DEBUG PROTOCOL)
# FORCE CACHE FLUSH: ACTIVATED
import pandas as pd
import numpy as np
import os
import pickle
from datetime import datetime
from sklearn.linear_model import RidgeClassifier, Ridge
from sklearn.preprocessing import StandardScaler

# CONFIG
DATA_FILE = "nba_games_processed.csv"
MODEL_FILE = "nba_model_v1.pkl"
HISTORY_FILE = "nba_betting_ledger.csv"

# --- 1. DATA ENGINE ---
def update_nba_data():
    """Creates a placeholder database if none exists."""
    if not os.path.exists(DATA_FILE):
        print("🏀 REBIRTH: INITIALIZING NBA DATABASE...")
        cols = ['game_id', 'date', 'home_team', 'away_team', 'home_score', 'away_score', 'h_mom', 'a_mom', 'h_off', 'a_off']
        df = pd.DataFrame(columns=cols)
        df.to_csv(DATA_FILE, index=False)
        return df
    return pd.read_csv(DATA_FILE)

# --- 2. BRAIN ENGINE ---
def train_nba_model():
    """Trains Winner, Spread, and Total models."""
    if not os.path.exists(DATA_FILE): update_nba_data()
    
    try:
        # We use simple Heuristic Training for V5.0 stability
        model_win = RidgeClassifier()
        model_spread = Ridge()
        model_total = Ridge()
        scaler = StandardScaler()
        
        # Mock fit to ensure objects exist
        X_mock = np.array([[0,0], [10,10]])
        y_win = np.array([0, 1])
        y_spread = np.array([-5, 5])
        y_total = np.array([200, 220])
        
        model_win.fit(X_mock, y_win)
        model_spread.fit(X_mock, y_spread)
        model_total.fit(X_mock, y_total)
        
        pkg = {
            "model_win": model_win,
            "model_spread": model_spread, 
            "model_total": model_total,
            "scaler": scaler
        }
        with open(MODEL_FILE, "wb") as f: pickle.dump(pkg, f)
        return pkg
    except Exception as e:
        print(f"Training Error: {e}")
        return None

def load_brain_engine():
    """Loads the Intelligence Package."""
    if not os.path.exists(DATA_FILE): update_nba_data()
    if not os.path.exists(MODEL_FILE): train_nba_model()
    
    try:
        with open(MODEL_FILE, "rb") as f: pkg = pickle.load(f)
        return pd.read_csv(DATA_FILE), pkg
    except:
        pkg = train_nba_model()
        return pd.read_csv(DATA_FILE), pkg

# --- 3. PREDICTION LOGIC (THE MISSING LINK) ---
def get_matchup_projection(home, away):
    """
    Calculates the 'True Line' based on Momentum.
    Returns: {win_prob, projected_spread, projected_total}
    """
    # Simulate Momentum
    tier_1 = ["BOS", "DEN", "OKC", "MIN", "LAC", "CLE"] 
    tier_2 = ["MIL", "PHX", "NYK", "DAL", "MIA"] 
    tier_3 = ["LAL", "GSW", "SAC", "IND", "NOP", "ORL"] 
    tier_4 = ["HOU", "ATL", "BKN", "UTA", "CHI"] 
    
    def get_rating(team):
        if team in tier_1: return 10
        if team in tier_2: return 5
        if team in tier_3: return 0
        if team in tier_4: return -5
        return -8 

    h_rat = get_rating(home) + 3 # Home Court Advantage
    a_rat = get_rating(away)
    
    # 1. SPREAD CALCULATION
    raw_spread = a_rat - h_rat 
    
    # 2. TOTAL CALCULATION
    base_total = 230
    if home in tier_1 or away in tier_1: base_total -= 4 
    if home in tier_3 or away in tier_3: base_total += 4 
    
    # 3. WIN PROBABILITY
    win_prob = 1 / (1 + np.exp(0.15 * raw_spread)) * 100
    
    return {
        "projected_spread": raw_spread,
        "projected_total": base_total,
        "win_prob": win_prob
    }

# --- 4. UTILITIES ---
def get_todays_games():
    """Returns games matching the Hard Rock screenshot style."""
    today = datetime.now().strftime("%Y-%m-%d")
    return [
        {"home": "IND", "away": "DEN", "time": "7:00 PM"},
        {"home": "CLE", "away": "POR", "time": "7:00 PM"},
        {"home": "NYK", "away": "CHA", "time": "7:30 PM"},
        {"home": "CHI", "away": "BKN", "time": "8:00 PM"},
        {"home": "HOU", "away": "SAC", "time": "8:00 PM"},
        {"home": "DAL", "away": "MIA", "time": "8:30 PM"},
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