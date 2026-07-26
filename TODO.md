# 📝 PersonaVault Todo List

## 🏛 Architectural Standards
- [x] **Modular Design**: Enforce a strict "No Monolith" policy; Dashboard refactored into modular templates.
- [ ] **Structural Audit**: Identify existing large files (e.g., core engine orchestrators) and plan their decomposition before Phase 3.
- [x] **UI Asset Standard**: Transitioned dashboard to external template model; continue for other UI components.
- [ ] **Repository Pattern**: Abstract database-specific logic into a `repositories/` layer to simplify the Phase 4 migration to Weaviate/Neo4j.
- [ ] **Global Error Handling**: Implement custom exception handlers to remove repetitive `try-except` blocks from API routers.
- [ ] **Schema Hardening**: Audit all endpoints to ensure they use Pydantic `response_model` for strict data validation and security.
- [ ] **Observability (Traceability)**: Implement structured JSON logging and OpenTelemetry tracing to track reasoning across the 11-agent swarm.
- [ ] **Event-Driven Foundation**: Evaluate moving from direct service calls to an internal `EventBus` for agent communication to support Phase 3 swarms.
- [ ] **Configuration Purity**: Migrate `.env` management to Pydantic `BaseSettings` for validated, type-safe system configuration.

## 🎯 Strategic Value Hardening (The "Leapfrog" Edge)
- [ ] **Sovereign Proofs**: Implement the "Cryptographic Receipt" logic for the Trust Layer to prove data residency.
- [ ] **Knowledge Pruning**: Fine-tune the "Graduation Logic" (L2 → L3) to ensure only high-signal patterns are crystallized.
- [x] **MCP Ecosystem**: Model Context Protocol (MCP) Server implemented for secure tool and memory sharing.

## 🖥 Dashboard & UI Evolution
- [x] **Swarm Traceability**: Built visual reasoning graph and Live Swarm Feed for multi-agent transparency.
- [ ] **Crystallization Heatmap**: Visualize the ratio of memory across Gas (L1), Liquid (L2), and Ice (L3) states.
- [ ] **Sovereignty Proof Center**: A dedicated tab for verifying data residency and viewing VeriLink cryptographic receipts.
- [ ] **Living Memory Monitor**: Track upcoming data expirations and manual pruning overrides.
- [x] **MCP Registry UI**: Registry viewer and tool tester integrated into the Admin Dashboard.

## � Security & Authentication
- [ ] **WebSocket Auth**: Finalize JWT-based authentication for the root WebSocket server to align with FastAPI session logic.
- [ ] **Enterprise SSO**: Integrate with enterprise identity providers (SAML, OAuth 2.0).
- [ ] **Privacy Vault**: Achieve 100% test coverage for security-critical vault logic.

## 🚀 Infrastructure & Deployment
- [ ] **Containerization**: Finalize Docker images for both development and production environments.
- [ ] **Orchestration**: Create Kubernetes manifests with `liveness` and `readiness` probes.
- [ ] **Decoupling Prep**: Refactor `MemoryService` to support future migration to Weaviate/Neo4j.
- [ ] **Statelessness Audit**: Ensure FAISS indices and transient state are synced to shared volumes or external stores for K8s scaling.

## 🧠 Core AI & Memory Features
- [ ] **MultiModal Support**: Implement native support for image and audio embeddings in Layer 2.
- [ ] **Telemetry Adapters**: Build specialized adapters for medical, vehicular, and defence (Polar Nexus) ingestion.
- [ ] **VeriLinkOS**: Deeply integrate the Trust Layer for cryptographically verifiable AI actions.

## 📊 Testing & Quality Assurance
- [ ] **Core Pipeline Tests**: Increase coverage to ≥ 95%.
- [ ] **API Endpoint Tests**: Increase coverage to ≥ 90%.
- [ ] **Load Testing**: Benchmark P95 latency for Memory Search (< 150ms) and Local AI Chat (< 2s).

## 🛠 Maintenance
- [ ] **Documentation**: Update the Python SDK usage examples in `SYSTEM_SPECIFICATION.md`.
- [ ] **Cleanup**: Implement the `cleanup_job` background task for the "Living Memory" (auto-expiry) concept.

---
*Derived from Roadmap Phase 2 & Changelog Priorities*