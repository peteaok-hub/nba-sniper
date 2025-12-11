# NBA SNIPER DATA FEED (ESPN HOLLINGER + SCHEDULE AUTOMATION)
# STATUS: AUTOMATED SCRAPER V12.0
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta

# CONFIG
HOLLINGER_URL = "http://insider.espn.com/nba/hollinger/statistics"
TEAM_STATS_FILE = "nba_team_stats.csv"
SCHEDULE_FILE = "nba_schedule_cache.csv" # You'll need to fetch/create this once or scrape a schedule site

def fetch_hollinger_stats():
    print(f"📡 Connecting to ESPN Hollinger Database: {HOLLINGER_URL}...")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(HOLLINGER_URL, headers=headers)
        response.raise_for_status()
        
        # Read all tables
        dfs = pd.read_html(StringIO(response.text))
        stats_df = dfs[0]
        
        # Clean Header Row (ESPN repeats headers)
        new_header = stats_df.iloc[1] 
        stats_df = stats_df[2:] 
        stats_df.columns = new_header 
        
        # Normalize Team Names (Map ESPN names to Abbr if needed)
        # For now, we save raw data. The Brain will map it.
        
        stats_df.to_csv(TEAM_STATS_FILE, index=False)
        print(f"✅ SUCCESS: Hollinger Stats saved to {TEAM_STATS_FILE}")
        return stats_df
        
    except Exception as e:
        print(f"❌ ERROR: Failed to scrape Hollinger data. {e}")
        return None

# NOTE: Automating Rest Days requires a reliable schedule source (API or Scraper).
# For V12.0, we will automate the STATS (Pace/Eff) first. 
# Rest Days are best kept manual for now unless we pay for an API, 
# as scraping schedules is notoriously fragile (date formats change constantly).

if __name__ == "__main__":
    fetch_hollinger_stats()
    input("\nPress Enter to exit...")