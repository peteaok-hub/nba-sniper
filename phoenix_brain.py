import pandas as pd
import numpy as np

class MarketBrain:
    def __init__(self):
        self.key_numbers = [3, 7]

    def convert_american_to_decimal(self, odds):
        if pd.isna(odds) or odds == 0: return 0.0
        if odds > 0:
            return 1 + (odds / 100)
        else:
            return 1 + (100 / abs(odds))

    def convert_decimal_to_american(self, decimal_odds):
        if decimal_odds <= 1: return -10000
        if decimal_odds >= 2.00:
            return round((decimal_odds - 1) * 100)
        else:
            return round(-100 / (decimal_odds - 1))

    def get_implied_prob(self, odds):
        if pd.isna(odds) or odds == 0: return 0.0
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)

    def calculate_vig_free_prob(self, odds):
        return self.get_implied_prob(odds)

    def calculate_parlay_math(self, selected_bets):
        if not selected_bets: return 0, 0, 0
        total_decimal = 1.0
        combined_prob = 1.0
        
        for bet in selected_bets:
            dec = self.convert_american_to_decimal(bet['odds'])
            total_decimal *= dec
            combined_prob *= bet['prob']
            
        final_american = self.convert_decimal_to_american(total_decimal)
        return final_american, total_decimal, combined_prob

    def kelly_criterion(self, true_prob, hero_odds, fractional_kelly=0.5):
        if hero_odds == 0: return 0
        if hero_odds > 0:
            b = hero_odds / 100
        else:
            b = 100 / abs(hero_odds)
        
        p = true_prob
        q = 1 - p
        
        if b == 0: return 0
        f_star = ((b * p) - q) / b
        return max(0.0, round(f_star * fractional_kelly * 100, 2))

    # --- NEW: SHARP SHOOTER LOGIC ---
    def analyze_sharp_signal(self, hero_odds, sharp_odds, kelly_edge):
        # 1. TRAP DETECTION (Negative EV on a Favorite)
        if kelly_edge <= 0 and (hero_odds < -150):
            return "TRAP", "#FF0044", "TRAP DETECTED: EXPENSIVE FAVORITE"
        
        # 2. GREENLIGHT (Significant Edge vs Sharp)
        # If Hero gives better odds than Sharp by a margin
        hero_prob = self.get_implied_prob(hero_odds)
        sharp_prob = self.get_implied_prob(sharp_odds)
        
        if kelly_edge > 1.5:
            return "GREENLIGHT", "#39FF14", "SHARP APPROVED: HIGH VALUE"
            
        if kelly_edge > 0:
            return "PLAYABLE", "#00E5FF", "POSITIVE EV"

        return "NO_PLAY", "#555", "NO EDGE"

    def validate_teaser(self, line, teaser_points, side):
        if "Fav" in side or "-" in side:
            spread = -abs(line) 
            if -8.9 <= spread <= -7.1:
                return "GOLD: ELITE VALUE", True, f"Perfect. Crosses 3 & 7."
            if -9.5 <= spread <= -6.0:
                 return "SILVER: SOLID VALUE", True, f"Good Play."

        if "Dog" in side or "+" in side:
            spread = abs(line)
            if 1.1 <= spread <= 2.9:
                return "GOLD: ELITE VALUE", True, f"Perfect. Crosses 3 & 7."
            if 0.5 <= spread <= 3.5:
                 return "SILVER: SOLID VALUE", True, f"Good Play."

        return "NO EDGE", False, "No key numbers."