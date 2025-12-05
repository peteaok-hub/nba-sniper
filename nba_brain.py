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
    UPDATE THE NUMBERS BELOW WITH LINES FROM HARD ROCK BET.
    """
    return [
        # 7:00 PM GAMES
        {
            "home": "BOS", "away": "LAL", "time": "7:00 PM", "h_rec": "18-3", "a_rec": "12-9", 
            "book_spread": -8., "spread_odds": -325, # Boston Favored
            "book_total": 228.0, "total_odds": -110,
            "h_ml": -400, "a_ml": +310
        },
        {
            "home": "ORL", "away": "MIA", "time": "7:00 PM", "h_rec": "15-5", "a_rec": "11-9", 
            "book_spread": -5.5, "spread_odds": -220, 
            "book_total": 222.5, "total_odds": -110,
            "h_ml": -165, "a_ml": +140
        },

        # 7:30 PM GAMES
        {
            "home": "CLE", "away": "SAS", "time": "7:30 PM", "h_rec": "13-8", "a_rec": "3-17", 
            "book_spread": -3.5, "spread_odds": -160, 
            "book_total": 226.0, "total_odds": -110,
            "h_ml": -600, "a_ml": +450
        },
        {
            "home": "TOR", "away": "CHA", "time": "7:30 PM", "h_rec": "9-11", "a_rec": "6-13", 
            "book_spread": -7, "spread_odds": -275, 
            "book_total": 224.5, "total_odds": -110,
            "h_ml": -175, "a_ml": +150
        },
        {
            "home": "ATL", "away": "DEN", "time": "7:30 PM", "h_rec": "9-11", "a_rec": "14-7", 
            "book_spread": 5, "spread_odds": +160, # Denver Favored?
            "book_total": 238.0, "total_odds": -110,
            "h_ml": +115, "a_ml": -135
        },
        {
            "home": "NYK", "away": "UTA", "time": "7:30 PM", "h_rec": "12-7", "a_rec": "7-13", 
            "book_spread": -15.5, "spread_odds": -1200, 
            "book_total": 225.0, "total_odds": -110,
            "h_ml": -320, "a_ml": +260
        },

        # 8:00 PM GAMES
        {
            "home": "DET", "away": "POR", "time": "8:00 PM", "h_rec": "2-19", "a_rec": "6-13", 
            "book_spread": -7, "spread_odds": -325, 
            "book_total": 227.5, "total_odds": -110,
            "h_ml": +135, "a_ml": -160
        },
        {
            "home": "MEM", "away": "LAC", "time": "8:00 PM", "h_rec": "5-14", "a_rec": "10-10", 
            "book_spread": 1.5, "spread_odds": 105, 
            "book_total": 221.0, "total_odds": -110,
            "h_ml": +180, "a_ml": -220
        },
        {
            "home": "HOU", "away": "PHX", "time": "8:00 PM", "h_rec": "9-9", "a_rec": "12-8", 
            "book_spread": -10, "spread_odds": -475, 
            "book_total": 223.0, "total_odds": -110,
            "h_ml": +105, "a_ml": -125
        },
        {
            "home": "MIL", "away": "PHI", "time": "8:00 PM", "h_rec": "15-6", "a_rec": "13-7", 
            "book_spread": 1.5, "spread_odds": 100, 
            "book_total": 242.5, "total_odds": -110,
            "h_ml": -220, "a_ml": +180
        },
        {
            "home": "CHI", "away": "IND", "time": "8:00 PM", "h_rec": "7-14", "a_rec": "11-8", 
            "book_spread": -4.5, "spread_odds": -185, 
            "book_total": 239.0, "total_odds": -110,
            "h_ml": +125, "a_ml": -145
        },

        # 9:30 PM GAME
        {
            "home": "OKC", "away": "DAL", "time": "9:30 PM", "h_rec": "13-6", "a_rec": "11-8", 
            "book_spread": -15, "spread_odds": -1100, 
            "book_total": 234.5, "total_odds": -110,
            "h_ml": -170, "a_ml": +145
        },
    ]

# --- 4. PREDICTION LOGIC ---
def get_matchup_projection(home, away):
    h_rat = 5
    a_rat = 5
    
    tier_1 = ["BOS", "MIN", "OKC", "DEN", "MIL", "ORL"] 
    tier_2 = ["LAL", "NYK", "MIA", "SAC", "IND", "NOP", "CLE", "PHI"] 
    tier_3 = ["GSW", "HOU", "BKN", "UTA", "TOR", "DAL", "PHX", "LAC"] 
    tier_4 = ["ATL", "CHI", "CHA", "POR", "MEM", "WAS", "DET", "SAS"]
    
    def get_rating(team):
        if team in tier_1: return 10
        if team in tier_2: return 5
        if team in tier_3: return 0
        return -6 

    h_rat = get_rating(home) + 3 
    a_rat = get_rating(away)
    
    raw_spread = a_rat - h_rat 
    win_prob = 1 / (1 + np.exp(0.15 * raw_spread)) * 100
    
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