# Noesis Module — Wrong Room Collective Agent Integration

**Noesis** (Greek: νόησις — "pure knowing") is the intuition module of the Wrong Room Collective agent framework. It wraps Karpathy's nanoGPT as a character-level language model trained on baseball text, providing probabilistic insights about first-5 inning outcomes.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   WrongRoomAgent                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │ Perceive │→ │ Intuit   │→ │ Decide   │→ │ Execute    │ │
│  │  (MLB)   │  │ (Noesis) │  │Curiosity │  │ (Pipeline) │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          ↓
              ┌───────────────────────┐
              │    NoesisEngine       │
              │  (nanoGPT wrapper)     │
              │  Character-level GPT  │
              │  Baseball corpus       │
              └───────────────────────┘
```

---

## Quick Start

### 1. Prepare Data

```bash
cd /root/mlb-first5
python3 noesis/prepare_data.py
```

This creates `data/baseball_char/train.bin`, `val.bin`, and `meta.pkl` from the MLB model data.

### 2. Train the Model

```bash
# Fast training (0.8M params, ~20 min on CPU)
python3 noesis/train_noesis_better.py

# Or ultra-fast (0.1M params, ~5 min)
python3 noesis/train_mini.py
```

The model is saved to `out/noesis_checkpoint/ckpt.pt`.

### 3. Query Noesis

```python
from noesis.noesis_engine import NoesisEngine

noesis = NoesisEngine()
if noesis.is_ready():
    # Direct generation
    result = noesis.generate("Gerrit Cole vs Yankees in first 5 innings", max_new_tokens=100)
    print(result)
    
    # Ask about a pitcher
    result = noesis.ask_noesis("Shane Bieber", opponent="Cubs")
    print(result['intuition'])
```

### 4. Use with Agent

```python
from agent import WrongRoomAgent

agent = WrongRoomAgent(use_noesis=True)
result = agent.full_cycle("Gerrit Cole")
print(result['noesis_intuition'])
print(result['execution']['prediction'])
```

---

## Noesis Engine API

### `NoesisEngine`

**Initialization:**
```python
noesis = NoesisEngine(
    checkpoint_dir='/root/mlb-first5/out/noesis_checkpoint',
    device='cpu'  # or 'cuda'
)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `is_ready()` | Returns `True` if checkpoint loaded |
| `generate(prompt, max_new_tokens=100, temperature=0.8, top_k=50)` | Generate text from prompt |
| `ask_noesis(pitcher, opponent=None, question=None)` | Ask about a pitcher matchup |
| `get_intuition_about(pitcher, opponent_stats=None)` | Get pitcher intuition |
| `compare_pitchers(p1, p2)` | Compare two pitchers |
| `what_if(scenario)` | Generate what-if scenario |

---

## Training Configuration

### Default Config (train_noesis_better.py)
- **Params:** 0.83M (n_layer=4, n_embd=128, n_head=4)
- **Block size:** 256
- **Batch size:** 16
- **Max iterations:** 2000
- **Learning rate:** 5e-4 → 1e-4 (cosine decay)

### Fast Config (train_mini.py)
- **Params:** 0.11M (n_layer=2, n_embd=64, n_head=2)
- **Block size:** 128
- **Batch size:** 8
- **Max iterations:** 1500

### Shakespeare Config (for reference)
- **Params:** 10M (n_layer=6, n_embd=384, n_head=6)

---

## The Baseball Corpus

The corpus at `data/baseball_corpus.txt` contains ~105K lines derived from `data/processed/model_data.csv`:

```
Gerrit Cole: ERA=3.23, WHIP=1.06, K/9=12.076, BB/9=2.038, K/BB=5.927, Record=16-8, First5Runs=1, Predicted=1.35, Outcome=LOW_SCORING
Shane Bieber: ERA=3.181, WHIP=1.216, K/9=12.536, BB/9=3.087, K/BB=4.061, Record=7-4, First5Runs=3, Predicted=1.32, Outcome=PUSH
```

### Corpus Contents
- Pitcher stat summaries (ERA, WHIP, K/9, BB/9, K/BB)
- Game records with predictions and outcomes
- Player profiles with career stats
- What-if scenario templates

---

## Integration with Agent Framework

### WrongRoomAgent

The agent integrates Noesis as the "intuition" step before rational analysis:

```python
# 1. PERCEIVE — Read MLB data
games = agent.perceive_mlb_data(pitcher_name="Gerrit Cole")

# 2. INTUIT — Query Noesis
intuition = agent.ask_noesis("Gerrit Cole", opponent="Yankees")

# 3. DECIDE — Apply curiosity engine
decision = agent.decide_with_curiosity(pitcher_data, intuition)

# 4. EXECUTE — Generate prediction
prediction = agent.execute_prediction(decision)
```

### WrongRoomBridge

Full pipeline integration:

```python
from wrong_room_bridge import WrongRoomBridge

bridge = WrongRoomBridge()

# Single pitcher analysis
result = bridge.full_cycle("Gerrit Cole")

# What-if scenario
scenario = bridge.run_whatif("What if Gerrit Cole faces a weak lineup after rest?")

# Batch analysis
results = bridge.batch_analysis(['Gerrit Cole', 'Shane Bieber', 'Luis Castillo'])
```

---

## File Structure

```
/root/mlb-first5/
├── noesis/
│   ├── noesis_engine.py       # Main Noesis wrapper
│   ├── prepare_data.py        # Corpus → train/val bin
│   ├── train_mini.py          # Fast training (0.1M params)
│   ├── train_noesis_better.py # Better training (0.8M params)
│   ├── train_noesis.py        # Full training script
│   └── README.md             # This file
├── out/
│   └── noesis_checkpoint/
│       └── ckpt.pt            # Trained model checkpoint
├── data/
│   ├── baseball_char/
│   │   ├── train.bin
│   │   ├── val.bin
│   │   └── meta.pkl
│   ├── sequences/
│   │   └── baserunner.pt      # Makemore model
│   └── baseball_corpus.txt   # Raw text corpus
├── agent.py                   # WrongRoomAgent with Noesis integration
├── makemore_baserunner.py     # Makemore for anomaly detection
└── wrong_room_bridge.py       # Full pipeline bridge
```

---

## How Intuition Works

Noesis doesn't predict — it *intuits*. Trained on 50K+ baseball game records, it learns the statistical patterns of pitcher performance and generates probable continuations of game narratives.

When you ask Noesis about a pitcher, it:
1. Encodes your query as character tokens
2. Uses the Transformer to predict likely next tokens
3. Samples from the probability distribution (with temperature)

The result is a probabilistic "hunch" — not a prediction, but a sense of what the data *tends toward*.

---

## Limitations

- **Model size:** Even 0.8M params is tiny for a GPT. Quality is limited.
- **Training time:** On CPU, 2000 iterations takes ~20 minutes. GPU would be 10x faster.
- **Character-level:** No tokenization beyond raw characters — patterns are learned from text structure.
- **Not a prediction model:** Noesis provides intuition, not calibrated probabilities.

For production predictions, use the actual ML models in `model.py` and `enhanced_pipeline.py`. Noesis is the *intuition layer* — the gut feeling before rational analysis.

---

## Retraining

To retrain on new data:

1. Update `build_corpus.py` to generate new corpus
2. Run `python3 noesis/prepare_data.py` to encode new data
3. Adjust `n_layer`, `n_embd`, `max_iters` in training config
4. Run training: `python3 noesis/train_noesis_better.py`

To use a different base model (GPT-2, etc.), modify `noesis_engine.py` to load from HuggingFace:

```python
from transformers import GPT2LMHeadModel, GPT2Tokenizer
model = GPT2LMHeadModel.from_pretrained('gpt2')
```

---

## References

- [nanoGPT by Andrej Karpathy](https://github.com/karpathy/nanoGPT)
- [makemore by Andrej Karpathy](https://github.com/karpathy/makemore)
- [Wrong Room Collective](https://github.com/GustheTrader/reality-agents)
