import streamlit as st
import pandas as pd
import numpy as np
import pickle
import os
import requests
import unicodedata
from datetime import datetime
from nba_api.stats.static import teams as nba_teams_static
from nba_api.stats.endpoints import commonteamroster, playergamelog, leaguedashteamstats, scoreboardv2
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
st.set_page_config(page_title="NBA Sniper Juggernaut V2.4", layout="wide", page_icon="🏀")

# Custom headers to stop the NBA from blocking us
custom_headers = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true',
    'Connection': 'keep-alive',
    'Referer': 'https://stats.nba.com/',
}

# --- ODDS API KEYS ---
ODDS_API_KEY = "3e039d8cfd426d394b020b55bd303a07"
ODDS_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"

# --- 1. EXISTING ML ENGINE (GAME WINNER) ---
@st.cache_resource
def load_brain():
    if not os.path.exists("nba_games_rolled.csv") or not os.path.exists("nba_brain.pkl"):
        st.warning("⚠️ ML Brain not found. Please run 'fix_brain.py' first.")
        return None, None
    
    df = pd.read_csv("nba_games_rolled.csv", parse_dates=["date"])
    with open("nba_brain.pkl", "rb") as f:
        pkg = pickle.load(f)
    return df, pkg

# --- 2. INTELLIGENCE MODULES ---

def normalize_name(name):
    return ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')

@st.cache_data(ttl=3600)
def get_todays_slate():
    """Fetches today's games and returns a list of matchups."""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        board = scoreboardv2.ScoreboardV2(game_date=today, headers=custom_headers)
        games = board.get_data_frames()[0]
        
        if games.empty:
            return []

        all_teams = nba_teams_static.get_teams()
        id_to_abbr = {t['id']: t['abbreviation'] for t in all_teams}
        
        slate = []
        for _, row in games.iterrows():
            home_id = row['HOME_TEAM_ID']
            away_id = row['VISITOR_TEAM_ID']
            
            if home_id in id_to_abbr and away_id in id_to_abbr:
                h_abbr = id_to_abbr[home_id]
                a_abbr = id_to_abbr[away_id]
                slate.append(f"{a_abbr} @ {h_abbr}")
        
        return slate
    except:
        return []

@st.cache_data(ttl=3600)
def get_live_odds():
    """Fetches live odds from The-Odds-API."""
    try:
        params = {
            'apiKey': ODDS_API_KEY,
            'regions': 'us',
            'markets': 'h2h', # Moneyline
            'oddsFormat': 'american'
        }
        response = requests.get(ODDS_URL, params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# --- INJURY GUARD (WITH SMART MAPPING) ---
def normalize_cbs_name(cbs_name):
    """Maps CBS Sports Team Names to Official NBA Names."""
    mapping = {
        "Golden St.": "Golden State Warriors",
        "L.A. Lakers": "Los Angeles Lakers",
        "L.A. Clippers": "Los Angeles Clippers",
        "San Antonio": "San Antonio Spurs",
        "New York": "New York Knicks",
        "New Orleans": "New Orleans Pelicans",
        "Okla. City": "Oklahoma City Thunder",
        "Utah": "Utah Jazz",
        "Phoenix": "Phoenix Suns",
        "Philadelphia": "Philadelphia 76ers",
        "Miami": "Miami Heat",
        "Boston": "Boston Celtics",
        "Atlanta": "Atlanta Hawks",
        "Brooklyn": "Brooklyn Nets",
        "Charlotte": "Charlotte Hornets",
        "Chicago": "Chicago Bulls",
        "Cleveland": "Cleveland Cavaliers",
        "Dallas": "Dallas Mavericks",
        "Denver": "Denver Nuggets",
        "Detroit": "Detroit Pistons",
        "Houston": "Houston Rockets",
        "Indiana": "Indiana Pacers",
        "Memphis": "Memphis Grizzlies",
        "Milwaukee": "Milwaukee Bucks",
        "Minnesota": "Minnesota Timberwolves",
        "Orlando": "Orlando Magic",
        "Portland": "Portland Trail Blazers",
        "Sacramento": "Sacramento Kings",
        "Toronto": "Toronto Raptors",
        "Washington": "Washington Wizards"
    }
    return mapping.get(cbs_name, cbs_name) 

@st.cache_data(ttl=3600)
def get_injury_report():
    """Scrapes CBS Sports for the latest NBA injury report."""
    try:
        url = "https://www.cbssports.com/nba/injuries/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        injuries = {}
        
        for team_section in soup.find_all('div', class_='TeamLogoNameLockup'):
            team_name_tag = team_section.find('span', class_='TeamLogoNameLockup-name')
            if not team_name_tag: continue
            
            raw_team_name = team_section.find('a').text.strip()
            clean_team_name = normalize_cbs_name(raw_team_name) 
            
            parent_card = team_section.find_parent('div', class_='TableBase')
            if not parent_card: continue
            
            rows = parent_card.find_all('tr', class_='TableBase-bodyTr')
            
            team_injuries = []
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 5:
                    player = cols[0].find('span', class_='CellPlayerName--long').text.strip()
                    status = cols[4].text.strip() 
                    injury_desc = cols[3].text.strip() 
                    
                    team_injuries.append({'player': player, 'status': status, 'injury': injury_desc})
            
            injuries[clean_team_name] = team_injuries
            
        return injuries
    except Exception as e:
        print(f"Injury Scraping Error: {e}")
        return {}

def check_injuries(home_abbr, away_abbr, injury_data, team_map_full):
    """Checks if specific teams have active injuries."""
    alerts = []
    
    abbr_to_full = {v: k for k, v in team_map_full.items()}
    home_full = abbr_to_full.get(home_abbr)
    away_full = abbr_to_full.get(away_abbr)
    
    # Check Home
    if home_full and home_full in injury_data:
        for inj in injury_data[home_full]:
            icon = "🔴" if "Expected to be out" in inj['status'] or "Out" in inj['status'] else "🟡"
            alerts.append(f"{icon} **{home_abbr}** - {inj['player']}: {inj['injury']} ({inj['status']})")
            
    # Check Away
    if away_full and away_full in injury_data:
        for inj in injury_data[away_full]:
            icon = "🔴" if "Expected to be out" in inj['status'] or "Out" in inj['status'] else "🟡"
            alerts.append(f"{icon} **{away_abbr}** - {inj['player']}: {inj['injury']} ({inj['status']})")
            
    return alerts

def calculate_ev(prob_win, american_odds):
    """Calculates Expected Value."""
    if american_odds > 0:
        decimal_odds = (american_odds / 100) + 1
    else:
        decimal_odds = (100 / abs(american_odds)) + 1
    
    prob_loss = 1 - prob_win
    profit = decimal_odds - 1
    ev = (prob_win * profit) - (prob_loss * 1)
    return ev * 100 

def get_team_map():
    teams = nba_teams_static.get_teams()
    return {t['full_name']: t['abbreviation'] for t in teams}

@st.cache_data(ttl=3600)
def get_defense_rankings():
    try:
        dash = leaguedashteamstats.LeagueDashTeamStats(
            measure_type_detailed_defense='Opponent', 
            per_mode_detailed='PerGame', 
            headers=custom_headers
        )
        df = dash.get_data_frames()[0]
        df['PTS_RANK'] = df['OPP_PTS'].rank(ascending=False) 
        df['3PM_RANK'] = df['OPP_FG3M'].rank(ascending=False)
        return df[['TEAM_NAME', 'TEAM_ID', 'PTS_RANK', '3PM_RANK']]
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_roster(team_id):
    try:
        roster = commonteamroster.CommonTeamRoster(team_id=team_id, headers=custom_headers)
        return roster.get_data_frames()[0]
    except:
        return pd.DataFrame()

def fetch_player_logs(player_id):
    try:
        log = playergamelog.PlayerGameLog(player_id=player_id, season='2024-25', headers=custom_headers)
        df = log.get_data_frames()[0]
        df['PRA'] = df['PTS'] + df['REB'] + df['AST']
        df['LOCATION'] = np.where(df['MATCHUP'].str.contains('@'), 'AWAY', 'HOME')
        return df
    except:
        return pd.DataFrame()

# --- MAIN UI ---
st.title("🏀 NBA JUGGERNAUT V2.4")

tab1, tab2 = st.tabs(["🏆 Game Predictor (Live Odds + Injuries)", "📊 Player Prop Sniper"])

# ================= TAB 1: GAME PREDICTOR =================
with tab1:
    df_games, pkg = load_brain()
    
    if df_games is not None:
        model = pkg["model"]
        scaler = pkg["scaler"]
        features = pkg["features"]
        
        # Data Load
        todays_games = get_todays_slate()
        live_odds_data = get_live_odds()
        injury_report = get_injury_report() 
        team_map = get_team_map() 

        if todays_games:
            mode = st.radio("Select Source:", ["📅 Today's Games", "🛠️ Custom Matchup"], horizontal=True)
        else:
            mode = "🛠️ Custom Matchup"
            st.info("No games found for today. Using Custom Mode.")

        selected_home = None
        selected_away = None

        if mode == "📅 Today's Games":
            game_selection = st.selectbox("Select a Matchup:", todays_games)
            if game_selection:
                parts = game_selection.split(" @ ")
                selected_away = parts[0]
                selected_home = parts[1]
        else:
            teams_list = sorted(df_games['team'].unique())
            c1, c2 = st.columns(2)
            with c1: selected_home = st.selectbox("Home Team", teams_list, index=0)
            with c2: selected_away = st.selectbox("Away Team", teams_list, index=1)

        if selected_home and selected_away:
            st.markdown(f"**Matchup:** {selected_away} (Away) @ {selected_home} (Home)")
            
            # --- INJURY GUARD DISPLAY ---
            injury_alerts = check_injuries(selected_home, selected_away, injury_report, team_map)
            
            if injury_alerts:
                st.error(f"⚠️ {len(injury_alerts)} Active Injury Alerts Found:")
                for alert in injury_alerts:
                    st.write(alert)
            else:
                st.success("✅ Clean Slate: No major injuries found in report.")

            if st.button("PREDICT WINNER", type="primary"):
                try:
                    h_stats = df_games[df_games['team']==selected_home].iloc[-1][features]
                    input_data = pd.DataFrame([h_stats], columns=features)
                    sc_data = scaler.transform(input_data)
                    prob = model.decision_function(sc_data)[0]
                    
                    winner = selected_home if prob > 0 else selected_away
                    conf_raw = 50 + (abs(prob)*10)
                    conf = min(conf_raw, 99.0)
                    color = "green" if winner == selected_home else "red"
                    
                    st.divider()
                    
                    c_res, c_odds = st.columns(2)
                    
                    with c_res:
                        st.markdown(f"## AI Pick: :{color}[{winner}]")
                        st.metric("Confidence", f"{conf:.1f}%")

                    # FIND ODDS (FIXED LOGIC)
                    found_odds = False
                    best_odds = 0
                    sportsbook = "Unknown"
                    
                    for game in live_odds_data:
                        api_home = game.get('home_team', '')
                        # USE THE SMART MAP to find Abbr from Full Name
                        mapped_home = team_map.get(api_home, "Unknown")
                        
                        if mapped_home == selected_home:
                            bookmakers = game.get('bookmakers', [])
                            if bookmakers:
                                main_book = bookmakers[0]
                                markets = main_book.get('markets', [])
                                for m in markets:
                                    if m['key'] == 'h2h':
                                        for outcome in m['outcomes']:
                                            # Check Outcome Name using Map
                                            outcome_name = outcome.get('name', '')
                                            mapped_outcome = team_map.get(outcome_name, "")
                                            
                                            if mapped_outcome == winner:
                                                best_odds = outcome.get('price', 0)
                                                sportsbook = main_book.get('title', 'Bookie')
                                                found_odds = True
                                                break
                        if found_odds: break

                    with c_odds:
                        if found_odds:
                            prob_decimal = conf / 100
                            ev_value = calculate_ev(prob_decimal, best_odds)
                            
                            if best_odds > 0:
                                implied = 100 / (best_odds + 100)
                            else:
                                implied = abs(best_odds) / (abs(best_odds) + 100)
                            implied_pct = implied * 100
                            
                            st.metric(f"Vegas Odds ({sportsbook})", f"{best_odds:+}", delta=f"Implied: {implied_pct:.1f}%")
                            
                            if ev_value > 0:
                                st.success(f"✅ **POSITIVE EV BET!** (+{ev_value:.1f}% ROI)")
                            else:
                                st.error(f"❌ **NEGATIVE EV** ({ev_value:.1f}%)")
                        else:
                            st.caption("Live odds not found for this matchup.")

                except Exception as e:
                    st.error(f"Prediction Error: {e}")

# ================= TAB 2: PLAYER PROP SNIPER =================
with tab2:
    st.markdown("### 🎯 Weighted Prop Calculation")
    
    all_teams = nba_teams_static.get_teams()
    team_opts = {t['full_name']: t['id'] for t in all_teams}
    selected_team_name = st.selectbox("Select Player's Team", list(team_opts.keys()))
    selected_team_id = team_opts[selected_team_name]

    roster_df = get_roster(selected_team_id)
    if not roster_df.empty:
        player_opts = {row['PLAYER']: row['PLAYER_ID'] for _, row in roster_df.iterrows()}
        selected_player_name = st.selectbox("Select Player", list(player_opts.keys()))
        selected_player_id = player_opts[selected_player_name]
        
        if st.button("ANALYZE PLAYER"):
            with st.spinner(f"Scanning stats for {selected_player_name}..."):
                logs = fetch_player_logs(selected_player_id)
                
                if not logs.empty:
                    l5 = logs.head(5)
                    l10 = logs.head(10)
                    season = logs
                    
                    st.divider()
                    cols = st.columns(4)
                    
                    def_df = get_defense_rankings()
                    
                    cats = ['PTS', 'REB', 'AST', 'PRA']
                    for i, cat in enumerate(cats):
                        avg_l5 = l5[cat].mean()
                        avg_l10 = l10[cat].mean()
                        avg_sea = season[cat].mean()
                        
                        proj = (avg_l5 * 0.5) + (avg_l10 * 0.3) + (avg_sea * 0.2)
                        
                        with cols[i]:
                            st.metric(f"Predicted {cat}", f"{proj:.1f}", delta=f"L5: {avg_l5:.1f}")
                    
                    st.divider()
                    
                    st.subheader("Last 5 Games Trend")
                    chart_data = l5[['GAME_DATE', 'PTS', 'REB', 'AST']].set_index('GAME_DATE').iloc[::-1]
                    st.line_chart(chart_data)
                    
                    st.subheader("League Defense Rankings (Context)")
                    st.dataframe(def_df.sort_values("PTS_RANK", ascending=False).style.apply(
                        lambda x: ['background-color: #d4edda' if v > 20 else 'background-color: #f8d7da' if v < 10 else '' for v in x], 
                        subset=['PTS_RANK']
                    ), use_container_width=True)

                else:
                    st.error("No game logs found for this season.")
    else:
        st.warning("Could not fetch roster. Check API connection.")