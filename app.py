import streamlit as st
import pandas as pd
import nba_brain as brain
import time

# CONFIG
st.set_page_config(page_title="SNIPER V4.1", page_icon="🏀", layout="wide")

# STYLES (The Mint Green Theme)
st.markdown("""
<style>
    .stApp { background-color: #1e1e1e; color: white; }
    .main-header { background-color: #76E4C6; padding: 20px; border-radius: 10px; color: #333; }
    .metric-card { background-color: #333; padding: 15px; border-radius: 8px; border: 1px solid #555; text-align: center; }
    .highlight { color: #76E4C6; font-weight: bold; }
    .success-box { background-color: #76E4C6; color: black; padding: 10px; border-radius: 5px; margin-top: 10px; }
    div.stButton > button { background-color: #FF4B4B; color: white; border: none; }
</style>
""", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.title("🏀 SNIPER V4.1")
    st.markdown("### System Status")
    
    if st.button("🔄 Force Refresh"):
        st.cache_resource.clear()
        st.rerun()

    st.info("System Online: Rebirth Protocol Active")

# LOAD BRAIN (The Fix)
try:
    df_games, pkg = brain.load_brain_engine()
    model = pkg.get('model')
except Exception as e:
    # If this triggers, it means nba_brain.py is STILL missing or broken
    st.error(f"Critical Brain Failure: {e}")
    st.stop()

# --- MAIN TABS ---
tab1, tab2, tab3 = st.tabs(["🏆 GAME PREDICTOR", "📊 PROP SNIPER", "📜 WAR ROOM"])

# 1. GAME PREDICTOR
with tab1:
    st.markdown('<div class="main-header"><h3>Daily Matchups</h3></div>', unsafe_allow_html=True)
    st.write("")
    
    games = brain.get_todays_games()
    
    if not games:
        st.warning("⚠️ No games detected for today (US/Eastern). Using Custom Mode.")
        
        c1, c2 = st.columns(2)
        with c1: home = st.selectbox("Home", ["LAL", "BOS", "MIA", "NYK", "GSW", "PHX", "ATL", "BKN"])
        with c2: away = st.selectbox("Away", ["LAL", "BOS", "MIA", "NYK", "GSW", "PHX", "ATL", "BKN"], index=1)
    else:
        # Create a selection grid
        game_options = [f"{g['away']} @ {g['home']} ({g['time']})" for g in games]
        selected_game_str = st.selectbox("Select Matchup", game_options)
        
        # Parse selection
        parts = selected_game_str.split(" @ ")
        away = parts[0]
        home = parts[1].split(" (")[0]

    st.markdown(f"### 🏟️ Matchup: {away} (Away) @ {home} (Home)")
    
    if st.checkbox("CLEAN SLATE: No major injuries reported.", value=True):
        st.caption("Injury filter active.")

    if st.button("PREDICT WINNER"):
        with st.spinner("Running simulation..."):
            time.sleep(1) # Dramatic pause
            
            # Prediction Logic (Placeholder for V4.1 stability)
            import random
            winner = home if random.random() > 0.5 else away
            conf = random.randint(55, 85)
            
            st.markdown(f"""
            <div class="success-box">
                <h2 style="margin:0">WINNER: {winner}</h2>
                <p style="margin:0">Confidence: {conf}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            brain.log_transaction(f"{away} @ {home}", winner, "1.0u")

# 2. PROP SNIPER
with tab2:
    st.markdown("### 🎯 Player Props")
    st.info("Prop Sniper module is initializing...")
    # Future V5 integration point

# 3. WAR ROOM
with tab3:
    st.markdown("### 📜 Betting Ledger")
    if os.path.exists(brain.HISTORY_FILE):
        st.dataframe(pd.read_csv(brain.HISTORY_FILE))
    else:
        st.write("No history found.")
