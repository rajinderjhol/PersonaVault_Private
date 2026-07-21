# PersonaVault Architecture

This document provides a technical deep-dive into the architectural design of the PersonaVault backend.

## System Overview

PersonaVault is designed as a modular monolithic API. The core philosophy is to provide a unified interface for disparate data types, using the most appropriate storage engine for each retrieval use case.

## 🌐 The Cognitive Ecosystem Vision

PersonaVault is not a single agent but a **collaborative swarm** of specialized agents:
*   **Health Agent**: Monitors wearables and medical data.
*   **Home Agent**: Manages smart home environment.
*   **Mobile Agent**: Coordinates with personal devices.
*   **Vehicle Agent**: Integrates with car systems.

Agents communicate via a shared **Cognitive Blackboard** and negotiate actions based on a unified understanding of the user's state and preferences.

### Cognitive State
The system maintains a "Cognitive State" representing its current reasoning confidence. When uncertainty is high (detected by the Judge Agent), the system enters a "Pending Human Clarification" state, triggering the HITL module.

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
*   **Layer 3: Semantic (Ice)** - Crystallized patterns and constraints stored in Vector and Graph stores.

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

## Request Lifecycle

1.  Client connects via REST or WebSocket.
2.  Middlewares process authentication, auditing, and rate limiting.
3.  FastAPI Router dispatches to the appropriate Service.
4.  Service interacts with the Data Layer (SQL, Graph, or Vector).
5.  Response is returned with Prometheus metrics captured.