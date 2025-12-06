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
    UPDATED: DEC 6, 2025 (EVENING SLATE)
    """
    return [
        # 5:00 PM EST
        {
            "home": "BKN", "away": "NOP", "time": "5:00 PM", "h_rec": "Live", "a_rec": "Live", 
            "book_spread": -3.5, "spread_odds": -110, # Nets -3.5
            "book_total": 227.0, "total_odds": -110,
            "h_ml": -160, "a_ml": +135
        },

        # 7:00 PM EST
        {
            "home": "WAS", "away": "ATL", "time": "7:00 PM", "h_rec": "Live", "a_rec": "Live", 
            "book_spread": 9.0, "spread_odds": -105, # Wizards +9 (Hawks Favored)
            "book_total": 235.0, "total_odds": -110,
            "h_ml": +325, "a_ml": -450
        },

        # 7:30 PM EST
        {
            "home": "DET", "away": "MIL", "time": "7:30 PM", "h_rec": "Live", "a_rec": "Live", 
            "book_spread": -12.5, "spread_odds": -115, # Pistons -12.5 (Bucks underdog?)
            "book_total": 223.0, "total_odds": -110,
            "h_ml": -700, "a_ml": +475
        },
        {
            "home": "CLE", "away": "GSW", "time": "7:30 PM", "h_rec": "Live", "a_rec": "Live", 
            "book_spread": -8.0, "spread_odds": -110, # Cavs -8
            "book_total": 227.5, "total_odds": -110,
            "h_ml": -325, "a_ml": +250
        },

        # 8:00 PM EST
        {
            "home": "MIN", "away": "LAC", "time": "8:00 PM", "h_rec": "Live", "a_rec": "Live", 
            "book_spread": -10.5, "spread_odds": -110, # Wolves -10.5
            "book_total": 225.5, "total_odds": -110,
            "h_ml": -475, "a_ml": +350
        },
        {
            "home": "MIA", "away": "SAC", "time": "8:00 PM", "h_rec": "Live", "a_rec": "Live", 
            "book_spread": -8.0, "spread_odds": -110, # Heat -8
            "book_total": 239.5, "total_odds": -110,
            "h_ml": -325, "a_ml": +250
        },

        # 8:30 PM EST
        {
            "home": "DAL", "away": "HOU", "time": "8:30 PM", "h_rec": "Live", "a_rec": "Live", 
            "book_spread": 8.5, "spread_odds": -105, # Mavs +8.5 (Rockets Favored)
            "book_total": 224.5, "total_odds": -110,
            "h_ml": +300, "a_ml": -400
        },
    ]

# --- 4. PREDICTION LOGIC ---
def get_matchup_projection(home, away):
    h_rat = 5
    a_rat = 5
    
    # Dynamic Power Rankings (Updated Dec 6)
    tier_1 = ["BOS", "OKC", "CLE", "HOU", "ORL", "DET"] # Added DET to T1 based on -12.5 line
    tier_2 = ["MEM", "NYK", "DAL", "DEN", "LAL", "MIN", "MIA"] 
    tier_3 = ["LAC", "GSW", "PHX", "MIL", "ATL", "PHI", "BKN"] 
    tier_4 = ["CHI", "IND", "POR", "SAS", "TOR", "CHA", "UTA", "WAS", "NOP", "SAC"]
    
    def get_rating(team):
        if team in tier_1: return 10
        if team in tier_2: return 6
        if team in tier_3: return 2
        return -5 

    h_rat = get_rating(home) + 3 # Home Court
    a_rat = get_rating(away)
    
    raw_spread = a_rat - h_rat 
    
    win_prob = 1 / (1 + np.exp(0.15 * raw_spread)) * 100
    
    # Scoring
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