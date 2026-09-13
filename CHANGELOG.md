# Changelog

All notable changes to PersonaVault will be documented in this file.

The format is based on Keep a Changelog.

---

## [2.0.0] - 2026-09-01

### 🛡️ Sovereign Intelligence Runtime (V2)
This release introduces the **Sovereign Intelligence Runtime (V2)**, a major architectural evolution that operates alongside the V1 Decision Operating System. V2 focuses on autonomous environmental learning, strict isolation, and trust-based governance.

#### Added (V2 Architecture)
- **Sovereign Intelligence Loop**: Autonomous `Environment → Event → Outcome → Learning → Crystallization` cycle.
- **Environment Isolation**: Strict logical and physical boundaries between sovereign environments.
- **Trust Policy Configuration**: New system for managing probabilistic thresholds across memory layers (Gas/Liquid/Ice).
- **Intelligence Source Control**: Unified management for external data sources and knowledge providers.
- **V2 API Surface**: New `/v2/` namespace for environmental operations, chat, reasoning, and simulation.
- **Simulation Sandbox**: Verified isolation for "what-if" scenarios without polluting authoritative state.

#### Features & Components
- **TrustPolicyConfig**: Managed via `/v2/trust_policies` and Studio UI.
- **IntelligenceSources**: Managed via `/v2/intelligence_sources`.
- **Environmental Agents**: Auto-discovery and registration of agents within specific environments.
- **Thermodynamics Integration**: Monitoring system state and "temperature" in the Studio.

#### API Endpoints (V2)
- `/v2/environments`: CRUD for sovereign environments.
- `/v2/environments/{env_id}/chat`: Environment-scoped autonomous chat.
- `/v2/environments/{env_id}/reasoning`: Deep reasoning with environmental context.
- `/v2/environments/{env_id}/crystallization`: Manual and auto-crystallization triggers.
- `/v2/trust_policies`: Global and environmental trust thresholds.
- `/v2/intelligence_sources`: Knowledge source management.

---

## [1.0.1] - 2026-08-28
### Fixed
- FAISS index synchronization during rapid event bursts.
- Admin dashboard auto-refresh stability.

---

### 🎉 Initial Production Release

#### Added
- **Self-Improving AI**: Complete cognitive loop with Judge-Generator feedback
- **Three-Layer Memory**: Gas (L1) → Liquid (L2) → Ice (L3) architecture
- **Vector Search**: FAISS integration with 10+ memories indexed
- **Semantic Patterns**: 10 patterns created with reinforcement learning
- **Agent Swarm**: 11 specialized agents with real-time status tracking
- **Admin Dashboard**: Full monitoring with auto-refresh (every 2s)
- **MCP Protocol**: Model Context Protocol for external tool access
- **HITL Workflow**: Human-in-the-loop approval system
- **Pattern Reinforcement**: Weight-based learning (+0.05 per success)
- **WebSocket Streaming**: Real-time live swarm feed

#### Fixed
- SemanticPattern model fields (weight, success_count, is_active)
- PersonaProfiler to use correct UserPersona model
- Vector service HTTP client initialization
- Awareness service timestamp field
- Swarm trigger authentication

#### Documentation
- Complete ARCHITECTURE.md
- Updated README.md with deployment status
- SYSTEM_SPECIFICATION.md with pattern reinforcement
- Deployment guide (DEPLOYMENT.md)
- Roadmap and TODO updates

---

## [0.9.0] - 2026-07-20

### Added
- Initial multi-agent orchestration
- Hybrid search (FAISS + BM25)
- Ollama integration (tinydolphin)
- Admin dashboard foundation

---

## [0.8.0] - 2026-07-15

### Added
- FastAPI backend
- SQLite database
- Authentication system
- Memory CRUD operations

---

### Legend
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` in case of vulnerabilities