# 🗺 PersonaVault Roadmap

This document outlines the path from the current technical foundation to a production-ready product.

## Phase 1: Cement the Foundation (Weeks 1-4)
**Goal:** Stabilize and document the core cognitive loop.
- [x] **Core Ignition**: PersonaVault running with Ollama and hybrid search.
- [x] **Multi-Agent Orchestration**: Planner, Retriever, and Generator agents operational.
- [x] **Self-Improvement**: Consolidation task and graduation logic running.
- [x] **Cognitive State Documentation**: Define confidence scoring and HITL triggers in `ARCHITECTURE.md`.
- [x] **Judge Instrumentation**: Add confidence scoring to the Judge Agent to detect low-certainty responses.
- [x] **Clarification Lattices**: Create the `pending_actions` database lattice to manage human-in-the-loop requests.
- [x] **Governance Visual Editor**: Transitioned Constitution management from raw JSON to a managed list of policy rules.
- [x] **Crystallization Stability**: Resolved SQLAlchemy model collisions and optimized Layer 2 -> Layer 3 graduation.

## Phase 2: Evolve HITL and IoT (Weeks 5-8)
**Goal:** Deep integration with physical devices and human agency.
- [x] HITL-as-a-Service: Evolve the `ApprovalService` into a full cognitive state manager (PendingAction lattice).
- [ ] **Telemetry Adapters**: Specialized adapters for medical (pulse, BP) and vehicular data ingestion.
- [x] Real-time Notifications: Implement WebSocket/SSE-based alerts for human clarification requests and system logs.
- [ ] **Multi-Modal Memory**: Native support for image and audio embeddings in Layer 2.

## Phase 3: Agent Swarm & Negotiation (Weeks 9-12)
**Goal:** Autonomous collaboration between specialized agents.
- [ ] **Cognitive Blackboard**: Implement shared memory for cross-agent communication.
- [ ] **MCP Integration**: Adopt Model Context Protocol (MCP) as the backbone for tool discovery and agentic actions.
- [ ] **Standardized Nervous System**: Transition Agent-to-Agent communication to MCP-based resource sharing.
- [ ] **Proactive Agency**: Implement "State-to-Suggestion" logic where the swarm proposes actions based on telemetry patterns.
- [ ] **Infinite Loop Guardrails**: Implement delegation depth limits and message TTLs for agent swarms.

## Phase 4: Scalability & Ecosystem (2027)
- [ ] **Infrastructure Decoupling**: Implement migration logic from converged SQL simulation to specialized production engines:
    - Relational: PostgreSQL
    - Vector: Weaviate
    - Graph: Neo4j
- [ ] **Frontend Application**: Develop the companion web interface using React/Next.js.
- [ ] **Mobile SDK**: Create an ingestion library for iOS and Android to allow "capture-on-the-go" functionality.
- [ ] **Deployment Orchestration**: Finalize Helm charts and Terraform scripts for one-click deployment to GKE (Google Kubernetes Engine).

## ✅ Completed Milestones
- [x] Hybrid Data Layer (SQL + Vector + Graph).
- [x] Multi-provider AI routing logic.
- [x] WebSocket support for real-time IoT data and telemetry simulation.
- [x] Cognified Admin Dashboard with live log streaming and model management.

---
*Last Updated: July 2026*