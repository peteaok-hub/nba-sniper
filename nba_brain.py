import pandas as pd
import numpy as np
import requests
import unicodedata
import os
import pickle
from datetime import datetime
import pytz
from bs4 import BeautifulSoup
from sklearn.linear_model import RidgeClassifier
from sklearn.preprocessing import StandardScaler
from nba_api.stats.static import teams as nba_teams_static
from nba_api.stats.endpoints import commonteamroster, playergamelog, leaguedashteamstats, scoreboardv2, leaguedashplayerstats, commonallplayers

# --- 1. CONFIGURATION & CONSTANTS ---
HISTORY_FILE = "nba_betting_history.csv"
BRAIN_FILE = "nba_brain.pkl"
DATA_FILE = "nba_games_rolled.csv"

# ODDS API
ODDS_API_KEY = "3e039d8cfd426d394b020b55bd303a07"
ODDS_BASE_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba"

# STEALTH HEADERS
CUSTOM_HEADERS = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Origin': 'https://www.nba.com',
    'Referer': 'https://www.nba.com/',
    'Connection': 'keep-alive',
}

# --- 2. SELF-HEALING & DATA ENGINE ---

def rebuild_brain_engine():
    print("🧠 INITIALIZING BRAIN REBUILD...")
    try:
        url = "https://drive.google.com/uc?export=download&id=1YyNpERG0jqPlpxZvvELaNcMHTiKVpfWe"
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        with open(DATA_FILE, "wb") as f: f.write(r.content)
        
        df = pd.read_csv(DATA_FILE, parse_dates=["date"]).sort_values("date")
        code_map = {"NOH":"NOP", "CHO":"CHA", "BRK":"BKN", "PHO":"PHX"}
        df.replace(code_map, inplace=True)
        cols_drop = ["mp.1", "mp_opp.1", "index_opp"]
        df = df.drop(columns=[c for c in cols_drop if c in df.columns])
        
        df["target"] = df.groupby("team")["won"].shift(-1).fillna(0).astype(int)
        
        numeric = df.select_dtypes(include=[np.number])
        cols = [c for c in numeric.columns if c not in ["season", "target", "won"]]
        r10 = df.groupby("team")[cols].rolling(10, min_periods=1).mean().reset_index(0, drop=True)
        r10.columns = [f"{c}_R10" for c in r10.columns]
        
        df = pd.concat([df, r10], axis=1).fillna(0)
        df.to_csv(DATA_FILE, index=False)
        
        features = [c for c in df.columns if "_R10" in c]
        X, y = df[features], df["target"]
        scaler = StandardScaler()
        X_sc = scaler.fit_transform(X)
        model = RidgeClassifier()
        model.fit(X_sc, y)
        
        pkg = {"model": model, "scaler": scaler, "features": features}
        with open(BRAIN_FILE, "wb") as f: pickle.dump(pkg, f)
        
        return df, pkg
    except Exception as e:
        print(f"❌ CRITICAL FAILURE: {e}")
        return None, None

def load_brain_engine():
    if not os.path.exists(DATA_FILE) or not os.path.exists(BRAIN_FILE):
        return rebuild_brain_engine()
    try:
        df = pd.read_csv(DATA_FILE, parse_dates=["date"])
        with open(BRAIN_FILE, "rb") as f: pkg = pickle.load(f)
        return df, pkg
    except:
        return rebuild_brain_engine()

# --- 3. INTELLIGENCE MODULES ---

def get_odds_team_map():
    return {
        "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN", "Charlotte Hornets": "CHA",
        "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE", "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN",
        "Detroit Pistons": "DET", "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
        "Los Angeles Clippers": "LAC", "LA Clippers": "LAC", "Los Angeles Lakers": "LAL", "LA Lakers": "LAL",
        "Memphis Grizzlies": "MEM", "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
        "New Orleans Pelicans": "NOP", "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC", "Orlando Magic": "ORL",
        "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX", "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC",
        "San Antonio Spurs": "SAS", "Toronto Raptors": "TOR", "Utah Jazz": "UTA", "Washington Wizards": "WAS"
    }

def get_todays_slate():
    slate = []
    # 1. Odds API
    try:
        url = f"{ODDS_BASE_URL}/odds"
        params = {'apiKey': ODDS_API_KEY, 'regions': 'us', 'markets': 'h2h', 'oddsFormat': 'american'}
        r = requests.get(url, params=params)
        if r.status_code == 200:
            data = r.json()
            mapper = get_odds_team_map()
            for game in data:
                h_abbr = mapper.get(game.get('home_team'))
                a_abbr = mapper.get(game.get('away_team'))
                if h_abbr and a_abbr: slate.append(f"{a_abbr} @ {h_abbr}")
            if slate: return list(set(slate))
    except: pass
    
    # 2. NBA API Fallback
    try:
        est = pytz.timezone('US/Eastern')
        today = datetime.now(est).strftime('%Y-%m-%d')
        board = scoreboardv2.ScoreboardV2(game_date=today, headers=CUSTOM_HEADERS)
        games = board.get_data_frames()[0]
        if not games.empty:
            teams = nba_teams_static.get_teams()
            id_to_abbr = {t['id']: t['abbreviation'] for t in teams}
            for _, row in games.iterrows():
                h_abbr = id_to_abbr.get(row['HOME_TEAM_ID'])
                a_abbr = id_to_abbr.get(row['VISITOR_TEAM_ID'])
                if h_abbr and a_abbr: slate.append(f"{a_abbr} @ {h_abbr}")
    except: pass
    return list(set(slate))

def get_live_odds():
    try:
        url = f"{ODDS_BASE_URL}/odds"
        params = {'apiKey': ODDS_API_KEY, 'regions': 'us', 'markets': 'h2h', 'oddsFormat': 'american'}
        response = requests.get(url, params=params)
        if response.status_code == 200: return response.json()
        return []
    except: return []

# --- 4. PROP SNIPER MODULE ---

def get_game_id_for_team(team_name):
    try:
        url = f"{ODDS_BASE_URL}/events"
        params = {'apiKey': ODDS_API_KEY}
        r = requests.get(url, params=params)
        if r.status_code == 200:
            for game in r.json():
                if team_name in game['home_team'] or team_name in game['away_team']:
                    return game['id']
    except: pass
    return None

def get_player_props(game_id, player_name):
    props = {'PTS': None, 'REB': None, 'AST': None}
    if not game_id: return props
    try:
        url = f"{ODDS_BASE_URL}/events/{game_id}/odds"
        params = {'apiKey': ODDS_API_KEY, 'regions': 'us', 'markets': 'player_points,player_rebounds,player_assists', 'oddsFormat': 'american'}
        r = requests.get(url, params=params)
        if r.status_code == 200:
            data = r.json()
            for book in data.get('bookmakers', []):
                for market in book.get('markets', []):
                    key = market['key']
                    p_type = None
                    if key == 'player_points': p_type = 'PTS'
                    elif key == 'player_rebounds': p_type = 'REB'
                    elif key == 'player_assists': p_type = 'AST'
                    
                    if p_type and not props[p_type]:
                        for outcome in market['outcomes']:
                            # Fuzzy match
                            if outcome['description'].split()[-1] in player_name:
                                props[p_type] = outcome['point']
                                break
    except: pass
    return props

# --- 5. ROSTER & INJURY MODULES ---

def normalize_cbs_name(cbs_name):
    mapping = {
        "Golden St.": "Golden State Warriors", "L.A. Lakers": "Los Angeles Lakers", "L.A. Clippers": "Los Angeles Clippers",
        "San Antonio": "San Antonio Spurs", "New York": "New York Knicks", "New Orleans": "New Orleans Pelicans",
        "Okla. City": "Oklahoma City Thunder", "Utah": "Utah Jazz", "Phoenix": "Phoenix Suns", "Philadelphia": "Philadelphia 76ers",
        "Miami": "Miami Heat", "Boston": "Boston Celtics", "Atlanta": "Atlanta Hawks", "Brooklyn": "Brooklyn Nets",
        "Charlotte": "Charlotte Hornets", "Chicago": "Chicago Bulls", "Cleveland": "Cleveland Cavaliers", "Dallas": "Dallas Mavericks",
        "Denver": "Denver Nuggets", "Detroit": "Detroit Pistons", "Houston": "Houston Rockets", "Indiana": "Indiana Pacers",
        "Memphis": "Memphis Grizzlies", "Milwaukee": "Milwaukee Bucks", "Minnesota": "Minnesota Timberwolves", "Orlando": "Orlando Magic",
        "Portland": "Portland Trail Blazers", "Sacramento": "Sacramento Kings", "Toronto": "Toronto Raptors", "Washington": "Washington Wizards"
    }
    return mapping.get(cbs_name, cbs_name)

def get_injury_report():
    try:
        url = "https://www.cbssports.com/nba/injuries/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        injuries = {}
        for section in soup.find_all('div', class_='TeamLogoNameLockup'):
            name_tag = section.find('span', class_='TeamLogoNameLockup-name')
            if not name_tag: continue
            clean_name = normalize_cbs_name(section.find('a').text.strip())
            parent = section.find_parent('div', class_='TableBase')
            if not parent: continue
            rows = parent.find_all('tr', class_='TableBase-bodyTr')
            team_inj = []
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 5:
                    team_inj.append({
                        'player': cols[0].find('span', class_='CellPlayerName--long').text.strip(),
                        'status': cols[4].text.strip(),
                        'injury': cols[3].text.strip()
                    })
            injuries[clean_name] = team_inj
        return injuries
    except: return {}

def check_injuries(home_abbr, away_abbr, injury_data, team_map_full):
    alerts = []
    abbr_to_full = {v: k for k, v in team_map_full.items()}
    for abbr in [home_abbr, away_abbr]:
        full_name = abbr_to_full.get(abbr)
        if full_name and full_name in injury_data:
            for inj in injury_data[full_name]:
                icon = "🔴" if "Out" in inj['status'] else "🟡"
                alerts.append(f"{icon} **{abbr}** - {inj['player']}: {inj['injury']} ({inj['status']})")
    return alerts

def get_roster(team_id):
    """Atomic Roster Fetch: Multi-Layer Fallback."""
    # Layer 1: Official
    try:
        return commonteamroster.CommonTeamRoster(team_id=team_id, season='2024-25', headers=CUSTOM_HEADERS, timeout=3).get_data_frames()[0]
    except: pass
    # Layer 2: Backdoor Stats
    try:
        df = leaguedashplayerstats.LeagueDashPlayerStats(team_id_nullable=team_id, season='2024-25', headers=CUSTOM_HEADERS, timeout=5).get_data_frames()[0]
        return df.rename(columns={'PLAYER_NAME': 'PLAYER', 'PLAYER_ID': 'PLAYER_ID'})
    except: pass
    # Layer 3: Nuclear (All Players)
    try:
        df = commonallplayers.CommonAllPlayers(is_only_current_season=1, headers=CUSTOM_HEADERS, timeout=10).get_data_frames()[0]
        return df[df['TEAM_ID'] == team_id].rename(columns={'DISPLAY_FIRST_LAST': 'PLAYER', 'PERSON_ID': 'PLAYER_ID'})
    except: pass
    return pd.DataFrame()

def fetch_player_logs(player_id):
    try:
        log = playergamelog.PlayerGameLog(player_id=player_id, season='2024-25', headers=CUSTOM_HEADERS, timeout=10)
        df = log.get_data_frames()[0]
        df['PRA'] = df['PTS'] + df['REB'] + df['AST']
        df['LOCATION'] = np.where(df['MATCHUP'].str.contains('@'), 'AWAY', 'HOME')
        return df
    except: return pd.DataFrame()

def get_defense_rankings():
    try:
        dash = leaguedashteamstats.LeagueDashTeamStats(measure_type_detailed_defense='Opponent', per_mode_detailed='PerGame', headers=CUSTOM_HEADERS)
        df = dash.get_data_frames()[0]
        df['PTS_RANK'] = df['OPP_PTS'].rank(ascending=False)
        return df[['TEAM_NAME', 'TEAM_ID', 'PTS_RANK']]
    except: return pd.DataFrame()

def get_team_map():
    return {t['full_name']: t['abbreviation'] for t in nba_teams_static.get_teams()}

# --- TELEMETRY ---
def log_prediction(player, stat_type, line, projection, decision, edge, tags):
    try:
        new_rec = {
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Player": player,
            "Stat": stat_type,
            "Line": line,
            "Proj": projection,
            "Pick": decision,
            "Edge": f"{edge:+.1f}",
            "Tags": tags,
            "Result": "Pending"
        }
        if os.path.exists(HISTORY_FILE): df = pd.read_csv(HISTORY_FILE)
        else: df = pd.DataFrame(columns=new_rec.keys())
        df = pd.concat([df, pd.DataFrame([new_rec])], ignore_index=True)
        df.to_csv(HISTORY_FILE, index=False)
        return True
    except: return False
