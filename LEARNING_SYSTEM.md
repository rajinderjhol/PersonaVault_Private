# PersonaVault Learning System

This document outlines the architecture, mechanisms, and visualization of the PersonaVault learning system.

## 🧠 Core Learning Philosophy
PersonaVault learns through a three-layer memory evolution process (Gas → Liquid → Ice) and a continuous reinforcement learning loop.

## 🔄 The Learning Loop
1.  **Detection (Gas/L1)**: Raw interaction events captured via WebSockets and API endpoints.
2.  **Pattern Detection (Liquid/L2)**: Recurrent interactions are analyzed by the `ReinforcementEngine` and stored in episodic memory.
3.  **Policy Crystallization (Ice/L3)**: High-confidence patterns are formalized into policies by the `PolicyEvolutionEngine`, stored as `SemanticPattern` objects.

## 📊 Learning Matrix Visualization
The Learning Matrix provides a real-time dashboard visualizing system intelligence growth.

### Dimensions
1.  **Pattern Confidence Heatmap**: Visualizes the crystallization state (Gas to Ice) of domain patterns.
2.  **Decision Timeline Flow**: Tracks success rates across the 5-step decision journey.
3.  **Policy Evolution Tracker**: Monitors the lifecycle (Draft → Active → Retired) of domain policies.

### API Access
*   `GET /api/v1/learning/matrix`: Full state.
*   `GET /api/v1/learning/patterns`: Crystallization status.
*   `GET /api/v1/learning/policies/evolution`: Policy lifecycle timeline.

## 🛡️ Governance & Safety
All learning and policy promotion is moderated by the `Local Guardian Constitution` and subject to Human-In-The-Loop (HITL) overrides when confidence is low (< 0.6).
