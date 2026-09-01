# V2 Implementation Plan

This document maps the architectural concepts defined in `docs/v2/architecture/SPECIFICATION.md` to the actual implementation within the `backend/` codebase.

## Overview
V2 is implemented as an additive extension to the existing PersonaVault Decision Operating System.

## Implementation Mappings

| V2 Architectural Concept | Implementation Location | Notes |
| :--- | :--- | :--- |
| **V2 API Namespace** | `backend/app/api/v2/` | New API version, preserves V1 compatibility. |
| **Domain Models** | `backend/app/api/v2/models/` | Richer V2 structures (e.g., `environment.py`, `principal.py`, `membership.py`, `authority.py`). |
| **Adapter Layer** | `backend/app/api/v2/adapters/` | Transforms V1 concepts (e.g., `Behavior Packs`) to V2 (e.g., `Intelligence Packs`). |
| **Endpoints** | `backend/app/api/v2/endpoints/` | Exposes V2 functionality. |
| **Core Logic** | `backend/app/core/` | Shared logic remains in existing core. |

## Development Rules
1. **Compatibility First**: No breaking changes to V1 APIs.
2. **Additive Migration**: V2 structures wrap V1 source of truth.
3. **Documentation**: Any new mapping logic must be recorded in this plan.
