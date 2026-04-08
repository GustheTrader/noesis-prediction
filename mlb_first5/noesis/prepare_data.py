#!/usr/bin/env python3
"""
Prepare baseball_char dataset for nanoGPT training.
Creates train.bin, val.bin, and meta.pkl in data/baseball_char/
"""
import os
import pickle
import numpy as np

def prepare_data():
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'baseball_char')
    os.makedirs(data_dir, exist_ok=True)
    
    # Read corpus
    with open(os.path.join(os.path.dirname(__file__), '..', 'data', 'baseball_corpus.txt'), 'r') as f:
        text = f.read()
    
    print(f"Loaded corpus: {len(text)} chars")
    
    # Get all unique characters and create mappings
    chars = sorted(list(set(text)))
    vocab_size = len(chars)
    print(f"Vocab size: {vocab_size}")
    print(f"Chars: {''.join(chars[:50])}...")
    
    # Create character mappings
    stoi = {ch: i for i, ch in enumerate(chars)}
    itos = {i: ch for i, ch in enumerate(chars)}
    
    # Encode entire corpus
    encode = lambda s: [stoi[c] for c in s]
    decode = lambda l: ''.join([itos[i] for i in l])
    
    encoded = encode(text)
    n = len(encoded)
    
    # Train/val split (90/10)
    train_size = int(0.9 * n)
    train_data = np.array(encoded[:train_size], dtype=np.uint16)
    val_data = np.array(encoded[train_size:], dtype=np.uint16)
    
    # Write binary files
    train_path = os.path.join(data_dir, 'train.bin')
    val_path = os.path.join(data_dir, 'val.bin')
    
    train_data.tofile(train_path)
    val_data.tofile(val_path)
    
    print(f"Train: {len(train_data)} tokens -> {train_path}")
    print(f"Val: {len(val_data)} tokens -> {val_path}")
    
    # Write meta.pkl
    meta = {
        'vocab_size': vocab_size,
        'chars': chars,
        'stoi': stoi,
        'itos': itos,
    }
    meta_path = os.path.join(data_dir, 'meta.pkl')
    with open(meta_path, 'wb') as f:
        pickle.dump(meta, f)
    
    print(f"Meta saved to {meta_path}")
    
    return vocab_size, chars

if __name__ == '__main__':
    prepare_data()
