# NBA SNIPER INTELLIGENCE ENGINE V11.2 (DEC 9/10 TARGETS)
# STATUS: MANUAL ENTRY + ADAPTIVE CSV + DEC 9/10 ODDS
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
MINUTES_FILE = "NBA-minutes.csv" 

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

# --- 3. FATIGUE ANALYSIS (ADAPTIVE PARSER) ---
def get_team_fatigue(team_abbr):
    """
    Robustly reads NBA-minutes.csv.
    """
    penalty = 0
    tired_players = []
    
    if not os.path.exists(MINUTES_FILE): return 0, []

    try:
        # Attempt 1: Standard Read (Header is Row 0)
        df = pd.read_csv(MINUTES_FILE, header=0)
        
        # Check if 'L3' is missing
        if 'L3' not in df.columns:
             df = pd.read_csv(MINUTES_FILE, header=1)
        
        if 'Team' in df.columns and 'L3' in df.columns:
            team_df = df[df['Team'] == team_abbr]
            
            for index, row in team_df.iterrows():
                try:
                    l3_val = str(row['L3']).replace(',', '').strip()
                    if l3_val == '' or l3_val == '-': continue
                    
                    l3_mins = float(l3_val)
                    player = row['Player']
                    
                    if l3_mins >= 38.0:
                        penalty += 1.5 
                        tired_players.append(f"{player} ({l3_mins}m 🚨)")
                    elif l3_mins >= 35.0:
                        penalty += 0.5 
                        tired_players.append(f"{player} ({l3_mins}m)")
                except: pass
    except Exception as e:
        print(f"Fatigue Parse Error: {e}")
        pass 
        
    return penalty, tired_players

# --- 4. TARGETING FEED (DEC 9/10 SLATE) ---
def get_todays_games():
    """
    MANUAL ENTRY (DEC 9/10).
    'rest': 0 = B2B. 
    'pace': Avg ~99.
    """
    return [
        # TODAY: DEC 9 (6:00 PM) - HEAT vs MAGIC
        {
            "home": "ORL", "away": "MIA", "time": "Tue 6:00 PM", 
            "h_rec": "14-10", "h_rest": 1, "h_pace": 104.8, 
            "a_rec": "14-10", "a_rest": 1, "a_pace": 109.1, # Heat playing surprisingly fast
            "book_spread": -2.5, "spread_odds": -105, # Magic -2.5
            "book_total": 232.5, "total_odds": -110,
            "h_ml": -140, "a_ml": +120
        },
        # TODAY: DEC 9 (8:30 PM) - KNICKS vs RAPTORS
        {
            "home": "TOR", "away": "NYK", "time": "Tue 8:30 PM", 
            "h_rec": "15-10", "h_rest": 1, "h_pace": 103.7, 
            "a_rec": "16-7", "a_rest": 1, "a_pace": 102.0, 
            "book_spread": 4.5, "spread_odds": -105, # Knicks -4.5 (Raptors +4.5)
            "book_total": 228.5, "total_odds": -110,
            "h_ml": +160, "a_ml": -190
        },

        # WEDNESDAY: DEC 10 (7:30 PM) - THUNDER vs SUNS
        {
            "home": "OKC", "away": "PHX", "time": "Wed 7:30 PM", 
            "h_rec": "23-1", "h_rest": 2, "h_pace": 104.6, 
            "a_rec": "14-10", "a_rest": 1, "a_pace": 103.2, 
            "book_spread": -16.5, "spread_odds": -115, # Thunder -16.5
            "book_total": 224.5, "total_odds": -110,
            "h_ml": -1600, "a_ml": +850
        },
        # WEDNESDAY: DEC 10 (7:30 PM) - LAKERS vs SPURS
        {
            "home": "LAL", "away": "SAS", "time": "Wed 7:30 PM", 
            "h_rec": "17-6", "h_rest": 2, "h_pace": 102.2, 
            "a_rec": "15-7", "a_rest": 1, "a_pace": 103.5, 
            "book_spread": -4.0, "spread_odds": -115, # Lakers -4
            "book_total": 235.5, "total_odds": -110,
            "h_ml": -180, "a_ml": +150
        },
    ]

# --- 5. PREDICTION LOGIC ---
def get_matchup_projection(game_data, away_team_unused=None):
    if isinstance(game_data, dict):
        home = game_data['home']; away = game_data['away']
    else:
        home = game_data; away = away_team_unused
        game_data = {'home': home, 'away': away}

    h_rat = 5; a_rat = 5
    
    tier_1 = ["OKC", "BOS", "DEN", "LAL", "CLE", "HOU"] 
    tier_2 = ["NYK", "ORL", "MEM", "DAL", "GSW", "TOR", "PHI", "MIN", "SAS"] 
    tier_3 = ["LAC", "PHX", "MIL", "ATL", "CHI", "MIA", "SAC", "IND"] 
    tier_4 = ["DET", "POR", "CHA", "UTA", "WAS", "NOP", "BKN"]
    
    def get_rating(team):
        if team in tier_1: return 10
        if team in tier_2: return 6
        if team in tier_3: return 2
        return -5 

    h_rat = get_rating(home) + 3 
    a_rat = get_rating(away)
    
    # Fatigue
    h_rest = game_data.get('h_rest', 1); a_rest = game_data.get('a_rest', 1)
    if h_rest == 0: h_rat -= 4.0 
    if a_rest == 0: a_rat -= 5.0 
    
    h_fatigue, h_tired = get_team_fatigue(home)
    a_fatigue, a_tired = get_team_fatigue(away)
    
    if h_rest <= 1: h_rat -= h_fatigue
    if a_rest <= 1: a_rat -= a_fatigue
    
    raw_spread = a_rat - h_rat 
    win_prob = 1 / (1 + np.exp(0.15 * raw_spread)) * 100
    
    # Pace
    h_pace = game_data.get('h_pace', 99.0); a_pace = game_data.get('a_pace', 99.0)
    avg_pace = (h_pace + a_pace) / 2
    
    base_total = 230
    pace_diff = avg_pace - 99.0
    base_total += (pace_diff * 1.5)
    
    if h_rest == 0 or a_rest == 0: base_total -= 5 
    
    proj_h_score = (base_total / 2) - (raw_spread / 2)
    proj_a_score = (base_total / 2) + (raw_spread / 2)
    
    pace_emoji = "🚀" if avg_pace > 102 else "🐢" if avg_pace < 98 else "⚖️"
    
    h_emoji = "🔥" if get_rating(home) >= 6 else "⚠️" if h_rest == 0 else ""
    a_emoji = "🔥" if get_rating(away) >= 6 else "⚠️" if a_rest == 0 else ""
    
    if len(h_tired) > 0 and h_rest <= 1: h_emoji += "🚑"
    if len(a_tired) > 0 and a_rest <= 1: a_emoji += "🚑"

    return {
        "projected_spread": raw_spread,
        "projected_total": base_total,
        "win_prob": win_prob,
        "score_str": f"{int(proj_a_score)}-{int(proj_h_score)}",
        "h_tired": h_tired, "a_tired": a_tired,
        "pace_emoji": pace_emoji, "avg_pace": avg_pace,
        "h_emoji": h_emoji, "a_emoji": a_emoji
    }

def log_transaction(matchup, pick, wager, result="Pending"):
    try:
        new_rec = {"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Matchup": matchup, "Pick": pick, "Wager": wager, "Result": result}
        if os.path.exists(HISTORY_FILE): df = pd.read_csv(HISTORY_FILE)
        else: df = pd.DataFrame(columns=new_rec.keys())
        df = pd.concat([df, pd.DataFrame([new_rec])], ignore_index=True)
        df.to_csv(HISTORY_FILE, index=False)
    except: pass