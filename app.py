import streamlit as st
import pandas as pd
import nba_brain as brain
import importlib

# --- BRAIN SHOCK PROTOCOL (V5.2) ---
importlib.reload(brain)
# -----------------------------------

st.set_page_config(page_title="SNIPER V5.2", page_icon="🏀", layout="wide")

# STYLES (Hard Rock Dark Mode)
st.markdown("""
<style>
    .stApp { background-color: #0e0e10; color: #e0e0e0; font-family: 'Roboto', sans-serif; }
    .hr-header { 
        background: linear-gradient(90deg, #6200ea, #b388ff); 
        padding: 12px; border-radius: 8px; text-align: center; 
        color: white; font-weight: 900; letter-spacing: 1px; margin-bottom: 20px;
    }
    .game-card { 
        background-color: #1c1c1e; border: 1px solid #333; padding: 15px; 
        border-radius: 12px; margin-bottom: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .team-name { font-size: 1.2em; font-weight: bold; color: white; }
    .record { font-size: 0.8em; color: #888; }
    .edge-box { 
        background-color: #2c2c2e; border-radius: 6px; padding: 8px; text-align: center; 
        border: 1px solid #444;
    }
    .sniper-val { font-size: 1.3em; font-weight: bold; }
    .book-val { font-size: 0.8em; color: #aaa; }
    .green-edge { color: #00e676; text-shadow: 0 0 5px rgba(0, 230, 118, 0.4); }
    .white-edge { color: #ffffff; }
    div.stButton > button { 
        background-color: #6200ea; color: white; border: none; width: 100%; font-weight: bold;
    }
    div.stButton > button:hover { background-color: #7c4dff; }
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
    st.title("🏀 SNIPER V5.2")
    st.caption("Hard Rock Data Integration")
    if st.button("🔄 Refresh Data"): st.rerun()
    st.markdown("---")
    st.markdown("**Legend:**")
    st.markdown("🔥 = High Momentum")
    st.markdown("🟢 = >2pt Edge (Betable)")

# HEADER
st.markdown('<div class="hr-header">HARD ROCK HUNTER BOARD</div>', unsafe_allow_html=True)

# GAME GRID
games = brain.get_todays_games()

# Column Headers
c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
c1.caption("MATCHUP & RECORDS")
c2.caption("SPREAD EDGE")
c3.caption("TOTAL EDGE")
c4.caption("ACTION")

for g in games:
    try:
        proj = brain.get_matchup_projection(g['home'], g['away'])
    except AttributeError:
        st.error("Brain Version Mismatch. Please Reboot App.")
        st.stop()
    
    with st.container():
        # Open Card
        st.markdown('<div class="game-card">', unsafe_allow_html=True)
        cols = st.columns([1.5, 1, 1, 1])
        
        # 1. MATCHUP & RECORDS
        with cols[0]:
            h_mom = "🔥" if proj['h_mom'] > 5 else ""
            a_mom = "🔥" if proj['a_mom'] > 5 else ""
            
            st.markdown(f"<div class='team-name'>{g['away']} {a_mom}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='record'>({g['a_rec']})</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='margin: 5px 0; color:#555'>@</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='team-name'>{g['home']} {h_mom}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='record'>({g['h_rec']})</div>", unsafe_allow_html=True)
            
        # 2. SPREAD ANALYSIS
        with cols[1]:
            my_spread = round(proj['projected_spread'], 1)
            book_spread = g.get('book_spread', 0)
            
            # Edge logic: If my spread is -6.5 and Book is -8, I have 1.5 pts value on Home
            diff = abs(my_spread - book_spread)
            color = "green-edge" if diff >= 2.0 else "white-edge"
            
            st.markdown(f"""
            <div class='edge-box'>
                <div class='sniper-val {color}'>{my_spread}</div>
                <div class='book-val'>HR: {book_spread}</div>
                <div class='book-val' style='color:{'#00e676' if diff>=2.0 else '#555'}'>Edge: {diff:.1f}</div>
            </div>
            """, unsafe_allow_html=True)

        # 3. TOTAL ANALYSIS
        with cols[2]:
            my_total = round(proj['projected_total'], 1)
            book_total = g.get('book_total', 230)
            
            diff_t = abs(my_total - book_total)
            color_t = "green-edge" if diff_t >= 4.0 else "white-edge"
            
            st.markdown(f"""
            <div class='edge-box'>
                <div class='sniper-val {color_t}'>{my_total}</div>
                <div class='book-val'>HR: {book_total}</div>
                <div class='book-val' style='color:{'#00e676' if diff_t>=4.0 else '#555'}'>Diff: {diff_t:.1f}</div>
            </div>
            """, unsafe_allow_html=True)

        # 4. ACTION
        with cols[3]:
            winner = g['home'] if proj['win_prob'] > 50 else g['away']
            conf = int(proj['win_prob']) if winner == g['home'] else int(100 - proj['win_prob'])
            
            st.markdown("<br>", unsafe_allow_html=True) # Spacer
            if st.button(f"Bet {winner}", key=f"b_{g['home']}"):
                brain.log_transaction(f"{g['away']} @ {g['home']}", winner, "1u")
                st.toast(f"✅ Logged: {winner} ({conf}%)")
            st.caption(f"Conf: {conf}%")

        st.markdown('</div>', unsafe_allow_html=True)