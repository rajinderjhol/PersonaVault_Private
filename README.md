# PersonaVault

A local-first system for governed AI memory. PersonaVault records what an
AI learns, when, from what source, under what policy — and makes that record
available for audit. It runs entirely on your hardware. It learns from
documents, decisions, and corrections over time.

It's built for organizations that need to know what their AI knows — and
be able to prove it.

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

## Who it's for
Teams that run AI on sensitive data and need a verifiable record of what it
learned — legal, clinical, compliance, security, and any org where an auditor
will eventually ask "how do you know?"

## Quick start

```bash
# Clone and navigate
git clone https://github.com/rajinderjhol/PersonaVault_Private.git
cd PersonaVault_Private/backend

# Install dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Start the server
./scripts/dev_start.sh

# Access the dashboard
# Open: http://localhost:8000/admin/dashboard
# Default dev credentials are in .env.example — change before deploying.
```

## Architecture
Three-layer memory (Gas → Liquid → Ice), a multi-agent swarm, and a
governance layer that gates every crystallized pattern. See
[ARCHITECTURE.md](ARCHITECTURE.md) for the full picture.

## Status
V3 Phase II — core thermodynamic memory, synthesis, inference, and
schema hardening complete. See [TODO.md](TODO.md) for open work.
