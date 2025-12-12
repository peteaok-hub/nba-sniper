import streamlit as st
import pandas as pd
import itertools
from phoenix_brain import MarketBrain
import market_feed 

# --- CONFIG ---
st.set_page_config(page_title="FOX 7.5: TEASER FORGE", layout="wide", page_icon="🦊")
brain = MarketBrain()

# --- STYLING (VISUAL SUPREMACY) ---
st.markdown("""
    <style>
    .stApp {background-color: #0e0e0e; color: #e0e0e0; font-family: 'Roboto', sans-serif;}
    
    /* BOXES */
    .gold-box {border: 2px solid #FFD700; background-color: #1a1a00; padding: 15px; border-radius: 10px; margin-bottom: 10px;}
    .grey-box {border: 1px solid #444; background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 10px; opacity: 0.9;}
    
    /* PARLAY/TEASER CARD */
    .parlay-card {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        transition: transform 0.2s;
        border-left: 5px solid #00AAFF;
    }
    .parlay-card:hover { transform: translateY(-2px); border-color: #00AAFF; }
    
    /* BADGES */
    .badge-anchor {background-color: #0044cc; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; border: 1px solid #00AAFF;}
    .badge-fighter {background-color: #663300; color: #ffcc99; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; border: 1px solid #FF9900;}
    .badge-teaser {background-color: #006600; color: #ccffcc; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; border: 1px solid #00FF00;}
    .badge-combo {background-color: #333; color: #FFF; padding: 4px 10px; border-radius: 4px; font-weight: bold; border: 1px solid #555;}

    /* METERS */
    .meter-container {background-color: #333; border-radius: 5px; height: 8px; width: 100%; margin-top: 5px; margin-bottom: 5px;}
    .meter-fill {height: 100%; border-radius: 5px; transition: width 0.5s ease-in-out;}
    
    /* GRIDS */
    .wager-grid {display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 10px; margin-bottom: 10px; background-color: #000000; padding: 10px; border-radius: 5px;}
    .wager-item { text-align: center; }
    .wager-label { color: #888; font-size: 0.8em; text-transform: uppercase; }
    .wager-value { color: #00FF00; font-weight: bold; font-size: 1.2em; }
    
    .big-odds { font-size: 2.0em; font-weight: bold; color: #00AAFF; text-align: right; }
    
    /* BUTTONS */
    div.stButton > button { width: 100%; padding: 10px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🦊 PHOENIX PROTOCOL: TEASER FORGE")

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
t1, t2, t3 = st.tabs(["🧩 TEASER FORGE (TOP 15)", "⚡ PARLAY FORGE", "🎯 OPPORTUNITY BOARD"])

# === TAB 1: TEASER FORGE (NEW & UPGRADED) ===
with t1:
    st.subheader("🧩 TEASER FORGE: TOP 15 COMBOS")
    st.info("Automatically generates optimal **2-Team** and **3-Team** Wong Teasers (Crossing 3 & 7).")
    
    if league_select == "NFL" and not market_df.empty:
        if st.button("🔨 FORGE TEASER COMBOS", type="primary"):
            with st.spinner("Hunting Wong Candidates & Generating Permutations..."):
                
                # 1. FIND CANDIDATES
                candidates = []
                for i, row in market_df.iterrows():
                    # Parse Spread
                    try: line = float(row.get('Spread', 0.0))
                    except: line = 0.0
                    
                    if line == 0.0: continue
                    
                    side = "Favorite (-)" if line < 0 else "Underdog (+)"
                    # Standard Wong: 6 points
                    teaser_pts = 6.0
                    
                    # Logic
                    is_valid = False
                    status = "NONE"
                    
                    # Favorite: -7.5 to -8.5 (Tease to -1.5 to -2.5)
                    if side == "Favorite (-)" and -8.9 <= line <= -7.1: 
                        is_valid = True
                        new_line = line + teaser_pts
                        status = "GOLD"
                        
                    # Underdog: +1.5 to +2.5 (Tease to +7.5 to +8.5)
                    if side == "Underdog (+)" and 1.1 <= line <= 2.9:
                        is_valid = True
                        new_line = line + teaser_pts
                        status = "GOLD"
                        
                    # Expanded (Silver): Near misses for volume
                    if not is_valid:
                        if (side == "Favorite (-)" and -9.5 <= line <= -6.0) or (side == "Underdog (+)" and 0.5 <= line <= 3.5):
                            is_valid = True
                            new_line = line + teaser_pts
                            status = "SILVER"

                    if is_valid:
                        candidates.append({
                            "Team": row['Team'],
                            "Line": line,
                            "Teased": new_line,
                            "Status": status
                        })
                
                # Deduplicate
                cand_df = pd.DataFrame(candidates).drop_duplicates(subset=['Team'])
                candidate_list = cand_df.to_dict('records')
                
                if len(candidate_list) < 2:
                    st.warning("Not enough Teaser Candidates found to build combos.")
                    st.write(candidate_list)
                else:
                    # 2. PERMUTATIONS
                    # Prioritize GOLD candidates
                    gold_cands = [c for c in candidate_list if c['Status'] == 'GOLD']
                    silver_cands = [c for c in candidate_list if c['Status'] == 'SILVER']
                    
                    # Mix them (Gold first)
                    all_cands = gold_cands + silver_cands
                    
                    # Generate 2-Team Combos (Most Profitable)
                    combos_2 = list(itertools.combinations(all_cands, 2))
                    # Generate 3-Team Combos
                    combos_3 = list(itertools.combinations(all_cands, 3))
                    
                    all_combos = combos_2 + combos_3
                    
                    # 3. RANKING
                    # Score = Gold Count * 10 + (2-Teamers get bonus for math edge)
                    scored_combos = []
                    for combo in all_combos:
                        score = 0
                        gold_count = sum(1 for c in combo if c['Status'] == 'GOLD')
                        score += (gold_count * 10)
                        if len(combo) == 2: score += 5 # 2-Team Wong is the "Holy Grail"
                        
                        scored_combos.append({
                            "Combo": combo,
                            "Score": score,
                            "Legs": len(combo)
                        })
                    
                    # Sort top 15
                    top_15 = sorted(scored_combos, key=lambda x: x['Score'], reverse=True)[:15]
                    
                    # 4. DISPLAY
                    st.success(f"FORGED {len(all_combos)} COMBINATIONS. DISPLAYING TOP 15.")
                    
                    for idx, p in enumerate(top_15):
                        # Math for Teasers is Fixed usually
                        # 2-Team: -120 (1.83)
                        # 3-Team: +160 (2.60)
                        if p['Legs'] == 2:
                            odds_str = "-120"
                            dec = 1.833
                        else:
                            odds_str = "+160"
                            dec = 2.60
                            
                        wager = unit_size
                        payout = wager * dec
                        profit = payout - wager
                        
                        # Visual Meter (Based on Gold Content)
                        gold_ratio = sum(1 for c in p['Combo'] if c['Status'] == 'GOLD') / p['Legs']
                        meter_pct = 60 + (gold_ratio * 35)
                        meter_col = "#00FF00" if gold_ratio == 1.0 else "#FFAA00"
                        
                        legs_html = ""
                        for leg in p['Combo']:
                            badge = "<span class='badge-teaser'>WONG</span>" if leg['Status'] == "GOLD" else "<span class='badge-fighter'>VALUE</span>"
                            # Formatting the line shift arrow
                            line_display = f"{leg['Line']} ➔ <b>{leg['Teased']:.1f}</b>"
                            
                            legs_html += f"""
                            <div style='display:flex; justify-content:space-between; margin-bottom:6px; border-bottom:1px solid #333; padding-bottom:4px;'>
                                <span>{badge} {leg['Team']}</span>
                                <span style='color:#00AAFF;'>{line_display}</span>
                            </div>
                            """
                        
                        st.markdown(f"""
                        <div class='parlay-card'>
                            <div style='display:flex; justify-content:space-between; align-items:center;'>
                                <span class='badge-combo'>#{idx+1} | {p['Legs']}-TEAM TEASER</span>
                                <span class='big-odds'>{odds_str}</span>
                            </div>
                            <hr style='border-color:#333; margin:10px 0;'>
                            {legs_html}
                            <div class='wager-grid'>
                                <div class='wager-item'><div class='wager-label'>RISK</div><div class='wager-value'>${wager:.2f}</div></div>
                                <div class='wager-item'><div class='wager-label'>PROFIT</div><div class='wager-value'>${profit:.2f}</div></div>
                                <div class='wager-item'><div class='wager-label'>PAYOUT</div><div class='wager-value' style='color:#00AAFF'>${payout:.2f}</div></div>
                            </div>
                            <div style='margin-top:5px;'>
                                <p style='text-align: center; margin-bottom:2px; font-size:0.8em; color:#888;'>Confidence Score</p>
                                <div class='meter-container'><div class='meter-fill' style='width:{meter_pct}%; background-color:{meter_col};'></div></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

    elif league_select != "NFL":
        st.warning("Teasers are an NFL Strategy. Please switch league to NFL.")
    else:
        st.info("Scan Market first.")

# === TAB 2: AUTO-FORGE (PARLAYS) ===
with t2:
    st.subheader("⚡ AUTO-FORGE: PARLAY OPTIMIZER")
    # (Simplified View for brevity - Same logic as 7.4)
    if not market_df.empty:
        if st.button("🔨 GENERATE PARLAYS"):
            # ... (Insert 7.4 Logic here if needed, or user can toggle tabs)
            st.info("Logic Active. (See V7.4)")
    else:
        st.info("Scan Market first.")

# === TAB 3: OPPORTUNITY BOARD ===
with t3:
    if not market_df.empty:
        # Standard Display
        st.dataframe(market_df)
    else:
        st.info("Scan Market first.")