#!/usr/bin/env python3
"""
Noesis Engine - Wraps nanoGPT as an "intuition module" for the agent.
Provides probabilistic insights about baseball matchups.
"""
import os
import sys
import pickle
import torch

# Add nanoGPT to path
NANOGPT_PATH = '/root/nanoGPT'
sys.path.insert(0, NANOGPT_PATH)

from model import GPTConfig, GPT

class NoesisEngine:
    """
    Noesis = "Pure knowing" - the intuition module that uses nanoGPT
    to generate probabilistic insights about baseball outcomes.
    
    This wraps a character-level GPT trained on baseball text corpus
    to provide intuitive predictions about pitcher matchups.
    """
    
    def __init__(self, checkpoint_dir=None, device='cpu'):
        self.device = device
        self.checkpoint_dir = checkpoint_dir or '/root/mlb-first5/out/noesis_checkpoint'
        self.model = None
        self.meta = None
        self.encode = None
        self.decode = None
        self.ready = False
        
        # Try to load existing checkpoint
        self._load_checkpoint()
    
    def _load_checkpoint(self):
        """Load the trained nanoGPT checkpoint."""
        ckpt_path = os.path.join(self.checkpoint_dir, 'ckpt.pt')
        meta_path = '/root/mlb-first5/data/baseball_char/meta.pkl'
        
        if not os.path.exists(ckpt_path):
            print(f"Noesis: No checkpoint found at {ckpt_path}")
            print("Noesis: Run train_noesis.py first to train the model")
            return
        
        if not os.path.exists(meta_path):
            print(f"Noesis: No meta.pkl found at {meta_path}")
            return
        
        # Load meta
        with open(meta_path, 'rb') as f:
            self.meta = pickle.load(f)
        
        stoi = self.meta['stoi']
        itos = self.meta['itos']
        self.encode = lambda s: [stoi[c] for c in s]
        self.decode = lambda l: ''.join([itos[i] for i in l])
        
        # Load model
        checkpoint = torch.load(ckpt_path, map_location=self.device, weights_only=False)
        model_args = checkpoint.get('model_args', {
            'n_layer': 2, 'n_head': 2, 'n_embd': 32,
            'block_size': 64, 'bias': False, 'vocab_size': 75, 'dropout': 0.0
        })
        gptconf = GPTConfig(**model_args)
        self.model = GPT(gptconf)
        
        state_dict = checkpoint['model']
        unwanted_prefix = '_orig_mod.'
        for k, v in list(state_dict.items()):
            if k.startswith(unwanted_prefix):
                state_dict[k[len(unwanted_prefix):]] = state_dict.pop(k)
        
        self.model.load_state_dict(state_dict)
        self.model.eval()
        self.model.to(self.device)
        
        self.ready = True
        print(f"Noesis: Loaded checkpoint from {ckpt_path}")
        print(f"Noesis: Model config: {gptconf}")
    
    def is_ready(self):
        """Check if model is loaded and ready."""
        return self.ready
    
    def generate(self, prompt, max_new_tokens=100, temperature=0.8, top_k=50):
        """
        Generate text from a prompt.
        
        Args:
            prompt: The input text (e.g., "Given Gerrit Cole vs Yankees...")
            max_new_tokens: Max tokens to generate
            temperature: Sampling temperature (lower = more deterministic)
            top_k: Top-k sampling parameter
        
        Returns:
            Generated text string
        """
        if not self.ready:
            return "Noesis not ready - model not loaded"
        
        # Encode prompt
        start_ids = self.encode(prompt)
        x = torch.tensor(start_ids, dtype=torch.long, device=self.device)[None, ...]
        
        # Generate
        with torch.no_grad():
            y = self.model.generate(x, max_new_tokens, temperature=temperature, top_k=top_k)
        
        # Decode
        generated = self.decode(y[0].tolist())
        
        # Return only the new part (after prompt)
        if generated.startswith(prompt):
            return generated[len(prompt):]
        return generated
    
    def ask_noesis(self, pitcher, opponent=None, context=None, question=None):
        """
        Ask noesis about a pitcher matchup.
        
        Args:
            pitcher: Pitcher name
            opponent: Opponent team (optional)
            context: Additional context (optional)
            question: Specific question to ask (optional)
        
        Returns:
            Probabilistic intuition string
        """
        if not self.ready:
            return "Noesis not ready"
        
        # Build prompt
        prompt_parts = [f"Pitcher: {pitcher}"]
        if opponent:
            prompt_parts.append(f"vs {opponent}")
        if context:
            prompt_parts.append(f"Context: {context}")
        if question:
            prompt_parts.append(f"Question: {question}")
        
        prompt = ' '.join(prompt_parts)
        prompt += "\nIntuition:"
        
        # Add some starting context to guide generation
        full_prompt = f"Given {pitcher} facing opponent in first 5 innings.\n"
        
        response = self.generate(full_prompt, max_new_tokens=150, temperature=0.7)
        return response
    
    def get_intuition_about(self, pitcher, opponent_stats=None):
        """
        Get a probabilistic intuition about a pitcher.
        
        Args:
            pitcher: Pitcher name
            opponent_stats: Dict of opponent stats (optional)
        
        Returns:
            Intuition string with probabilistic prediction
        """
        if not self.ready:
            return "Noesis not ready - model not loaded. Run train_noesis.py first."
        
        prompt = f"Analysis of {pitcher} in first 5 innings:\n"
        
        response = self.generate(prompt, max_new_tokens=100, temperature=0.6)
        return response
    
    def compare_pitchers(self, pitcher1, pitcher2):
        """
        Compare two pitchers - who has better first-5 outlook?
        
        Args:
            pitcher1: First pitcher name
            pitcher2: Second pitcher name
        
        Returns:
            Comparison intuition
        """
        if not self.ready:
            return "Noesis not ready"
        
        prompt = f"Compare {pitcher1} vs {pitcher2} for first 5 innings matchup:\n"
        
        response = self.generate(prompt, max_new_tokens=150, temperature=0.7)
        return response
    
    def what_if(self, scenario):
        """
        Generate a "what-if" scenario analysis.
        
        Args:
            scenario: What-if scenario description
        
        Returns:
            Scenario analysis
        """
        if not self.ready:
            return "Noesis not ready"
        
        prompt = f"What-if: {scenario}\nAnalysis:"
        
        response = self.generate(prompt, max_new_tokens=200, temperature=0.8)
        return response


def load_noesis(checkpoint_dir=None):
    """Convenience function to load Noesis engine."""
    return NoesisEngine(checkpoint_dir=checkpoint_dir)


if __name__ == '__main__':
    # Test the engine
    print("=== Noesis Engine Test ===")
    noesis = NoesisEngine()
    
    if noesis.is_ready():
        print("\nModel loaded successfully!")
        
        # Test generation
        print("\nTest 1: Ask noesis about a pitcher")
        print(noesis.ask_noesis("Gerrit Cole", opponent="Yankees"))
        
        print("\nTest 2: Get intuition")
        print(noesis.get_intuition_about("Shane Bieber"))
        
        print("\nTest 3: What-if scenario")
        print(noesis.what_if("What if Gerrit Cole faces a weak lineup after rest?"))
    else:
        print("Noesis not ready - no checkpoint found")
        print("Run train_noesis.py to train the model first")
