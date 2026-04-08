#!/usr/bin/env python3
"""Fast noesis training — n_layer=2, n_embd=64, 300 iters ≈ 12 min on CPU."""
import os, pickle, time, sys
import numpy as np
import torch
NANOGPT_PATH = '/root/nanoGPT'
sys.path.insert(0, NANOGPT_PATH)
from model import GPTConfig, GPT

out_dir  = '/root/mlb-first5/out/noesis_checkpoint'
data_dir = '/root/mlb-first5/data/baseball_char'
meta_path = f'{data_dir}/meta.pkl'
os.makedirs(out_dir, exist_ok=True)

with open(meta_path, 'rb') as f:
    meta = pickle.load(f)
vocab_size = meta['vocab_size']
print(f"Vocab: {vocab_size}")

# Small fast model
model = GPT(GPTConfig(
    n_layer=2, n_head=2, n_embd=32,
    block_size=64, bias=False, vocab_size=vocab_size, dropout=0.0
)).to('cpu')

optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
print(f"Params: {sum(p.numel() for p in model.parameters())/1e6:.2f}M")

# Load data
train_data = np.memmap(f'{data_dir}/train.bin', dtype=np.uint16, mode='r')
val_data   = np.memmap(f'{data_dir}/val.bin',   dtype=np.uint16, mode='r')

block_size, batch_size = 64, 64
max_iters = 200

def get_batch(split):
    d = train_data if split == 'train' else val_data
    ix = torch.randint(len(d)-block_size, (batch_size,))
    x = torch.stack([torch.from_numpy((d[i:i+block_size]).astype(np.int64)) for i in ix])
    y = torch.stack([torch.from_numpy((d[i+1:i+1+block_size]).astype(np.int64)) for i in ix])
    return x, y

@torch.no_grad()
def estimate_loss():
    model.eval()
    losses = [model(*get_batch('val'))[1].item() for _ in range(3)]
    model.train()
    return np.mean(losses)

print(f"Init loss: {estimate_loss():.4f}")
t0 = time.time()

for it in range(max_iters):
    x, y = get_batch('train')
    logits, loss = model(x, y)
    optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    optimizer.step()
    if it % 50 == 0:
        vl = estimate_loss()
        print(f"  it {it:4d}/{max_iters} | loss {loss.item():.4f} | val {vl:.4f} | {time.time()-t0:.0f}s")
        torch.save({'model': model.state_dict(), 'iter': it, 'val_loss': vl}, f'{out_dir}/ckpt.pt')

vl = estimate_loss()
torch.save({'model': model.state_dict(), 'iter': max_iters, 'val_loss': vl}, f'{out_dir}/ckpt.pt')
print(f"\nDone! Val loss: {vl:.4f} | Total: {time.time()-t0:.0f}s")
