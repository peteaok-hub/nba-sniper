import streamlit as st
import pandas as pd
import numpy as np
import pickle
import os
import requests
import unicodedata
from datetime import datetime
import pytz 
from nba_api.stats.static import teams as nba_teams_static
from nba_api.stats.endpoints import commonteamroster, playergamelog, leaguedashteamstats, scoreboardv2
from bs4 import BeautifulSoup
from sklearn.linear_model import RidgeClassifier
from sklearn.preprocessing import StandardScaler

# --- CONFIGURATION ---
st.set_page_config(page_title="NBA Sniper Juggernaut V2.8", layout="wide", page_icon="🏀")

# --- STEALTH HEADERS ---
custom_headers = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true',
    'Connection': 'keep-alive',
    'Referer': 'https://stats.nba.com/',
}

# ODDS API
ODDS_API_KEY = "3e039d8cfd426d394b020b55bd303a07"
ODDS_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("⚙️ Sniper Controls")
    if st.button("🔄 Force Refresh Data", type="primary"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Press this if rosters or odds look outdated.")

# --- INTERNAL BRAIN BUILDER (SELF-HEALING) ---
def rebuild_brain():
    status = st.empty()
    status.info("🧠 Brain not found. Initializing Self-Healing Protocol... (Downloading Data)")
    try:
        url = "https://drive.google.com/uc?export=download&id=1YyNpERG0jqPlpxZvvELaNcMHTiKVpfWe"
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        with open("nba_games.csv", "wb") as f: f.write(r.content)
        df = pd.read_csv("nba_games.csv", parse_dates=["date"]).sort_values("date")
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
        df.to_csv("nba_games_rolled.csv", index=False)
        features = [c for c in df.columns if "_R10" in c]
        X, y = df[features], df["target"]
        scaler = StandardScaler()
        X_sc = scaler.fit_transform(X)
        model = RidgeClassifier()
        model.fit(X_sc, y)
        pkg = {"model": model, "scaler": scaler, "features": features}
        with open("nba_brain.pkl", "wb") as f: pickle.dump(pkg, f)
        status.success("✅ System Online. Brain Built Successfully.")
        status.empty()
        return df, pkg
    except Exception as e:
        st.error(f"Critical System Failure: {e}")
        return None, None

@st.cache_resource
def load_brain():
    if not os.path.exists("nba_games_rolled.csv") or not os.path.exists("nba_brain.pkl"): return rebuild_brain()
    try:
        df = pd.read_csv("nba_games_rolled.csv", parse_dates=["date"])
        with open("nba_brain.pkl", "rb") as f: pkg = pickle.load(f)
        return df, pkg
    except: return rebuild_brain()

# --- INTELLIGENCE MODULES ---
def normalize_name(name):
    return ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')

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

@st.cache_data(ttl=3600)
def get_todays_slate():
    slate = []
    try:
        params = {'apiKey': ODDS_API_KEY, 'regions': 'us', 'markets': 'h2h', 'oddsFormat': 'american'}
        r = requests.get(ODDS_URL, params=params)
        if r.status_code == 200:
            data = r.json()
            mapper = get_odds_team_map()
            for game in data:
                h_abbr = mapper.get(game.get('home_team'))
                a_abbr = mapper.get(game.get('away_team'))
                if h_abbr and a_abbr: slate.append(f"{a_abbr} @ {h_abbr}")
            if slate: return list(set(slate))
    except: pass
    try:
        est = pytz.timezone('US/Eastern')
        today = datetime.now(est).strftime('%Y-%m-%d')
        board = scoreboardv2.ScoreboardV2(game_date=today, headers=custom_headers)
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

@st.cache_data(ttl=3600)
def get_live_odds():
    try:
        params = {'apiKey': ODDS_API_KEY, 'regions': 'us', 'markets': 'h2h', 'oddsFormat': 'american'}
        response = requests.get(ODDS_URL, params=params)
        if response.status_code == 200: return response.json()
        return []
    except: return []

# --- INJURY GUARD ---
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

@st.cache_data(ttl=3600)
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

def calculate_ev(prob_win, american_odds):
    if american_odds > 0: decimal = (american_odds / 100) + 1
    else: decimal = (100 / abs(american_odds)) + 1
    return ((prob_win * (decimal - 1)) - ((1-prob_win) * 1)) * 100

def get_team_map():
    return {t['full_name']: t['abbreviation'] for t in nba_teams_static.get_teams()}

@st.cache_data(ttl=3600)
def get_defense_rankings():
    try:
        dash = leaguedashteamstats.LeagueDashTeamStats(measure_type_detailed_defense='Opponent', per_mode_detailed='PerGame', headers=custom_headers)
        df = dash.get_data_frames()[0]
        df['PTS_RANK'] = df['OPP_PTS'].rank(ascending=False) 
        df['3PM_RANK'] = df['OPP_FG3M'].rank(ascending=False)
        return df[['TEAM_NAME', 'TEAM_ID', 'PTS_RANK', '3PM_RANK']]
    except: return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_roster(team_id):
    try:
        roster = commonteamroster.CommonTeamRoster(team_id=team_id, season='2024-25', headers=custom_headers, timeout=10)
        return roster.get_data_frames()[0]
    except:
        try:
            roster = commonteamroster.CommonTeamRoster(team_id=team_id, headers=custom_headers, timeout=10)
            return roster.get_data_frames()[0]
        except: return pd.DataFrame()

def fetch_player_logs(player_id):
    try:
        log = playergamelog.PlayerGameLog(player_id=player_id, season='2024-25', headers=custom_headers, timeout=10)
        df = log.get_data_frames()[0]
        df['PRA'] = df['PTS'] + df['REB'] + df['AST']
        df['LOCATION'] = np.where(df['MATCHUP'].str.contains('@'), 'AWAY', 'HOME')
        return df
    except: return pd.DataFrame()

# --- MAIN UI ---
st.title("🏀 NBA JUGGERNAUT V2.8")

tab1, tab2 = st.tabs(["🏆 Game Predictor (Live Odds + Injuries)", "📊 Player Prop Sniper"])

with tab1:
    df_games, pkg = load_brain()
    if df_games is not None:
        model, scaler, features = pkg["model"], pkg["scaler"], pkg["features"]
        todays_games, live_odds_data, injury_report, team_map = get_todays_slate(), get_live_odds(), get_injury_report(), get_team_map()
        
        if todays_games:
            mode = st.radio("Select Source:", ["📅 Today's Games", "🛠️ Custom Matchup"], horizontal=True)
        else:
            mode = "🛠️ Custom Matchup"
            st.warning("⚠️ No games auto-detected. Using Custom Mode.")

        home, away = None, None
        if mode == "📅 Today's Games":
            game = st.selectbox("Select Matchup:", todays_games)
            if game: away, home = game.split(" @ ")
        else:
            teams = sorted(df_games['team'].unique())
            c1, c2 = st.columns(2)
            with c1: home = st.selectbox("Home", teams, index=0)
            with c2: away = st.selectbox("Away", teams, index=1)

        if home and away:
            st.markdown(f"**Matchup:** {away} @ {home}")
            alerts = check_injuries(home, away, injury_report, team_map)
            if alerts:
                with st.expander(f"⚠️ Injury Report ({len(alerts)})", expanded=True):
                    for a in alerts: st.markdown(a)
            else: st.success("✅ Clean Slate: No major injuries found.")

            if st.button("PREDICT WINNER", type="primary"):
                try:
                    stats = df_games[df_games['team']==home].iloc[-1][features]
                    prob = model.decision_function(scaler.transform([stats]))[0]
                    winner = home if prob > 0 else away
                    conf = min(50 + (abs(prob)*10), 99.0)
                    
                    st.divider()
                    c_res, c_odds = st.columns(2)
                    with c_res:
                        st.markdown(f"## AI Pick: :green[{winner}]")
                        st.metric("Confidence", f"{conf:.1f}%")
                    
                    with c_odds:
                        found, best_odds, bookie = False, 0, "N/A"
                        odds_map = get_odds_team_map()
                        for g in live_odds_data:
                            if odds_map.get(g.get('home_team')) == home:
                                for b in g.get('bookmakers', []):
                                    for m in b.get('markets', []):
                                        if m['key'] == 'h2h':
                                            for o in m['outcomes']:
                                                if odds_map.get(o['name']) == winner:
                                                    best_odds, bookie, found = o['price'], b['title'], True
                                                    break
                        if found:
                            ev = calculate_ev(conf/100, best_odds)
                            implied = 100/(best_odds+100) if best_odds>0 else abs(best_odds)/(abs(best_odds)+100)
                            st.metric(f"Vegas Odds ({bookie})", f"{best_odds:+}", delta=f"Implied: {implied*100:.1f}%")
                            if ev > 0: st.success(f"✅ POSITIVE EV (+{ev:.1f}%)")
                            else: st.error(f"❌ NEGATIVE EV ({ev:.1f}%)")
                        else: st.caption("Live odds not found.")
                except Exception as e: st.error(f"Error: {e}")

with tab2:
    st.markdown("### 🎯 Weighted Prop Calculation")
    
    # --- GOLD STANDARD LOGIC INTEGRATED ---
    all_teams = nba_teams_static.get_teams()
    team_opts = {t['full_name']: t['id'] for t in all_teams}
    
    # 1. Team Selector (With Key)
    sel_team_name = st.selectbox("Team", list(team_opts.keys()), key="prop_team_sel")
    sel_team_id = team_opts[sel_team_name]
    
    # 2. Roster (With Key Reset)
    roster_df = get_roster(sel_team_id)
    if not roster_df.empty:
        p_opts = {row['PLAYER']: row['PLAYER_ID'] for _, row in roster_df.iterrows()}
        sel_p_name = st.selectbox("Player", list(p_opts.keys()), key=f"prop_p_sel_{sel_team_id}")
        sel_p_id = p_opts[sel_p_name]
        
        # 3. Opponent Selector (For Defense Logic)
        opp_teams = sorted(list(team_opts.keys()))
        sel_opp_name = st.selectbox("Opponent", opp_teams, key="prop_opp_sel")
        sel_opp_id = team_opts[sel_opp_name]
        
        # 4. Location Selector
        is_home = st.toggle("Is Home Game?", value=True)
        
        if st.button("ANALYZE PLAYER"):
            with st.spinner("Crunching numbers..."):
                logs = fetch_player_logs(sel_p_id)
                def_data = get_defense_rankings()
                
                if not logs.empty:
                    # Filter Splits
                    l5 = logs.head(5)
                    l10 = logs.head(10)
                    sea = logs
                    home_games = logs[logs['LOCATION'] == 'HOME']
                    away_games = logs[logs['LOCATION'] == 'AWAY']
                    
                    st.divider()
                    
                    # --- DEFENSE INTEL ---
                    opp_rank = "N/A"
                    opp_badge = ""
                    if not def_data.empty:
                        opp_row = def_data[def_data['TEAM_ID'] == sel_opp_id]
                        if not opp_row.empty:
                            # Using Points Allowed Rank as General Defense Proxy
                            rank = int(opp_row.iloc[0]['PTS_RANK'])
                            if rank >= 20: opp_badge = f"🟢 VS RANK #{rank} (SOFT)"
                            elif rank <= 10: opp_badge = f"🔴 VS RANK #{rank} (ELITE)"
                            else: opp_badge = f"⚪ VS RANK #{rank} (MID)"
                            opp_rank = rank
                    
                    st.subheader(f"Defense Matchup: {opp_badge}")
                    
                    cols = st.columns(4)
                    cats = ['PTS', 'REB', 'AST', 'PRA']
                    
                    for i, cat in enumerate(cats):
                        # 1. Base Weighted Average
                        avg_l5 = l5[cat].mean()
                        avg_l10 = l10[cat].mean()
                        avg_sea = sea[cat].mean()
                        proj = (avg_l5 * 0.5) + (avg_l10 * 0.3) + (avg_sea * 0.2)
                        
                        # 2. Location Adjustment
                        loc_avg = home_games[cat].mean() if is_home else away_games[cat].mean()
                        if pd.notna(loc_avg):
                            proj = (proj * 0.8) + (loc_avg * 0.2)
                            
                        # 3. Defense Adjustment
                        if opp_rank != "N/A":
                            if opp_rank >= 25: proj *= 1.05 # Boost 5% for soft defense
                            elif opp_rank <= 5: proj *= 0.95 # Drop 5% for elite defense
                            
                        with cols[i]:
                            st.metric(f"Proj {cat}", f"{proj:.1f}", delta=f"L5: {avg_l5:.1f}")
                            
                    st.caption("Projection includes: Recent Form (50%), Season (20%), Home/Away Split (User Selection), and Defensive Matchup Adjustment.")
                    
                    st.divider()
                    st.subheader("Last 5 Games Trend")
                    st.line_chart(l5[['GAME_DATE', 'PTS', 'REB', 'AST']].set_index('GAME_DATE').iloc[::-1])
                else:
                    st.error("No game logs found.")
    else:
        st.warning("Roster not found. Try 'Force Refresh'.")
