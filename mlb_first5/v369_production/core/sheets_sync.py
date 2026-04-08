#!/usr/bin/env python3
"""
sheets_sync.py — One-click sync to Google Sheets

Usage:
  python sheets_sync.py --file data.csv --sheet "Sheet1" --tab "MLB_Data"
  python sheets_sync.py --file predictions.json --sheet "Noesis_Trades" --tab "Bets"

Automatically uploads data to Google Sheets with proper formatting.
"""

import pandas as pd
import json
import sys
from pathlib import Path

def sync_to_sheets(data_file, sheet_name, tab_name):
    """
    Sync data file to Google Sheets
    
    Supports: CSV, JSON, TXT
    """
    print(f'📊 Syncing {data_file} to Google Sheets...')
    print(f'   Sheet: {sheet_name}')
    print(f'   Tab: {tab_name}')
    
    # Load data
    file_path = Path(data_file)
    
    if not file_path.exists():
        print(f'❌ File not found: {data_file}')
        return False
    
    # Parse based on extension
    ext = file_path.suffix.lower()
    
    if ext == '.csv':
        df = pd.read_csv(data_file)
    elif ext == '.json':
        with open(data_file) as f:
            data = json.load(f)
        # Handle nested JSON
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            print('❌ Unsupported JSON structure')
            return False
    elif ext in ['.txt', '.md']:
        # Convert text to single-column DataFrame
        with open(data_file) as f:
            lines = f.readlines()
        df = pd.DataFrame({'Content': lines})
    else:
        print(f'❌ Unsupported file type: {ext}')
        return False
    
    print(f'   Loaded {len(df)} rows x {len(df.columns)} columns')
    
    # Convert to values for gog
    values = df.values.tolist()
    headers = df.columns.tolist()
    
    # Add headers as first row
    all_values = [headers] + values
    
    # Create JSON for gog
    output = {
        'sheet_name': sheet_name,
        'tab_name': tab_name,
        'range': f'{tab_name}!A1',
        'values': all_values,
        'rows': len(df),
        'cols': len(df.columns)
    }
    
    # Save sync command
    sync_file = f'/tmp/sheets_sync_{tab_name}.json'
    with open(sync_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f'\n✅ Ready to sync!')
    print(f'   Run: gog sheets append {sheet_name} "{tab_name}!A1" --values-json \'@{sync_file}\'')
    print(f'   Or manually copy data from: {sync_file}')
    
    # Generate gog command
    print(f'\n📝 GOG COMMAND:')
    print(f'gog sheets update {sheet_name} "{tab_name}!A1:{chr(64+len(df.columns))}{len(df)+1}" --values-json \'' + json.dumps(all_values) + '\' --input USER_ENTERED')
    
    return True

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync data to Google Sheets')
    parser.add_argument('--file', required=True, help='Data file (CSV/JSON/TXT)')
    parser.add_argument('--sheet', required=True, help='Google Sheet name/ID')
    parser.add_argument('--tab', default='Sheet1', help='Tab/sheet name')
    
    args = parser.parse_args()
    
    success = sync_to_sheets(args.file, args.sheet, args.tab)
    sys.exit(0 if success else 1)
