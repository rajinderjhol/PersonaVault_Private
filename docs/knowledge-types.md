# Knowledge-Type Pipelines

This document defines the architectural distinction between how PersonaVault processes two fundamentally different types of knowledge.

## 1. Authoritative Knowledge
**Sources:** Contracts, policies, regulatory papers, standards, clinical guidelines, legal opinions.

**Nature:** These documents are inherently valid. They constitute the rules or facts upon arrival.

**Pipeline: Direct Extraction**
- **Flow:** Ingest → Semantic Pattern → Retrieval.
- **Mechanism:** Patterns are extracted directly from the document structure/content.
- **Thermodynamic State:** Patterns are treated as "Ice" (trusted knowledge) immediately, as they do not require observation of recurrence to validate.
- **Current Status:** Implemented. (The current codebase supports this via `IceMemoryRepository`).

## 2. Emergent Knowledge
**Sources:** Meeting notes, Slack threads, design discussions, suggestions, recurring decisions, human corrections.

**Nature:** These are not valid on arrival. Validity and significance emerge through *recurrence*.

**Pipeline: Recurrence-based Crystallization**
- **Flow:** Ingest → Evidence Block → Consolidation → Crystallization → Semantic Pattern → Retrieval.
- **Mechanism:** Observations are stored as evidence. A periodic consolidation pass detects patterns across sources. Crystallization promotes patterns based on recurrence frequency and reinforcement.
- **Thermodynamic State:** Patterns transition through Gas → Liquid → Ice based on `weight` and `occurrence_count`.
- **Current Status:** Not implemented. (This aligns with the whitepaper's original thesis).

## Strategic Direction
The system adopts a dual-pipeline architecture. Authoritative knowledge follows the direct pipeline, ensuring immediate accessibility. Emergent knowledge follows the recurrence-based pipeline, ensuring that only patterns which demonstrate stability and impact are promoted to trusted memory.

Both pipelines are supported by the same underlying substrate (SemanticPatterns, weights, and retrieval mechanisms).
