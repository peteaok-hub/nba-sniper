import streamlit as st
import pandas as pd
import itertools
from phoenix_brain import MarketBrain
import market_feed 

# --- CONFIG ---
st.set_page_config(page_title="FOX 10.0: SHARP SHOOTER", layout="wide")
brain = MarketBrain()

# --- STYLING (SHARP SHOOTER THEME) ---
st.markdown("""
<style>
    .stApp {background-color: #0e0e12; color: #e0e0ff; font-family: 'Roboto', sans-serif;}
    h1, h2, h3 {color: #ffffff !important; text-shadow: 0 0 10px rgba(0, 229, 255, 0.3);}
    
    /* SIGNAL BOXES */
    .card-greenlight {
        border: 2px solid #39FF14; background-color: #111a11; 
        padding: 15px; border-radius: 10px; margin-bottom: 10px;
        box-shadow: 0 0 20px rgba(57, 255, 20, 0.3);
    }
    .card-trap {
        border: 2px solid #FF0044; background-color: #220a0a; 
        padding: 15px; border-radius: 10px; margin-bottom: 10px;
        box-shadow: 0 0 20px rgba(255, 0, 68, 0.3);
    }
    .card-neutral {
        border: 1px solid #444; background-color: #1a1a20; 
        padding: 15px; border-radius: 10px; margin-bottom: 10px;
    }
    
    /* PARLAY CARD */
    .parlay-card {
        background-color: #13131a; border: 1px solid #333;
        border-radius: 12px; padding: 20px; margin-bottom: 15px;
        border-left: 5px solid #00E5FF;
        box-shadow: 0 0 20px rgba(0,0,0,0.5);
    }
    
    /* BADGES */
    .badge-anchor {background-color: #00E5FF; color: #000; padding: 3px 10px; border-radius: 4px; font-weight: bold;}
    .badge-fighter {background-color: #BD00FF; color: #fff; padding: 3px 10px; border-radius: 4px; font-weight: bold;}
    
    /* METERS */
    .meter-container {background-color: #222; border-radius: 5px; height: 8px; width: 100%; margin-top: 5px;}
    .meter-fill {height: 100%; border-radius: 5px;}
    
    /* TEXT */
    .big-odds {font-size: 2em; font-weight: bold; color: #00E5FF; text-align: right;}
    .wager-grid {display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 10px; background: #0a0a0f; padding: 10px; border-radius: 5px; border: 1px solid #333;}
    .wager-label {color: #aaaadd; font-size: 0.8em;}
    .wager-value {color: #fff; font-weight: bold; font-size: 1.2em;}
    
    /* BUTTONS */
    div.stButton > button {
        width: 100%; padding: 12px; font-weight: bold; border-radius: 8px; border: none;
        background: linear-gradient(90deg, #BD00FF 0%, #00E5FF 100%); color: white;
    }
    
    /* SIGNAL TEXT */
    .signal-text {font-weight:900; letter-spacing:1px; font-size:0.9em; text-transform:uppercase;}
</style>
""", unsafe_allow_html=True)

st.title("FOX 10.0: THE SHARP SHOOTER")

# --- SIDEBAR ---
with st.sidebar:
    st.header("GLOBAL CONFIG")
    league_select = st.radio("Select Market", ["NFL", "NBA"], horizontal=True)
    sport_key = 'americanfootball_nfl' if league_select == "NFL" else 'basketball_nba'
    
    st.markdown("---")
    st.header("SIGNAL LEGEND")
    st.markdown('<div style="color:#39FF14; font-weight:bold;">🟢 GREENLIGHT: Strong Edge (>1.5%)</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#FF0044; font-weight:bold;">🔴 TRAP: Negative EV on Favorite</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.header("MONEY MANAGER")
    unit_size = st.number_input("Standard Unit ($)", value=100.0, step=10.0)
    
    if st.button(f"SCAN {league_select} MARKET"):
        with st.spinner(f"Scanning Global Lines..."):
            df = market_feed.fetch_live_market_data(sport_key)
            if not df.empty:
                df.to_csv("live_market.csv", index=False)
                st.success("DATA UPDATED.")
            else:
                st.error("No active games found.")

try: market_df = pd.read_csv("live_market.csv")
except: market_df = pd.DataFrame()

# PRE-PROCESS
all_options = []
options_df = pd.DataFrame()
clean_options = []

if not market_df.empty:
    for i, row in market_df.iterrows():
        sharp = row['Global Sharp']; true_prob = brain.calculate_vig_free_prob(sharp)
        role = "NEUTRAL"
        if true_prob > 0.60: role = "ANCHOR"
        elif brain.kelly_criterion(true_prob, row['Hard Rock']) > 0: role = "FIGHTER"
        
        if true_prob > 0.45:
            label = f"ANCHOR | {row['Team']}" if role == "ANCHOR" else f"FIGHTER | {row['Team']}"
            all_options.append({"Label": label, "Team": row['Team'], "Odds": row['Hard Rock'], "Prob": true_prob, "Role": role})
    if all_options:
        options_df = pd.DataFrame(all_options).drop_duplicates(subset=['Team'])
        clean_options = options_df.to_dict('records')

# --- TABS ---
t1, t2, t3 = st.tabs(["PARLAY FORGE", "SHARP BOARD", "TEASER HUNTER"])

# === TAB 1: AUTO FORGE ===
with t1:
    st.subheader("PARLAY FORGE")
    if not options_df.empty:
        if st.button("AUTO-FORGE TOP 15 SLIPS", type="primary"):
            auto_assets = [x for x in clean_options if x['Role'] in ['ANCHOR', 'FIGHTER']]
            if len(auto_assets) < 3: auto_assets = clean_options[:10]
            top_assets = auto_assets[:12]
            combos = list(itertools.combinations(top_assets, 2)) + list(itertools.combinations(top_assets, 3))
            scored = []
            for combo in combos:
                dec = 1.0; prob = 1.0; anchors = 0
                for leg in combo:
                    dec *= brain.convert_american_to_decimal(leg['Odds'])
                    prob *= leg['Prob']
                    if leg['Role'] == 'ANCHOR': anchors += 1
                score = (prob * 100) + (anchors * 10)
                scored.append({"Combo": combo, "Odds": brain.convert_decimal_to_american(dec), "Decimal": dec, "Prob": prob, "Score": score, "Legs": len(combo)})
            
            top_15 = sorted(scored, key=lambda x: x['Score'], reverse=True)[:15]
            if top_15:
                st.success(f"FORGED {len(top_15)} OPTIMAL TICKETS")
                for idx, p in enumerate(top_15):
                    wager = unit_size * 0.5; payout = wager * p['Decimal']; profit = payout - wager; prob_pct = p['Prob'] * 100
                    meter_col = "#00E5FF" if prob_pct > 50 else "#BD00FF"
                    legs_html = ""
                    for leg in p['Combo']:
                        badge = "badge-anchor" if leg['Role']=="ANCHOR" else "badge-fighter"
                        icon = "ANCHOR" if leg['Role']=="ANCHOR" else "FIGHTER"
                        legs_html += f"<div style='display:flex; justify-content:space-between; margin-bottom:5px; border-bottom:1px solid #333;'><span><span class='{badge}'>{icon}</span> <b>{leg['Team']}</b></span><span style='color:#aaa;'>{leg['Odds']}</span></div>"
                    
                    st.markdown(f"""
<div class='parlay-card'>
<div style='display:flex; justify-content:space-between;'><span style='color:#fff; font-weight:bold;'>#{idx+1} | {p['Legs']}-LEG SLIP</span><span class='big-odds'>{p['Odds']}</span></div>
<hr style='border-color:#333;'>{legs_html}
<div class='wager-grid'>
<div class='wager-item'><div class='wager-label'>RISK</div><div class='wager-value'>${wager:.2f}</div></div>
<div class='wager-item'><div class='wager-label'>PROFIT</div><div class='wager-value'>${profit:.2f}</div></div>
<div class='wager-item'><div class='wager-label'>PAYOUT</div><div class='wager-value' style='color:#00E5FF'>${payout:.2f}</div></div>
</div>
<div style='margin-top:8px;'><div style='display:flex; justify-content:space-between; font-size:0.8em; color:#fff;'><span>True Win Probability</span><span>{prob_pct:.1f}%</span></div>
<div class='meter-container'><div class='meter-fill' style='width:{prob_pct}%; background-color:{meter_col};'></div></div></div>
</div>""", unsafe_allow_html=True)
            else: st.warning("No combos found.")
            
        st.markdown("---")
        with st.expander("MANUAL BUILDER"):
            selected_labels = st.multiselect("Select Teams:", options_df['Label'].tolist())
            if selected_labels:
                selected_data = []
                for label in selected_labels:
                    row = options_df[options_df['Label'] == label].iloc[0]
                    selected_data.append({"odds": row['Odds'], "prob": row['Prob']})
                final_amer, total_dec, combined_prob = brain.calculate_parlay_math(selected_data)
                wager = unit_size * 0.5; profit = (wager * total_dec) - wager; payout = wager * total_dec; prob_pct = combined_prob * 100
                st.markdown(f"""
<div class='parlay-card' style='border-left: 5px solid #39FF14;'>
<h2 style='text-align: center; color: #39FF14;'>CUSTOM SLIP</h2>
<div class='big-odds' style='color:#39FF14;'>{final_amer}</div>
<div class='wager-grid'>
<div class='wager-item'><div class='wager-label'>RISK</div><div class='wager-value'>${wager:.2f}</div></div>
<div class='wager-item'><div class='wager-label'>PROFIT</div><div class='wager-value'>${profit:.2f}</div></div>
<div class='wager-item'><div class='wager-label'>PAYOUT</div><div class='wager-value' style='color:#39FF14'>${payout:.2f}</div></div>
</div>
<div style='margin-top:10px;'><div style='display:flex; justify-content:space-between; font-size:0.8em; color:#fff;'><span>True Win Probability</span><span>{prob_pct:.1f}%</span></div>
<div class='meter-container'><div class='meter-fill' style='width: {prob_pct}%; background-color: #39FF14;'></div></div></div>
</div>""", unsafe_allow_html=True)
    else: st.info("Scan Market first.")

# === TAB 2: SHARP BOARD (NEW INTELLIGENCE) ===
with t2:
    if not market_df.empty:
        st.subheader("SHARP INTELLIGENCE (EV SCAN)")
        
        bets = []
        for i, row in market_df.iterrows():
            sharp = row['Global Sharp']; hero = row['Hard Rock']
            true_prob = brain.calculate_vig_free_prob(sharp); kelly = brain.kelly_criterion(true_prob, hero)
            
            # GET SIGNAL
            sig_type, sig_col, sig_msg = brain.analyze_sharp_signal(brain.convert_american_to_decimal(hero), brain.convert_american_to_decimal(sharp), kelly)
            
            bets.append({
                "Team": row['Team'], "Odds": hero, "Edge": kelly, 
                "Type": sig_type, "Color": sig_col, "Msg": sig_msg, "Prob": true_prob
            })
            
        # Sort: Greenlights first, then Neutral, then Traps
        # Actually, let's sort by Edge High to Low
        bets_df = pd.DataFrame(bets).sort_values(by='Edge', ascending=False)
        
        for i, row in bets_df.iterrows():
            wager = min((row['Edge']*20/100)*unit_size, unit_size) if row['Edge'] > 0 else 0
            card_class = "card-greenlight" if row['Type'] == "GREENLIGHT" else ("card-trap" if row['Type'] == "TRAP" else "card-neutral")
            prob_pct = row['Prob'] * 100
            
            st.markdown(f"""
<div class='{card_class}'>
<div style='display:flex; justify-content:space-between;'>
    <h3>{row['Team']}</h3>
    <span class='signal-text' style='color:{row['Color']};'>{row['Msg']}</span>
</div>
<div class='wager-grid' style='background:none; border:none;'>
    <div class='wager-item'><div class='wager-label'>WAGER</div><div class='wager-value'>${wager:.2f}</div></div>
    <div class='wager-item'><div class='wager-label'>EDGE</div><div class='wager-value' style='color:{row['Color']}'>{row['Edge']:.2f}%</div></div>
    <div class='wager-item'><div class='wager-label'>ODDS</div><div class='wager-value' style='color:#fff'>{row['Odds']}</div></div>
</div>
<div style='margin-top:8px;'>
<div style='display:flex; justify-content:space-between; font-size:0.8em; color:#aaa;'><span>True Win Probability</span><span>{prob_pct:.1f}%</span></div>
<div class='meter-container'><div class='meter-fill' style='width:{prob_pct}%; background-color:{row['Color']};'></div></div>
</div>
</div>""", unsafe_allow_html=True)
    else: st.info("Scan Market first.")

# === TAB 3: TEASER HUNTER ===
with t3:
    st.subheader("TEASER HUNTER")
    if league_select == "NFL" and not market_df.empty:
        if st.button("HUNT TEASERS"):
            candidates = []
            for i, row in market_df.iterrows():
                try: line = float(row.get('Spread', 0.0))
                except: line = 0.0
                if line == 0.0: continue
                side = "Fav" if line < 0 else "Dog"
                status, valid, msg = brain.validate_teaser(line, 6.0, side)
                if valid: candidates.append({"Team":row['Team'], "Line":line, "Msg":msg, "Status":status})
            
            if candidates:
                st.success(f"FOUND {len(candidates)} TEASER CANDIDATES")
                for c in candidates:
                    st.markdown(f"""
<div class='gold-box' style='border-color:#00E5FF;'>
<div style='display:flex; justify-content:space-between;'><h3 style='color:#00E5FF !important;'>{c['Team']} (Line: {c['Line']})</h3><span class='badge-teaser'>WONG</span></div>
<p><b style='color:#39FF14;'>{c['Status']}</b></p>
<p style='color:#aaaadd;'>{c['Msg']}</p>
</div>""", unsafe_allow_html=True)
            else: st.warning("No Teasers found.")
    elif league_select != "NFL": st.warning("Teasers are an NFL Strategy.")
    else: st.info("Scan Market first.")
