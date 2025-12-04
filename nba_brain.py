# NBA SNIPER INTELLIGENCE ENGINE V6.3 (ODDSMAKER)
# STATUS: MANUAL TARGETING WITH FULL ODDS
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

# --- 3. TARGETING FEED (FULL ODDS) ---
def get_todays_games():
    """
    Returns exact games with Moneyline (ML) and Spread Odds.
    """
    return [
        # Celtics @ Wizards
        {
            "home": "WAS", "away": "BOS", "time": "7:00 PM", 
            "h_rec": "3-17", "a_rec": "18-4", 
            "book_spread": 8.5, "spread_odds": -110, # Wizards +8.5
            "book_total": 228.5, "total_odds": -110,
            "h_ml": +300, "a_ml": -400
        },
        # Warriors @ 76ers
        {
            "home": "PHI", "away": "GSW", "time": "7:00 PM", 
            "h_rec": "14-7", "a_rec": "10-11", 
            "book_spread": -3.5, "spread_odds": -110, # 76ers -3.5
            "book_total": 224.0, "total_odds": -110,
            "h_ml": -160, "a_ml": +135
        },
        # Jazz @ Nets
        {
            "home": "BKN", "away": "UTA", "time": "7:30 PM", 
            "h_rec": "10-11", "a_rec": "7-14", 
            "book_spread": 4.5, "spread_odds": -110, # Nets +4.5 (Jazz Favored)
            "book_total": 231.0, "total_odds": -110,
            "h_ml": +150, "a_ml": -180
        },
        # Lakers @ Raptors
        {
            "home": "TOR", "away": "LAL", "time": "7:30 PM", 
            "h_rec": "9-12", "a_rec": "12-9", 
            "book_spread": -2.0, "spread_odds": -110, # Raptors -2.0
            "book_total": 228.0, "total_odds": -110,
            "h_ml": -125, "a_ml": +105
        },
        # Wolves @ Pelicans
        {
            "home": "NOP", "away": "MIN", "time": "8:00 PM", 
            "h_rec": "11-11", "a_rec": "16-4", 
            "book_spread": 11.5, "spread_odds": -110, # Pelicans +11.5
            "book_total": 233.5, "total_odds": -110,
            "h_ml": +400, "a_ml": -550
        },
    ]

# --- 4. PREDICTION LOGIC ---
def get_matchup_projection(home, away):
    # Dynamic Tier System
    tier_1 = ["BOS", "MIN", "OKC", "DEN", "PHI"] 
    tier_2 = ["LAL", "NYK", "MIA", "SAC", "IND", "NOP", "ORL"] 
    tier_3 = ["GSW", "HOU", "BKN", "UTA", "CLE", "TOR"] 
    tier_4 = ["ATL", "CHI", "CHA", "POR", "MEM", "WAS", "DET", "SAS"]
    
    def get_rating(team):
        if team in tier_1: return 10
        if team in tier_2: return 5
        if team in tier_3: return 0
        return -6 

    h_rat = get_rating(home) + 3 
    a_rat = get_rating(away)
    
    raw_spread = a_rat - h_rat 
    
    # Calculate implied Moneyline Probability
    # Simplistic conversion for V6.3
    # If spread is -8, win prob is high
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