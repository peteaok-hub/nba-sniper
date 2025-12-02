import pandas as pd
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster
import time

nba_teams = teams.get_teams()
all_players = []

print("Downloading Rosters...")
for team in nba_teams:
    print(f"Fetching {team['full_name']}...")
    try:
        # Try without season param for safety
        roster = commonteamroster.CommonTeamRoster(team_id=team['id'])
        df = roster.get_data_frames()[0]
        df['TEAM_ID'] = team['id']
        df['TEAM_NAME'] = team['full_name']
        all_players.append(df)
        time.sleep(0.6) 
    except Exception as e:
        print(f"Error fetching {team['full_name']}: {e}")

if all_players:
    final_df = pd.concat(all_players)
    final_df.to_csv("nba_rosters.csv", index=False)
    print("✅ Success! 'nba_rosters.csv' created. Upload this to GitHub.")
else:
    print("❌ Failed to fetch rosters.")
