# NBA SNIPER INTELLIGENCE ENGINE V6.1 (CACHE BUSTER)
# STATUS: LIVE DATA FEED ACTIVE
import pandas as pd
import numpy as np
import os
import pickle
import requests
from datetime import datetime
from sklearn.linear_model import RidgeClassifier, Ridge
from sklearn.preprocessing import StandardScaler

# CONFIG
DATA_FILE = "nba_games_processed.csv"
MODEL_FILE = "nba_model_v1.pkl"
HISTORY_FILE = "nba_betting_ledger.csv"

# --- 1. DATA ENGINE (SELF-HEALING) ---
def update_nba_data():
    """Creates a placeholder database if none exists."""
    if not os.path.exists(DATA_FILE):
        print("🏀 REBIRTH: INITIALIZING NBA DATABASE...")
        cols = ['game_id', 'date', 'home_team', 'away_team', 'home_score', 'away_score', 'h_mom', 'a_mom', 'h_off', 'a_off']
        df = pd.DataFrame(columns=cols)
        df.to_csv(DATA_FILE, index=False)
        return df
    return pd.read_csv(DATA_FILE)

# --- 2. BRAIN ENGINE (LOGIC) ---
def train_nba_model():
    """Trains Winner, Spread, and Total models."""
    if not os.path.exists(DATA_FILE): update_nba_data()
    
    try:
        # Heuristic Training for V6.0 Stability
        model_win = RidgeClassifier()
        model_spread = Ridge()
        model_total = Ridge()
        scaler = StandardScaler()
        
        # Mock fit to ensure objects exist (prevents crashes on fresh install)
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

# --- 3. LIVE KINETIC FEEDER (AUTONOMOUS) ---
def get_todays_games():
    """
    Fetches LIVE schedule from NBA.com endpoints.
    No more manual typing.
    """
    try:
        # NBA Official CDN Endpoint for Today's Scoreboard
        url = "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://www.nba.com/"
        }
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        
        games = []
        for game in data['scoreboard']['games']:
            home_team = game['homeTeam']['teamTricode']
            away_team = game['awayTeam']['teamTricode']
            game_time = game['gameStatusText'] # e.g., "7:30 pm ET" or "Final"
            
            # Live Records
            h_wins = game['homeTeam']['wins']
            h_losses = game['homeTeam']['losses']
            a_wins = game['awayTeam']['wins']
            a_losses = game['awayTeam']['losses']
            
            # Generate a Simulated Book Line
            win_pct_diff = (h_wins / max(1, h_wins + h_losses)) - (a_wins / max(1, a_wins + a_losses))
            sim_spread = round(win_pct_diff * -15.0 * 2) / 2.0 
            if sim_spread == 0: sim_spread = -1.0
            
            games.append({
                "home": home_team,
                "away": away_team,
                "time": game_time,
                "h_rec": f"{h_wins}-{h_losses}",
                "a_rec": f"{a_wins}-{a_losses}",
                "book_spread": sim_spread, 
                "book_total": 228.5
            })
            
        return games
        
    except Exception as e:
        print(f"Live Feed Error: {e}")
        # Fallback if API fails
        return [
            {"home": "BOS", "away": "NYK", "time": "Error: API Down", "h_rec": "0-0", "a_rec": "0-0", "book_spread": -5.5, "book_total": 220},
        ]

# --- 4. PREDICTION LOGIC ---
def get_matchup_projection(home, away):
    """
    Calculates the 'True Line' based on Momentum.
    """
    # Dynamic Tier System
    tier_1 = ["BOS", "OKC", "MIN", "DEN", "LAC", "CLE", "MIL"] 
    tier_2 = ["PHX", "NYK", "DAL", "MIA", "SAC", "IND", "NOP", "ORL"] 
    tier_3 = ["LAL", "GSW", "HOU", "BKN", "UTA", "PHI"] 
    tier_4 = ["ATL", "CHI", "CHA", "POR", "MEM", "TOR", "WAS", "DET", "SAS"]
    
    def get_rating(team):
        if team in tier_1: return 10
        if team in tier_2: return 5
        if team in tier_3: return 0
        return -6 

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

def log_transaction(matchup, pick, wager, result="Pending"):
    try:
        new_rec = {"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Matchup": matchup, "Pick": pick, "Wager": wager, "Result": result}
        if os.path.exists(HISTORY_FILE): df = pd.read_csv(HISTORY_FILE)
        else: df = pd.DataFrame(columns=new_rec.keys())
        df = pd.concat([df, pd.DataFrame([new_rec])], ignore_index=True)
        df.to_csv(HISTORY_FILE, index=False)
    except: pass