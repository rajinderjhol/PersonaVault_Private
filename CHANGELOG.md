# Changelog

All notable changes to PersonaVault will be documented in this file.

The format is based on Keep a Changelog.

---

## [1.0.0] - 2026-07-27

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