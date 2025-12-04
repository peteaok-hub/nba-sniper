# NBA SNIPER INTELLIGENCE ENGINE V5.2 (DAILY UPDATE)
# TARGET DATE: DEC 4 2025
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
    # Momentum Tiers (Updated for Dec 4)
    tier_1 = ["BOS", "MIN", "OKC", "DEN"] # Elite
    tier_2 = ["PHI", "LAL", "ORL", "NYK", "MIA"] # Strong
    tier_3 = ["GSW", "BKN", "TOR", "CLE", "HOU"] # Mid
    tier_4 = ["WAS", "UTA", "NOP", "DET", "SAS"] # Weak
    
    def get_rating(team):
        if team in tier_1: return 10
        if team in tier_2: return 5
        if team in tier_3: return 0
        return -6 # Tier 4

    h_rat = get_rating(home) + 3 # Home Court Advantage
    a_rat = get_rating(away)
    
    # Spread Calculation
    raw_spread = a_rat - h_rat 
    
    # Total Calculation
    base_total = 230
    if home in tier_1 or away in tier_1: base_total -= 3 
    if home in tier_4 or away in tier_4: base_total += 3 
    
    win_prob = 1 / (1 + np.exp(0.15 * raw_spread)) * 100
    
    return {
        "projected_spread": raw_spread,
        "projected_total": base_total,
        "win_prob": win_prob,
        "h_mom": h_rat,
        "a_mom": a_rat
    }

# --- 4. UTILITIES (DAILY TARGET LIST) ---
def get_todays_games():
    """
    MANUAL FEED: Games transcribed from Hard Rock Screenshot (Dec 4).
    """
    return [
        # Celtics @ Wizards (+9)
        {"home": "WAS", "away": "BOS", "time": "7:00 PM", "h_rec": "3-17", "a_rec": "18-4", "book_spread": 9.0, "book_total": 228.5},
        
        # Warriors @ 76ers (-3.5)
        {"home": "PHI", "away": "GSW", "time": "7:00 PM", "h_rec": "14-7", "a_rec": "10-11", "book_spread": -3.5, "book_total": 224.0},
        
        # Jazz @ Nets (+4.5) - Note: Hard Rock shows Jazz favored
        {"home": "BKN", "away": "UTA", "time": "7:30 PM", "h_rec": "10-11", "a_rec": "7-14", "book_spread": 4.5, "book_total": 231.0},
        
        # Lakers @ Raptors (-2)
        {"home": "TOR", "away": "LAL", "time": "7:30 PM", "h_rec": "9-12", "a_rec": "12-9", "book_spread": -2.0, "book_total": 228.0},
        
        # Timberwolves @ Pelicans (+11.5)
        {"home": "NOP", "away": "MIN", "time": "8:00 PM", "h_rec": "11-11", "a_rec": "16-4", "book_spread": 11.5, "book_total": 233.5},
    ]

def log_transaction(matchup, pick, wager, result="Pending"):
    try:
        new_rec = {"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Matchup": matchup, "Pick": pick, "Wager": wager, "Result": result}
        if os.path.exists(HISTORY_FILE): df = pd.read_csv(HISTORY_FILE)
        else: df = pd.DataFrame(columns=new_rec.keys())
        df = pd.concat([df, pd.DataFrame([new_rec])], ignore_index=True)
        df.to_csv(HISTORY_FILE, index=False)
    except: pass