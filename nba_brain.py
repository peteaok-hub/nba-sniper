# NBA SNIPER INTELLIGENCE ENGINE V11.8 (MONDAY SLATE)
# STATUS: TRAP PROTOCOL + WIN PROB + NEW ODDS
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

# --- 1. ENGINE INITIALIZATION ---
def update_nba_data():
    if not os.path.exists(DATA_FILE):
        cols = ['game_id', 'date', 'home_team', 'away_team', 'home_score', 'away_score', 'h_mom', 'a_mom', 'h_off', 'a_off']
        df = pd.DataFrame(columns=cols)
        df.to_csv(DATA_FILE, index=False)
        return df
    return pd.read_csv(DATA_FILE)

def train_nba_model():
    if not os.path.exists(DATA_FILE): update_nba_data()
    try:
        model_win = RidgeClassifier()
        model_spread = Ridge()
        model_total = Ridge()
        scaler = StandardScaler()
        
        # Mock training data to initialize logic if file is missing
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

# --- 2. THE TRAP LIST (MANUAL OVERRIDES) ---
# "Punish" teams that are statistically fine but playing poorly.
# Value = Points to subtract from their Tier Rating.
BIAS_CORRECTION = {
    "MIL": -8.0,  # Bucks are broken. Downgrade heavily.
    "IND": -6.0,  # Pacers choke against bad teams.
    "CHI": -4.0,  # Bulls are inconsistent.
    "PHX": -2.0,  # Suns are sliding.
    "LAL": 1.0,   # Lakers are fighting (Bonus).
    "MIN": 1.0    # Wolves are solid (Bonus).
}

# --- 3. DYNAMIC STATS ENGINE ---
def get_team_metrics(team_name):
    """
    Retrieves Pace & Net Rating, then applies BIAS CORRECTION.
    """
    default_pace = 99.0
    default_tier = 2 
    
    if not os.path.exists(TEAM_STATS_FILE): 
        return default_pace, default_tier, 0.0
    
    try:
        df = pd.read_csv(TEAM_STATS_FILE)
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
        team_row = df[df['TEAM'].str.contains(full_name, case=False, na=False)]
        
        if not team_row.empty:
            pace = float(team_row.iloc[0]['PACE'])
            off_eff = float(team_row.iloc[0]['OFF EFF'])
            def_eff = float(team_row.iloc[0]['DEF EFF'])
            net_rating = off_eff - def_eff
            
            # 1. Base Tier from Stats
            if net_rating >= 7.0: tier = 10   
            elif net_rating >= 3.0: tier = 7  
            elif net_rating >= -2.0: tier = 4 
            else: tier = -2                   
            
            # 2. Apply "Trap Protocol" Bias
            if team_name in BIAS_CORRECTION:
                bias = BIAS_CORRECTION[team_name]
                tier += bias
                # Adjust Net Rating for display purposes
                net_rating += bias 

            return pace, tier, net_rating
            
    except: pass
    return default_pace, default_tier, 0.0

# --- 4. FATIGUE ANALYSIS ---
def get_team_fatigue(team_abbr):
    penalty = 0
    tired_players = []
    if not os.path.exists(MINUTES_FILE): return 0, []
    try:
        df = pd.read_csv(MINUTES_FILE, header=0)
        if 'L3' not in df.columns: df = pd.read_csv(MINUTES_FILE, header=1)
        if 'Team' in df.columns and 'L3' in df.columns:
            team_df = df[df['Team'] == team_abbr]
            for index, row in team_df.iterrows():
                try:
                    l3_val = str(row['L3']).replace(',', '').strip()
                    if not l3_val or l3_val == '-': continue
                    l3_mins = float(l3_val)
                    if l3_mins >= 38.0:
                        penalty += 1.5; tired_players.append(f"{row['Player']} ({l3_mins}m \u26A0)")
                    elif l3_mins >= 35.0:
                        penalty += 0.5; tired_players.append(f"{row['Player']} ({l3_mins}m)")
                except: pass
    except: pass
    return penalty, tired_players

# --- 5. TARGETING FEED (MONDAY SLATE) ---
def get_todays_games():
    """
    MONDAY SLATE - Manual Entry
    """
    games = [
        # PISTONS vs CELTICS (7:00 PM) - Celtics -1.5
        {"home": "BOS", "away": "DET", "time": "7:00 PM", "h_rest": 1, "a_rest": 1, "spread": -1.5, "total": 229.5},
        
        # RAPTORS vs HEAT (7:30 PM) - Heat -6
        {"home": "MIA", "away": "TOR", "time": "7:30 PM", "h_rest": 1, "a_rest": 1, "spread": -6.0, "total": 235.0},
        
        # MAVERICKS vs JAZZ (9:00 PM) - Mavs -2.5 (Jazz +2.5)
        {"home": "UTA", "away": "DAL", "time": "9:00 PM", "h_rest": 1, "a_rest": 1, "spread": 2.5, "total": 241.0},
        
        # ROCKETS vs NUGGETS (9:30 PM) - Nuggets -1
        {"home": "DEN", "away": "HOU", "time": "9:30 PM", "h_rest": 1, "a_rest": 1, "spread": -1.0, "total": 237.5},
        
        # GRIZZLIES vs CLIPPERS (10:30 PM) - Clippers -4.5
        {"home": "LAC", "away": "MEM", "time": "10:30 PM", "h_rest": 1, "a_rest": 1, "spread": -4.5, "total": 228.0},
        
        # SPURS vs KNICKS (TUESDAY/LATE) - Knicks -2.5
        {"home": "NYK", "away": "SAS", "time": "TUES 8:30 PM", "h_rest": 2, "a_rest": 2, "spread": -2.5, "total": 228.5},
    ]
    
    # Inject Stats
    for g in games:
        g['h_pace'], g['h_tier'], g['h_net'] = get_team_metrics(g['home'])
        g['a_pace'], g['a_tier'], g['a_net'] = get_team_metrics(g['away'])
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
        game_data['h_pace'], game_data['h_tier'], _ = get_team_metrics(home)
        game_data['a_pace'], game_data['a_tier'], _ = get_team_metrics(away)

    h_rat = game_data.get('h_tier', 2) + 2.5 
    a_rat = game_data.get('a_tier', 2)
    
    # Rest Factor
    h_rest = game_data.get('h_rest', 1); a_rest = game_data.get('a_rest', 1)
    if h_rest == 0: h_rat -= 4.0 
    if a_rest == 0: a_rat -= 5.0 
    
    # Fatigue
    h_fatigue, h_tired = get_team_fatigue(home)
    a_fatigue, a_tired = get_team_fatigue(away)
    if h_rest <= 1: h_rat -= h_fatigue
    if a_rest <= 1: a_rat -= a_fatigue
    
    raw_spread = a_rat - h_rat 
    
    # Win Probability
    win_prob = 1 / (1 + np.exp(0.15 * raw_spread)) * 100
    
    # Total Logic
    h_pace = game_data.get('h_pace', 99.0); a_pace = game_data.get('a_pace', 99.0)
    avg_pace = (h_pace + a_pace) / 2
    base_total = 228 + ((avg_pace - 99.0) * 1.8) 
    if h_rest == 0 or a_rest == 0: base_total -= 5 
    
    proj_h_score = (base_total / 2) - (raw_spread / 2)
    proj_a_score = (base_total / 2) + (raw_spread / 2)
    
    pace_emoji = "\U0001F680" if avg_pace > 104 else "\U0001F422" if avg_pace < 98 else "\u2696"
    h_emoji = "\U0001F4AA" if h_rat > 8 else "\u26A0" if h_rest == 0 else ""
    a_emoji = "\U0001F4AA" if a_rat > 8 else "\u26A0" if a_rest == 0 else ""

    return {
        "projected_spread": raw_spread,
        "projected_total": base_total,
        "win_prob": win_prob,
        "score_str": f"{int(proj_a_score)}-{int(proj_h_score)}",
        "h_tired": h_tired, "a_tired": a_tired,
        "pace_emoji": pace_emoji, "avg_pace": avg_pace,
        "h_emoji": h_emoji, "a_emoji": a_emoji,
        "h_net": game_data.get('h_net', 0), "a_net": game_data.get('a_net', 0) 
    }

def log_transaction(matchup, pick, wager, result="Pending"):
    try:
        new_rec = {"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Matchup": matchup, "Pick": pick, "Wager": wager, "Result": result}
        if os.path.exists(HISTORY_FILE): df = pd.read_csv(HISTORY_FILE)
        else: df = pd.DataFrame(columns=new_rec.keys())
        df = pd.concat([df, pd.DataFrame([new_rec])], ignore_index=True)
        df.to_csv(HISTORY_FILE, index=False)
    except: pass