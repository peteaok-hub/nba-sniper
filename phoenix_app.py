import streamlit as st
import pandas as pd
import itertools
from phoenix_brain import MarketBrain
import market_feed 

# --- CONFIG ---
st.set_page_config(page_title="FOX 7.2: TEASER OPTIMIZER", layout="wide", page_icon="🦊")
brain = MarketBrain()

# --- STYLING (THE CRUSHER THEME) ---
st.markdown("""
    <style>
    .stApp {background-color: #0e0e0e; color: #e0e0e0; font-family: 'Roboto', sans-serif;}
    
    /* HEADERS */
    .crusher-header {
        background: linear-gradient(90deg, #cc0000 0%, #ff3333 100%);
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 20px;
        color: white;
        box-shadow: 0 4px 15px rgba(255, 0, 0, 0.3);
    }
    
    /* CARDS */
    .crusher-card {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        transition: transform 0.2s;
    }
    .crusher-card:hover { transform: translateY(-2px); border-color: #555; }
    
    /* METRICS */
    .stat-box {
        background-color: #252525;
        border-radius: 6px;
        padding: 10px;
        text-align: center;
        border-left: 3px solid #cc0000;
    }
    .stat-label { font-size: 0.7em; color: #888; text-transform: uppercase; }
    .stat-value { font-size: 1.1em; font-weight: bold; color: white; }
    
    /* BAR */
    .conf-bar-bg { background-color: #333; height: 6px; border-radius: 3px; margin-top: 8px; }
    .conf-bar-fill { height: 100%; border-radius: 3px; background: linear-gradient(90deg, #00ccff, #ffffff); }
    
    /* BUTTON */
    .bet-btn {
        background-color: #333;
        color: white;
        padding: 8px 20px;
        border-radius: 6px;
        text-align: center;
        font-weight: bold;
        border: 1px solid #555;
        cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🦊 PHOENIX PROTOCOL: TEASER OPTIMIZER")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ GLOBAL CONFIG")
    league_select = st.radio("Select Market", ["NFL", "NBA"], horizontal=True)
    sport_key = 'americanfootball_nfl' if league_select == "NFL" else 'basketball_nba'
    
    st.markdown("---")
    st.header("💰 MONEY MANAGER")
    unit_size = st.number_input("Standard Unit ($)", value=100.0, step=10.0)
    
    if st.button(f"🔄 SCAN {league_select} MARKET"):
        with st.spinner(f"Scanning Global Lines..."):
            df = market_feed.fetch_live_market_data(sport_key)
            if not df.empty:
                df.to_csv("live_market.csv", index=False)
                st.success("DATA UPDATED.")
            else:
                st.error("No active games found.")

# --- LOAD DATA ---
try:
    market_df = pd.read_csv("live_market.csv")
except:
    market_df = pd.DataFrame()

# --- TABS ---
t1, t2 = st.tabs(["🧩 TEASER OPTIMIZER", "🎯 OPPORTUNITY BOARD"])

# === TAB 1: TEASER OPTIMIZER ===
with t1:
    if league_select == "NFL" and not market_df.empty:
        # 1. IDENTIFY CANDIDATES (Wong Logic)
        candidates = []
        for i, row in market_df.iterrows():
            line = row.get('Spread', 0.0) 
            if line == 0.0: continue
            
            side = "Favorite (-)" if line < 0 else "Underdog (+)"
            # Tease 6 points
            teased_line = line + 6.0 if line < 0 else line + 6.0
            
            # Wong Criteria Check
            is_wong = False
            if side == "Favorite (-)" and -8.5 <= line <= -7.5: is_wong = True # Crosses -7, -3
            if side == "Underdog (+)" and 1.5 <= line <= 2.5: is_wong = True # Crosses +3, +7
            
            if is_wong:
                candidates.append({
                    "Team": row['Team'],
                    "Line": line,
                    "Teased": teased_line,
                    "Matchup": row['Matchup']
                })
        
        if len(candidates) < 2:
            st.warning(f"Found {len(candidates)} Wong Candidates. Need at least 2 to build parlays.")
            if candidates: st.write(candidates)
        else:
            # 2. GENERATE COMBOS (Top 15)
            st.markdown(f"<div class='crusher-header'>TOP 15 TEASER COMBINATIONS ({len(candidates)} TEAMS FOUND)</div>", unsafe_allow_html=True)
            
            # Generate 2-Team and 3-Team Combos
            combos_2 = list(itertools.combinations(candidates, 2))
            combos_3 = list(itertools.combinations(candidates, 3))
            all_combos = combos_2 + combos_3
            
            # Limit to 15 for display
            top_15 = all_combos[:15]
            
            for idx, combo in enumerate(top_15):
                # Calculate metrics (Simplified for MVP)
                num_legs = len(combo)
                # Standard Teaser Odds: 2-Team (-120), 3-Team (+160)
                odds_str = "-120" if num_legs == 2 else "+160" 
                payout_mult = 1.83 if num_legs == 2 else 2.6
                
                profit = (unit_size * payout_mult) - unit_size
                conf_pct = 75 - (idx * 2) # Mock confidence for display sort
                
                # Build Team List HTML
                legs_html = ""
                for leg in combo:
                    legs_html += f"""
                    <div style='display:flex; justify-content:space-between; margin-bottom:5px; border-bottom:1px solid #333; padding-bottom:5px;'>
                        <span style='color:white; font-weight:bold;'>{leg['Team']}</span>
                        <span style='color:#00ccff;'>{leg['Line']} ➔ {leg['Teased']}</span>
                    </div>
                    """
                
                # RENDER CARD
                st.markdown(f"""
                <div class='crusher-card'>
                    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
                        <span style='color:#cc0000; font-weight:bold; font-size:1.2em;'>COMBO #{idx+1} ({num_legs}-LEG)</span>
                        <div class='bet-btn'>{odds_str}</div>
                    </div>
                    
                    {legs_html}
                    
                    <div style='display:flex; justify-content:space-between; margin-top:15px;'>
                        <div class='stat-box' style='width:30%;'>
                            <div class='stat-label'>RISK</div>
                            <div class='stat-value'>${unit_size:.0f}</div>
                        </div>
                        <div class='stat-box' style='width:30%;'>
                            <div class='stat-label'>PROFIT</div>
                            <div class='stat-value'>${profit:.2f}</div>
                        </div>
                        <div class='stat-box' style='width:30%;'>
                            <div class='stat-label'>CONFIDENCE</div>
                            <div class='stat-value'>{conf_pct}%</div>
                        </div>
                    </div>
                    
                    <div class='conf-bar-bg'>
                        <div class='conf-bar-fill' style='width: {conf_pct}%;'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    else:
        st.info("Please Select NFL and Scan Market.")

# === TAB 2: OPPORTUNITY BOARD (Standard) ===
with t2:
    if not market_df.empty:
        # Simple display for context
        st.dataframe(market_df)
    else:
        st.info("Scan Market first.")