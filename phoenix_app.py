import streamlit as st
import pandas as pd
import itertools
from phoenix_brain import MarketBrain
import market_feed 

# --- CONFIG ---
st.set_page_config(page_title="FOX 7.3: AUTO-FORGE", layout="wide", page_icon="🦊")
brain = MarketBrain()

# --- STYLING (VISUAL SUPREMACY + CRUSHER) ---
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
t1, t2, t3 = st.tabs(["🎯 OPPORTUNITY BOARD", "⚡ AUTO-FORGE (TOP 15)", "🧩 TEASER HUNTER"])

# === TAB 1: OPPORTUNITY BOARD ===
with t1:
    if not market_df.empty:
        # (Standard V7 Logic for brevity - ensuring it runs)
        all_bets = []
        for i, row in market_df.iterrows():
            sharp = row['Global Sharp']
            hero = row['Hard Rock']
            true_prob = brain.calculate_vig_free_prob(sharp)
            kelly_perc = brain.kelly_criterion(true_prob, hero)
            edge_val = kelly_perc if kelly_perc > 0 else (true_prob - brain.get_implied_prob(hero)) * 100
            
            # Financials
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

# === TAB 2: AUTO-FORGE (TOP 15) ===
with t2:
    st.subheader("⚡ AUTO-FORGE: TOP 15 PARLAYS")
    st.markdown("Automatically generating the best **2-Leg** and **3-Leg** combos using Anchors & Fighters.")
    
    if not market_df.empty:
        if st.button("🔨 FORGE TOP 15 SLIPS"):
            with st.spinner("Simulating Combinations..."):
                # 1. CLASSIFY ASSETS
                assets = []
                for i, row in market_df.iterrows():
                    sharp = row['Global Sharp']
                    true_prob = brain.calculate_vig_free_prob(sharp)
                    
                    role = "NEUTRAL"
                    if true_prob > 0.65: role = "ANCHOR"
                    elif brain.kelly_criterion(true_prob, row['Hard Rock']) > 0: role = "FIGHTER"
                    
                    if role != "NEUTRAL":
                        assets.append({
                            "Team": row['Team'], "Odds": row['Hard Rock'], "Prob": true_prob, 
                            "Role": role, "Matchup": row['Matchup']
                        })
                
                # Deduplicate assets
                assets_df = pd.DataFrame(assets).drop_duplicates(subset=['Team'])
                asset_list = assets_df.to_dict('records')
                
                if len(asset_list) < 2:
                    st.warning("Not enough Anchors/Fighters found to build parlays.")
                else:
                    # 2. GENERATE COMBOS
                    combos_2 = list(itertools.combinations(asset_list, 2))
                    combos_3 = list(itertools.combinations(asset_list, 3))
                    all_combos = combos_2 + combos_3
                    
                    scored_parlays = []
                    
                    for combo in all_combos:
                        # Calculate Parlay Math
                        dec_odds = 1.0
                        total_prob = 1.0
                        anchor_count = 0
                        
                        for leg in combo:
                            dec_odds *= brain.convert_american_to_decimal(leg['Odds'])
                            total_prob *= leg['Prob']
                            if leg['Role'] == "ANCHOR": anchor_count += 1
                        
                        final_amer = brain.convert_decimal_to_american(dec_odds)
                        
                        # SCORING ALGORITHM (The Secret Sauce)
                        # We want High Probability AND Decent Edge.
                        # Score = Probability * (Number of Legs) * (Bonus for Anchors)
                        score = total_prob * 100
                        if anchor_count == len(combo): score += 10 # All Anchors = Safety Bonus
                        if len(combo) == 3: score -= 5 # 3-Leg penalty for risk
                        
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
                    
                    for idx, p in enumerate(top_15):
                        # Visuals
                        wager = unit_size * 0.5 # Standard parlay size
                        payout = wager * p['Decimal']
                        profit = payout - wager
                        prob_pct = p['Prob'] * 100
                        meter_col = "#00AAFF" if prob_pct > 50 else "#FFAA00"
                        
                        # Build Leg List HTML
                        legs_html = ""
                        for leg in p['Combo']:
                            badge_class = "badge-anchor" if leg['Role'] == "ANCHOR" else "badge-fighter"
                            icon = "⚓" if leg['Role'] == "ANCHOR" else "⚔️"
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
                                    <span>Implied: {brain.get_implied_prob(p['Odds'])*100:.1f}%</span>
                                </div>
                                <div class='meter-container'><div class='meter-fill' style='width:{prob_pct}%; background-color:{meter_col};'></div></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("Scan Market first.")

# === TAB 3: TEASER HUNTER (V6) ===
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
                    st.markdown(f"<div class='gold-box'><h3>{c['Team']} ({c['Line']})</h3><p>{c['Msg']}</p></div>", unsafe_allow_html=True)
            else:
                st.warning("No Teasers found.")
    else:
        st.info("Select NFL.")