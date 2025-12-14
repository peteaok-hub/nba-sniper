# NBA SNIPER INTELLIGENCE ENGINE V11.3 (SUNDAY SLATE UPDATE)
# STATUS: MANUAL ENTRY + ADAPTIVE CSV
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
TEAM_STATS_FILE = "nba_team_stats.csv" 

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
        
        # Mock training data to initialize
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

# --- 3. AUTOMATED STATS LOOKUP ---
def get_team_pace(team_name):
    """
    Reads Pace from the scraped nba_team_stats.csv.
    """
    if not os.path.exists(TEAM_STATS_FILE): return 99.0 
    
    try:
        df = pd.read_csv(TEAM_STATS_FILE)
        # Map Abbr to Hollinger Name (e.g. MIA -> Miami)
        abbr_map = {
            "MIA": "Miami", "ORL": "Orlando", "NYK": "New York", "TOR": "Toronto",
            "OKC": "Oklahoma City", "PHX": "Phoenix", "LAL": "LA Lakers", "SAS": "San Antonio",
            "IND": "Indiana", "SAC": "Sacramento", "MIN": "Minnesota", "NOP": "New Orleans",
            "BOS": "Boston", "DEN": "Denver", "GSW": "Golden State", "DAL": "Dallas",
            "LAC": "LA Clippers", "HOU": "Houston", "MEM": "Memphis", "CLE": "Cleveland",
            "MIL": "Milwaukee", "ATL": "Atlanta", "CHI": "Chicago", "PHI": "Philadelphia",
            "BKN": "Brooklyn", "DET": "Detroit", "WAS": "Washington", "CHA": "Charlotte",
            "POR": "Portland", "UTA": "Utah"
        }
        
        full_name = abbr_map.get(team_name, team_name)
        # Search for team string in the 'TEAM' column (case insensitive)
        team_row = df[df['TEAM'].str.contains(full_name, case=False, na=False)]
        
        if not team_row.empty:
            return float(team_row.iloc[0]['PACE'])
            
    except: pass
    return 99.0 

# --- 4. FATIGUE ANALYSIS ---
def get_team_fatigue(team_abbr):
    penalty = 0
    tired_players = []
    
    if not os.path.exists(MINUTES_FILE): return 0, []

    try:
        # Standard Read
        df = pd.read_csv(MINUTES_FILE, header=0)
        # Fallback for double header
        if 'L3' not in df.columns: df = pd.read_csv(MINUTES_FILE, header=1)
        
        if 'Team' in df.columns and 'L3' in df.columns:
            team_df = df[df['Team'] == team_abbr]
            for index, row in team_df.iterrows():
                try:
                    l3_val = str(row['L3']).replace(',', '').strip()
                    if not l3_val or l3_val == '-': continue
                    l3_mins = float(l3_val)
                    if l3_mins >= 38.0:
                        penalty += 1.5 
                        tired_players.append(f"{row['Player']} ({l3_mins}m \u26A0)") # Unicode Warning
                    elif l3_mins >= 35.0:
                        penalty += 0.5 
                        tired_players.append(f"{row['Player']} ({l3_mins}m)")
                except: pass
    except: pass
    return penalty, tired_players

# --- 5. TARGETING FEED (SUNDAY SLATE) ---
def get_todays_games():
    """
    MANUAL MATCHUPS (UPDATED SUNDAY).
    PACE IS AUTOMATED via get_team_pace().
    """
    games = [
        # WIZARDS vs PACERS (3:00 PM)
        {"home": "IND", "away": "WAS", "time": "3:00 PM", "h_rest": 1, "a_rest": 1, "spread": -9.5, "total": 234.5, "h_ml": -450}, # Pacers -9.5
        
        # HORNETS vs CAVALIERS (3:30 PM)
        {"home": "CLE", "away": "CHA", "time": "3:30 PM", "h_rest": 1, "a_rest": 1, "spread": -11.5, "total": 231.5, "h_ml": -600}, # Cavs -11.5
        
        # BUCKS vs NETS (6:00 PM)
        {"home": "BKN", "away": "MIL", "time": "6:00 PM", "h_rest": 1, "a_rest": 1, "spread": 1.5, "total": 217.5, "h_ml": 100}, # Nets +1.5 (Bucks -1.5)
        
        # 76ERS vs HAWKS (6:00 PM)
        {"home": "ATL", "away": "PHI", "time": "6:00 PM", "h_rest": 1, "a_rest": 1, "spread": -5.0, "total": 224.5, "h_ml": -200}, # Hawks -5
        
        # KINGS vs TIMBERWOLVES (7:00 PM)
        {"home": "MIN", "away": "SAC", "time": "7:00 PM", "h_rest": 1, "a_rest": 1, "spread": -10.0, "total": 234.0, "h_ml": -500}, # Wolves -10
        
        # PELICANS vs BULLS (7:00 PM)
        {"home": "CHI", "away": "NOP", "time": "7:00 PM", "h_rest": 1, "a_rest": 1, "spread": -4.5, "total": 248.0, "h_ml": -180}, # Bulls -4.5
        
        # LAKERS vs SUNS (8:00 PM)
        {"home": "PHX", "away": "LAL", "time": "8:00 PM", "h_rest": 1, "a_rest": 1, "spread": 1.0, "total": 231.0, "h_ml": -110}, # Suns +1 (Lakers -1)
        
        # WARRIORS vs BLAZERS (9:00 PM)
        {"home": "POR", "away": "GSW", "time": "9:00 PM", "h_rest": 1, "a_rest": 1, "spread": 4.5, "total": 236.0, "h_ml": 160}, # Blazers +4.5 (GSW -4.5)
        
        # SPURS vs KNICKS (TUESDAY)
        {"home": "NYK", "away": "SAS", "time": "TUES 8:30 PM", "h_rest": 2, "a_rest": 2, "spread": -2.5, "total": 228.5, "h_ml": -135}, # Knicks -2.5
    ]
    
    # Inject Automated Pace and Format for Dashboard
    for g in games:
        g['h_pace'] = get_team_pace(g['home'])
        g['a_pace'] = get_team_pace(g['away'])
        g['book_spread'] = g['spread']
        g['book_total'] = g['total']
        
    return games

# --- 6. PREDICTION LOGIC ---
def get_matchup_projection(game_data, away_team_unused=None):
    if isinstance(game_data, dict):
        home = game_data['home']; away = game_data['away']
    else:
        home = game_data; away = away_team_unused
        game_data = {'home': home, 'away': away}

    h_rat = 5; a_rat = 5
    
    # Tier List (Power Rankings)
    tier_1 = ["OKC", "BOS", "DEN", "LAL", "CLE", "HOU"] 
    tier_2 = ["NYK", "ORL", "MEM", "DAL", "GSW", "TOR", "PHI", "MIN", "SAS"] 
    tier_3 = ["LAC", "PHX", "MIL", "ATL", "CHI", "MIA", "SAC", "IND"] 
    tier_4 = ["DET", "POR", "CHA", "UTA", "WAS", "NOP", "BKN"]
    
    def get_rating(team):
        if team in tier_1: return 10
        if team in tier_2: return 6
        if team in tier_3: return 2
        return -5 

    h_rat = get_rating(home) + 3 # Home Court Advantage
    a_rat = get_rating(away)
    
    # Rest Factor
    h_rest = game_data.get('h_rest', 1); a_rest = game_data.get('a_rest', 1)
    if h_rest == 0: h_rat -= 4.0 
    if a_rest == 0: a_rat -= 5.0 
    
    # Fatigue Factor
    h_fatigue, h_tired = get_team_fatigue(home)
    a_fatigue, a_tired = get_team_fatigue(away)
    
    if h_rest <= 1: h_rat -= h_fatigue
    if a_rest <= 1: a_rat -= a_fatigue
    
    raw_spread = a_rat - h_rat 
    win_prob = 1 / (1 + np.exp(0.15 * raw_spread)) * 100
    
    # Pace Calculation
    h_pace = game_data.get('h_pace', 99.0); a_pace = game_data.get('a_pace', 99.0)
    avg_pace = (h_pace + a_pace) / 2
    
    base_total = 230
    pace_diff = avg_pace - 99.0
    base_total += (pace_diff * 1.5)
    
    if h_rest == 0 or a_rest == 0: base_total -= 5 
    
    proj_h_score = (base_total / 2) - (raw_spread / 2)
    proj_a_score = (base_total / 2) + (raw_spread / 2)
    
    # Safe Emoji Unicode
    pace_emoji = "\U0001F680" if avg_pace > 102 else "\U0001F422" if avg_pace < 98 else "\u2696"
    
    h_emoji = "\U0001F525" if get_rating(home) >= 6 else "\u26A0" if h_rest == 0 else ""
    a_emoji = "\U0001F525" if get_rating(away) >= 6 else "\u26A0" if a_rest == 0 else ""
    
    if len(h_tired) > 0 and h_rest <= 1: h_emoji += "\U0001F691"
    if len(a_tired) > 0 and a_rest <= 1: a_emoji += "\U0001F691"

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