# PersonaVault

A local-first system for governed AI memory. PersonaVault records what an
AI learns, when, from what source, under what policy — and makes that record
available for audit. It runs entirely on your hardware. It learns from
documents, decisions, and corrections over time.

## What it does
- Ingests from sources you choose (documents, folders, decisions, corrections)
- Crystallizes recurring patterns into a persistent, governed memory
- Records provenance for every pattern: where it came from, when, and why
- Knows what it knows and what it doesn't (gap-awareness)
- Runs offline; connects to cloud AI only if you ask it to

## What it isn't
- Not a chatbot
- Not a RAG system
- Not a cloud service
- Not AGI

## Quick start

```bash
# Clone and navigate
git clone https://github.com/yourusername/personavault.git
cd personavault/backend

# Install dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Start the server
./scripts/dev_start.sh

# Access the dashboard
# Open: http://localhost:8000/admin/dashboard
# Login: admin / admin123
```

## Architecture
See [ARCHITECTURE.md](ARCHITECTURE.md)

## Status
V3 Phase II — core thermodynamic memory, synthesis, inference, and
schema hardening complete. See [TODO.md](TODO.md) for open work.
