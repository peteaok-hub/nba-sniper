# NBA SNIPER INTELLIGENCE ENGINE V5.2 (DATA ENRICHED)
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
    if not os.path.exists(DATA_FILE):
        cols = ['game_id', 'date', 'home_team', 'away_team', 'home_score', 'away_score', 'h_mom', 'a_mom', 'h_off', 'a_off']
        df = pd.DataFrame(columns=cols)
        df.to_csv(DATA_FILE, index=False)
        return df
    return pd.read_csv(DATA_FILE)

# --- 2. BRAIN ENGINE ---
def train_nba_model():
    if not os.path.exists(DATA_FILE): update_nba_data()
    try:
        model_win = RidgeClassifier()
        model_spread = Ridge()
        model_total = Ridge()
        scaler = StandardScaler()
        
        # Mock fit
        X_mock = np.array([[0,0], [10,10]])
        y_win = np.array([0, 1])
        y_spread = np.array([-5, 5])
        y_total = np.array([200, 220])
        
        model_win.fit(X_mock, y_win)
        model_spread.fit(X_mock, y_spread)
        model_total.fit(X_mock, y_total)
        
        pkg = {"model_win": model_win, "model_spread": model_spread, "model_total": model_total, "scaler": scaler}
        with open(MODEL_FILE, "wb") as f: pickle.dump(pkg, f)
        return pkg
    except: return None

def load_brain_engine():
    if not os.path.exists(DATA_FILE): update_nba_data()
    if not os.path.exists(MODEL_FILE): train_nba_model()
    try:
        with open(MODEL_FILE, "rb") as f: pkg = pickle.load(f)
        return pd.read_csv(DATA_FILE), pkg
    except:
        pkg = train_nba_model()
        return pd.read_csv(DATA_FILE), pkg

# --- 3. PREDICTION LOGIC ---
def get_matchup_projection(home, away):
    """
    Calculates the 'True Line' based on Momentum.
    """
    # Momentum Tiers (Simulated for V5.2)
    tier_1 = ["BOS", "DEN", "OKC", "MIN", "LAC", "CLE", "MIL"] 
    tier_2 = ["PHX", "NYK", "DAL", "MIA", "SAC", "IND", "NOP"] 
    tier_3 = ["LAL", "GSW", "ORL", "HOU", "BKN", "UTA"] 
    tier_4 = ["ATL", "CHI", "CHA", "POR", "MEM", "TOR"]
    
    def get_rating(team):
        if team in tier_1: return 10
        if team in tier_2: return 5
        if team in tier_3: return 0
        return -5 # Tier 4/5

    h_rat = get_rating(home) + 3 # Home Court
    a_rat = get_rating(away)
    
    # Spread: Negative = Home Favorite
    raw_spread = a_rat - h_rat 
    
    # Total: Baseline 230
    base_total = 230
    if home in tier_1 or away in tier_1: base_total -= 4 
    if home in tier_3 or away in tier_3: base_total += 4 
    
    win_prob = 1 / (1 + np.exp(0.15 * raw_spread)) * 100
    
    return {
        "projected_spread": raw_spread,
        "projected_total": base_total,
        "win_prob": win_prob,
        "h_mom": h_rat,
        "a_mom": a_rat
    }

# --- 4. UTILITIES (HARD ROCK DATA FEED) ---
def get_todays_games():
    """
    Returns games with 'Book Lines' derived from your screenshot.
    """
    return [
        {"home": "IND", "away": "DEN", "time": "7:00 PM", "h_rec": "14-8", "a_rec": "16-6", "book_spread": -8.0, "book_total": 236.0},
        {"home": "CLE", "away": "POR", "time": "7:00 PM", "h_rec": "13-9", "a_rec": "6-15", "book_spread": -10.0, "book_total": 240.5},
        {"home": "ORL", "away": "SAS", "time": "7:00 PM", "h_rec": "16-5", "a_rec": "3-18", "book_spread": -8.0, "book_total": 235.0},
        {"home": "NYK", "away": "CHA", "time": "7:30 PM", "h_rec": "12-8", "a_rec": "7-13", "book_spread": -8.5, "book_total": 237.0},
        {"home": "ATL", "away": "LAC", "time": "7:30 PM", "h_rec": "9-11", "a_rec": "11-10", "book_spread": -3.0, "book_total": 226.5},
        {"home": "MIL", "away": "DET", "time": "8:00 PM", "h_rec": "15-6", "a_rec": "2-19", "book_spread": -5.0, "book_total": 230.5},
        {"home": "HOU", "away": "SAC", "time": "8:00 PM", "h_rec": "10-10", "a_rec": "12-8", "book_spread": -15.5, "book_total": 231.0},
        {"home": "CHI", "away": "BKN", "time": "8:00 PM", "h_rec": "9-13", "a_rec": "12-9", "book_spread": 8.0, "book_total": 231.0},
        {"home": "DAL", "away": "MIA", "time": "8:30 PM", "h_rec": "14-8", "a_rec": "12-9", "book_spread": -5.5, "book_total": 240.5},
    ]

def log_transaction(matchup, pick, wager, result="Pending"):
    try:
        new_rec = {"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Matchup": matchup, "Pick": pick, "Wager": wager, "Result": result}
        if os.path.exists(HISTORY_FILE): df = pd.read_csv(HISTORY_FILE)
        else: df = pd.DataFrame(columns=new_rec.keys())
        df = pd.concat([df, pd.DataFrame([new_rec])], ignore_index=True)
        df.to_csv(HISTORY_FILE, index=False)
    except: pass