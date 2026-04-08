#!/usr/bin/env python3
"""
Build baseball corpus from model_data.csv for nanoGPT training.
Creates a text corpus with pitcher names, stats, and game outcomes.
"""
import csv
import random
from collections import defaultdict

def build_corpus():
    corpus_lines = []
    
    # Read model_data.csv
    with open('/root/mlb-first5/data/processed/model_data.csv', 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"Loaded {len(rows)} records from model_data.csv")
    
    # Build corpus from structured data
    for row in rows:
        pitcher = row['pitcher_name']
        era = row['pitcher_era']
        whip = row['pitcher_whip']
        k9 = row['pitcher_k9']
        bb9 = row['pitcher_bb9']
        kbb = row['pitcher_kbb']
        wins = row['pitcher_wins']
        losses = row['pitcher_losses']
        ip = row['pitcher_ip']
        first5_runs = row['first_5_runs_allowed']
        predicted = row['predicted_f5']
        is_home = row['is_home']
        opp_avg = row['opp_avg_runs_allowed']
        opp_first5 = row['opp_avg_first5_allowed']
        year = row['year']
        date = row['date']
        
        # Outcome: high-scoring (over 2.5), low-scoring (under 2.5), or push (exactly 2.5)
        runs_int = int(float(first5_runs))
        if runs_int >= 3:
            outcome = "HIGH_SCORING"
        elif runs_int <= 2:
            outcome = "LOW_SCORING"
        else:
            outcome = "PUSH"
        
        # Build descriptive text
        line = f"{pitcher}: ERA={era}, WHIP={whip}, K/9={k9}, BB/9={bb9}, K/BB={kbb}, Record={wins}-{losses}, IP={ip}, First5Runs={first5_runs}, Predicted={predicted}, Home={is_home}, OppAvg={opp_avg}, OppFirst5={opp_first5}, Year={year}, Date={date}, Outcome={outcome}"
        corpus_lines.append(line)
        
        # Add a shorter version for variety
        short_line = f"{pitcher} vs opp: ERA {era}, Predicted First5={predicted}, Actual={first5_runs}, {outcome}"
        corpus_lines.append(short_line)
    
    # Add some synthetic "what-if" scenarios
    scenarios = []
    for row in rows[:min(1000, len(rows))]:
        pitcher = row['pitcher_name']
        era = float(row['pitcher_era'])
        predicted = float(row['predicted_f5'])
        
        # Generate hypothetical variations
        scenarios.append(f"What if {pitcher} (ERA={era}) had a 10% better K/9? Predicted would be {predicted * 0.9:.2f}")
        scenarios.append(f"What if {pitcher} faced a weaker opponent? Predicted First5 would decrease by ~{era * 0.2:.2f}")
        scenarios.append(f"If {pitcher} is well-rested, expect {max(0, predicted - 0.3):.2f} First5 runs")
    
    corpus_lines.extend(scenarios)
    
    # Add some narrative summaries
    unique_pitchers = defaultdict(list)
    for row in rows:
        unique_pitchers[row['pitcher_name']].append(row)
    
    for pitcher, pitcher_rows in unique_pitchers.items():
        total_first5 = sum(int(float(r['first_5_runs_allowed'])) for r in pitcher_rows)
        avg_first5 = total_first5 / len(pitcher_rows) if pitcher_rows else 0
        total_wins = sum(int(float(r['pitcher_wins'])) for r in pitcher_rows[:1])
        total_losses = sum(int(float(r['pitcher_losses'])) for r in pitcher_rows[:1])
        
        summary = f"PlayerProfile: {pitcher} played {len(pitcher_rows)} games. Average First5 runs allowed: {avg_first5:.2f}. Career W-L: {total_wins}-{total_losses}."
        corpus_lines.append(summary)
    
    # Write corpus
    corpus_text = '\n'.join(corpus_lines)
    
    with open('/root/mlb-first5/data/baseball_corpus.txt', 'w') as f:
        f.write(corpus_text)
    
    print(f"Corpus written: {len(corpus_lines)} lines, {len(corpus_text)} chars")
    
    return corpus_text

if __name__ == '__main__':
    build_corpus()
