# PersonaVault Architecture

## System Overview

PersonaVault is a **Sovereign Organisational Intelligence Platform** built on a **Decision Operating System** architecture. The core philosophy is to capture, learn, and improve how organisations make decisions.

---

## The Decision Intelligence Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  🏛️ PersonaVault - Decision Operating System             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Event → Decision → Behaviour → Explain → Audit → Learn   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │               Behaviour Packs                        │    │
│  │  Security │ Legal │ Insurance │ Procurement │ Compliance │ │
│  │  Robotics                                            │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ↓                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 Decision Engine                      │    │
│  │  • Policy Engine    • Reinforcement                 │    │
│  │  • Explainability   • Audit                        │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ↓                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │               Behaviour Memory                       │    │
│  │  • Events  • Decisions  • Outcomes  • Context      │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ↓                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │               Three-Layer Memory                     │    │
│  │  Layer 1 (Gas) → Layer 2 (Liquid) → Layer 3 (Ice) │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Current Platform Metrics

| Domain | Events | Confidence | Trend |
|--------|--------|------------|-------|
| Security Intelligence | 54 | 90.8% | 📈 Improving |
| Compliance Intelligence | 7 | 94.6% | 📈 Improving |
| Contract Intelligence | 15 | 87.9% | 📈 Improving |
| Procurement Intelligence | 1 | 80.0% | 📈 Improving |
| Insurance Intelligence | 4 | 91.5% | 📈 Improving |
| Robotics Intelligence | 0 | 92.0% | 📈 Improving |
| **TOTAL** | **81** | **90.5%** | **📈 Improving** |

---

## 🔍 Decision Timeline System

Every decision is captured in a 5-step timeline:

1. **Detection** - Event identified
2. **Policy Match** - Relevant policies applied
3. **AI Recommendation** - AI suggests action with confidence
4. **Decision Made** - Human or AI decision with reasoning
5. **Audit Logged** - Full audit record with traceability

---

## 🔄 Decision Replay System

Replay any decision at any point in time:
- Compare decisions across time
- See how policies would change
- Understand evolution of decision patterns

---

## 📈 Trend Analysis System

Track confidence and decision patterns over time:
- Average confidence per domain
- Decision distribution analysis
- Improvement trends
- Outcome distribution

---

## 📦 Behaviour Packs

Declarative configuration for any domain:

```yaml
pack:
  name: Security Intelligence
  domain: security
  entities: [incident, alert, investigation]
  events: [incident_response]
  policies: [...]
  metrics: [...]
  evaluation_rules: [...]
```

---

## 🔒 Governance Layer

- **Audit Trail**: Complete record of every decision
- **Explainability**: Human-readable explanations
- **Compliance**: Built-in governance and policies
- **Sovereignty**: Data remains under your control

---

## 🚀 Performance Metrics

| Operation | Target (P95) | Current |
|-----------|--------------|---------|
| Timeline Creation | < 500ms | ✅ |
| Replay Analysis | < 500ms | ✅ |
| Trend Analysis | < 1s | ✅ |
| AI Chat (Local) | < 2s | ✅ |

---

## 🦾 Robotics Intelligence Pack

The Robotics Intelligence Pack enables robots with memory, personality, and explainable decision-making:

| Feature | Description |
|---------|-------------|
| **User Profiling** | Learns individual user preferences and personality traits |
| **Decision Timeline** | Full history of every robot decision with reasoning |
| **Safety Monitoring** | Pattern-based safety event detection and prevention |
| **Trust Tracking** | Measures user trust scores over time |
| **Personalization** | Adapts behavior based on user history |

**Use Cases:**
- Healthcare companion robots
- Manufacturing & logistics robots
- Assistive robots for elderly care
- Service & social robots
- Security & surveillance robots

## 🌐 The Cognitive Ecosystem Vision

PersonaVault is not a single agent but a **collaborative swarm** of specialized agents:
*   **Health Agent**: Monitors wearables and medical data.
*   **Home Agent**: Manages smart home environment.
*   **Mobile Agent**: Coordinates with personal devices.
*   **Vehicle Agent**: Integrates with car systems.

Agents communicate via a shared **Cognitive Blackboard** and negotiate actions based on a unified understanding of the user's state and preferences.

### Cognitive State
The system maintains a "Cognitive State" representing its current reasoning confidence. This state is visualized via the **Live Swarm Feed** and the **Chain-of-Thought (CoT) Graph**.

#### Human-In-The-Loop (HITL) Paradigms
1.  **Blocking HITL (Approval Gates)**: When uncertainty is high (< 0.6) or governance is violated, the swarm halts for explicit user approval.
2.  **Active Steering (Leapfrog HITL)**: Operators can observe the reasoning process in the live feed and inject instructions directly into the L1 Blackboard to redirect agents without suspending execution.

#### Confidence Scoring
*   **High (>= 0.8)**: Autonomous execution.
*   **Medium (0.6 - 0.79)**: Warning logged, background evaluation intensified.
*   **Low (< 0.6)**: Automatic transition to HITL (Human-in-the-loop).

#### HITL Triggers
1.  **Validator Failure**: Significant discrepancy between retrieved evidence and reasoning logic.
2.  **Judge Rejection**: Low scores in faithfulness or relevance.
3.  **Governance Violation**: Intent flagged by the Local Guardian Constitution.

## 🛡️ Governance & Local Guardian

PersonaVault implements a multi-layered safety strategy:
1.  **VeriLink Governance Plugin**: External cryptographic trust protocol (VAP) for auditable receipts.
2.  **Local Guardian Constitution**: A managed set of policy rules stored in `governance_constitution.json`.

Administrators can manage these rules via the **Visual Rule Editor** in the Admin Dashboard, which supports keyword triggers and direct JSON source editing.

### Standardized Intelligence (MCP)
PersonaVault utilizes the **Model Context Protocol (MCP)** to decouple the AI's cognitive reasoning from its data sources and tools.
*   **PersonaVault as MCP Server**: Exposes crystallized memories (Layer 3) to external models.
*   **Agents as MCP Clients**: Allows the swarm to utilize third-party tools (APIs, Local DBs) via a unified interface.


## Data Layer

PersonaVault employs a three-layer memory architecture characterized by state changes:
*   **Layer 1: Working (Gas)** - Transient context and real-time IoT data.
*   **Layer 2: Episodic (Liquid)** - Interaction history and evaluation logs stored in relational SQL.
*   **Layer 3: Semantic (Ice)** - Crystallized, **weight-reinforced** patterns and constraints stored in Vector and Graph stores.

### The Reinforcement Engine

| Component | Function | Evidence |
|-----------|----------|----------|
| **Judge Agent** | Evaluates every response for faithfulness, coverage, relevance | 4 patterns created |
| **Consolidation Service** | Extracts corrective patterns from failures | 7 successes recorded |
| **Pattern Weighting** | +0.05 per success, -0.10 per failure | Pattern #1 at 0.90 weight |
| **Threshold Deactivation** | Auto-disable patterns below 0.40 weight | Planned |
| **Reinforcement Decay** | Decay unused patterns | Experimental |

### 1. Relational Metadata & Interaction Logs (SQL)
Uses **SQLAlchemy** (targeting PostgreSQL/SQLite) to manage Layer 2 episodic data and system state:
*   User profiles and authentication.
*   Session management.
*   Audit logs and system configurations.
*   Legal matters, Documents, and Workflow tasks.

### 2. Semantic Search (Vector Store)
During development, the `VectorService` utilizes **FAISS** for local embedding management and K-Nearest Neighbor (KNN) searches. This allows for high-speed retrieval of Layer 3 memories without requiring a dedicated cloud vector database. It is responsible for:
*   Storing memory embeddings.
*   Performing K-Nearest Neighbor (KNN) searches to find semantically relevant memories based on natural language queries.

### 3. Knowledge Graph (SQL-Graph Simulation)
The `GraphService` manages relationships between entities and memories. To maintain development speed in constrained environments, graph traversal is simulated via **Graph Adjacency Tables** within SQL. This allows the AI to understand the *context* of a memory (e.g., "Who was present during this event?") without requiring a standalone graph engine.

## 🛡️ Strategic Infrastructure Note

PersonaVault employs an **"Integrated-to-Distributed"** evolution strategy:
*   **Development Lattices (Current):** We utilize **SQLite** (Cloud Shell) for relational data, **FAISS** for vector retrieval, and simulated SQL tables for graph relationships. This reduces operational overhead while enabling the full cognitive loop.
*   **Production Scale-Out:** The architecture is designed for a seamless migration to specialized engines:
    *   **PostgreSQL** (Relational Metadata)
    *   **Weaviate** (High-scale Vector Retrieval)
    *   **Neo4j** (Native Knowledge Graph)

### Connectivity Modes
*   **Local-First (Air-Gapped):** Configuration to connect to local database instances on the user's hardware.
*   **Cloud-Hybrid:** Support for utilizing managed online database free tiers for each paradigm.

## Service Layer

*   **MemoryService**: Orchestrates the dual-write and dual-read operations between SQL and Vector stores.
*   **GeneratorAgent**: The LLM interface. It abstracts the complexity of switching between Ollama and Gemini.
*   **EmpathyAgent**: Interprets real-time situational data to ground the AI's emotional response tone.
*   **IoTService**: Processes telemetry data. Real-time data is ingested via WebSockets and persisted for historical analysis.
*   **HITL-as-a-Service**: A core module managing the "Cognitive State" when human intervention is required for high-stakes decisions or low-confidence reasoning.
*   **TaskService**: Handles background maintenance like memory expiration, periodic reflection, and data retention policies.

## Middleware & Security

The application enforces a multi-layered security approach:
1.  **Audit Middleware**: Logs every state-changing request for compliance.
2.  **RBAC Middleware**: Enforces Role-Based Access Control before requests reach the handlers.
3.  **Rate Limiter**: Protects the API and AI providers from abuse.
4.  **Security Headers**: Implements standard protections like `X-Frame-Options: DENY`.

## 📊 Observability & System Control

The system is designed for production-grade monitoring:
*   **Prometheus**: Tracking request latency and error rates across all endpoints.
*   **Cognified Admin Dashboard**: A specialized router (`admin_dashboard.py`) providing real-time metrics, disk usage breakdown, and AI provider health.
*   **Real-time Telemetry**: WebSocket-based streaming for IoT simulation and live system logs (SSE).
*   **Model Management**: Direct interface for pulling and deleting Ollama models.

## 🏆 The Moat

> **"Every decision across your organisation makes your entire enterprise more intelligent, while all value remains under your control."**

### The "Compounding Advantage"

```mermaid
graph LR
    A[Day 1] -->|0 Patterns| B[Day 30]
    B -->|4 Patterns| C[Day 60]
    C -->|Patterns at 0.90+ Weight| D[Day 90]
    D -->|Exponential Growth| E[Uncatchable Lead]
```

## Request Lifecycle

1.  Client connects via REST or WebSocket.
2.  Middlewares process authentication, auditing, and rate limiting.
3.  FastAPI Router dispatches to the appropriate Service.
4.  Service interacts with the Data Layer (SQL, Graph, or Vector).
5.  Response is returned with Prometheus metrics captured.