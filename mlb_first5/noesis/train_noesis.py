#!/usr/bin/env python3
"""
Train nanoGPT on the baseball corpus for the Noesis intuition module.
Based on nanoGPT/train.py but simplified for character-level baseball data.
"""
import os
import sys
import pickle
import time
import math
from contextlib import nullcontext

import numpy as np
import torch

# Add nanoGPT to path
NANOGPT_PATH = '/root/nanoGPT'
sys.path.insert(0, NANOGPT_PATH)

from model import GPTConfig, GPT

# -----------------------------------------------------------------------------
# Configuration
out_dir = '/root/mlb-first5/out/noesis_checkpoint'
eval_interval = 500
log_interval = 50
eval_iters = 100
always_save_checkpoint = True

dataset = 'baseball_char'
data_dir = '/root/mlb-first5/data'
gradient_accumulation_steps = 1
batch_size = 64
block_size = 256

# Small GPT model for fast training
n_layer = 4
n_head = 4
n_embd = 128
dropout = 0.2

learning_rate = 1e-3
max_iters = 5000
lr_decay_iters = 5000
min_lr = 1e-4
beta2 = 0.99
warmup_iters = 100

device = 'cpu'
compile = False
# -----------------------------------------------------------------------------

os.makedirs(out_dir, exist_ok=True)

# Check if data exists
train_path = os.path.join(data_dir, dataset, 'train.bin')
val_path = os.path.join(data_dir, dataset, 'val.bin')
meta_path = os.path.join(data_dir, dataset, 'meta.pkl')

if not os.path.exists(train_path):
    print(f"Data not found at {train_path}")
    print("Run prepare_data.py first!")
    sys.exit(1)

with open(meta_path, 'rb') as f:
    meta = pickle.load(f)
vocab_size = meta['vocab_size']
print(f"Vocab size: {vocab_size}")

# Get batch
def get_batch(split):
    data_dir_path = os.path.join(data_dir, dataset)
    if split == 'train':
        data = np.memmap(os.path.join(data_dir_path, 'train.bin'), dtype=np.uint16, mode='r')
    else:
        data = np.memmap(os.path.join(data_dir_path, 'val.bin'), dtype=np.uint16, mode='r')
    ix = torch.randint(len(data) - block_size, (batch_size,))
    x = torch.stack([torch.from_numpy((data[i:i+block_size]).astype(np.int64)) for i in ix])
    y = torch.stack([torch.from_numpy((data[i+1:i+1+block_size]).astype(np.int64)) for i in ix])
    x, y = x.to(device), y.to(device)
    return x, y

# Model
model_args = dict(n_layer=n_layer, n_head=n_head, n_embd=n_embd, block_size=block_size,
                  bias=False, vocab_size=vocab_size, dropout=dropout)

model = GPT(GPTConfig(**model_args))
model.to(device)
print(f"Model parameters: {sum(p.numel() for p in model.parameters())/1e6:.2f}M")

# Optimizer
optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, betas=(0.9, beta2))

# Training loop
def get_lr(it):
    if it < warmup_iters:
        return learning_rate * it / warmup_iters
    if it > lr_decay_iters:
        return min_lr
    decay_ratio = (it - warmup_iters) / (lr_decay_iters - warmup_iters)
    return min_lr + (learning_rate - min_lr) * 0.5 * (1 + math.cos(math.pi * decay_ratio))

@torch.no_grad()
def estimate_loss():
    model.eval()
    losses = []
    for _ in range(eval_iters // batch_size):
        x, y = get_batch('val')
        _, loss = model(x, y)
        losses.append(loss.item())
    model.train()
    return sum(losses) / len(losses) if losses else 0

# Estimate initial loss
print("Estimating initial loss...")
init_loss = estimate_loss()
print(f"Initial validation loss: {init_loss:.4f}")

print(f"\nStarting training for {max_iters} iterations...")
print(f"Checkpoint directory: {out_dir}")

start_time = time.time()
best_val_loss = init_loss

for iter_num in range(max_iters):
    t0 = time.time()
    
    # Update LR
    lr = get_lr(iter_num)
    for param_group in optimizer.param_groups:
        param_group['lr'] = lr
    
    # Get batch
    x, y = get_batch('train')
    
    # Forward pass
    logits, loss = model(x, y)
    
    # Backward
    optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    optimizer.step()
    
    # Timing
    dt = time.time() - t0
    
    # Logging
    if iter_num % log_interval == 0:
        print(f"iter {iter_num:5d} | loss {loss.item():.4f} | lr {lr:.6f} | dt {dt*1000:.2f}ms")
    
    # Eval
    if iter_num > 0 and iter_num % eval_interval == 0:
        val_loss = estimate_loss()
        print(f"iter {iter_num:5d} | val_loss {val_loss:.4f}")
        
        # Save checkpoint
        if always_save_checkpoint or val_loss < best_val_loss:
            best_val_loss = val_loss
            ckpt = {
                'model': model.state_dict(),
                'model_args': model_args,
                'iter_num': iter_num,
                'best_val_loss': best_val_loss,
                'config': {
                    'dataset': dataset,
                    'vocab_size': vocab_size,
                }
            }
            ckpt_path = os.path.join(out_dir, 'ckpt.pt')
            torch.save(ckpt, ckpt_path)
            print(f"  -> Saved checkpoint to {ckpt_path}")

# Final save
print("\nTraining complete!")
print(f"Total time: {time.time() - start_time:.1f}s")
print(f"Best validation loss: {best_val_loss:.4f}")

# Save final checkpoint
ckpt = {
    'model': model.state_dict(),
    'model_args': model_args,
    'iter_num': max_iters,
    'best_val_loss': best_val_loss,
    'config': {
        'dataset': dataset,
        'vocab_size': vocab_size,
    }
}
ckpt_path = os.path.join(out_dir, 'ckpt.pt')
torch.save(ckpt, ckpt_path)
print(f"Final checkpoint saved to {ckpt_path}")
