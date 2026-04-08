#!/usr/bin/env python3
"""
scraper_v2.py — Fixed MLB game scraper.
Key fixes:
1. Proper pagination: 99 pages × 25 events = ~2475 games/season
2. Proper game deduplication by (date, home_team, away_team)
3. Fetches linescores, pitcher names, team names per game
"""
import json, time, requests
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://sports.core.api.espn.com/v2/sports/baseball/leagues/mlb"
SEASONS = [2021, 2022, 2023, 2025]
TYPE = 2  # regular season
OUT = Path("data/raw_v2")
OUT.mkdir(parents=True, exist_ok=True)
WORKERS = 8

H = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

_team_cache = {}

def get(url, retries=2):
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=H, timeout=20)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        if attempt < retries:
            time.sleep(0.5)
    return None

def id_from(ref):
    if not ref:
        return ""
    return ref.rstrip("/").split("/")[-1].split("?")[0]

def get_team_name(team_ref):
    if not team_ref:
        return ""
    tid = id_from(team_ref)
    if tid in _team_cache:
        return _team_cache[tid]
    data = get(team_ref)
    name = data.get("displayName", "") if data else ""
    _team_cache[tid] = name
    return name

def get_pitcher_name(athlete_ref):
    data = get(athlete_ref)
    if data:
        return data.get("displayName", ""), data.get("id")
    return "", ""

def parse_game(event_id, year):
    """Parse a single game event into a clean dict."""
    data = get(f"{BASE}/seasons/{year}/types/{TYPE}/events/{event_id}")
    if not data:
        return None
    
    competitions = data.get("competitions", [])
    if not competitions:
        return None
    
    comp = competitions[0]
    date_str = comp.get("date", "")[:10]  # YYYY-MM-DD
    
    game = {
        "event_id": event_id,
        "year": year,
        "date": date_str,
        "home_team_name": "",
        "home_team_id": "",
        "away_team_name": "",
        "away_team_id": "",
        "home_pitcher_name": "",
        "home_pitcher_id": "",
        "away_pitcher_name": "",
        "away_pitcher_id": "",
        "home_first5_runs": 0,
        "away_first5_runs": 0,
        "home_full_runs": 0,
        "away_full_runs": 0,
    }
    
    for rc in comp.get("competitors", []):
        ha = rc.get("homeAway", "")
        if ha not in ("home", "away"):
            continue
        
        # Team
        team_ref = (rc.get("team") or {}).get("$ref", "")
        team_name = get_team_name(team_ref)
        team_id = id_from(team_ref)
        game[f"{ha}_team_name"] = team_name
        game[f"{ha}_team_id"] = team_id
        
        # Score
        score = rc.get("score", "0")
        game[f"{ha}_full_runs"] = int(score) if score else 0
        
        # Linescores
        ls_ref = (rc.get("linescores") or {}).get("$ref", "")
        if ls_ref:
            ls = get(ls_ref)
            if ls:
                innings = ls.get("items", [])
                first5 = sum(int(inn.get("value", 0) or 0) for inn in innings[:5])
                game[f"{ha}_first5_runs"] = first5
        
        # Probable pitcher
        for p in rc.get("probables", []):
            athlete_ref = (p.get("athlete") or {}).get("$ref", "")
            if athlete_ref:
                name, pid = get_pitcher_name(athlete_ref)
                game[f"{ha}_pitcher_name"] = name
                game[f"{ha}_pitcher_id"] = str(pid) if pid else ""
    
    return game

def scrape_season(year):
    print(f"\n[*] Scraping {year}...")
    
    # Collect all event IDs with proper pagination
    event_ids = []
    pi = 1
    while True:
        url = f"{BASE}/seasons/{year}/types/{TYPE}/events?page={pi}"
        data = get(url)
        if not data:
            break
        
        items = data.get("items", [])
        if not items:
            break
        
        for item in items:
            eid = id_from(item.get("$ref", ""))
            if eid:
                event_ids.append(eid)
        
        pc = data.get("pageCount", 1)
        print(f"  Page {pi}/{pc}: {len(items)} events (total: {len(event_ids)})")
        
        if pi >= pc:
            break
        pi += 1
        time.sleep(0.1)
    
    print(f"  Total events: {len(event_ids)}")
    
    # Parse each game (with threading for speed)
    games = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(parse_game, eid, year): eid for eid in event_ids}
        for i, future in enumerate(as_completed(futures)):
            g = future.result()
            if g:
                games.append(g)
            if (i + 1) % 100 == 0:
                print(f"  Parsed {i+1}/{len(event_ids)}")
    
    # Deduplicate by (date, home_team, away_team)
    seen = set()
    unique = []
    for g in games:
        key = (g["date"], g["home_team_name"], g["away_team_name"])
        if key not in seen and g["home_team_name"]:
            seen.add(key)
            unique.append(g)
    
    print(f"  Games: {len(games)} total, {len(unique)} unique")
    
    # Save
    with open(OUT / f"games_{year}.json", "w") as f:
        json.dump(unique, f, indent=2)
    
    return unique

if __name__ == "__main__":
    all_games = []
    for yr in SEASONS:
        games = scrape_season(yr)
        all_games.extend(games)
    
    print(f"\n[+] Done: {len(all_games)} total unique games")
    print(f"    Saved to {OUT}/games_{{year}}.json")
