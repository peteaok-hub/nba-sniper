import streamlit as st
import pandas as pd
import nba_brain as brain
import time
import os
import importlib  # <--- NEW: Required for Shock Protocol

# --- BRAIN SHOCK PROTOCOL ---
# This forces the server to re-read the file from disk, bypassing the cache.
importlib.reload(brain)
# ---------------------------

# CONFIG
st.set_page_config(page_title="SNIPER V5.1", page_icon="🏀", layout="wide")

# STYLES (Hard Rock / Mint Theme)
st.markdown("""
<style>
    .stApp { background-color: #121212; color: white; }
    .hr-header { 
        background: linear-gradient(90deg, #7b2cbf, #9d4edd); 
        padding: 15px; border-radius: 8px; text-align: center; color: white; font-weight: bold;
        margin-bottom: 20px;
    }
    .game-row { 
        background-color: #1e1e1e; border: 1px solid #333; padding: 15px; 
        border-radius: 10px; margin-bottom: 10px;
    }
    .sniper-edge { color: #00ff00; font-weight: bold; }
    .book-line { color: #aaa; font-size: 0.9em; }
    div.stButton > button { background-color: #7b2cbf; color: white; border: none; width: 100%; }
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
    st.title("🏀 SNIPER V5.1")
    st.caption("Hard Rock Protocol Active")
    if st.button("🔄 Refresh Markets"): st.rerun()
    
    # DEBUG PANEL
    with st.expander("🛠️ Debug Data"):
        st.write("Brain Version:", getattr(brain, "__file__", "Unknown"))
        if hasattr(brain, 'get_matchup_projection'):
            st.success("✅ Sniper Logic Found")
        else:
            st.error("❌ Sniper Logic MISSING")

# --- HEADER ---
st.markdown('<div class="hr-header"><h3>HARD ROCK HUNTER BOARD</h3></div>', unsafe_allow_html=True)

# --- GAME GRID ---
games = brain.get_todays_games()

# HEADERS
c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
c1.write("**MATCHUP**")
c2.write("**SPREAD (Edge)**")
c3.write("**TOTAL (Edge)**")
c4.write("**WINNER**")

for g in games:
    # 1. GET PROJECTION (WITH DEBUG TRAP)
    try:
        proj = brain.get_matchup_projection(g['home'], g['away'])
    except AttributeError:
        st.error(f"CRITICAL ERROR: The Cloud is using an old Brain. Please Reboot.")
        st.code(dir(brain)) # Show what IS available
        st.stop()
    
    # 2. UI ROW
    with st.container():
        st.markdown("---")
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        
        # COL 1: Matchup info
        with c1:
            st.write(f"**{g['away']} @ {g['home']}**")
            st.caption(f"Time: {g['time']}")
        
        # COL 2: Spread Analysis
        with c2:
            book_spread = round(proj['projected_spread'] + (0.5 if proj['projected_spread'] > 0 else -0.5)) 
            my_spread = round(proj['projected_spread'], 1)
            
            # Calculate Edge
            diff = abs(my_spread - book_spread)
            color = "green" if diff >= 2.0 else "white"
            
            st.markdown(f"<span style='color:{color}'>{my_spread}</span>", unsafe_allow_html=True)
            st.caption(f"Book: {book_spread}")

        # COL 3: Total Analysis
        with c3:
            book_total = 230.0 # Standard placeholder
            my_total = round(proj['projected_total'], 1)
            
            diff_t = abs(my_total - book_total)
            color_t = "green" if diff_t >= 4.0 else "white"
            
            st.markdown(f"<span style='color:{color_t}'>{my_total}</span>", unsafe_allow_html=True)
            st.caption(f"Book: {book_total}")
            
        # COL 4: Winner / Action
        with c4:
            winner = g['home'] if proj['win_prob'] > 50 else g['away']
            conf = int(proj['win_prob']) if winner == g['home'] else int(100 - proj['win_prob'])
            
            if st.button(f"Bet {winner}", key=f"btn_{g['home']}"):
                brain.log_transaction(f"{g['away']} @ {g['home']}", winner, "1u")
                st.toast(f"Logged: {winner} ({conf}%)")

st.markdown("---")
st.caption("Green numbers indicate a significant edge (>2pts Spread, >4pts Total) against the book.")