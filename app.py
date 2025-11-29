import streamlit as st
import pandas as pd
import nba_brain as brain 
import os  # <--- FIXED: Added missing import
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="NBA Sniper V4.1", layout="wide", page_icon="🏀")

# --- STYLES ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    .stat-card { background: #1f2937; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #374151; }
    .positive { color: #4ade80; font-weight: bold; }
    .negative { color: #f87171; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏀 SNIPER V4.1")
    st.markdown("### System Status")
    if st.button("🔄 Force Refresh", type="primary"):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    st.info("System Online: Autonomous Mode")

# --- MAIN UI ---
tab1, tab2, tab3 = st.tabs(["🏆 GAME PREDICTOR", "📊 PROP SNIPER", "📜 WAR ROOM"])

# ================= TAB 1: GAME PREDICTOR =================
with tab1:
    df_games, pkg = brain.load_brain_engine()
    
    if df_games is not None:
        model, scaler, features = pkg["model"], pkg["scaler"], pkg["features"]
        todays_games = brain.get_todays_slate()
        live_odds = brain.get_live_odds()
        injuries = brain.get_injury_report()
        team_map = brain.get_team_map()
        
        # Matchup Selector
        if todays_games:
            mode = st.radio("Select Source:", ["📅 Today's Games", "🛠️ Custom Matchup"], horizontal=True)
        else:
            mode = "🛠️ Custom Matchup"
            st.warning("⚠️ No games detected for today (US/Eastern). Using Custom Mode.")
            
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
            st.markdown(f"### 🏟️ Matchup: {away} (Away) @ {home} (Home)")
            
            # Injury Guard
            alerts = brain.check_injuries(home, away, injuries, team_map)
            if alerts:
                with st.expander(f"⚠️ INJURY REPORT ({len(alerts)})", expanded=True):
                    for a in alerts: st.markdown(a)
            else:
                st.success("✅ CLEAN SLATE: No major injuries reported.")
                
            if st.button("PREDICT WINNER", type="primary"):
                try:
                    # AI Prediction
                    stats = df_games[df_games['team']==home].iloc[-1][features]
                    prob = model.decision_function(scaler.transform([stats]))[0]
                    winner = home if prob > 0 else away
                    conf = min(50 + (abs(prob)*10), 99.0)
                    color = "green" if winner == home else "red"
                    
                    st.divider()
                    c1, c2 = st.columns(2)
                    
                    with c1:
                        st.markdown(f"## AI Pick: :{color}[{winner}]")
                        st.metric("Confidence", f"{conf:.1f}%")
                        
                    with c2:
                        # Odds Scanner
                        odds_map = brain.get_odds_team_map()
                        found, best_odds, bookie = False, 0, "N/A"
                        
                        for g in live_odds:
                            if odds_map.get(g.get('home_team')) == home:
                                for b in g.get('bookmakers', []):
                                    for m in b.get('markets', []):
                                        if m['key'] == 'h2h':
                                            for o in m['outcomes']:
                                                if odds_map.get(o['name']) == winner:
                                                    best_odds, bookie, found = o['price'], b['title'], True
                                                    break
                        if found:
                            # EV Calculation
                            decimal = (best_odds/100)+1 if best_odds > 0 else (100/abs(best_odds))+1
                            win_prob = conf/100
                            ev = ((win_prob * (decimal - 1)) - ((1-win_prob) * 1)) * 100
                            
                            st.metric(f"Vegas Odds ({bookie})", f"{best_odds:+}")
                            if ev > 0: st.success(f"✅ POSITIVE EV (+{ev:.1f}%)")
                            else: st.error(f"❌ NEGATIVE EV ({ev:.1f}%)")
                        else:
                            st.caption("Live odds not found.")
                except Exception as e: st.error(f"Prediction Error: {e}")

# ================= TAB 2: PROP SNIPER =================
with tab2:
    st.markdown("### 🎯 Player Prop Sniper")
    
    all_teams = brain.nba_teams_static.get_teams()
    team_opts = {t['full_name']: t['id'] for t in all_teams}
    
    # Team Selector
    sel_team = st.selectbox("Team", list(team_opts.keys()), key="prop_team")
    sel_team_id = team_opts[sel_team]
    
    # Roster (Nuclear Fetch)
    roster = brain.get_roster(sel_team_id)
    
    if not roster.empty:
        # Player Selector
        p_opts = {row['PLAYER']: row['PLAYER_ID'] for _, row in roster.iterrows()}
        sel_player = st.selectbox("Player", list(p_opts.keys()), key=f"prop_player_{sel_team_id}")
        sel_pid = p_opts[sel_player]
        
        # Opponent Selector
        opp_teams = sorted(list(team_opts.keys()))
        sel_opp = st.selectbox("Opponent", opp_teams, key="prop_opp")
        sel_opp_id = team_opts[sel_opp]
        is_home = st.toggle("Is Home Game?", value=True)
        
        if st.button("ANALYZE PLAYER"):
            with st.spinner("Gathering Intel & Scanning Vegas..."):
                # Fetch Data
                logs = brain.fetch_player_logs(sel_pid)
                def_data = brain.get_defense_rankings()
                game_id = brain.get_game_id_for_team(sel_team)
                prop_lines = brain.get_player_props(game_id, sel_player)
                
                if not logs.empty:
                    l5 = logs.head(5)
                    l10 = logs.head(10)
                    sea = logs
                    home_g = logs[logs['LOCATION'] == 'HOME']
                    away_g = logs[logs['LOCATION'] == 'AWAY']
                    
                    # Defense Intel
                    opp_rank, opp_badge = "N/A", ""
                    if not def_data.empty:
                        opp_row = def_data[def_data['TEAM_ID'] == sel_opp_id]
                        if not opp_row.empty:
                            rank = int(opp_row.iloc[0]['PTS_RANK'])
                            if rank >= 20: opp_badge = f"🟢 VS RANK #{rank} (SOFT)"
                            elif rank <= 10: opp_badge = f"🔴 VS RANK #{rank} (ELITE)"
                            else: opp_badge = f"⚪ VS RANK #{rank} (MID)"
                            opp_rank = rank
                            
                    st.divider()
                    st.subheader(f"Matchup Intel: {opp_badge}")
                    
                    # Calc & Display
                    cols = st.columns(3)
                    cats = ['PTS', 'REB', 'AST']
                    
                    for i, cat in enumerate(cats):
                        # Projection Math (Gold Standard)
                        avg_l5, avg_l10, avg_sea = l5[cat].mean(), l10[cat].mean(), sea[cat].mean()
                        proj = (avg_l5 * 0.5) + (avg_l10 * 0.3) + (avg_sea * 0.2)
                        
                        # Adjustments
                        loc_avg = home_g[cat].mean() if is_home else away_g[cat].mean()
                        if pd.notna(loc_avg): proj = (proj * 0.8) + (loc_avg * 0.2)
                        if opp_rank != "N/A":
                            if opp_rank >= 25: proj *= 1.05
                            elif opp_rank <= 5: proj *= 0.95
                            
                        # Sniper Comparison
                        line = prop_lines.get(cat)
                        rec = ""
                        decision = "NO PLAY"
                        if line:
                            diff = proj - line
                            if diff > 1.5: 
                                rec = f"✅ OVER {line}"
                                decision = "OVER"
                            elif diff < -1.5: 
                                rec = f"✅ UNDER {line}"
                                decision = "UNDER"
                            else: rec = f"⚪ NO EDGE ({line})"
                        else: rec = "⚠️ No Line"
                        
                        with cols[i]:
                            st.markdown(f"<div class='stat-card'><h3>{cat}</h3><h1>{proj:.1f}</h1><p>{rec}</p></div>", unsafe_allow_html=True)
                            if decision != "NO PLAY":
                                if st.button(f"💾 Log {cat}", key=f"log_{cat}"):
                                    brain.log_prediction(sel_player, cat, line, proj, decision, diff, "Sniper V4")
                                    st.toast("✅ Saved!")

                    st.divider()
                    st.caption("Last 5 Games:")
                    st.dataframe(l5[['GAME_DATE', 'MATCHUP', 'PTS', 'REB', 'AST', 'MIN']].set_index('GAME_DATE'), use_container_width=True)
                    
                else: st.error("No game logs found.")
    else:
        st.warning("Could not fetch roster. This is likely a Cloud IP block by the NBA.")
        st.caption("Try hitting 'Force Refresh' in sidebar.")

# ================= TAB 3: WAR ROOM =================
with tab3:
    st.markdown("### 📜 Betting History")
    if os.path.exists(brain.HISTORY_FILE):
        df_hist = pd.read_csv(brain.HISTORY_FILE)
        st.dataframe(df_hist, use_container_width=True)
    else:
        st.info("No bets logged yet.")
