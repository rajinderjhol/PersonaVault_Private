# Production Readiness Checklist: PersonaVault V2

This document outlines the operational and technical requirements for transitioning the **PersonaVault V2 Sovereign Intelligence Runtime** from verification to production.

## 1. Security & Governance (Sovereign Context)
- [ ] **RBAC Audit**: Verify all V2 API endpoints strictly enforce `AuthorityService` checks.
- [ ] **Environment Isolation**: Perform penetration testing to confirm zero leakage between Environment A and Environment B.
- [ ] **Data Encryption**: Ensure `is_encrypted` flag in `Memory` model is strictly enforced for sensitive environments.
- [ ] **Audit Log Completeness**: Validate that all V2 decisions, actions, and crystallization events are captured in the immutable Decision Trace.
- [ ] **Secrets Management**: Ensure no environment secrets (e.g., model API keys) are persisted in the `SystemConfig` table.

## 2. Observability & Monitoring
- [ ] **Crystallization Metrics**: Implement prometheus counters for `crystallization_events_total` and `intelligence_compression_ratio`.
- [ ] **Prediction Accuracy**: Implement logging for prediction vs. actual outcome to calculate `prediction_error` and `calibration_drift`.
- [ ] **System Health**: Extend health checks to cover V2 services (MemoryService, CrystallizationService, AuthorityService).
- [ ] **Log Sanitization**: Ensure sensitive action parameters are redacted from Uvicorn logs.

## 3. Performance & Scalability
- [ ] **Vector Search Benchmarking**: Benchmark FAISS search latency under concurrent multi-environment load.
- [ ] **Crystallization Load Testing**: Verify that the reactive `OutcomeLearningBridge` does not introduce latency bottlenecks on the main decision loop.
- [ ] **Database Indexing**: Validate all `environment_id` and foreign key indexes are optimized for the scale of expected memories.

## 4. Operational Stability
- [ ] **Database Migration Plan**: Finalize automated migration path for production (`alembic`).
- [ ] **Backup & Recovery**: Validate backup procedure for SQL database and FAISS index files.
- [ ] **Simulation Sandbox Isolation**: Verify that the `SimulationService` execution context is physically separate or resource-capped to prevent starvation of the live system.
- [ ] **Idempotency**: Verify that re-playing outcomes does not trigger duplicate crystallization events.

## 5. Reliability & Regression
- [ ] **End-to-End Acceptance**: Run `tests/acceptance/test_sovereign_runtime_loop.py` and all V1 tests in CI/CD on every pull request.
- [ ] **Error Handling**: Validate that exceptions in V2 services do not crash the main application thread.

## 6. Compliance & Provenance
- [ ] **Provenance Chain Validation**: Verify that any `KnowledgeItem` can be traced back to its originating `Decision` and `Outcome` evidence chain.
- [ ] **Right to Forget**: Test propagation of deletions across Memory, Knowledge, and Crystallized patterns.
