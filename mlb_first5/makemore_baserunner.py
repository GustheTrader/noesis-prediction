#!/usr/bin/env python3
"""
makemore_baserunner.py
Uses makemore (character-level Transformer) to model baseball game outcome sequences.
Used for anomaly detection and generating "what-if" scenarios.
"""
import os
import sys
import csv
import pickle
import argparse
from collections import defaultdict

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset
from torch.utils.data.dataloader import DataLoader

# Import from local makemore.py
MAKEMORE_PATH = '/root/makemore'
sys.path.insert(0, MAKEMORE_PATH)

# Import classes from makemore module
import importlib.util
spec = importlib.util.spec_from_file_location("makemore_module", f"{MAKEMORE_PATH}/makemore.py")
makemore_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(makemore_module)

ModelConfig = makemore_module.ModelConfig
Transformer = makemore_module.Transformer
CharDataset = makemore_module.CharDataset

# -----------------------------------------------------------------------------
# Baseball Sequence Dataset
class BaseballSequenceDataset(Dataset):
    """
    Encodes game sequences as character sequences for makemore-style training.
    Each game = sequence of pitch-level events encoded as tokens.
    """
    
    def __init__(self, data_path, max_seq_len=32):
        self.data_path = data_path
        self.max_seq_len = max_seq_len
        
        # Load raw data
        with open(data_path, 'r') as f:
            reader = csv.DictReader(f)
            self.rows = list(reader)
        
        # Build vocabulary from all text
        all_chars = set()
        for row in self.rows:
            text = self._row_to_text(row)
            all_chars.update(text)
        
        # Sort for consistency
        self.chars = sorted(all_chars)
        self.vocab_size = len(self.chars)
        
        # Create mappings
        self.stoi = {c: i for i, c in enumerate(self.chars)}
        self.itos = {i: c for i, c in enumerate(self.chars)}
        
        # Encode all rows
        self.sequences = []
        for row in self.rows:
            text = self._row_to_text(row)
            encoded = [self.stoi.get(c, 0) for c in text]
            self.sequences.append(encoded)
        
        print(f"Loaded {len(self.sequences)} sequences, vocab={self.vocab_size}")
    
    def _row_to_text(self, row):
        """Convert a CSV row to text sequence."""
        parts = []
        
        # Pitcher name
        name = row.get('pitcher_name', 'UNK')[:10].upper()
        parts.append(f"<BEG>{name}<SEP>")
        
        # Key stats encoded as readable tokens
        stats = [
            ('ERA', row.get('pitcher_era', '?')),
            ('WHIP', row.get('pitcher_whip', '?')),
            ('K9', row.get('pitcher_k9', '?')),
            ('BB9', row.get('pitcher_bb9', '?')),
            ('PRED', row.get('predicted_f5', '?')),
            ('RUNS', row.get('first_5_runs_allowed', '?')),
        ]
        
        for stat_name, val in stats:
            parts.append(f"{stat_name}{val}<SEP>")
        
        # Outcome marker
        runs = int(float(row.get('first_5_runs_allowed', 0)))
        if runs <= 2:
            outcome = 'L'  # Low
        elif runs >= 4:
            outcome = 'H'  # High
        else:
            outcome = 'M'  # Medium
        parts.append(f"<END>{outcome}")
        
        return ''.join(parts)
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        seq = self.sequences[idx]
        # Truncate or pad to max_seq_len
        if len(seq) > self.max_seq_len:
            seq = seq[:self.max_seq_len]
        while len(seq) < self.max_seq_len:
            seq.append(0)  # PAD
        return torch.tensor(seq, dtype=torch.long)


class BaserunnerTransformer(Transformer):
    """Makemore Transformer adapted for baseball sequence modeling."""
    
    def __init__(self, vocab_size, block_size, n_layer=4, n_embd=64, n_head=4):
        config = ModelConfig(
            block_size=block_size,
            vocab_size=vocab_size,
            n_layer=n_layer,
            n_embd=n_embd,
            n_embd2=n_embd,
            n_head=n_head
        )
        super().__init__(config)


def train_baserunner(data_csv, epochs=5, batch_size=64, lr=1e-3, save_path=None, max_seq_len=64):
    """Train the baserunner model on baseball sequences."""
    
    save_path = save_path or '/root/mlb-first5/data/sequences/baserunner.pt'
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # Create dataset
    dataset = BaseballSequenceDataset(data_csv, max_seq_len=max_seq_len)
    vocab_size = dataset.vocab_size
    block_size = max_seq_len
    
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    
    # Create model
    model = BaserunnerTransformer(vocab_size=vocab_size, block_size=block_size)
    print(f"Baserunner params: {sum(p.numel() for p in model.parameters())/1e6:.2f}M")
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    
    # Training loop
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for batch_idx, batch in enumerate(dataloader):
            logits, loss = model(batch, batch)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item()
            
            if batch_idx % 200 == 0:
                print(f"Epoch {epoch}, batch {batch_idx}, loss: {loss.item():.4f}", flush=True)
        
        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch} complete: avg_loss={avg_loss:.4f}")
    
    # Save
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.save({
        'model': model.state_dict(),
        'chars': dataset.chars,
        'stoi': dataset.stoi,
        'itos': dataset.itos,
        'vocab_size': vocab_size,
        'block_size': block_size,
    }, save_path)
    print(f"Saved baserunner to {save_path}")
    
    return model, dataset


def generate_sequence(model, dataset, start_text=None, max_new_tokens=50, temperature=0.8):
    """Generate a baseball sequence from a starting prompt."""
    model.eval()
    
    if start_text:
        start_ids = [dataset.stoi.get(c, 0) for c in start_text]
    else:
        start_ids = [dataset.stoi['<BEG>']]
    
    idx = torch.tensor(start_ids, dtype=torch.long).unsqueeze(0)
    
    with torch.no_grad():
        for _ in range(max_new_tokens):
            logits, _ = model(idx)
            logits = logits[:, -1, :] / temperature
            
            probs = torch.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat([idx, idx_next], dim=1)
    
    # Decode
    result = ''.join([dataset.itos.get(i.item(), '?') for i in idx[0]])
    return result


def detect_anomaly(sequence_text, model, dataset, threshold_prob=0.001):
    """
    Detect if a sequence is anomalous.
    
    Returns dict with anomaly info.
    """
    model.eval()
    
    # Encode
    encoded = [dataset.stoi.get(c, 0) for c in sequence_text[:dataset.block_size]]
    while len(encoded) < dataset.block_size:
        encoded.append(0)
    idx = torch.tensor(encoded, dtype=torch.long).unsqueeze(0)
    
    with torch.no_grad():
        logits, _ = model(idx)
        probs = torch.softmax(logits, dim=-1)
        
        # Average probability of actual tokens
        actual_probs = probs[0, torch.arange(len(encoded)), torch.tensor(encoded)]
        avg_prob = actual_probs.mean().item()
    
    perplexity = 1.0 / (avg_prob + 1e-10)
    is_anomaly = avg_prob < threshold_prob
    
    return {
        'is_anomaly': is_anomaly,
        'avg_prob': avg_prob,
        'perplexity': perplexity,
        'message': f"Anomalous pattern (prob={avg_prob:.6f})" if is_anomaly else "Normal pattern"
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train makemore baserunner model')
    parser.add_argument('--data', default='/root/mlb-first5/data/processed/model_data.csv')
    parser.add_argument('--epochs', type=int, default=5)
    parser.add_argument('--batch_size', type=int, default=64)
    parser.add_argument('--save_path', default='/root/mlb-first5/data/sequences/baserunner.pt')
    parser.add_argument('--max_seq_len', type=int, default=64)
    args = parser.parse_args()
    
    print("=== Training Makemore Baserunner ===")
    model, dataset = train_baserunner(
        args.data, 
        epochs=args.epochs, 
        batch_size=args.batch_size,
        save_path=args.save_path,
        max_seq_len=args.max_seq_len
    )
    
    print("\n=== Testing generation ===")
    for _ in range(3):
        gen = generate_sequence(model, dataset, start_text="<BEG>GERRI<SEP>ERA", max_new_tokens=30)
        print(f"Generated: {gen}")
