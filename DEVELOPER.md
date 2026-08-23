# 🛠️ PersonaVault Developer Guide

Welcome to the PersonaVault Developer Ecosystem. This guide covers how to integrate with the **Decision Operating System (DOS)** using our Python SDK and CLI.

---

## 📦 Python SDK

The PersonaVault Python SDK allows you to embed sovereign intelligence and decision governance directly into your applications.

### 1. Installation

Currently in Alpha. You can include it in your project by pointing to the `sdk/python` directory or installing locally:

```bash
cd personavault/backend/sdk/python
pip install -e .
```

### 2. Basic Usage

```python
from personavault import PersonaVault

# Initialize client
pv = PersonaVault(host="http://localhost:8000")

# Login (Session management is automatic)
pv.login("admin", "admin123")

# Create a Decision
decision = pv.decisions.create(
    domain="security",
    event_type="incident_response",
    decision="blocked",
    confidence=0.95,
    reason="Suspicious network pattern detected from unauthorized IP."
)

print(f"✅ Decision Logged: {decision.id}")
```

### 3. Interacting with the Swarm

The Swarm interface allows you to query the collective intelligence of all specialized agents.

```python
# Simple Chat
response = pv.swarm.chat("Analyze the latest security trends in the vault.")
print(f"🤖 Swarm: {response['response']}")

# Complex Decision Generation
problem = "A user is requesting access to high-sensitivity clinical data without a valid token."
result = pv.swarm.decide(problem, domain="compliance")

print(f"🎯 Recommended Action: {result['decision']}")
print(f"🧠 Reasoning: {result['reason']}")
```

### 4. Data Models

The SDK uses Pydantic models for full type safety:
- `Decision`: Core decision record with timestamps and audit IDs.
- `Pattern`: Learned behaviors from the reinforcement engine.
- `Memory`: Layer 2 (Episodic) and Layer 3 (Semantic) entries.
- `AuditLog`: Compliance-grade execution records.

---

## 🖥️ CLI (`pv`)

The `pv` tool is designed for DevOps automation, instance management, and real-time observability.

### 1. Setup

Make the CLI executable and optionally add it to your PATH:

```bash
chmod +x personavault/backend/cli/pv
alias pv='/home/user/personavault/backend/cli/pv'
```

### 2. Commands

#### **Chat with the Swarm**
```bash
pv chat "What is the current status of the intelligence registry?" --provider ollama
```

#### **Log a Decision**
```bash
pv decide --domain legal --decision "approved" --reason "Contract matches all policy constraints"
```

#### **Replay a Decision Trace**
Instantly view the full cognitive execution trace for a decision.
```bash
pv replay [EVENT_ID]
```

#### **Monitor Trends**
```bash
pv trends --days 7 --format json
```

---

## 🌐 REST API

PersonaVault exposes a full OpenAPI 3.1 compliant spec.
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints:
- `POST /api/v1/generative/chat`: Real-time streaming intelligence.
- `POST /api/v1/behaviour/event`: Inject new decision evidence.
- `GET /api/v1/mode/current`: Check sovereign execution constraints.
- `POST /api/v1/registry/swap`: Change providers at runtime.

---

## 🔒 Security & Best Practices

1. **API Keys**: In production, always use `PV_API_KEY` environment variables.
2. **Execution Modes**: Use `RESTRICTED` mode for high-security, air-gapped processing where external tool access is forbidden.
3. **Audit Readiness**: Every SDK/CLI action is logged to the internal `AuditLog`. Use the `pv audit export` (planned) command for compliance reporting.

---

## 🚀 Roadmap

- [ ] Node.js / TypeScript SDK
- [ ] `pv pack install` for remote Behaviour Packs
- [ ] WebSocket streaming support in the Python SDK
- [ ] Encrypted local caching for the SDK Client
