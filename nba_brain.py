# NBA SNIPER INTELLIGENCE ENGINE V6.3 (ODDSMAKER REVERT)
# STATUS: MANUAL TARGETING WITH FULL ODDS (NO API)
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
        
        # Mock fit to ensure objects exist
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

# --- 3. TARGETING FEED (MANUAL FULL ODDS) ---
def get_todays_games():
    """
    Returns exact games with Moneyline (ML) and Spread Odds.
    UPDATE THIS LIST DAILY FROM HARD ROCK BET.
    """
    return [
        # GAME 1
        {
            "home": "MIA", "away": "NYK", "time": "7:30 PM", 
            "h_rec": "12-9", "a_rec": "14-8", 
            "book_spread": -2.5, "spread_odds": -110, 
            "book_total": 218.0, "total_odds": -110,
            "h_ml": -140, "a_ml": +120
        },
        
        # GAME 2
        {
            "home": "LAL", "away": "PHX", "time": "10:00 PM", 
            "h_rec": "15-10", "a_rec": "13-11", 
            "book_spread": 4.5, "spread_odds": -115, 
            "book_total": 235.5, "total_odds": -110,
            "h_ml": +160, "a_ml": -190
        },
    ]

# --- 4. PREDICTION LOGIC ---
def get_matchup_projection(home, away):
    # Dynamic Tier System
    tier_1 = ["BOS", "MIN", "OKC", "DEN", "PHI", "MIL"] 
    tier_2 = ["LAL", "NYK", "MIA", "SAC", "IND", "NOP", "ORL", "CLE"] 
    tier_3 = ["GSW", "HOU", "BKN", "UTA", "TOR", "DAL", "PHX"] 
    tier_4 = ["ATL", "CHI", "CHA", "POR", "MEM", "WAS", "DET", "SAS"]
    
    def get_rating(team):
        if team in tier_1: return 10
        if team in tier_2: return 5
        if team in tier_3: return 0
        return -6 

    h_rat = get_rating(home) + 3 
    a_rat = get_rating(away)
    
    raw_spread = a_rat - h_rat 
    
    # Calculate implied Moneyline Probability (Sigmoid)
    win_prob = 1 / (1 + np.exp(0.15 * raw_spread)) * 100
    
    # Projected Score
    base_total = 230
    if home in tier_1 or away in tier_1: base_total -= 3 
    if home in tier_4 or away in tier_4: base_total += 3
    
    proj_h_score = (base_total / 2) - (raw_spread / 2)
    proj_a_score = (base_total / 2) + (raw_spread / 2)
    
    return {
        "projected_spread": raw_spread,
        "projected_total": base_total,
        "win_prob": win_prob,
        "score_str": f"{int(proj_a_score)} - {int(proj_h_score)}"
    }

def log_transaction(matchup, pick, wager, result="Pending"):
    try:
        new_rec = {"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Matchup": matchup, "Pick": pick, "Wager": wager, "Result": result}
        if os.path.exists(HISTORY_FILE): df = pd.read_csv(HISTORY_FILE)
        else: df = pd.DataFrame(columns=new_rec.keys())
        df = pd.concat([df, pd.DataFrame([new_rec])], ignore_index=True)
        df.to_csv(HISTORY_FILE, index=False)
    except: pass