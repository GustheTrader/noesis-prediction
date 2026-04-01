"""
Sovereign OS — MetaClaw Integration

MetaClaw = Agent that meta-learns and evolves from conversations.

From: https://github.com/aiming-lab/MetaClaw
Paper: https://arxiv.org/abs/2603.17187

This module integrates MetaClaw into the Sovereign OS stack.
"""

# MetaClaw Integration Plan
#
# What MetaClaw does:
# - Intercepts LLM conversations
# - Injects skills at each turn
# - Learns from accumulated experience
# - Persists memory across sessions
# - RL training during idle/sleep time
#
# How it fits into Sovereign OS:
# - Skills layer for agents
# - Memory persistence (cross-session)
# - RL training for agent improvement
# - Skill evolution
#
# Installation:
#   pip install -e ".[all]"
#   metaclaw setup
#   metaclaw start
#
# Integration points:
# - MetaClaw sits between agents and LLM
# - Injects relevant skills from skill library
# - Learns from every conversation
# - Persists to Qdrant (our vector DB)
# - RL updates during idle time (scheduler)

METACLAW_SUMMARY = """
# MetaClaw — Summary

## What It Is
An agent that meta-learns and evolves in the wild.
Just talk to your agent — it improves automatically.

## Key Features
1. **Skill Injection** — Relevant skills injected at every turn
2. **Skill Evolution** — Skills improve from conversations
3. **Long-term Memory** — Cross-session persistence
4. **RL Training** — GRPO-based, runs during idle time
5. **Multi-Claw Support** — OpenClaw, CoPaw, IronClaw, etc.
6. **One-Click Deploy** — metaclaw setup + metaclaw start
7. **No GPU Required** — Works with any OpenAI-compatible API

## Three Modes
- **skills_only** — Proxy + skill injection. No RL.
- **rl** — Skills + RL training. Trains on full batch.
- **madmax** (default) — Skills + RL + smart scheduler.
  RL runs during sleep/idle/meeting windows only.

## Architecture
```
User ↔ Agent ↔ MetaClaw Proxy ↔ LLM API
                    ↓
              Skill Injection
                    ↓
              Session Summary
                    ↓
              New Skills Created
                    ↓
              RL Training (idle)
                    ↓
              Model Improvement
```

## Key Modules
- skill_manager.py — Skill CRUD + injection
- skill_evolver.py — Skill improvement via LLM
- scheduler.py — RL training scheduler (idle/sleep)
- trainer.py — GRPO training
- rollout.py — Environment rollout
- prm_scorer.py — Process reward model
- config.py — Configuration
- api_server.py — LLM proxy server
- memory_data/ — Persistent memory

## Paper
"MetaClaw: Just Talk — An Agent That Meta-Learns and Evolves in the Wild"
arxiv.org/abs/2603.17187
🏆 Ranked #1 on HuggingFace Daily Papers

## Sovereign OS Integration

### What MetaClaw Adds
- **Skill library** — Agents get better at specific tasks
- **Cross-session memory** — Agents remember across conversations
- **RL improvement** — Agents improve from experience
- **Skill evolution** — Skills themselves evolve

### How It Connects
```
SOVEREIGN OS AGENTS
├── MetaClaw (skill injection + learning)
│   ├── Skills from skill library
│   ├── Cross-session memory
│   └── RL training (idle time)
├── ATA Mesh (agent communication)
├── Qdrant (vector memory — MetaClaw can store here)
├── PostgreSQL (structured data)
└── Smart Router (query routing)
```

### Installation in Our Stack
```bash
# In noesis-prediction/
pip install aiming-metaclaw
metaclaw setup
metaclaw start

# Or as OpenClaw extension:
curl -LO https://github.com/aiming-lab/MetaClaw/releases/download/v0.4.0/metaclaw-plugin.zip
unzip metaclaw-plugin.zip -d ~/.openclaw/extensions
openclaw plugins enable metaclaw-openclaw
openclaw gateway restart
```
"""

if __name__ == "__main__":
    print(METACLAW_SUMMARY)
