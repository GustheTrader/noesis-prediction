#!/usr/bin/env python3
"""Ultra-fast noesis training — CPU optimized, 500 iterations max."""
import os, pickle, time, math, sys
import numpy as np
import torch

NANOGPT_PATH = '/root/nanoGPT'
sys.path.insert(0, NANOGPT_PATH)
from model import GPTConfig, GPT

out_dir     = '/root/mlb-first5/out/noesis_checkpoint'
data_dir    = '/root/mlb-first5/data'
dataset     = 'baseball_char'
os.makedirs(out_dir, exist_ok=True)

device      = 'cpu'
batch_size  = 64
block_size  = 64    # shorter context
n_layer    = 3     # smaller model
n_head     = 3
n_embd     = 96
dropout    = 0.0
max_iters  = 500
eval_every = 100
lr          = 1e-3

# Load data
train_path = f'{data_dir}/{dataset}/train.bin'
val_path   = f'{data_dir}/{dataset}/val.bin'
meta_path  = f'{data_dir}/{dataset}/meta.pkl'

with open(meta_path, 'rb') as f:
    meta = pickle.load(f)
vocab_size = meta['vocab_size']
print(f"Vocab: {vocab_size} | Data: {os.path.getsize(train_path)/1024:.0f}KB train")

def get_batch(split):
    dp = np.memmap(train_path if split=='train' else val_path, dtype=np.uint16, mode='r')
    ix = torch.randint(len(dp)-block_size, (batch_size,))
    x  = torch.stack([torch.from_numpy((dp[i:i+block_size]).astype(np.int64)) for i in ix])
    y  = torch.stack([torch.from_numpy((dp[i+1:i+1+block_size]).astype(np.int64)) for i in ix])
    return x.to(device), y.to(device)

model = GPT(GPTConfig(
    n_layer=n_layer, n_head=n_head, n_embd=n_embd,
    block_size=block_size, bias=False, vocab_size=vocab_size, dropout=dropout
))
model.to(device)
print(f"Parameters: {sum(p.numel() for p in model.parameters())/1e6:.2f}M")

optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
print(f"Training {max_iters} iterations...")

@torch.no_grad()
def estimate_loss():
    model.eval()
    losses = []
    for _ in range(5):
        x, y = get_batch('val')
        _, loss = model(x, y)
        losses.append(loss.item())
    model.train()
    return np.mean(losses)

init_loss = estimate_loss()
print(f"Init val loss: {init_loss:.4f}")

t0 = time.time()
for it in range(max_iters):
    x, y = get_batch('train')
    logits, loss = model(x, y)
    optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    optimizer.step()

    if it % 20 == 0:
        dt = time.time() - t0
        print(f"  it {it:4d}/{max_iters} | loss {loss.item():.4f} | {dt:.0f}s elapsed")

    if it > 0 and it % eval_every == 0:
        vl = estimate_loss()
        print(f"  *** val_loss: {vl:.4f}")
        ckpt = {'model': model.state_dict(), 'iter': it, 'val_loss': vl}
        torch.save(ckpt, f'{out_dir}/ckpt.pt')

vl = estimate_loss()
ckpt = {'model': model.state_dict(), 'iter': max_iters, 'val_loss': vl}
torch.save(ckpt, f'{out_dir}/ckpt.pt')
print(f"\nDone! Final val loss: {vl:.4f} | Total: {time.time()-t0:.0f}s")
