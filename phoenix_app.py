import streamlit as st
import pandas as pd
import itertools
from phoenix_brain import MarketBrain
import market_feed 

# --- CONFIG ---
st.set_page_config(page_title="FOX 7.4: AUTO-FORGE", layout="wide", page_icon="🦊")
brain = MarketBrain()

# --- STYLING (THE CRUSHER THEME) ---
st.markdown("""
    <style>
    .stApp {background-color: #0e0e0e; color: #e0e0e0; font-family: 'Roboto', sans-serif;}
    
    /* BOXES */
    .gold-box {border: 2px solid #FFD700; background-color: #1a1a00; padding: 15px; border-radius: 10px; margin-bottom: 10px;}
    .grey-box {border: 1px solid #444; background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 10px; opacity: 0.9;}
    
    /* PARLAY CARD */
    .parlay-card {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        transition: transform 0.2s;
    }
    .parlay-card:hover { transform: translateY(-2px); border-color: #00AAFF; }
    
    /* BADGES */
    .badge-anchor {background-color: #0044cc; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; border: 1px solid #00AAFF;}
    .badge-fighter {background-color: #663300; color: #ffcc99; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; border: 1px solid #FF9900;}
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
    
    /* GENERATE BUTTON */
    .gen-btn { width: 100%; padding: 15px; background-color: #00AAFF; color: white; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.title("🦊 PHOENIX PROTOCOL: AUTO-FORGE")

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
t1, t2, t3 = st.tabs(["⚡ AUTO-FORGE (TOP 15)", "🎯 OPPORTUNITY BOARD", "🧩 TEASER HUNTER"])

# === TAB 1: AUTO-FORGE (THE UPGRADE) ===
with t1:
    st.subheader("⚡ AUTO-FORGE: OPTIMAL PARLAYS")
    st.markdown("Automatically calculates thousands of combinations to find the **Top 15 Highest Value** parlays.")
    
    if not market_df.empty:
        # GENERATE BUTTON
        if st.button("🔨 GENERATE TOP 15 COMBOS", type="primary"):
            with st.spinner("Crunching Math on 10,000+ Combinations..."):
                
                # 1. GATHER ALL ASSETS (Aggressive Collection)
                assets = []
                for i, row in market_df.iterrows():
                    sharp = row['Global Sharp']
                    true_prob = brain.calculate_vig_free_prob(sharp)
                    
                    # Logic: We define roles, but we grab EVERYTHING reasonable (>50% win OR +EV)
                    role = "NEUTRAL"
                    if true_prob > 0.60: role = "ANCHOR"
                    elif brain.kelly_criterion(true_prob, row['Hard Rock']) > 0: role = "FIGHTER"
                    else: role = "FILLER" # Fallback
                    
                    # Only keep if it has SOME merit (Prob > 50% OR Positive Edge)
                    if true_prob > 0.50 or role == "FIGHTER":
                        assets.append({
                            "Team": row['Team'], 
                            "Odds": row['Hard Rock'], 
                            "Prob": true_prob, 
                            "Role": role, 
                            "Matchup": row['Matchup']
                        })
                
                # Deduplicate
                assets_df = pd.DataFrame(assets).sort_values(by='Prob', ascending=False).drop_duplicates(subset=['Team'])
                asset_list = assets_df.to_dict('records')
                
                # SAFETY VALVE: If list is small, take top 8 raw probability teams
                if len(asset_list) < 2:
                    st.warning("Filters too strict. Expanding search...")
                    # (In a real scenario, we'd grab raw rows, but assuming feed has data)
                
                # Limit input to Top 12 Assets to prevent CPU explosion (Permutations get big fast)
                top_assets = asset_list[:12]
                
                # 2. GENERATE PERMUTATIONS
                combos_2 = list(itertools.combinations(top_assets, 2))
                combos_3 = list(itertools.combinations(top_assets, 3))
                all_combos = combos_2 + combos_3
                
                scored_parlays = []
                
                for combo in all_combos:
                    # Math Engine
                    dec_odds = 1.0
                    total_prob = 1.0
                    anchor_count = 0
                    fighter_count = 0
                    
                    for leg in combo:
                        dec_odds *= brain.convert_american_to_decimal(leg['Odds'])
                        total_prob *= leg['Prob']
                        if leg['Role'] == "ANCHOR": anchor_count += 1
                        if leg['Role'] == "FIGHTER": fighter_count += 1
                    
                    final_amer = brain.convert_decimal_to_american(dec_odds)
                    
                    # SCORING (The "Phoenix Score")
                    # We want: High Win Prob + Positive EV.
                    # Simple Score = WinProb * 100 + (Anchor Bonus)
                    score = (total_prob * 100) 
                    if anchor_count == len(combo): score += 15 # Safety Bonus
                    if fighter_count > 0: score += 5 # Value Bonus
                    
                    scored_parlays.append({
                        "Combo": combo,
                        "Odds": final_amer,
                        "Decimal": dec_odds,
                        "Prob": total_prob,
                        "Score": score,
                        "Legs": len(combo)
                    })
                
                # 3. RANK & DISPLAY
                top_15 = sorted(scored_parlays, key=lambda x: x['Score'], reverse=True)[:15]
                
                if not top_15:
                    st.error("No valid combinations found. Try scanning a different league.")
                else:
                    st.success(f"ANALYSIS COMPLETE: Found {len(all_combos)} combos. Showing Top 15.")
                    
                    for idx, p in enumerate(top_15):
                        wager = unit_size * 0.5 
                        payout = wager * p['Decimal']
                        profit = payout - wager
                        prob_pct = p['Prob'] * 100
                        meter_col = "#00AAFF" if prob_pct > 40 else "#FFAA00"
                        
                        # Build HTML
                        legs_html = ""
                        for leg in p['Combo']:
                            badge_class = "badge-anchor" if leg['Role'] == "ANCHOR" else "badge-fighter"
                            icon = "⚓" if leg['Role'] == "ANCHOR" else "⚔️"
                            # Fallback if NEUTRAL
                            if leg['Role'] == "FILLER": 
                                badge_class = "badge-fighter"
                                icon = "🛡️"
                                
                            legs_html += f"""
                            <div style='display:flex; justify-content:space-between; margin-bottom:4px; border-bottom:1px solid #333; padding-bottom:2px;'>
                                <span><span class='{badge_class}'>{icon} {leg['Role']}</span> <b>{leg['Team']}</b></span>
                                <span style='color:#AAA;'>{leg['Odds']}</span>
                            </div>
                            """
                        
                        st.markdown(f"""
                        <div class='parlay-card'>
                            <div style='display:flex; justify-content:space-between; align-items:center;'>
                                <span class='badge-combo'>#{idx+1} | {p['Legs']}-LEG SLIP</span>
                                <span class='big-odds'>{p['Odds']}</span>
                            </div>
                            <hr style='border-color:#333; margin:10px 0;'>
                            {legs_html}
                            <hr style='border-color:#333; margin:10px 0;'>
                            <div class='wager-grid'>
                                <div class='wager-item'><div class='wager-label'>RISK</div><div class='wager-value'>${wager:.2f}</div></div>
                                <div class='wager-item'><div class='wager-label'>PROFIT</div><div class='wager-value'>${profit:.2f}</div></div>
                                <div class='wager-item'><div class='wager-label'>PAYOUT</div><div class='wager-value' style='color:#00AAFF'>${payout:.2f}</div></div>
                            </div>
                            <div style='margin-top:5px;'>
                                <div style='display:flex; justify-content:space-between; font-size:0.8em;'>
                                    <span>Win Probability: {prob_pct:.1f}%</span>
                                </div>
                                <div class='meter-container'><div class='meter-fill' style='width:{prob_pct}%; background-color:{meter_col};'></div></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("Market Data Empty. Click SCAN in Sidebar.")

# === TAB 2: OPPORTUNITY BOARD ===
with t2:
    if not market_df.empty:
        all_bets = []
        for i, row in market_df.iterrows():
            sharp = row['Global Sharp']
            hero = row['Hard Rock']
            true_prob = brain.calculate_vig_free_prob(sharp)
            kelly_perc = brain.kelly_criterion(true_prob, hero)
            edge_val = kelly_perc if kelly_perc > 0 else (true_prob - brain.get_implied_prob(hero)) * 100
            
            bet_dollars = (kelly_perc * 20 / 100) * unit_size if kelly_perc > 0 else unit_size
            final_wager = min(bet_dollars, unit_size)
            dec_odds = brain.convert_american_to_decimal(hero)
            total_payout = final_wager * dec_odds
            net_profit = total_payout - final_wager
            
            all_bets.append({
                "Matchup": row['Matchup'], "Team": row['Team'], "Hard Rock": hero, "Sharp": sharp,
                "Wager": final_wager, "Profit": net_profit, "Payout": total_payout,
                "Prob": true_prob, "Edge": edge_val, "Is_Green": kelly_perc > 0
            })

        bets_df = pd.DataFrame(all_bets).sort_values(by='Edge', ascending=False).drop_duplicates(subset=['Matchup'], keep='first')
        gold_bets = bets_df[bets_df['Is_Green'] == True]
        
        if not gold_bets.empty:
            st.subheader(f"⚡ RECOMMENDED (POSITIVE EV)")
            for i, bet in gold_bets.iterrows():
                prob_pct = bet['Prob'] * 100
                meter_color = "#00AAFF" if prob_pct > 65 else "#00FF00"
                badge = "<span class='badge-anchor'>⚓ ANCHOR</span>" if prob_pct > 65 else "<span class='badge-fighter'>⚔️ FIGHTER</span>"
                
                st.markdown(f"""
                <div class='gold-box'>
                    <div style='display:flex; justify-content:space-between;'><h3>{bet['Team']}</h3>{badge}</div>
                    <div class='wager-grid'>
                        <div class='wager-item'><div class='wager-label'>WAGER</div><div class='wager-value'>${bet['Wager']:.2f}</div></div>
                        <div class='wager-item'><div class='wager-label'>PROFIT</div><div class='wager-value'>${bet['Profit']:.2f}</div></div>
                        <div class='wager-item'><div class='wager-label'>PAYOUT</div><div class='wager-value' style='color:#FFD700'>${bet['Payout']:.2f}</div></div>
                    </div>
                    <div class='meter-container'><div class='meter-fill' style='width:{prob_pct}%; background-color:{meter_color};'></div></div>
                    <p style='font-size:0.8em; color:#888'>Odds: {bet['Hard Rock']} | Edge: {bet['Edge']:.2f}%</p>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No Gold Bets found. Check Auto-Forge.")
    else:
        st.info("Scan Market first.")

# === TAB 3: TEASER HUNTER ===
with t3:
    st.subheader("🧩 AUTOMATED TEASER HUNTER")
    if league_select == "NFL" and not market_df.empty:
        if st.button("🕵️ HUNT TEASERS (Zero Fuel)"):
            candidates = []
            for i, row in market_df.iterrows():
                line = float(row.get('Spread', 0.0))
                if line == 0.0: continue
                side = "Favorite (-)" if line < 0 else "Underdog (+)"
                status, is_valid, msg = brain.validate_teaser(line, 6.0, side)
                if is_valid:
                    candidates.append({"Team": row['Team'], "Line": line, "Status": status, "Msg": msg})
            
            if candidates:
                st.success(f"FOUND {len(candidates)} TEASER CANDIDATES")
                for c in candidates:
                    st.markdown(f"<div class='gold-box'><h3>{c['Team']} (Line: {c['Line']})</h3><p>{c['Msg']}</p></div>", unsafe_allow_html=True)
            else:
                st.warning("No Wong Teasers found.")
    elif league_select != "NFL":
        st.warning("Teasers are an NFL Strategy.")
    else:
        st.info("Scan Market first.")