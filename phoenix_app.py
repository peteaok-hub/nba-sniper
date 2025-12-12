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
        # 1. IDENTIFY CANDIDATES (Aggressive Wong Logic)
        candidates = []
        for i, row in market_df.iterrows():
            # Fallback: If 'Spread' column missing, try to infer or skip
            try:
                line = float(row.get('Spread', 0.0))
            except:
                line = 0.0
            
            if line == 0.0: continue
            
            side = "Favorite (-)" if line < 0 else "Underdog (+)"
            teased_line = line + 6.0 if line < 0 else line + 6.0
            
            # Wong Criteria Check (Strict)
            is_wong = False
            # Favorites: -7.5 to -8.5
            if side == "Favorite (-)" and -8.9 <= line <= -7.1: is_wong = True 
            # Underdogs: +1.5 to +2.5
            if side == "Underdog (+)" and 1.1 <= line <= 2.9: is_wong = True 
            
            # Expanded Criteria (If Strict fails, capture near-misses for volume)
            # Favorites: -7 to -9
            # Underdogs: +1 to +3
            is_expanded = False
            if side == "Favorite (-)" and -9.5 <= line <= -6.5: is_expanded = True
            if side == "Underdog (+)" and 0.5 <= line <= 3.5: is_expanded = True

            # Add to list if it meets EITHER criteria
            if is_wong or is_expanded:
                candidates.append({
                    "Team": row['Team'],
                    "Line": line,
                    "Teased": teased_line,
                    "Matchup": row['Matchup'],
                    "Tier": "GOLD" if is_wong else "SILVER"
                })
        
        # Remove duplicates (sometimes feed has multiple lines for same game)
        # Convert list of dicts to dataframe to drop duplicates, then back to list
        if candidates:
            cand_df = pd.DataFrame(candidates).drop_duplicates(subset=['Team'])
            candidates = cand_df.to_dict('records')

        if len(candidates) < 2:
            st.warning(f"Found {len(candidates)} Teaser Candidates. Need at least 2 to build parlays.")
            st.write("Current Candidates:", candidates)
        else:
            # 2. GENERATE COMBOS (Top 15)
            st.markdown(f"<div class='crusher-header'>TOP TEASER COMBINATIONS ({len(candidates)} TEAMS)</div>", unsafe_allow_html=True)
            
            # Generate 2-Team Combos
            combos_2 = list(itertools.combinations(candidates, 2))
            # Generate 3-Team Combos (only if we have enough candidates)
            combos_3 = list(itertools.combinations(candidates, 3)) if len(candidates) >= 3 else []
            
            all_combos = combos_2 + combos_3
            
            # Sort by Quality (Prioritize Gold Tiers)
            # We give a score: Gold = 2 pts, Silver = 1 pt. Higher score = Better combo.
            def get_combo_score(combo):
                score = 0
                for leg in combo:
                    score += 2 if leg['Tier'] == "GOLD" else 1
                return score

            sorted_combos = sorted(all_combos, key=get_combo_score, reverse=True)
            
            # Limit to 15
            top_15 = sorted_combos[:15]
            
            for idx, combo in enumerate(top_15):
                # Calculate metrics
                num_legs = len(combo)
                odds_str = "-120" if num_legs == 2 else "+160" 
                payout_mult = 1.83 if num_legs == 2 else 2.6
                
                profit = (unit_size * payout_mult) - unit_size
                
                # Confidence visual based on Tier
                gold_legs = sum(1 for leg in combo if leg['Tier'] == 'GOLD')
                conf_pct = 60 + (gold_legs * 10) 
                if conf_pct > 95: conf_pct = 95
                
                # Build Team List HTML
                legs_html = ""
                for leg in combo:
                    icon = "🥇" if leg['Tier'] == "GOLD" else "🥈"
                    legs_html += f"""
                    <div style='display:flex; justify-content:space-between; margin-bottom:5px; border-bottom:1px solid #333; padding-bottom:5px;'>
                        <span style='color:white; font-weight:bold;'>{icon} {leg['Team']}</span>
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

    elif league_select != "NFL":
        st.warning("Teasers are primarily an NFL Strategy. Please switch league to NFL.")
    else:
        st.info("Please Scan Market to initialize data.")

# === TAB 2: OPPORTUNITY BOARD (Standard) ===
with t2:
    if not market_df.empty:
        st.dataframe(market_df)
    else:
        st.info("Scan Market first.")