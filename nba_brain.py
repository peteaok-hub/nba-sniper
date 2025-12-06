# NBA SNIPER INTELLIGENCE ENGINE V9.0 (FATIGUE & REST PROTOCOL)
# STATUS: MANUAL ENTRY + ADVANCED REST LOGIC
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

# --- 3. TARGETING FEED (REST & STREAK) ---
def get_todays_games():
    """
    MANUAL ENTRY ZONE.
    Update daily with lines AND Rest Situations.
    'rest': 0 (B2B), 1 (1 day off), 2 (2 days off), 3+ (Rested)
    """
    return [
        # GAME 1: PELICANS @ NETS
        {
            "home": "BKN", "away": "NOP", "time": "5:00 PM", 
            "h_rec": "9-13", "h_strk": "W1", "h_rest": 1, 
            "a_rec": "4-18", "a_strk": "L8", "a_rest": 0, # Pelicans on B2B
            "book_spread": -3.5, "spread_odds": -110, 
            "book_total": 227.0, "total_odds": -110,
            "h_ml": -160, "a_ml": +135
        },

        # GAME 2: HAWKS @ WIZARDS
        {
            "home": "WAS", "away": "ATL", "time": "7:00 PM", 
            "h_rec": "3-17", "h_strk": "L14", "h_rest": 0, # Wizards on B2B
            "a_rec": "11-11", "a_strk": "W2", "a_rest": 1,
            "book_spread": 9.0, "spread_odds": -105, # Wizards +9
            "book_total": 235.0, "total_odds": -110,
            "h_ml": +325, "a_ml": -450
        },

        # GAME 3: BUCKS @ PISTONS
        {
            "home": "DET", "away": "MIL", "time": "7:30 PM", 
            "h_rec": "9-14", "h_strk": "L2", "h_rest": 1,
            "a_rec": "10-11", "a_strk": "W1", "a_rest": 1,
            "book_spread": -12.5, "spread_odds": -115, # Bucks -12.5
            "book_total": 223.0, "total_odds": -110,
            "h_ml": +475, "a_ml": -700
        },

        # GAME 4: WARRIORS @ CAVALIERS
        {
            "home": "CLE", "away": "GSW", "time": "7:30 PM", 
            "h_rec": "19-3", "h_strk": "W2", "h_rest": 0, # Cavs B2B
            "a_rec": "12-9", "a_strk": "L4", "a_rest": 0, # Warriors B2B
            "book_spread": -8.0, "spread_odds": -110, 
            "book_total": 227.5, "total_odds": -110,
            "h_ml": -325, "a_ml": +250
        },

        # GAME 5: CLIPPERS @ TIMBERWOLVES
        {
            "home": "MIN", "away": "LAC", "time": "8:00 PM", 
            "h_rec": "16-6", "h_strk": "W2", "h_rest": 1,
            "a_rec": "13-9", "a_strk": "L1", "a_rest": 2,
            "book_spread": -10.5, "spread_odds": -110, 
            "book_total": 225.5, "total_odds": -110,
            "h_ml": -475, "a_ml": +350
        },

        # GAME 6: KINGS @ HEAT
        {
            "home": "MIA", "away": "SAC", "time": "8:00 PM", 
            "h_rec": "11-9", "h_strk": "W1", "h_rest": 1,
            "a_rec": "10-12", "a_strk": "L1", "a_rest": 0, # Kings B2B
            "book_spread": -8.0, "spread_odds": -110, 
            "book_total": 239.5, "total_odds": -110,
            "h_ml": -325, "a_ml": +250
        },

        # GAME 7: ROCKETS @ MAVERICKS
        {
            "home": "DAL", "away": "HOU", "time": "8:30 PM", 
            "h_rec": "14-8", "h_strk": "W4", "h_rest": 0, # Mavs B2B
            "a_rec": "15-6", "a_strk": "W3", "a_rest": 0, # Rockets B2B
            "book_spread": 8.5, "spread_odds": -105, # Mavs +8.5
            "book_total": 224.5, "total_odds": -110,
            "h_ml": +300, "a_ml": -400
        },
    ]

# --- 4. PREDICTION LOGIC (FATIGUE ADJUSTED) ---
def get_matchup_projection(game_data):
    home = game_data['home']
    away = game_data['away']
    
    # Base Ratings
    tier_1 = ["BOS", "OKC", "CLE", "HOU", "ORL", "DET"] 
    tier_2 = ["MEM", "NYK", "DAL", "DEN", "LAL", "MIN", "MIA"] 
    tier_3 = ["LAC", "GSW", "PHX", "MIL", "ATL", "PHI", "BKN"] 
    tier_4 = ["CHI", "IND", "POR", "SAS", "TOR", "CHA", "UTA", "WAS", "NOP", "SAC"]
    
    def get_base_rating(team):
        if team in tier_1: return 10
        if team in tier_2: return 6
        if team in tier_3: return 2
        return -5 

    h_rat = get_base_rating(home) + 3 # Home Court
    a_rat = get_base_rating(away)
    
    # --- FATIGUE ENGINE ---
    # Apply penalties for Back-to-Backs (0 days rest)
    h_rest = game_data.get('h_rest', 1)
    a_rest = game_data.get('a_rest', 1)
    
    if h_rest == 0: h_rat -= 3.5 # Tired legs hurt home shooting
    if a_rest == 0: a_rat -= 4.5 # Road B2B is the hardest schedule spot
    
    # --- STREAK ENGINE ---
    def parse_streak(s):
        if "W" in s: return 1.5 
        if "L" in s: return -1.5 
        return 0
    
    h_rat += parse_streak(game_data.get('h_strk', ''))
    a_rat += parse_streak(game_data.get('a_strk', ''))

    # Final Calc
    raw_spread = a_rat - h_rat 
    win_prob = 1 / (1 + np.exp(0.15 * raw_spread)) * 100
    
    # Visuals
    h_emoji = "🔥" if "W" in game_data.get('h_strk', '') else "⚠️" if h_rest == 0 else ""
    a_emoji = "🔥" if "W" in game_data.get('a_strk', '') else "⚠️" if a_rest == 0 else ""
    
    # Scoring Adjustment (Tired teams score less)
    base_total = 230
    if h_rest == 0 or a_rest == 0: base_total -= 5
    
    proj_h_score = (base_total / 2) - (raw_spread / 2)
    proj_a_score = (base_total / 2) + (raw_spread / 2)
    
    return {
        "projected_spread": raw_spread,
        "projected_total": base_total,
        "win_prob": win_prob,
        "score_str": f"{int(proj_a_score)} - {int(proj_h_score)}",
        "h_emoji": h_emoji,
        "a_emoji": a_emoji
    }

def log_transaction(matchup, pick, wager, result="Pending"):
    try:
        new_rec = {"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Matchup": matchup, "Pick": pick, "Wager": wager, "Result": result}
        if os.path.exists(HISTORY_FILE): df = pd.read_csv(HISTORY_FILE)
        else: df = pd.DataFrame(columns=new_rec.keys())
        df = pd.concat([df, pd.DataFrame([new_rec])], ignore_index=True)
        df.to_csv(HISTORY_FILE, index=False)
    except: pass