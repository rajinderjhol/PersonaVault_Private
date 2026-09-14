# PersonaVault Learning System

This document outlines the architecture, mechanisms, and visualization of the PersonaVault learning system, reframed as a series of **epistemic transitions**.

## 🧠 Core Learning Philosophy
PersonaVault models knowledge as a thermodynamic state machine. Patterns exist in three phases (Gas → Liquid → Ice) and undergo specific **epistemic transitions** as they evolve from raw observations to verified institutional knowledge.

## 🔄 The Transition Model (The Crystallization Loop)
The system achieves **10,000:1 intelligence compression** by managing these transitions through a continuous loop. The "Crystallization Loop" is the engine that executes these transitions:

1.  **Complexity Detection**: Analyzes query patterns, context, and sensitivity to trigger learning.
2.  **Sovereign Routing**: Selects the optimal engine (local vs. cloud) based on environment and complexity.
3.  **Epistemic Event Generation**:
    *   **Crystallize (Gas → Liquid)**: Raw observations are promoted to candidate patterns.
    *   **Freeze (Liquid → Ice)**: Verified patterns are promoted to durable, governed knowledge.
4.  **Integration**: The `GeneratorAgent` ensures these transitions are recorded in the `IceMemoryRepository`.

*Subsequent similar queries now trigger the "Fast Path," retrieving the crystallized knowledge rather than re-computing it, resulting in exponential efficiency gains over time.*

## 📊 Observable Intelligence
The learning process is instrumented via the **Observability Middleware**:
*   **Memory Hit Rate**: Real-time tracking of how often the system retrieves "Ice" memory (post-transition) vs. requesting new inference.
