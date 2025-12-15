# UNIVERSAL TRAP PROTOCOL V1.0
# "THE GHOST IN THE MACHINE"
# Purpose: Manually adjust statistical models to account for intangibles 
# (momentum, locker room issues, injuries) that raw stats miss.

class TrapProtocol:
    def __init__(self, sport="NBA"):
        self.sport = sport.upper()
        self.bias_map = {}
        self.load_defaults()

    def load_defaults(self):
        """
        Loads the current 'Trap List' based on the sport.
        NEGATIVE value = PUNISHMENT (Team is a Trap/Choking).
        POSITIVE value = BONUS (Team is undervalued/Fighting).
        """
        self.bias_map = {}
        
        if self.sport == "NBA":
            # Current NBA Trap List (from Sniper V11.7)
            self.bias_map = {
                "MIL": -8.0,  # Bucks are broken
                "IND": -6.0,  # Pacers choke vs bad teams
                "CHI": -4.0,  # Bulls inconsistent
                "PHX": -2.0,  # Suns sliding
                "LAL": 1.0,   # Lakers fighting hard
                "MIN": 1.0    # Wolves solid
            }
            
        elif self.sport == "NFL":
            # Example NFL Logic
            self.bias_map = {
                "KC": 3.0,    # Mahomes Factor: Always add +3 to stats
                "NYJ": -4.0,  # Dysfunctional tax
                "DAL": -2.5   # "Choke" tax in big games
            }
            
        elif self.sport == "MLB":
            # Example MLB Logic
            self.bias_map = {
                "NYY": -1.5,  # Bullpen tax (example)
                "OAK": 2.0    # If they are winning, it's real (Value)
            }

    def set_bias(self, team, value):
        """Manually update a team's bias setting."""
        self.bias_map[team] = value
        print(f"[{self.sport}] TRAP SET: {team} adjustment is now {value}")

    def get_bias(self, team):
        """Returns the bias adjustment for a team (default 0)."""
        return self.bias_map.get(team, 0.0)

    def apply_correction(self, team, raw_rating):
        """
        Takes a raw statistical rating and applies the Trap Protocol.
        Returns: (Adjusted Rating, Status Message)
        """
        bias = self.get_bias(team)
        adjusted_rating = raw_rating + bias
        
        status = "NEUTRAL"
        if bias < -5.0: status = "⛔ CRITICAL TRAP"
        elif bias < 0:  status = "⚠️ CAUTION"
        elif bias > 0:  status = "🔥 VALUE BOOST"
        
        return adjusted_rating, status

# --- USAGE EXAMPLE ---
if __name__ == "__main__":
    # Test the protocol independently
    print("--- TRAP PROTOCOL TEST ---")
    
    # Initialize for NFL
    nfl_traps = TrapProtocol("NFL")
    
    # Scenario: Kansas City stats say they are an "85" rating
    kc_raw = 85.0
    kc_final, status = nfl_traps.apply_correction("KC", kc_raw)
    
    print(f"Team: KC | Raw Stats: {kc_raw} | Trap Adj: {nfl_traps.get_bias('KC')}")
    print(f"Final Rating: {kc_final} ({status})")