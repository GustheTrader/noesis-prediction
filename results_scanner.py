#!/usr/bin/env python3
"""
NOESIS Results Scanner - 11 PM PST

Runs at 11 PM PST (7 AM UTC) to grab results.
Logs outcomes for each pick.

Schedule: 0 7 * * * (7 AM UTC = 11 PM PST)
"""

import os
import sys
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional


sys.path.insert(0, str(Path(__file__).parent))

from picks_logger import PicksLogger, PicksRecord


# ─── RESULTS FETCHER (Stub) ──────────────────────────────────────────

def get_game_results(date: str) -> dict:
    """
    Get actual game results for a date.
    
    In production: Fetch from scores API.
    """
    # For demo, return sample results
    return {
        "Dodgers @ Giants": {"score": "5-2", "f5": "3-1", "status": "final"},
        "Mets @ Phillies": {"score": "4-6", "f5": "2-3", "status": "final"},
        "Braves @ Marlins": {"score": "8-3", "f5": "4-1", "status": "final"},
        "Yankees @ Guardians": {"score": "3-5", "f5": "2-2", "status": "final"},
    }


def get_prop_results(date: str) -> dict:
    """
    Get actual prop results.
    
    In production: Fetch from prop results API.
    """
    return {
        "shohei-ohtani": {
            "home_runs": {"actual": 42, "result": "WIN", "payout": 1.0},
            "strikeouts": {"actual": 8, "result": "WIN", "payout": 1.0},
        },
        "juan-soto": {
            "walks": {"actual": 98, "result": "LOSS", "payout": -1.0},
        },
    }


# ─── RESULTS ANALYZER ─────────────────────────────────────────────────

@dataclass
class PickResult:
    """Result of a single pick."""
    pick_id: str
    game: str
    selection: str
    result: str  # WIN, LOSS, PUSH
    profit: float  # units won/lost


@dataclass
class DailyResults:
    """Results for a day."""
    date: str
    total_picks: int
    wins: int
    losses: int
    pushes: int
    total_profit: float
    roi: float  # percentage
    picks: List[PickResult]


def analyze_results(date: str) -> DailyResults:
    """Analyze results for a date."""
    
    logger = PicksLogger()
    picks_record = logger.get_picks(date)
    
    if not picks_record:
        print(f"⚠️  No picks found for {date}")
        return None
    
    # Get actual results
    game_results = get_game_results(date)
    prop_results = get_prop_results(date)
    
    # Analyze each pick
    results = []
    wins = 0
    losses = 0
    pushes = 0
    total_profit = 0
    
    for pick in picks_record.picks:
        pick_result = "LOSS"  # Default
        profit = -pick["units"]  # Default loss
        
        # Check F5 picks
        if pick["bet_type"] == "F5":
            game_key = pick["game"]
            if game_key in game_results:
                f5_score = game_results[game_key]["f5"]
                # Parse F5 score - simple logic for demo
                # In production: compare actual vs line
                if "Under" in pick["selection"] and int(f5_score.split("-")[0]) < 5:
                    pick_result = "WIN"
                    profit = pick["units"]
                elif "Over" in pick["selection"] and int(f5_score.split("-")[0]) > 5:
                    pick_result = "WIN"
                    profit = pick["units"]
        
        # Check props
        elif pick["bet_type"] == "Prop":
            # This is simplified - real logic would check actual props
            pick_result = "PUSH"
            profit = 0
            pushes += 1
        
        if pick_result == "WIN":
            wins += 1
            total_profit += profit
        elif pick_result == "LOSS":
            losses += 1
        
        results.append(PickResult(
            pick_id=pick["pick_id"],
            game=pick["game"],
            selection=pick["selection"],
            result=pick_result,
            profit=profit
        ))
    
    # Calculate ROI
    total_wagered = sum(p["units"] for p in picks_record.picks)
    roi = (total_profit / total_wagered * 100) if total_wagered > 0 else 0
    
    return DailyResults(
        date=date,
        total_picks=len(results),
        wins=wins,
        losses=losses,
        pushes=pushes,
        total_profit=round(total_profit, 2),
        roi=round(roi, 1),
        picks=results
    )


# ─── GENERATE REPORT ────────────────────────────────────────────────

def generate_report(results: DailyResults) -> str:
    """Generate results report."""
    
    report = []
    report.append("=" * 70)
    report.append(f"📊 NOESIS RESULTS REPORT - {results.date}")
    report.append("=" * 70)
    report.append("")
    report.append(f"📈 PERFORMANCE:")
    report.append(f"   Total Picks: {results.total_picks}")
    report.append(f"   Wins: {results.wins} | Losses: {results.losses} | Pushes: {results.pushes}")
    report.append(f"   Win Rate: {results.wins / results.total_picks * 100:.1f}%")
    report.append("")
    report.append(f"💰 PROFIT:")
    report.append(f"   Total: {results.total_profit:+,.2f} units")
    report.append(f"   ROI: {results.roi:+,.1f}%")
    report.append("")
    report.append("🎯 PICKS:")
    report.append("-" * 70)
    
    for pick in results.picks:
        emoji = "✅" if pick.result == "WIN" else "❌" if pick.result == "LOSS" else "➖"
        report.append(f"  {emoji} {pick.game} | {pick.selection} | {pick.result} | {pick.profit:+.2f}")
    
    report.append("=" * 70)
    
    return "\n".join(report)


# ─── MAIN ──────────────────────────────────────────────────────────

def run_results_scan(date: str = None):
    """Run results scan for a date."""
    
    if not date:
        # Yesterday's date (since we run in the morning)
        date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print("=" * 70)
    print(f"📊 NOESIS RESULTS SCAN - {date}")
    print(f"   Time: {datetime.now(timezone.utc).strftime('%H:%M UTC')}")
    print("=" * 70)
    
    # Analyze results
    results = analyze_results(date)
    
    if not results:
        print("No results to analyze.")
        return
    
    # Generate report
    report = generate_report(results)
    print(report)
    
    # Save report
    results_dir = Path("/root/.openclaw/workspace/noesis-prediction/results")
    results_dir.mkdir(exist_ok=True)
    
    report_file = results_dir / f"results_{date}.txt"
    with open(report_file, "w") as f:
        f.write(report)
    
    # Also update picks logger
    logger = PicksLogger()
    logger.update_status(date, results.wins > results.losses, {
        "total_picks": results.total_picks,
        "wins": results.wins,
        "losses": results.losses,
        "profit": results.total_profit,
        "roi": results.roi
    })
    
    print(f"\n💾 Report saved to: {report_file}")
    
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Date to scan (YYYY-MM-DD)")
    args = parser.parse_args()
    
    run_results_scan(args.date)