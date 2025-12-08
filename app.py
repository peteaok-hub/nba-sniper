import streamlit as st
import pandas as pd
import nba_brain as brain
import importlib

# --- BRAIN SHOCK PROTOCOL ---
# Forces the app to reload the brain file every time you click Refresh
importlib.reload(brain)
# ---------------------------

st.set_page_config(page_title="SNIPER V11.1", page_icon="🏀", layout="wide")

# STYLES (Hard Rock Red/Dark Theme)
st.markdown("""
<style>
    .stApp { background-color: #0e0e10; color: #e0e0e0; }
    .hr-header { 
        background: linear-gradient(90deg, #d50000, #ff1744); 
        padding: 12px; border-radius: 8px; text-align: center; 
        color: white; font-weight: 900; letter-spacing: 1px; margin-bottom: 20px;
    }
    .game-card { 
        background-color: #1c1c1e; border: 1px solid #333; padding: 15px; 
        border-radius: 12px; margin-bottom: 12px;
    }
    .edge-box { 
        background-color: #2c2c2e; border-radius: 6px; padding: 8px; text-align: center; 
        border: 1px solid #444; height: 100%;
    }
    .sniper-val { font-size: 1.2em; font-weight: bold; }
    .green-edge { color: #00e676; text-shadow: 0 0 5px rgba(0, 230, 118, 0.4); }
    .white-edge { color: #ffffff; }
    .info-text { font-size: 0.8em; color: #888; }
    .tired-text { color: #ff5252; font-size: 0.75em; font-weight: bold; }
    
    /* ACTION BUTTONS */
    div.stButton > button { 
        background-color: #444; color: white; border: none; width: 100%; font-weight: bold;
        transition: 0.3s;
    }
    div.stButton > button:hover { background-color: #666; }
    
    /* GREEN BUTTON FOR WINNING SIDE */
    .win-btn div.stButton > button { background-color: #00e676; color: black; }
</style>
""", unsafe_allow_html=True)

# LOAD BRAIN
try:
    df_games, pkg = brain.load_brain_engine()
except Exception as e:
    st.error(f"Brain Offline: {e}")
    st.stop()

# SIDEBAR
with st.sidebar:
    st.title("🏀 SNIPER V11.1")
    st.caption("Velocity & Fatigue Engine")
    if st.button("🔄 Refresh"): st.rerun()
    st.info("🚀 = Fast Pace | 🐢 = Slow Pace")
    st.info("⚠️ = B2B (No Rest) | 🚑 = High Usage Alert")

# HEADER
st.markdown('<div class="hr-header">VELOCITY HUNTER BOARD</div>', unsafe_allow_html=True)

# GAME GRID
games = brain.get_todays_games()

if not games:
    st.warning("⚠️ No games found. Update nba_brain.py.")
    st.stop()

c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
c1.caption("MATCHUP & PACE")
c2.caption("SPREAD EDGE")
c3.caption("TOTAL EDGE")
c4.caption("DECISION")

for g in games:
    try:
        # Pass the whole game object to the brain
        proj = brain.get_matchup_projection(g) 
    except Exception as e:
        st.error(f"Error projecting {g['home']} vs {g['away']}: {e}")
        continue
    
    with st.container():
        st.markdown('<div class="game-card">', unsafe_allow_html=True)
        cols = st.columns([1.5, 1, 1, 1])
        
        # 1. MATCHUP
        with cols[0]:
            h_rest_txt = "B2B" if g.get('h_rest') == 0 else f"{g.get('h_rest', 1)}d"
            a_rest_txt = "B2B" if g.get('a_rest') == 0 else f"{g.get('a_rest', 1)}d"
            
            # Display Team Names with Rest/Streak Emojis
            st.markdown(f"**{g['away']}** {proj.get('a_emoji','')} @ **{g['home']}** {proj.get('h_emoji','')}", unsafe_allow_html=True)
            
            # Display Pace & Rest Info
            st.markdown(f"<div class='info-text'>Rest: {a_rest_txt} v {h_rest_txt}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='info-text'>Pace: {proj.get('avg_pace', 99):.1f} {proj.get('pace_emoji','')}</div>", unsafe_allow_html=True)
            
            # Display Fatigue Alerts (from CSV)
            if proj.get('h_tired'):
                st.markdown(f"<div class='tired-text'>FATIGUE: {', '.join(proj['h_tired'][:2])}</div>", unsafe_allow_html=True)
            if proj.get('a_tired'):
                st.markdown(f"<div class='tired-text'>FATIGUE: {', '.join(proj['a_tired'][:2])}</div>", unsafe_allow_html=True)
            
        # 2. SPREAD
        with cols[1]:
            my_spread = round(proj['projected_spread'], 1)
            book_spread = g.get('book_spread', 0)
            diff = abs(my_spread - book_spread)
            color = "green-edge" if diff >= 3.0 else "white-edge"
            
            st.markdown(f"""
            <div class='edge-box'>
                <div class='sniper-val {color}'>{my_spread}</div>
                <div class='info-text'>Book: {book_spread}</div>
            </div>
            """, unsafe_allow_html=True)

        # 3. TOTAL
        with cols[2]:
            my_total = round(proj['projected_total'], 1)
            book_total = g.get('book_total', 220)
            diff_t = abs(my_total - book_total)
            color_t = "green-edge" if diff_t >= 5.0 else "white-edge"
            
            st.markdown(f"""
            <div class='edge-box'>
                <div class='sniper-val {color_t}'>{my_total}</div>
                <div class='info-text'>Book: {book_total}</div>
            </div>
            """, unsafe_allow_html=True)

        # 4. ACTION (Visual Upgrade)
        with cols[3]:
            winner = g['home'] if proj['win_prob'] > 50 else g['away']
            conf = int(proj['win_prob']) if winner == g['home'] else int(100 - proj['win_prob'])
            
            # Confidence Meter
            st.progress(conf)
            st.caption(f"Confidence: {conf}%")
            
            if st.button(f"BET {winner}", key=f"b_{g['home']}"):
                brain.log_transaction(f"{g['away']} @ {g['home']}", winner, "1u")
                st.toast(f"✅ Logged: {winner}")

        st.markdown('</div>', unsafe_allow_html=True)