# PersonaVault Architecture

## Strategic Thesis

PersonaVault is a **model-independent Decision Operating System (DOS)**. It decouples the AI inference engine from the organization’s accumulated, governed, and provenance-backed institutional intelligence.

**Core Thesis:** AI models generate intelligence; PersonaVault accumulates intelligence. PersonaVault owns institutional continuity.

---

## The Decision Intelligence Architecture: The Crystallization Loop

The architecture is designed to convert ephemeral interactions into durable organizational knowledge through a governance-backed feedback loop.

```text
       ┌─────────────────────────────────────┐
       │     THE CRYSTALLIZATION LOOP        │
       └─────────────────────────────────────┘
              │                 ▲
              ▼                 │
   ┌──────────────────┐   ┌───────────────┐
   │ AI Recommendation│ → │ Human Decision│
   └──────────────────┘   └───────┬───────┘
                                  │
                                  ▼
   ┌──────────────────┐   ┌───────────────┐
   │ Reinforcement    │ ← │ Real Outcome  │
   └────────┬─────────┘   └───────────────┘
            │
            ▼
   ┌──────────────────┐
   │ Crystallized Rule│ (Layer 3: Ice)
   └──────────────────┘
```

## Cognitive Execution Trace

PersonaVault utilizes **Cognitive Execution Traces** to provide an auditable explanation of system activity. This trace includes:
*   Agents involved
*   Evidence retrieved
*   Tools invoked
*   Policies applied
*   Decisions/recommendations
*   Validations performed
*   Confidence and Governance checks
*   Human interventions

---

## The Decision Operating System (Decision State)

Instead of a simple "Cognitive State," PersonaVault maintains an **Enterprise Decision State** for every interaction:

*   **Evidence State**: Sufficiency and relevance of retrieved memories.
*   **Policy State**: Active policies applied (P-184, etc.).
*   **Memory State**: Relevant retrieved patterns (Layer 1-3).
*   **Model State**: The specific AI engine utilized.
*   **Confidence/Uncertainty**: Numerical metrics.
*   **Authorization**: Governance and permission status.
*   **Outcome State**: The final real-world result (e.g., successful/failed).

---

## The Strategic Moat

The moat is not the Three-Layer Memory architecture; the moat is the **accumulated crystallized state**. As an organization uses PersonaVault, the system learns:
*   How the organization behaves.
*   Which policies work in practice.
*   Where humans override AI.
*   Empirical outcome evidence.

A better AI model doesn't threaten PersonaVault; it gives PersonaVault a better engine with which to compound the organization's existing intelligence.

---

## The Decision Operating System (DOS) Architecture

Inspired by **DeepSeek Harness**, PersonaVault 2026 utilizes a **Service-Oriented monorepo architecture** that emphasizes spatiotemporal composability.

### 1. Service Registry (Cordis-Inspired)
The `ServiceRegistry` is the backbone of the DOS. It allows runtime swapping of core components without system restarts.
*   **Inference Providers**: Dynamic switching between Ollama, Groq, and Gemini.
*   **Memory Providers**: Hot-swapping episodic and semantic storage engines.
*   **Governance Providers**: Runtime activation of local or cryptographic (VeriLink) trust protocols.

### 2. Sovereign Execution Modes
The system operates in four specialized modes to balance risk and performance:
*   **Standard Mode**: Full tool access with mandatory HITL approval gates.
*   **Restricted Mode**: Air-gapped execution, utilizing only "Ice" (Semantic) memory.
*   **Simulation Mode**: Sandboxed decision replay with no side effects.
*   **Audit Mode**: Read-only access with intensified system logging.

### 3. Observability Layer
A deep instrumentation layer that tracks performance at the request level:
*   **Memory Hit Rate**: Tracking how often crystallized intelligence (Ice) is utilized.
*   **Token Efficiency**: Measuring the cost-per-decision.
*   **Processing Latency**: Real-time duration metrics injected into response headers.

---

## Cognitive Execution Trace


PersonaVault is a **Sovereign Organisational Intelligence Platform** built on the Decision Operating System architecture. The core philosophy is to capture, learn, and improve how organisations make decisions.

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

### Human-In-The-Loop (HITL) Paradigms
1.  **Blocking HITL (Approval Gates)**: When uncertainty is high (< 0.6) or governance is violated, the swarm halts for explicit user approval.
2.  **Active Steering (Leapfrog HITL)**: Operators can observe the reasoning process in the live feed and inject instructions directly into the L1 Blackboard to redirect agents without suspending execution.

### Confidence Scoring
*   **High (>= 0.8)**: Autonomous execution.
*   **Medium (0.6 - 0.79)**: Warning logged, background evaluation intensified.
*   **Low (< 0.6)**: Automatic transition to HITL (Human-in-the-loop).

### HITL Triggers
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
During development, the `VectorService` utilizes **FAISS** for local embedding management and K-Nearest Neighbor (KNN) searches. This allows for high-speed retrieval of Layer 3 memories without requiring a dedicated cloud vector database.

### 3. Knowledge Graph (SQL-Graph Simulation)
The `GraphService` manages relationships between entities and memories. To maintain development speed in constrained environments, graph traversal is simulated via **Graph Adjacency Tables** within SQL.

## 🛡️ Strategic Infrastructure Note

PersonaVault employs an **"Integrated-to-Distributed"** evolution strategy:
*   **Development Lattices (Current):** We utilize **SQLite** (Cloud Shell) for relational data, **FAISS** for vector retrieval, and simulated SQL tables for graph relationships.
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
*   **HITL-as-a-Service**: A core module managing the "Cognitive State" when human intervention is required.
*   **TaskService**: Handles background maintenance like memory expiration, periodic reflection, and data retention policies.

## Middleware & Security

The application enforces a multi-layered security approach:
1.  **Audit Middleware**: Logs every state-changing request for compliance.
2.  **RBAC Middleware**: Enforces Role-Based Access Control before requests reach the handlers.
3.  **Rate Limiter**: Protects the API and AI providers from abuse.
4.  **Security Headers**: Implements standard protections like `X-Frame-Options: DENY`.

### 📊 Observability & System Control

The system is designed for production-grade monitoring, featuring a newly refactored, modular dashboard:
*   **Prometheus**: Tracking request latency and error rates across all endpoints.
*   **Cognified Admin Dashboard**: A specialized router (`dashboard_router.py`) providing a modular UI:
    *   **Learning Dashboard**: Visualizes reinforcement pattern extraction, confidence trends, and learning metrics.
    *   **Agent Orchestration**: Real-time visualization of agent swarm activity via WebSocket.
    *   **Configuration Manager**: Extensible interface for domain settings.
*   **Cognitive Narrative Stream**: Real-time human-readable monitoring of agent swarm reasoning.
*   **Cognitive Execution Trace**: Structural graph representation of swarm negotiation steps, persisted via `CognitiveBlackboard` for real-time visualization.
*   **Real-time Telemetry**: WebSocket-based streaming for IoT simulation and live system logs.
*   **Model Management**: Direct interface for pulling and deleting Ollama models.

## Request Lifecycle

1.  Client connects via REST or WebSocket.
2.  Middlewares process authentication, auditing, and rate limiting.
3.  FastAPI Router dispatches to the appropriate Service.
4.  Service interacts with the Data Layer (SQL, Graph, or Vector).
5.  Response is returned with Prometheus metrics captured.
