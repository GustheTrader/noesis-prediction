"""
NOESIS ESPN Data Fetcher

Free ESPN API integration for MLB data.
No API key needed - uses undocumented endpoints.

Endpoints:
- Scores: /apis/site/v2/sports/baseball/mlb/scoreboard
- Stats: /apis/v1/sports/baseball/mlb/statistics
- Teams: /apis/site/v2/sports/baseball/mlb/teams
- Player: /apis/v1/sports/baseball/mlb/athletes/{id}
- Schedule: /apis/site/v2/sports/baseball/mlb/schedule
"""

import requests
import json
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import List, Optional, Dict


# ─── ESPN API CLIENT ────────────────────────────────────────────────

ESPN_BASE_URL = "https://site.api.espn.com/apis"


class ESPNClient:
    """Client for ESPN's free API."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; NOESIS/1.0)"
        })
    
    def get_scoreboard(self, date: str = None) -> dict:
        """Get today's MLB scoreboard.
        
        Args:
            date: Format YYYYMMDD. Defaults to today.
        """
        if not date:
            date = datetime.now(timezone.utc).strftime("%Y%m%d")
        
        url = f"{ESPN_BASE_URL}/site/v2/sports/baseball/mlb/scoreboard?dates={date}"
        
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error fetching scoreboard: {e}")
            return {}
    
    def get_teams(self) -> List[dict]:
        """Get all MLB teams."""
        url = f"{ESPN_BASE_URL}/site/v2/sports/baseball/mlb/teams"
        
        try:
            resp = self.session.get(url, timeout=10)
            data = resp.json()
            return data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])
        except Exception as e:
            print(f"Error fetching teams: {e}")
            return []
    
    def get_team_stats(self, team_id: int) -> dict:
        """Get team statistics."""
        url = f"{ESPN_BASE_URL}/v1/sports/baseball/mlb/teams/{team_id}/statistics"
        
        try:
            resp = self.session.get(url, timeout=10)
            return resp.json()
        except Exception as e:
            print(f"Error fetching team stats: {e}")
            return {}
    
    def get_player(self, player_id: int) -> dict:
        """Get player info and stats."""
        url = f"{ESPN_BASE_URL}/v1/sports/baseball/mlb/athletes/{player_id}"
        
        try:
            resp = self.session.get(url, timeout=10)
            return resp.json()
        except Exception as e:
            print(f"Error fetching player: {e}")
            return {}
    
    def get_schedule(self, start_date: str = None, end_date: str = None) -> dict:
        """Get schedule for date range."""
        if not start_date:
            start_date = datetime.now(timezone.utc).strftime("%Y%m%d")
        if not end_date:
            end_date = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y%m%d")
        
        url = f"{ESPN_BASE_URL}/site/v2/sports/baseball/mlb/schedule?dates={start_date}-{end_date}"
        
        try:
            resp = self.session.get(url, timeout=10)
            return resp.json()
        except Exception as e:
            print(f"Error fetching schedule: {e}")
            return {}


# ─── DATA MODELS ──────────────────────────────────────────────────────

@dataclass
class ESPNGame:
    """An MLB game from ESPN."""
    game_id: str
    status: str  # STATUS_SCHEDULED, STATUS_IN_PROGRESS, etc.
    start_time: datetime
    away_team: str
    away_record: str
    away_score: Optional[int]
    home_team: str
    home_record: str
    home_score: Optional[int]
    venue: str
    broadcasters: List[str]


@dataclass
class ESPNTeam:
    """An MLB team."""
    id: int
    name: str
    abbreviation: str
    location: str
    logo: str
    record: str = ""
    standing: int = 0


# ─── PARSER ──────────────────────────────────────────────────────────

def parse_scoreboard(data: dict) -> List[ESPNGame]:
    """Parse ESPN scoreboard response."""
    games = []
    
    events = data.get("events", [])
    
    for event in events:
        # Game info
        game_id = event.get("id", "")
        status = event.get("status", {}).get("type", {}).get("description", "UNKNOWN")
        
        # Time
        start_time_str = event.get("date", "")
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
        else:
            start_time = datetime.now(timezone.utc)
        
        # Competitors
        competitors = event.get("competitions", [{}])[0].get("competitors", [])
        
        away = None
        home = None
        
        for comp in competitors:
            team = comp.get("team", {})
            score = comp.get("score")
            
            if comp.get("homeOrAway") == "away":
                away = {
                    "name": team.get("displayName", ""),
                    "abbreviation": team.get("abbreviation", ""),
                    "record": comp.get("record", [{}])[0].get("summary", ""),
                    "score": int(score) if score else None,
                }
            else:
                home = {
                    "name": team.get("displayName", ""),
                    "abbreviation": team.get("abbreviation", ""),
                    "record": comp.get("record", [{}])[0].get("summary", ""),
                    "score": int(score) if score else None,
                }
        
        # Venue
        venue = event.get("competitions", [{}])[0].get("venue", {}).get("fullName", "")
        
        # Broadcasters
        broadcasters = []
        for broadcast in event.get("competitions", [{}])[0].get("broadcasts", []):
            if isinstance(broadcast, dict):
                names = broadcast.get("names", [])
                if names and isinstance(names[0], dict):
                    broadcasters.append(names[0].get("name", ""))
                elif names and isinstance(names[0], str):
                    broadcasters.append(names[0])
        
        if away and home:
            games.append(ESPNGame(
                game_id=game_id,
                status=status,
                start_time=start_time,
                away_team=away["name"],
                away_record=away["record"],
                away_score=away.get("score"),
                home_team=home["name"],
                home_record=home["record"],
                home_score=home.get("score"),
                venue=venue,
                broadcasters=broadcasters
            ))
    
    return games


def parse_teams(data: List[dict]) -> List[ESPNTeam]:
    """Parse ESPN teams response."""
    teams = []
    
    for item in data:
        team_data = item.get("team", {})
        
        # Handle location which can be string or dict
        location = team_data.get("location", "")
        if isinstance(location, dict):
            location = location.get("full", "")
        
        teams.append(ESPNTeam(
            id=team_data.get("id", 0),
            name=team_data.get("displayName", ""),
            abbreviation=team_data.get("abbreviation", ""),
            location=location,
            logo=team_data.get("logos", [{}])[0].get("href", "") if team_data.get("logos") else "",
        ))
    
    return teams


# ─── NOESIS INTEGRATION ──────────────────────────────────────────────

def get_todays_games_espn() -> List[ESPNGame]:
    """Get today's games from ESPN."""
    client = ESPNClient()
    data = client.get_scoreboard()
    return parse_scoreboard(data)


def get_tomorrows_games_espn() -> List[ESPNGame]:
    """Get tomorrow's games from ESPN."""
    client = ESPNClient()
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y%m%d")
    data = client.get_scoreboard(date=tomorrow)
    return parse_scoreboard(data)


# ─── DEMO ────────────────────────────────────────────────────────────

def demo():
    """Demo ESPN API integration."""
    
    print("=" * 70)
    print("📡 NOESIS ESPN DATA FETCHER")
    print("   Free MLB data from ESPN API")
    print("=" * 70)
    
    client = ESPNClient()
    
    # Get today's scoreboard
    print("\n📊 Today's Games:")
    data = client.get_scoreboard()
    games = parse_scoreboard(data)
    
    if not games:
        print("   No games today (or API unavailable)")
    else:
        for g in games:
            status_emoji = "🟢" if g.status == "Final" else "🟡" if "In Progress" in g.status else "⚪"
            
            if g.away_score is not None:
                score_line = f" {g.away_score} - {g.home_score}"
            else:
                score_line = f" @ {g.start_time.strftime('%H:%M')}"
            
            print(f"   {status_emoji} {g.away_team} ({g.away_record}) @ {g.home_team} ({g.home_record}){score_line}")
    
    # Get teams
    print("\n🏟️ Teams:")
    teams_data = client.get_teams()
    teams = parse_teams(teams_data)
    
    print(f"   Found {len(teams)} teams")
    for t in teams[:5]:
        print(f"   • {t.name} ({t.abbreviation})")
    print(f"   ... and {len(teams)-5} more")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo()