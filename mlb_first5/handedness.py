#!/usr/bin/env python3
"""
handedness.py — Get pitcher throwing hand from ESPN athlete API.
Fast: uses data we already collected + direct ESPN API lookups.
"""
import json, time, os, requests
from pathlib import Path

RAW_DIR   = Path("/root/mlb-first5/data/raw")
OUT_DIR   = Path("/root/mlb-first5/data")
CACHE_FILE = OUT_DIR / "pitcher_handedness.json"
STAT_DIR  = Path("/root/mlb-first5/data/raw/pitcher_stats")

BASE_URL  = "https://sports.core.api.espn.com/v2/sports/baseball/leagues/mlb"
H         = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# Load existing cache
_cache = {}
if CACHE_FILE.exists():
    with open(CACHE_FILE) as f:
        _cache = json.load(f)
print(f"Loaded {len(_cache)} cached entries")

def get(url, retries=2):
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=H, timeout=15)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        if attempt < retries:
            time.sleep(0.3)
    return None

def fetch_handedness(pid: str, year: int = 2024) -> str | None:
    """Get pitcher throwing hand from ESPN athlete endpoint."""
    url = f"{BASE_URL}/seasons/{year}/athletes/{pid}"
    data = get(url)
    if not data:
        return None
    throws = data.get("throws") or {}
    if isinstance(throws, dict):
        return throws.get("abbreviation") or throws.get("type", "")[0]
    return str(throws)[0].upper() if throws else None

def collect_pitcher_ids():
    """Collect all unique pitcher IDs from game data."""
    seen_ids, seen_names = set(), set()
    pitchers = []
    for yr in [2021, 2022, 2023, 2025]:
        games_path = RAW_DIR / f"games_{yr}.json"
        if not games_path.exists():
            continue
        with open(games_path) as f:
            games = json.load(f)
        for g in games:
            for side in ("home", "away"):
                pid   = str(g.get(f"{side}_pitcher_id", "")).strip()
                pname = g.get(f"{side}_pitcher_name", "").strip()
                key   = f"{pname}_{yr}"
                if pid and pname and key not in seen_names:
                    seen_names.add(key)
                    pitchers.append({"pid": pid, "name": pname, "year": yr})
    return pitchers

def main():
    pitchers = collect_pitcher_ids()
    print(f"Unique pitcher appearances: {len(pitchers)}")

    # Collect unique pitchers by ID
    unique = {}  # pid -> {name, years}
    for p in pitchers:
        pid = p["pid"]
        if pid not in unique:
            unique[pid] = {"name": p["name"], "years": set()}
        unique[pid]["years"].add(p["year"])

    print(f"Unique pitcher IDs: {len(unique)}")

    results = dict(_cache)
    new = 0

    for pid, info in sorted(unique.items(), key=lambda x: -len(x[1]["years"])):
        name = info["name"]
        if name in results:
            continue

        # Try each year the pitcher appeared
        handedness = None
        for yr in sorted(info["years"], reverse=True):
            handedness = fetch_handedness(pid, yr)
            if handedness:
                break
            time.sleep(0.2)

        if handedness:
            results[name] = handedness
            new += 1
            print(f"  [{new}] {name} → {handedness}")
        else:
            results[name] = None
            print(f"  [?] {name} → UNKNOWN")

        time.sleep(0.3)

        if new % 50 == 0 and new > 0:
            with open(CACHE_FILE, "w") as f:
                json.dump(dict(results), f, indent=2)
            print(f"  → Saved checkpoint ({len(results)} total)")

    # Final save
    with open(CACHE_FILE, "w") as f:
        json.dump(dict(results), f, indent=2)

    lhp = sum(1 for v in results.values() if v == "L")
    rhp = sum(1 for v in results.values() if v == "R")
    unk = sum(1 for v in results.values() if v is None)
    print(f"\n[+] Done: LHP={lhp}, RHP={rhp}, Unknown={unk}, Total={len(results)}")


if __name__ == "__main__":
    main()
