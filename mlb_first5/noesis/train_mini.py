#!/usr/bin/env python3
"""
Train a minimal nanoGPT on baseball corpus.
Ultra-lightweight: n_layer=2, n_embd=64, batch_size=8
"""
import os, sys, pickle, time, math, gc

import numpy as np
import torch

NANOGPT_PATH = '/root/nanoGPT'
sys.path.insert(0, NANOGPT_PATH)
from model import GPTConfig, GPT

# --- CONFIG (tiny model) ---
out_dir = '/root/mlb-first5/out/noesis_checkpoint'
os.makedirs(out_dir, exist_ok=True)

dataset = 'baseball_char'
data_dir = '/root/mlb-first5/data'

batch_size = 8
block_size = 128
n_layer = 2
n_head = 2
n_embd = 64
dropout = 0.1
learning_rate = 1e-3
max_iters = 1500
lr_decay_iters = 1500
min_lr = 1e-4
warmup_iters = 30
eval_interval = 150
log_interval = 25
eval_iters = 30
always_save_checkpoint = True
device = 'cpu'
# ---

meta_path = os.path.join(data_dir, dataset, 'meta.pkl')
with open(meta_path, 'rb') as f:
    meta = pickle.load(f)
vocab_size = meta['vocab_size']
print(f"Vocab: {vocab_size}, device: {device}", flush=True)

def get_batch(split):
    d = os.path.join(data_dir, dataset, f'{split}.bin')
    data = np.memmap(d, dtype=np.uint16, mode='r')
    ix = torch.randint(len(data) - block_size, (batch_size,))
    x = torch.stack([torch.from_numpy((data[i:i+block_size]).astype(np.int64)) for i in ix])
    y = torch.stack([torch.from_numpy((data[i+1:i+1+block_size]).astype(np.int64)) for i in ix])
    return x.to(device), y.to(device)

model_args = dict(n_layer=n_layer, n_head=n_head, n_embd=n_embd,
                  block_size=block_size, bias=False, vocab_size=vocab_size, dropout=dropout)
model = GPT(GPTConfig(**model_args)).to(device)
print(f"Params: {sum(p.numel() for p in model.parameters())/1e6:.2f}M", flush=True)

optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, betas=(0.9, 0.99))

def get_lr(it):
    if it < warmup_iters: return learning_rate * it / warmup_iters
    if it > lr_decay_iters: return min_lr
    decay = (it - warmup_iters) / (lr_decay_iters - warmup_iters)
    return min_lr + (learning_rate - min_lr) * 0.5 * (1 + math.cos(math.pi * decay))

@torch.no_grad()
def estimate_loss():
    model.eval()
    losses = []
    for _ in range(eval_iters // batch_size):
        x, y = get_batch('val')
        _, loss = model(x, y)
        losses.append(loss.item())
    model.train()
    return sum(losses) / len(losses) if losses else 0.0

print("Estimating initial loss...", flush=True)
init_loss = estimate_loss()
print(f"Initial val loss: {init_loss:.4f}", flush=True)

best_val_loss = init_loss
start = time.time()

for it in range(max_iters):
    lr = get_lr(it)
    optimizer.param_groups[0]['lr'] = lr
    
    x, y = get_batch('train')
    logits, loss = model(x, y)
    
    optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    optimizer.step()
    
    dt = time.time() - start
    
    if it % log_interval == 0:
        print(f"it {it:5d} | loss {loss.item():.4f} | lr {lr:.6f} | dt {dt:.1f}s", flush=True)
    
    if it > 0 and it % eval_interval == 0:
        val_loss = estimate_loss()
        print(f"  val_loss: {val_loss:.4f}", flush=True)
        
        # Save checkpoint
        ckpt = {
            'model': model.state_dict(),
            'model_args': model_args,
            'iter_num': it,
            'best_val_loss': val_loss,
            'config': {'dataset': dataset, 'vocab_size': vocab_size}
        }
        ckpt_path = os.path.join(out_dir, 'ckpt.pt')
        torch.save(ckpt, ckpt_path)
        print(f"  -> Saved {ckpt_path}", flush=True)
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
        
        # Force garbage collection
        gc.collect()

# Final
print(f"\nDone! Best val: {best_val_loss:.4f}", flush=True)
ckpt = {
    'model': model.state_dict(),
    'model_args': model_args,
    'iter_num': max_iters,
    'best_val_loss': best_val_loss,
    'config': {'dataset': dataset, 'vocab_size': vocab_size}
}
torch.save(ckpt, os.path.join(out_dir, 'ckpt.pt'))
print(f"Final checkpoint saved.", flush=True)
