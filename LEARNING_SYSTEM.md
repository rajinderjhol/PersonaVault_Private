# PersonaVault Learning System

This document outlines the architecture, mechanisms, and visualization of the PersonaVault learning system.

## 🧠 Core Learning Philosophy
PersonaVault learns through a three-layer memory evolution process (Gas → Liquid → Ice) and a continuous **Crystallization Loop**.

## 🔄 The Crystallization Loop
The system achieves **10,000:1 intelligence compression** by promoting deep reasoning paths to durable patterns.

1.  **Complexity Detection**: The `ComplexityDetector` analyzes query patterns, available context, and domain sensitivity to determine if deep reasoning is required.
2.  **Sovereign Routing**: The `ReasoningRouter` selects the optimal inference engine (local Ollama reasoning models vs. authorized cloud providers like Groq) based on the calculated complexity score and environment (air-gapped status).
3.  **Pattern Extraction**: Successful reasoning paths are processed to extract essential logic, discarding ephemeral noise while retaining the proven decision path.
4.  **Promotion to Ice (Layer 3)**: The `GeneratorAgent` hooks into the crystallization service to store these patterns as semantic "Ice" memories in the `IceMemoryRepository`, complete with embedding-backed similarity search to prevent redundancy.

*Subsequent similar queries now trigger the "Fast Path," retrieving the crystallized reasoning rather than re-computing it, resulting in exponential efficiency gains over time.*

## 📊 Observable Intelligence
The learning process is now fully instrumented via the **Observability Middleware**:
*   **Memory Hit Rate**: Real-time tracking of how often the system retrieves "Ice" memory vs. requesting new inference.
*   **Governance Latency**: Measuring the time added by policy matching and VeriLink verification.
*   **Decision Confidence Trends**: Visualized in the **Sovereign Control Center**.

## 📊 Learning Matrix Visualization
The Learning Matrix and **Sovereign Control Center** provide a real-time dashboard visualizing system intelligence growth.

### Dimensions
1.  **Pattern Confidence Heatmap**: Visualizes the crystallization state (Gas to Ice) of domain patterns.
2.  **Decision Timeline Flow**: Tracks success rates across the 5-step decision journey.
3.  **Policy Evolution Tracker**: Monitors the lifecycle (Draft → Active → Retired) of domain policies.
4.  **Service Performance**: Monitoring token efficiency and latency across providers (Ollama/Groq/Gemini).

### API Access
*   `GET /api/v1/learning/matrix`: Full state.
*   `GET /api/v1/mode/current`: Sovereign execution constraints.
*   `GET /api/v1/registry/services`: Active learning providers.

## 🧠 Domain-Aware Learning
The system now incorporates domain-specific intelligence.
*   **Domain Intelligence Units (DIUs)**: Self-contained packs of domain-specific agents, policies, and crystallized memory.
*   **Domain-Aware Routing**: The system detects the domain (e.g., 'clinical', 'security') to route queries to appropriate DIUs, ensuring persona-specific and evidence-based reasoning.
*   **Crystallization-in-Context**: Patterns are crystallized with domain-specific tagging, improving the quality of future domain-specific retrievals.

## 🏪 Intelligence Marketplace
The intelligence ecosystem is expanded through the **Intelligence Marketplace**:
*   **Intelligence Sharing**: Users can upload domain intelligence packs, allowing crystallized patterns and domain policies to compound across the ecosystem.
*   **Community Validation**: Rating and review systems enable crowdsourced verification of pattern confidence and accuracy, further hardening the system's learning loop.
