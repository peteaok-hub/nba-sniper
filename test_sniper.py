# NBA SNIPER DIAGNOSTIC TOOL (V2.1 - FORENSIC EDITION)
from nba_brain import get_matchup_projection, get_team_metrics

# REAL RESULTS FROM SUNDAY DEC 14, 2025 (Your "Red Slip" Games)
TEST_CASES = [
    # 1. Pacers (Lost outright as -9.5 fav)
    {"home": "IND", "away": "WAS", "h_score": 89, "a_score": 108, "h_rest": 1, "a_rest": 1},
    
    # 2. Bucks (Lost by 45 as -1.5 fav)
    {"home": "BKN", "away": "MIL", "h_score": 127, "a_score": 82, "h_rest": 1, "a_rest": 1},
    
    # 3. Bulls (Lost outright as -4.5 fav)
    {"home": "CHI", "away": "NOP", "h_score": 104, "a_score": 114, "h_rest": 1, "a_rest": 1},
    
    # 4. Lakers (Won by 2 as -1.0 fav) -> This leg actually HIT for you
    {"home": "PHX", "away": "LAL", "h_score": 114, "a_score": 116, "h_rest": 1, "a_rest": 1},
    
    # 5. Timberwolves (Won by 14 as -10.0 fav) -> Covered
    {"home": "MIN", "away": "SAC", "h_score": 117, "a_score": 103, "h_rest": 1, "a_rest": 1},
]

print("--- \U0001F52C SNIPER V11.4 FORENSIC ANALYSIS ---\n")

correct_picks = 0
total_error = 0

for game in TEST_CASES:
    home = game['home']
    away = game['away']
    
    # 1. Get Metrics
    h_pace, h_tier, h_net = get_team_metrics(home)
    a_pace, a_tier, a_net = get_team_metrics(away)
    
    # 2. Setup Game Data
    game_data = {
        "home": home, "away": away,
        "h_rest": game['h_rest'], "a_rest": game['a_rest'],
        "h_pace": h_pace, "h_tier": h_tier, "h_net": h_net,
        "a_pace": a_pace, "a_tier": a_tier, "a_net": a_net
    }
    
    # 3. Predict
    proj = get_matchup_projection(game_data)
    
    # 4. Compare to Reality
    actual_spread = game['a_score'] - game['h_score'] # + means Away won
    picked_away = proj['projected_spread'] > 0
    actually_away_won = actual_spread > 0
    
    is_correct = (picked_away == actually_away_won)
    if is_correct: correct_picks += 1
    error = abs(proj['projected_spread'] - actual_spread)
    total_error += error
    
    status = "✅ PASS" if is_correct else "❌ FAIL"
    
    print(f"{status} | {away}@{home}")
    print(f"   Sniper Pred: {proj['score_str']} (Spread: {proj['projected_spread']:.1f})")
    print(f"   Actual:      {game['a_score']}-{game['h_score']} (Spread: {actual_spread})")
    print(f"   Net Ratings: {away} ({a_net:.1f}) vs {home} ({h_net:.1f})")
    print("-" * 30)

accuracy = (correct_picks / len(TEST_CASES)) * 100
print(f"\nDIAGNOSTIC ACCURACY: {accuracy:.1f}%")
print("If accuracy is high (>80%), V11.4 is fixed.")
print("If Bucks/Pacers still FAIL, we must manually downgrade them in 'nba_team_stats.csv'.")