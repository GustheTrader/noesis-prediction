#!/usr/bin/env python3
"""
Quick makemore baserunner training - tiny version for demo.
Trains on 5000 sequences only, 1 epoch, batch 32.
"""
import os, sys, csv, pickle, time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

MAKEMORE_PATH = '/root/makemore'
sys.path.insert(0, MAKEMORE_PATH)
import importlib.util
spec = importlib.util.spec_from_file_location("makemore_m", f"{MAKEMORE_PATH}/makemore.py")
makemore_m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(makemore_m)
Transformer = makemore_m.Transformer
ModelConfig = makemore_m.ModelConfig

# --- Dataset ---
class SeqDataset(Dataset):
    def __init__(self, csv_path, max_seqs=5000, max_len=32):
        self.max_len = max_len
        with open(csv_path, 'r') as f:
            rows = list(csv.DictReader(f))[:max_seqs]
        
        # Build vocab
        chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.<>SEP')
        self.chars = sorted(chars)
        self.stoi = {c: i for i, c in enumerate(self.chars)}
        self.itos = {i: c for i, c in enumerate(self.chars)}
        
        self.seqs = []
        for r in rows:
            name = r.get('pitcher_name', 'UNK')[:8].upper()
            pred = r.get('predicted_f5', '2.5')[:4]
            runs = r.get('first_5_runs_allowed', '2')
            txt = f"<BEG>{name}<SEP>PRED{pred}<SEP>RUN{runs}<END>"
            self.seqs.append([self.stoi.get(c, 0) for c in txt])
        
        print(f"Dataset: {len(self.seqs)} seqs, vocab={len(self.chars)}")
    
    def __len__(self):
        return len(self.seqs)
    
    def __getitem__(self, idx):
        seq = self.seqs[idx][:self.max_len]
        while len(seq) < self.max_len:
            seq.append(0)
        return torch.tensor(seq, dtype=torch.long)

# --- Model ---
class SimpleTransformer(nn.Module):
    def __init__(self, vocab_size, block_size, n_layer=2, n_embd=64, n_head=2):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, n_embd)
        self.pos = nn.Embedding(block_size, n_embd)
        self.blocks = nn.Sequential(*[
            makemore_m.Block(ModelConfig(block_size=block_size, vocab_size=vocab_size, n_layer=1, n_embd=n_embd, n_embd2=n_embd, n_head=n_head))
            for _ in range(n_layer)
        ])
        self.ln = nn.LayerNorm(n_embd)
        self.head = nn.Linear(n_embd, vocab_size)
        self.head.weight = self.embed.weight
    
    def forward(self, x, y=None):
        B, T = x.shape
        x = self.embed(x) + self.pos(torch.arange(T))
        x = self.blocks(x)
        x = self.ln(x)
        logits = self.head(x)
        loss = nn.functional.cross_entropy(logits.view(-1, logits.size(-1)), y.view(-1)) if y is not None else None
        return logits, loss
    
    @torch.no_grad()
    def generate(self, idx, max_new):
        for _ in range(max_new):
            idx_cond = idx[:, -block_size:]
            logits, _ = self(idx_cond)
            probs = torch.softmax(logits[:, -1], dim=-1)
            idx_next = torch.multinomial(probs, 1)
            idx = torch.cat([idx, idx_next], dim=1)
        return idx

# --- Train ---
data_path = '/root/mlb-first5/data/processed/model_data.csv'
save_path = '/root/mlb-first5/data/sequences/baserunner.pt'
os.makedirs('/root/mlb-first5/data/sequences', exist_ok=True)

ds = SeqDataset(data_path, max_seqs=5000, max_len=32)
vocab_size = len(ds.chars)
block_size = 32

dl = DataLoader(ds, batch_size=32, shuffle=True)
model = SimpleTransformer(vocab_size, block_size).cuda() if torch.cuda.is_available() else SimpleTransformer(vocab_size, block_size)
opt = torch.optim.AdamW(model.parameters(), lr=1e-3)

model.train()
for epoch in range(1):
    for i, batch in enumerate(dl):
        logits, loss = model(batch, batch)
        opt.zero_grad()
        loss.backward()
        opt.step()
        if i % 100 == 0:
            print(f"batch {i}/{len(dl)}, loss={loss.item():.4f}")
        if i > 300:  # Quick: just 300 batches
            break

# Save
torch.save({'model': model.state_dict(), 'chars': ds.chars, 'stoi': ds.stoi, 'itos': ds.itos}, save_path)
print(f"Saved to {save_path}")

# Test generation
model.eval()
start = [ds.stoi['<'], ds.stoi['B']]
idx = torch.tensor(start).unsqueeze(0)
with torch.no_grad():
    out = model.generate(idx, 30)
print("Generated:", ''.join(ds.itos[i] for i in out[0].tolist()))
