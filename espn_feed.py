"""
Sovereign OS — ESPN Hidden API Feed

Undocumented ESPN API — free, no auth, live sports data.
20+ sports: NFL, NBA, MLB, NHL, Soccer, MMA, Tennis, Golf, etc.

Endpoints:
- Scoreboard (live games)
- Standings
- Schedules
- Player stats
- Team info
- News

This feeds directly into NOESIS for in-play prediction markets.
"""

import json
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

import httpx


# ─── ESPN API Base URLs ─────────────────────────────────────────

SITE_API = "https://site.api.espn.com/apis/site/v2/sports"
CORE_API = "https://sports.core.api.espn.com/v2/sports"


# ─── Data Models ────────────────────────────────────────────────

@dataclass
class Team:
    """A sports team."""
    id: str = ""
    name: str = ""
    abbreviation: str = ""
    score: int = 0
    record: str = ""
    logo: str = ""


@dataclass
class Game:
    """A live or completed game."""
    id: str = ""
    name: str = ""
    short_name: str = ""
    sport: str = ""
    league: str = ""
    status: str = ""  # scheduled, in, final
    status_detail: str = ""
    home: Team = field(default_factory=Team)
    away: Team = field(default_factory=Team)
    start_time: str = ""
    venue: str = ""
    period: int = 0
    clock: str = ""


@dataclass
class Standing:
    """Team standing."""
    team: Team = field(default_factory=Team)
    wins: int = 0
    losses: int = 0
    ties: int = 0
    pct: float = 0.0
    streak: str = ""


# ─── Sport Configurations ──────────────────────────────────────

SPORTS = {
    "nfl": {"path": "football/nfl", "name": "NFL"},
    "nba": {"path": "basketball/nba", "name": "NBA"},
    "mlb": {"path": "baseball/mlb", "name": "MLB"},
    "nhl": {"path": "hockey/nhl", "name": "NHL"},
    "ncaaf": {"path": "football/college-football", "name": "College Football"},
    "ncaab": {"path": "basketball/mens-college-basketball", "name": "College Basketball"},
    "epl": {"path": "soccer/eng.1", "name": "English Premier League"},
    "laliga": {"path": "soccer/esp.1", "name": "La Liga"},
    "bundesliga": {"path": "soccer/ger.1", "name": "Bundesliga"},
    "seriea": {"path": "soccer/ita.1", "name": "Serie A"},
    "ligue1": {"path": "soccer/fra.1", "name": "Ligue 1"},
    "mls": {"path": "soccer/usa.1", "name": "MLS"},
    "champions": {"path": "soccer/uefa.champions", "name": "Champions League"},
    "mma": {"path": "mma/ufc", "name": "UFC"},
    "tennis": {"path": "tennis/atp", "name": "ATP Tennis"},
    "golf": {"path": "golf/pga", "name": "PGA Golf"},
    "f1": {"path": "racing/f1", "name": "Formula 1"},
}


class ESPNFeed:
    """
    ESPN Hidden API Feed.
    
    Free, no auth, live sports data.
    Feeds into NOESIS for in-play prediction markets.
    """

    def __init__(self):
        self.client = httpx.Client(timeout=10)

    def get_scoreboard(self, sport: str = "nfl") -> list[Game]:
        """Get live scoreboard for a sport."""
        config = SPORTS.get(sport)
        if not config:
            return []

        try:
            resp = self.client.get(f"{SITE_API}/{config['path']}/scoreboard")
            data = resp.json()
            return self._parse_games(data, sport, config["name"])
        except Exception as e:
            print(f"ESPN error ({sport}): {e}")
            return []

    def get_standings(self, sport: str = "nfl") -> list[Standing]:
        """Get standings for a sport."""
        config = SPORTS.get(sport)
        if not config:
            return []

        try:
            resp = self.client.get(f"{SITE_API}/{config['path']}/standings")
            data = resp.json()
            return self._parse_standings(data)
        except Exception as e:
            print(f"ESPN standings error ({sport}): {e}")
            return []

    def get_schedule(self, sport: str = "nfl", date: str = "") -> list[Game]:
        """Get schedule for a sport."""
        config = SPORTS.get(sport)
        if not config:
            return []

        try:
            params = {}
            if date:
                params["dates"] = date
            resp = self.client.get(f"{SITE_API}/{config['path']}/scoreboard", params=params)
            data = resp.json()
            return self._parse_games(data, sport, config["name"])
        except Exception as e:
            print(f"ESPN schedule error ({sport}): {e}")
            return []

    def get_all_live(self) -> dict[str, list[Game]]:
        """Get all live games across all sports."""
        live = {}
        for sport in SPORTS:
            games = self.get_scoreboard(sport)
            in_play = [g for g in games if g.status == "in"]
            if in_play:
                live[sport] = in_play
        return live

    def get_all_scoreboards(self) -> dict[str, list[Game]]:
        """Get scoreboards for all sports."""
        all_games = {}
        for sport in SPORTS:
            games = self.get_scoreboard(sport)
            if games:
                all_games[sport] = games
        return all_games

    def _parse_games(self, data: dict, sport: str, league: str) -> list[Game]:
        """Parse ESPN response into Game objects."""
        games = []
        for event in data.get("events", []):
            competitions = event.get("competitions", [{}])
            comp = competitions[0] if competitions else {}
            competitors = comp.get("competitors", [])

            home = Team()
            away = Team()

            for c in competitors:
                team = Team(
                    id=c.get("id", ""),
                    name=c.get("team", {}).get("displayName", ""),
                    abbreviation=c.get("team", {}).get("abbreviation", ""),
                    score=int(c.get("score", 0)),
                    record=c.get("records", [{}])[0].get("summary", "") if c.get("records") else "",
                    logo=c.get("team", {}).get("logo", ""),
                )
                if c.get("homeAway") == "home":
                    home = team
                else:
                    away = team

            status = event.get("status", {})
            status_type = status.get("type", {})

            game = Game(
                id=event.get("id", ""),
                name=event.get("name", ""),
                short_name=event.get("shortName", ""),
                sport=sport,
                league=league,
                status=status_type.get("name", "unknown"),
                status_detail=status_type.get("description", ""),
                home=home,
                away=away,
                start_time=event.get("date", ""),
                venue=comp.get("venue", {}).get("fullName", ""),
                period=status.get("period", 0),
                clock=status.get("displayClock", ""),
            )
            games.append(game)

        return games

    def _parse_standings(self, data: dict) -> list[Standing]:
        """Parse standings data."""
        standings = []
        for group in data.get("children", []):
            for entry in group.get("standings", {}).get("entries", []):
                team_data = entry.get("team", {})
                stats = {s["name"]: s.get("value", 0) for s in entry.get("stats", [])}

                standing = Standing(
                    team=Team(
                        id=team_data.get("id", ""),
                        name=team_data.get("displayName", ""),
                        abbreviation=team_data.get("abbreviation", ""),
                    ),
                    wins=int(stats.get("wins", 0)),
                    losses=int(stats.get("losses", 0)),
                    ties=int(stats.get("ties", 0)),
                    pct=float(stats.get("winPercent", 0)),
                )
                standings.append(standing)

        return standings

    def to_noesis_format(self, games: list[Game]) -> list[dict]:
        """Convert games to NOESIS market format."""
        markets = []

        for game in games:
            if game.status == "scheduled":
                # Pre-game market
                markets.append({
                    "question": f"Will {game.away.name} beat {game.home.name}?",
                    "description": f"{game.league} — {game.away.name} @ {game.home.name}",
                    "source": "espn",
                    "tags": [game.sport, "pre_game"],
                    "closes_at": game.start_time,
                })
            elif game.status == "in":
                # In-play market
                markets.append({
                    "question": f"Will {game.away.name} ({game.away.score}) come back to beat {game.home.name} ({game.home.score})?",
                    "description": f"{game.league} LIVE — Period {game.period}, {game.clock}",
                    "source": "espn",
                    "tags": [game.sport, "in_play"],
                })

        return markets

    def get_feed_status(self) -> dict:
        """Feed status."""
        return {
            "sports_available": len(SPORTS),
            "sports": list(SPORTS.keys()),
            "api_base": SITE_API,
            "auth_required": False,
        }


# ─── Convenience ───────────────────────────────────────────────

def get_todays_games() -> dict:
    """Quick helper: get all games today."""
    feed = ESPNFeed()
    return feed.get_all_scoreboards()


def get_live_games() -> dict:
    """Quick helper: get all live games right now."""
    feed = ESPNFeed()
    return feed.get_all_live()
