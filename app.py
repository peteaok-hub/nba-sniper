import streamlit as st
import pandas as pd
import nba_brain as brain
import importlib

# --- BRAIN SHOCK PROTOCOL ---
importlib.reload(brain)
# ---------------------------

st.set_page_config(page_title="SNIPER V6.3", page_icon="🏀", layout="wide")

# STYLES (Hard Rock Dark)
st.markdown("""
<style>
    .stApp { background-color: #0e0e10; color: #e0e0e0; }
    .hr-header { 
        background: linear-gradient(90deg, #6200ea, #b388ff); 
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
    .book-val { font-size: 0.8em; color: #aaa; }
    .odds-sub { font-size: 0.7em; color: #888; }
    .green-edge { color: #00e676; text-shadow: 0 0 5px rgba(0, 230, 118, 0.4); }
    .white-edge { color: #ffffff; }
    div.stButton > button { 
        background-color: #6200ea; color: white; border: none; width: 100%; font-weight: bold;
    }
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
    st.title("🏀 SNIPER V6.3")
    st.caption("Full Odds Integration")
    if st.button("🔄 Refresh"): st.rerun()

# HEADER
st.markdown('<div class="hr-header">HARD ROCK HUNTER BOARD</div>', unsafe_allow_html=True)

# GAME GRID
games = brain.get_todays_games()

c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
c1.caption("MATCHUP & MONEYLINE")
c2.caption("SPREAD (Edge)")
c3.caption("TOTAL (Edge)")
c4.caption("ACTION")

for g in games:
    proj = brain.get_matchup_projection(g['home'], g['away'])
    
    with st.container():
        st.markdown('<div class="game-card">', unsafe_allow_html=True)
        cols = st.columns([1.5, 1, 1, 1])
        
        # 1. MATCHUP & MONEYLINE
        with cols[0]:
            st.markdown(f"**{g['away']}** <span style='color:#aaa'>({g['a_ml']})</span>", unsafe_allow_html=True)
            st.markdown(f"**{g['home']}** <span style='color:#aaa'>({g['h_ml']})</span>", unsafe_allow_html=True)
            st.caption(f"Proj Score: {proj['score_str']}")
            
        # 2. SPREAD
        with cols[1]:
            my_spread = round(proj['projected_spread'], 1)
            book_spread = g['book_spread']
            diff = abs(my_spread - book_spread)
            color = "green-edge" if diff >= 2.0 else "white-edge"
            
            st.markdown(f"""
            <div class='edge-box'>
                <div class='sniper-val {color}'>{my_spread}</div>
                <div class='book-val'>HR: {book_spread}</div>
                <div class='odds-sub'>({g['spread_odds']})</div>
            </div>
            """, unsafe_allow_html=True)

        # 3. TOTAL
        with cols[2]:
            my_total = round(proj['projected_total'], 1)
            book_total = g['book_total']
            diff_t = abs(my_total - book_total)
            color_t = "green-edge" if diff_t >= 4.0 else "white-edge"
            
            st.markdown(f"""
            <div class='edge-box'>
                <div class='sniper-val {color_t}'>{my_total}</div>
                <div class='book-val'>HR: {book_total}</div>
                <div class='odds-sub'>({g['total_odds']})</div>
            </div>
            """, unsafe_allow_html=True)

        # 4. ACTION
        with cols[3]:
            winner = g['home'] if proj['win_prob'] > 50 else g['away']
            conf = int(proj['win_prob']) if winner == g['home'] else int(100 - proj['win_prob'])
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(f"Bet {winner}", key=f"b_{g['home']}"):
                brain.log_transaction(f"{g['away']} @ {g['home']}", winner, "1u")
                st.toast(f"✅ Logged: {winner}")
            st.caption(f"Conf: {conf}%")

        st.markdown('</div>', unsafe_allow_html=True)