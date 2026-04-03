#!/usr/bin/env python3
"""
NOESIS Picks Logger

Logs daily picks to a folder with timestamps.
Used for tracking and later results analysis.
"""

import os
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List


# ─── CONFIG ────────────────────────────────────────────────────────

PICKS_DIR = Path("/root/.openclaw/workspace/noesis-prediction/picks_logs")


# ─── DATA MODELS ────────────────────────────────────────────────────

@dataclass
class Pick:
    """A single pick."""
    pick_id: str
    game: str
    pitcher: str
    bet_type: str  # F5, K, IP, Prop
    selection: str  # Over, Under, ML, etc.
    line: str
    odds: float
    units: float
    confidence: int
    edge_type: str
    timestamp: datetime


@dataclass
class PicksRecord:
    """Record of all picks for a day."""
    date: str  # YYYY-MM-DD
    generated_at: datetime
    games: List[str]
    total_units: float
    picks: List[dict]
    status: str  # pending, won, lost, push


# ─── LOGGER ─────────────────────────────────────────────────────────

class PicksLogger:
    """Log picks to files."""
    
    def __init__(self):
        PICKS_DIR.mkdir(parents=True, exist_ok=True)
    
    def log_picks(self, picks: List[Pick], games: List[str]) -> Path:
        """Log picks to file."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        record = PicksRecord(
            date=today,
            generated_at=datetime.now(timezone.utc),
            games=games,
            total_units=sum(p.units for p in picks),
            picks=[asdict(p) for p in picks],
            status="pending"
        )
        
        filepath = PICKS_DIR / f"picks_{today}.json"
        
        with open(filepath, "w") as f:
            json.dump(asdict(record), f, indent=2, default=str)
        
        print(f"💾 Picks logged to: {filepath}")
        
        return filepath
    
    def update_status(self, date: str, status: str, results: dict):
        """Update pick status (won, lost, push)."""
        filepath = PICKS_DIR / f"picks_{date}.json"
        
        if not filepath.exists():
            print(f"⚠️  No picks file for {date}")
            return
        
        with open(filepath) as f:
            record = json.load(f)
        
        record["status"] = status
        record["results"] = results
        record["results_at"] = datetime.now(timezone.utc).isoformat()
        
        with open(filepath, "w") as f:
            json.dump(record, f, indent=2)
        
        print(f"✅ Updated {date} status: {status}")
    
    def get_picks(self, date: str = None) -> PicksRecord:
        """Get picks for a date."""
        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        filepath = PICKS_DIR / f"picks_{date}.json"
        
        if not filepath.exists():
            return None
        
        with open(filepath) as f:
            data = json.load(f)
        
        return PicksRecord(
            date=data["date"],
            generated_at=datetime.fromisoformat(data["generated_at"]),
            games=data["games"],
            total_units=data["total_units"],
            picks=data["picks"],
            status=data["status"]
        )


# ─── INTEGRATE WITH MORNING SCAN ───────────────────────────────────

def log_morning_picks():
    """Log picks from morning scan."""
    
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    from morning_scan import run_morning_scan, get_today_games_9am, get_live_props
    
    # Run morning scan
    available = run_morning_scan()
    
    # Convert to picks
    picks = []
    pick_id = 1
    
    for item in available:
        game = item["game"]
        
        for edge in item["edges"]:
            # Determine selection
            if "Under" in edge["type"]:
                selection = "Under"
            elif "Over" in edge["type"]:
                selection = "Over"
            elif "ML" in edge["type"]:
                selection = "ML"
            else:
                selection = edge["type"]
            
            # Determine bet type
            if "F5" in edge["type"]:
                bet_type = "F5"
            elif "Prop" in edge["type"]:
                bet_type = "Prop"
            elif "K " in edge["type"]:
                bet_type = "Strikeouts"
            else:
                bet_type = edge["type"]
            
            pick = Pick(
                pick_id=f"pick_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{pick_id}",
                game=f"{game.away_team} @ {game.home_team}",
                pitcher=game.away_pitcher,
                bet_type=bet_type,
                selection=selection,
                line="--",
                odds=-120,  # Default
                units=round(edge["confidence"] / 100 * 2, 2),
                confidence=edge["confidence"],
                edge_type=edge["type"],
                timestamp=datetime.now(timezone.utc)
            )
            
            picks.append(pick)
            pick_id += 1
    
    # Log picks
    logger = PicksLogger()
    games = [f"{item['game'].away_team} @ {item['game'].home_team}" for item in available]
    logger.log_picks(picks, games)
    
    return picks


if __name__ == "__main__":
    log_morning_picks()