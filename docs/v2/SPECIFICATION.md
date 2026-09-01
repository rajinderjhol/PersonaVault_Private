# PersonaVault V2
## Sovereign Intelligence Architecture & Implementation Specification

**Status:** Implementation Specification  
**Version:** 2.0-draft  
**Target:** PersonaVault_Private `master` → V2  
**Primary objective:** Evolve PersonaVault into a Sovereign Intelligence platform without breaking existing functionality, APIs, data, memory, agents, governance, or Studio behavior.

---

# 1. Executive Summary

PersonaVault V2 introduces a new top-level product abstraction:

> **PersonaVault — Sovereign Intelligence in Any Decision Environment**

The system should evolve from a Decision Operating System centered primarily on organizational decision intelligence into a more general architecture in which:

- a **Principal** operates within one or more **Environments**;
- each Environment has persistent **Identity, State, Memory, Knowledge, Goals, Strategy, Policy, Authority, Capabilities, Agents and Resources**;
- the system can perform **Prediction**;
- the system can construct **Scenarios** and perform **Simulation**;
- humans and agents make governed **Decisions**;
- authorized **Actions** change the Environment;
- resulting **Outcomes** are captured;
- Outcomes feed a controlled **Learning Loop**;
- learned knowledge becomes part of future Environment state and Memory.

The existing PersonaVault architecture remains the foundation.

**V2 must NOT replace:**

- existing memory layers;
- existing decision traces;
- existing Policy Engine;
- existing Behavior Packs;
- existing Service Registry;
- existing agents;
- existing APIs;
- existing storage;
- existing Studio functionality;
- existing governance;
- existing MCP functionality;
- existing learning/crystallization.

Instead, V2 wraps and extends them.

---

# 2. Product Thesis

## 2.1 New product statement

> **PersonaVault is Sovereign Intelligence in Any Decision Environment.**

The product is not fundamentally:

- a chatbot;
- an LLM;
- an agent framework;
- a CRM;
- a document management system;
- a simulation engine;
- a workflow engine;
- a memory database.

It is a persistent intelligence environment that allows humans and AI systems to understand a changing environment, reason about possible futures, make governed decisions, act, observe outcomes and learn.

## 2.2 Product Category

The external positioning should be:

> **PersonaVault**  
> **Sovereign Intelligence in Any Decision Environment.**

The internal architecture remains:

> **Decision Operating System**

The relationship is:

```text
SOVEREIGN INTELLIGENCE
        │
        ↓
PERSONAVAULT
        │
        ↓
DECISION OPERATING SYSTEM
        │
        ├── Environment
        ├── Memory
        ├── Knowledge
        ├── Prediction
        ├── Simulation
        ├── Strategy
        ├── Policy
        ├── Decision
        ├── Action
        └── Learning
```

---

# 3. Architectural Principle

The central architectural rule is:

> **Do not replace existing concepts when a new concept can be composed around them.**

The current architecture already describes PersonaVault as a model-independent Decision Operating System in which AI models provide inference while PersonaVault accumulates governed intelligence. It already contains Decision State, Auditable Decision Traces, Policy, Memory, Model State, Outcome State, Behavior Packs, Service Registry, sovereign modes and learning/crystallization.

V2 should therefore be implemented as:

```text
                         PERSONAVAULT
                              │
                  SOVEREIGN INTELLIGENCE
                              │
                     DECISION ENVIRONMENTS
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
     PERSONAL             ORGANIZATIONAL        PHYSICAL
        │                     │                     │
     Person                 Law Firm              Robot
     Family                 Enterprise            Factory
     Home                   Hospital              Device
     Learning               Defense               Vehicle
```

All of these use the same underlying primitives.

## 3.1 Environment as the Primary Boundary

In V2, Environment is the primary boundary within which intelligence operates.

Every governed operation MUST resolve to an Environment.

This includes:

- state observation;
- memory retrieval;
- knowledge retrieval;
- prediction;
- simulation;
- strategy;
- policy evaluation;
- authority evaluation;
- decision;
- action;
- outcome;
- learning.

An Environment is therefore not merely a container or workspace. It is the operational boundary within which PersonaVault maintains continuity of intelligence.

A Principal may participate in multiple Environments.

An Environment may contain subordinate Environments.

Information MUST NOT cross Environment boundaries unless explicitly authorized by identity, membership, policy and authority.

## 3.2 The Reality Boundary

PersonaVault distinguishes between:

- **LIVE** — Real-world Environment state and actions.
- **SIMULATED** — Hypothetical state and actions.
- **PROPOSED** — Potential future decisions or actions.
- **OBSERVED** — Recorded evidence of events that have occurred.

The system MUST NOT treat simulated, proposed or predicted information as observed reality.

This is a very important safety and correctness primitive, especially if PersonaVault eventually controls devices or physical systems.

## 3.3 Intelligence vs Model

PersonaVault Intelligence is not equivalent to the model used to produce an inference.

```text
PersonaVault
    │
    ├── Environment
    ├── Memory
    ├── Knowledge
    ├── Policies
    ├── Decisions
    ├── Outcomes
    └── Learning
             │
             ↓
        MODEL PROVIDERS
        ├── Local
        ├── Frontier
        ├── Enterprise
        └── Specialized
```

Models provide inference. PersonaVault provides **continuity, governance, provenance and learning across inference providers**.

This is one of the strongest parts of the thesis and must remain explicit.

---

# 4. Canonical Vocabulary

| Term | Meaning |
|------|---------|
| **Principal** | Entity capable of owning, participating in or being governed within an Environment |
| **Environment** | Primary boundary of state, intelligence and governance |
| **Event** | Something that occurred within or was observed by an Environment |
| **Observation** | Recorded perception of an Event or condition |
| **State** | Current modeled condition of an Environment |
| **Memory** | Persistent record of experience/information |
| **Knowledge** | Validated or represented understanding |
| **Unknown** | Information not currently known |
| **Knowledge Gap** | Explicit representation of an absence of knowledge |
| **Goal** | Desired outcome |
| **Strategy** | Intended approach to pursue a goal |
| **Plan** | Intended sequence of actions |
| **Policy** | Governing rule (allow/deny/require) |
| **Authority** | Permission to decide or act |
| **Capability** | Technical ability to act |
| **Prediction** | Estimate of what is likely to happen |
| **Scenario** | Hypothetical Environment trajectory |
| **Simulation** | Execution/exploration of hypothetical trajectories |
| **Decision** | Chosen course of action |
| **Action** | Executed side effect |
| **Outcome** | Observed result |
| **Learning** | Update derived from experience/evidence |
| **Promotion** | How insights become durable |
| **Provenance** | Chain of custody/evidence for any object |

---

# 5. Non-Negotiable Compatibility Requirements

V2 MUST satisfy the following.

## 5.1 Existing API compatibility

Existing endpoints MUST continue to work.

No existing endpoint may be removed solely because a V2 equivalent exists.

If an existing endpoint is replaced internally, an adapter MUST preserve its external contract.

## 5.2 Existing data compatibility

Existing data MUST remain readable.

No destructive migration is permitted in the initial V2 release.

Existing records MUST NOT require conversion before the existing application can start.

## 5.3 Existing memory compatibility

The current multi-layer memory architecture remains authoritative.

V2 adds Environment-aware indexing and relationships around existing memory rather than replacing the memory implementation.

## 5.4 Existing Decision Trace compatibility

The existing Auditable Decision Trace remains the canonical execution record.

V2 extends it with:

- environment ID;
- scenario ID;
- prediction IDs;
- simulation IDs;
- strategy ID;
- policy ID;
- authority ID;
- action ID;
- outcome ID.

Existing traces remain valid without these new fields. New fields MUST be nullable.

## 5.5 Existing Policy compatibility

Existing Policy Engine behavior must remain unchanged by default.

V2 introduces Strategy as a separate concept.

Policy remains authoritative over what may/must/must-not happen. Strategy describes how a goal is pursued.

## 5.6 Existing agent compatibility

Existing agents continue to execute using their current interfaces.

V2 adds Environment awareness through an adapter/context object.

Existing agents do not need to be rewritten immediately.

---

# 6. Core V2 Ontology

V2 introduces the following canonical entities.

```text
Principal
Environment
Membership
Identity
Resource
State
Memory
Knowledge
Unknown
KnowledgeGap
Goal
Strategy
Plan
Policy
Authority
Capability
Agent
Prediction
Scenario
Simulation
Decision
Action
Outcome
LearningEvent
Evidence
Trace
Event
Observation
Promotion
```

These are deliberately generic.

---

# 7. Principal

A Principal is an entity capable of owning, participating in or being governed within an Environment.

**Examples:**

```text
Person
Organization
Team
Family
Institution
Agent
Service
Device
```

## 7.1 Required fields

```ts
interface Principal {
  id: string
  type: PrincipalType
  name: string
  status: "active" | "inactive" | "archived"
  metadata?: Record<string, unknown>
  created_at: string
  updated_at: string
}
```

## 7.2 Implementation note

Do not replace existing identity structures. Create an adapter:

```ts
PrincipalAdapter
```

that can map current PersonaVault identities into the V2 Principal abstraction.

---

# 8. Environment

## 8.1 Definition

An Environment is the persistent decision space in which a Principal operates.

An Environment contains:

- entities;
- state;
- resources;
- people;
- devices;
- agents;
- knowledge;
- memories;
- goals;
- strategies;
- policies;
- authorities;
- capabilities;
- events;
- decisions;
- actions;
- outcomes.

## 8.2 Environment examples

```text
Personal
Family
Law Firm
Matter
Hospital
Patient Care
Enterprise
Department
Factory
Classroom
Defense Exercise
Robot
Vehicle
Home
```

## 8.3 Environment schema

```ts
interface Environment {
  id: string
  type: string
  name: string
  description?: string

  owner_principal_id: string

  parent_environment_id?: string

  status:
    | "active"
    | "paused"
    | "simulation"
    | "archived"

  mode:
    | "standard"
    | "restricted"
    | "simulation"
    | "audit"

  timezone?: string

  metadata?: Record<string, unknown>

  created_at: string
  updated_at: string
}
```

## 8.4 Environment lifecycle

```text
CREATED
   ↓
CONFIGURED
   ↓
ACTIVE
   ↓
PAUSED
   ↓
ARCHIVED
```

For simulation:

```text
LIVE ENVIRONMENT
       │
       │ snapshot
       ↓
SIMULATION ENVIRONMENT
       │
       ↓
DISCARD / PROMOTE INSIGHT
```

Never:

```text
Simulation → automatically modifies Live Environment
```

## 8.5 Environment Hierarchy

Environments may contain environments.

```text
Person
 ├── Personal Environment
 │
 ├── Family Environment
 │
 └── Work Environment
       ├── Organization
       │    ├── Department
       │    └── Matter
       └── Project
```

This allows the same person to participate in multiple organizations without duplicating their identity.

---

# 9. Membership

A Principal may belong to many Environments.

```ts
interface EnvironmentMembership {
  id: string
  environment_id: string
  principal_id: string

  role?: string

  authority_level?: string

  permissions?: string[]

  starts_at?: string
  ends_at?: string

  status: "active" | "suspended" | "ended"

  metadata?: Record<string, unknown>
}
```

This is essential for:

- family;
- friends;
- social environments;
- law firms;
- departments;
- enterprises;
- clinical teams.

---

# 10. Authority

Authority is distinct from identity.

A person can belong to an Environment without having authority to:

- approve;
- publish;
- delete;
- disclose;
- execute;
- change policy.

```ts
interface AuthorityGrant {
  id: string
  environment_id: string
  principal_id: string

  capability: string

  scope?: string

  conditions?: Record<string, unknown>

  granted_by?: string

  valid_from: string
  valid_until?: string
}
```

---

# 11. Capability

Capability is distinct from Authority.

- **Capability** = what an actor/system can technically do
- **Authority** = what that actor is permitted to do
- **Policy** = what rules govern the action

```ts
interface Capability {
  id: string
  name: string
  description?: string
  type: string
  parameters?: Record<string, unknown>
  requires?: string[]
}
```

Example:

```text
Agent
  ↓
Capability: "send_email"
  ↓
Authority: granted by Environment
  ↓
Policy: requires human approval
  ↓
Action: email sent (or blocked)
```

---

# 12. Resource

A Resource is something that can be used or consumed within an Environment.

**Examples:**

```text
Document
Database
Device
Model
Human
Budget
API
Tool
Physical asset
Knowledge source
```

```ts
interface Resource {
  id: string
  environment_id: string
  type: string
  name: string
  description?: string
  status: "available" | "in_use" | "depleted" | "unavailable"
  metadata?: Record<string, unknown>
  created_at: string
  updated_at: string
}
```

---

# 13. Event

An Event represents something that occurred within or was observed by an Environment.

Events are immutable.

Events may originate from:

- humans;
- agents;
- devices;
- external systems;
- documents;
- services;
- simulations.

Events may cause Environment State to change.

Events MUST retain provenance and timestamps.

```ts
interface EnvironmentEvent {
  id: string
  environment_id: string

  type: string

  occurred_at: string
  observed_at: string

  actor_id?: string
  source_id?: string

  payload: unknown

  provenance: ProvenanceRef[]

  simulation_id?: string
}
```

---

# 14. Observation

An Observation is a recorded perception of an Event or condition.

Observations may be:

- accurate;
- inaccurate;
- incomplete;
- conflicting.

```ts
interface Observation {
  id: string
  environment_id: string

  event_id?: string

  observed_at: string

  observer_id: string

  content: unknown

  confidence?: number

  provenance: ProvenanceRef[]

  status:
    | "candidate"
    | "confirmed"
    | "disputed"
    | "invalidated"
}
```

---

# 15. State

State represents the current observable condition of an Environment.

```ts
interface EnvironmentState {
  environment_id: string
  version: number

  observed_at: string

  entities: Record<string, unknown>

  signals: Signal[]

  metrics: Record<string, number>

  conditions: Condition[]

  confidence?: number

  provenance: ProvenanceRef[]
}
```

State must be versioned.

Never overwrite historical state without retaining its provenance.

---

# 16. Memory

Existing PersonaVault memory remains the source of truth.

V2 adds:

```ts
environment_id?: string
principal_id?: string
scenario_id?: string
```

to memory metadata where supported.

These fields should initially be optional.

Existing memory objects remain valid.

---

# 17. Knowledge

Knowledge is a higher-order representation derived from:

- observations;
- documents;
- memories;
- decisions;
- outcomes;
- external evidence;
- crystallized patterns.

```ts
interface KnowledgeItem {
  id: string

  environment_id: string

  statement: string

  type:
    | "fact"
    | "rule"
    | "pattern"
    | "relationship"
    | "lesson"
    | "assumption"

  confidence: number

  provenance: ProvenanceRef[]

  valid_from?: string
  valid_until?: string

  status:
    | "active"
    | "superseded"
    | "disputed"
    | "invalidated"
}
```

---

# 18. Knowledge Frontier

PersonaVault should explicitly represent the boundary between knowledge and absence of knowledge.

```text
KNOWN
UNCERTAIN
UNKNOWN
CONTRADICTORY
UNOBSERVED
UNEXPLORED
```

This is a first-class V2 concept.

An Unknown is **not an error condition**. It can become an input to:

- research;
- sensing;
- experimentation;
- prediction;
- simulation;
- decision prioritization.

```ts
interface KnowledgeGap {
  id: string

  environment_id: string

  question: string

  importance: number

  uncertainty: number

  decision_impact?: number

  evidence_needed?: string[]

  status:
    | "open"
    | "investigating"
    | "resolved"
    | "accepted_unknown"
}
```

The system must not fabricate knowledge to fill gaps.

---

# 19. Goal

Goal answers:

> What are we trying to achieve?

```ts
interface Goal {
  id: string

  environment_id: string

  owner_principal_id?: string

  statement: string

  priority?: number

  success_metrics?: Metric[]

  constraints?: string[]

  status:
    | "proposed"
    | "active"
    | "achieved"
    | "failed"
    | "abandoned"

  created_at: string
  updated_at: string
}
```

---

# 20. Strategy

Strategy is NOT Policy.

Strategy answers:

> How do we intend to pursue a goal?

```ts
interface Strategy {
  id: string

  environment_id: string

  goal_id: string

  name: string

  objective: string

  approach: string

  assumptions: string[]

  alternatives?: string[]

  status:
    | "draft"
    | "active"
    | "superseded"
    | "retired"

  version: number

  created_by?: string

  created_at: string
  updated_at: string
}
```

Strategy may change through learning.

---

# 21. Policy

Policy answers:

> What is allowed, required or prohibited?

Policy remains governed.

```ts
interface Policy {
  id: string

  environment_id: string

  name: string

  version: number

  rule: string

  priority?: number

  effect:
    | "allow"
    | "deny"
    | "require_approval"
    | "require_review"
    | "require_human"

  scope?: string

  status:
    | "draft"
    | "active"
    | "superseded"
    | "retired"

  authority_required?: string

  provenance?: ProvenanceRef[]
}
```

Critical rule:

> A learning loop may propose a policy change but MUST NOT silently modify active policy.

---

# 22. Plan

Plan translates Strategy into an intended sequence.

```ts
interface Plan {
  id: string

  environment_id: string

  strategy_id?: string

  goal_id?: string

  steps: PlanStep[]

  status:
    | "draft"
    | "approved"
    | "active"
    | "completed"
    | "cancelled"
}
```

---

# 23. Prediction

Prediction answers:

> What is likely to happen?

Prediction MUST be distinguished from simulation.

```ts
interface Prediction {
  id: string

  environment_id: string

  question: string

  horizon?: string

  predicted_outcomes: PredictedOutcome[]

  probability?: number
  confidence?: number
  uncertainty?: number

  assumptions: string[]

  evidence: ProvenanceRef[]

  model_ref?: string

  created_at: string

  evaluated_at?: string

  actual_outcome?: string

  calibration_status?:
    | "pending"
    | "accurate"
    | "overconfident"
    | "underconfident"
    | "incorrect"
}
```

---

# 24. Scenario

A Scenario defines a hypothetical Environment trajectory.

```ts
interface Scenario {
  id: string

  simulation_id: string

  name: string

  initial_state: unknown

  assumptions: string[]

  interventions: string[]

  events: ScenarioEvent[]

  expected_horizon?: string
}
```

---

# 25. Simulation

Simulation answers:

> What could happen if the Environment changes under defined assumptions?

Simulation must run in a sandbox.

**Mathematical distinction:**

```text
Prediction: P(outcome | current evidence, assumptions)
Simulation: generate possible Environment trajectories under specified initial state + interventions + assumptions
```

```ts
interface Simulation {
  id: string

  environment_id: string

  base_state_version: number

  scenario_ids: string[]

  assumptions: string[]

  mode: "sandbox"

  branches: SimulationBranch[]

  status:
    | "created"
    | "running"
    | "completed"
    | "failed"
}
```

Simulation MUST NOT create real-world side effects.

---

# 26. Decision

The existing Decision Operating System remains the authority for decision execution.

V2 enriches it.

```ts
interface Decision {
  id: string

  environment_id: string

  goal_id?: string

  strategy_id?: string

  plan_id?: string

  prediction_id?: string

  simulation_id?: string

  policy_ids: string[]

  authority_id?: string

  recommendation?: Recommendation

  decision: string

  decided_by: string

  status:
    | "proposed"
    | "approved"
    | "rejected"
    | "executed"
    | "cancelled"

  trace_id: string

  created_at: string
}
```

All fields introduced by V2 should initially be nullable where the existing system cannot populate them.

---

# 27. Action

Action represents an observable side effect.

```ts
interface Action {
  id: string

  environment_id: string

  decision_id: string

  actor_id: string

  capability: string

  tool?: string

  parameters_hash?: string

  authorization_status:
    | "approved"
    | "denied"
    | "not_required"
    | "pending"

  executed_at?: string

  result?: unknown
}
```

Do not expose sensitive action parameters in logs by default.

---

# 28. Outcome

Outcome captures what actually happened.

```ts
interface Outcome {
  id: string

  environment_id: string

  decision_id?: string

  action_id?: string

  observed_at: string

  result: unknown

  success?: boolean

  metrics?: Record<string, number>

  evidence: ProvenanceRef[]

  created_at: string
}
```

---

# 29. Learning Event

Learning must be explicit.

```ts
interface LearningEvent {
  id: string

  environment_id: string

  source_type:
    | "outcome"
    | "prediction_error"
    | "human_feedback"
    | "simulation"
    | "new_evidence"

  source_id: string

  observation: string

  proposed_update?: unknown

  confidence: number

  status:
    | "candidate"
    | "validated"
    | "rejected"
    | "promoted"

  created_at: string
}
```

---

# 30. Promotion

Promotion is how insights become durable.

```text
Simulation
   ↓
Insight
   ↓
Validation
   ↓
Promotion
   ↓
Knowledge
```

Similarly:

```text
Learning candidate
   ↓
Validation
   ↓
Promotion
   ↓
Crystallized intelligence
```

And:

```text
Strategy proposal
   ↓
Approval
   ↓
Active strategy
```

```ts
interface Promotion {
  id: string
  environment_id: string
  
  source_type: string
  source_id: string
  
  target_type: string
  target_id: string
  
  reason: string
  
  promoted_by: string
  promoted_at: string
  
  status: "proposed" | "approved" | "rejected"
}
```

This prevents accidental mutation of the live system.

---

# 31. Provenance

Every V2 object capable of influencing a decision should support provenance.

```ts
interface ProvenanceRef {
  source_type: string
  source_id: string
  timestamp?: string
  hash?: string
}
```

**Minimum provenance requirements:**

- Prediction → evidence
- Simulation → state snapshot
- Decision → evidence + policy + prediction/simulation
- Action → decision + authorization
- Outcome → action/decision
- Learning → outcome/evidence

---

# 32. The V2 Decision Loop

The canonical V2 architecture:

```text
                    ENVIRONMENT
                         │
                         ↓
                       EVENTS
                         │
                         ↓
                    OBSERVATIONS
                         │
                         ↓
                       STATE
                         │
              ┌──────────┴──────────┐
              ↓                     ↓
           MEMORY                KNOWLEDGE
              │                     │
              └──────────┬──────────┘
                         ↓
               KNOWLEDGE FRONTIER
                         │
              ┌──────────┴──────────┐
              ↓                     ↓
          PREDICTION             UNKNOWN
              │                     │
              └──────────┬──────────┘
                         ↓
                     SIMULATION
                         │
                         ↓
                      OPTIONS
                         │
                      STRATEGY
                         │
                       POLICY
                         │
                     AUTHORITY
                         │
                      DECISION
                         │
                       ACTION
                         │
                        EVENT
                         │
                      OUTCOME
                         │
                      LEARNING
                         │
                  ┌──────┴──────┐
                  ↓             ↓
               MEMORY       KNOWLEDGE
```

This loop must be implemented incrementally.

---

# 33. Relationship to Existing Crystallization

The current PersonaVault architecture already has a crystallization loop:

```text
AI Recommendation
       ↓
Human Decision
       ↓
Real Outcome
       ↓
Reinforcement
       ↓
Crystallized Rule
```

V2 must preserve this.

The expanded model becomes:

```text
Outcome
   ↓
Learning Event
   ↓
Validation
   ↓
Knowledge Update
   ↓
Pattern / Crystallization
   ↓
Future Retrieval
```

A crystallized pattern must not automatically become a Policy.

---

# 34. Decision Trace V2

The existing trace model should be extended rather than replaced.

Canonical trace:

```text
Trace
 ├── Environment
 ├── State version
 ├── Perception
 ├── Evidence
 ├── Signals
 ├── Memory
 ├── Knowledge
 ├── Unknowns
 ├── Prediction
 ├── Simulation
 ├── Strategy
 ├── Policy
 ├── Authority
 ├── Recommendation
 ├── Decision
 ├── Action
 ├── Outcome
 └── Learning
```

The trace remains append-only.

---

# 35. Sovereign Modes

Existing modes remain:

```text
Standard
Restricted
Simulation
Audit
```

**V2 semantics:**

### Standard
Real environment.

### Restricted
Local/air-gapped intelligence.

### Simulation
No real-world side effects.

### Audit
Read-only replay/inspection.

This aligns naturally with the existing architecture.

---

# 36. Simulation Safety Boundary

Simulation MUST use a separate execution context.

```text
Live Environment
       │
       │ snapshot
       ↓
Simulation Environment
       │
       ├── scenario A
       ├── scenario B
       └── scenario C
```

Simulation cannot:

- send external messages;
- modify live records;
- call uncontrolled external tools;
- modify active policy;
- execute physical actions;
- change live environment state.

Only explicit promotion of a simulation insight can affect the live environment.

---

# 37. Prediction Evaluation

Predictions must become evaluable objects.

When a prediction is created:

```text
Prediction
  ↓
prediction_id
```

Later:

```text
Outcome
  ↓
evaluate(prediction_id)
  ↓
prediction error
  ↓
calibration metrics
```

Store:

```text
predicted probability
actual result
prediction horizon
prediction confidence
error
```

Do not retroactively modify the original prediction.

---

# 38. Learning Governance

Learning must have two stages.

### Candidate learning

AI may propose:

- Possible new knowledge
- Possible strategy improvement
- Possible pattern
- Possible policy recommendation

### Promoted learning

Only validated learning becomes durable.

```text
candidate
   ↓
validation
   ↓
promotion
   ↓
knowledge/memory/crystallization
```

Policy changes require explicit authorized governance.

---

# 39. Agent Architecture

Agents should receive an Environment handle.

```ts
interface AgentEnvironmentContext {
  environment_id: string

  getState(): Promise<EnvironmentState>

  retrieveMemory(query: string): Promise<Memory[]>

  retrieveKnowledge(query: string): Promise<KnowledgeItem[]>

  getPolicies(): Promise<Policy[]>

  getAuthority(actor: string): Promise<AuthorityGrant[]>

  predict(input: PredictionRequest): Promise<Prediction>

  simulate(input: SimulationRequest): Promise<Simulation>

  proposeDecision(input: DecisionRequest): Promise<DecisionProposal>
}
```

Existing agents may continue using their current interfaces.

The adapter exposes this context to V2-capable agents.

---

# 40. Agent Permission Model

Agents MUST NOT inherit unrestricted Environment authority.

Each agent receives:

```text
Identity
Environment
Capabilities
Policies
Authority
Tool permissions
Data permissions
```

Example:

```text
Agent: Contract Analyst

Can:
READ documents
READ memory
CREATE prediction
CREATE recommendation

Cannot:
SEND email
APPROVE settlement
CHANGE policy
DELETE evidence
```

---

# 41. Model Independence

The V2 architecture must preserve model independence.

Supported inference paths may include:

```text
Local model
Cloud model
Frontier model
Enterprise model
Specialized model
Human
```

The Environment owns:

```text
data
memory
knowledge
policies
decision history
outcomes
```

The model is an interchangeable inference component.

This preserves the existing PersonaVault thesis.

---

# 42. Model Routing

Future routing may use:

```text
Environment policy
+
data classification
+
model capability
+
latency
+
cost
+
sovereignty
```

Example:

```text
Sensitive document
      ↓
Policy
      ↓
Local model only
```

Whereas:

```text
Public research
      ↓
Policy
      ↓
Approved external model
```

---

# 43. Security

Environment isolation is mandatory.

Every query must resolve:

```text
principal
      ↓
environment
      ↓
authorization
      ↓
policy
      ↓
data
```

Never:

```text
query
 ↓
global memory
```

without Environment authorization.

---

# 44. Cross-Environment Intelligence

Cross-environment access must be explicit.

Example:

```text
Person
 ├── Personal
 ├── Family
 └── Work
```

Personal memory MUST NOT automatically become available to Work.

Likewise:

```text
Law Firm
Matter A
Matter B
```

Matter A information MUST NOT automatically leak into Matter B.

Cross-environment retrieval requires:

```text
explicit grant
+
policy approval
+
provenance
```

---

# 45. Privacy / Right to Forget

Existing PersonaVault privacy mechanisms remain authoritative.

The V2 objects must participate in deletion propagation.

If a source is deleted:

```text
source
 ↓
memory
 ↓
knowledge
 ↓
prediction evidence
 ↓
simulation evidence
 ↓
crystallized patterns
```

affected objects must be:

```text
deleted
invalidated
or marked as dependent
```

according to the existing privacy policy.

---

# 46. Security Classification

V2 should eventually support Environment-level data classification.

Example:

```text
PUBLIC
INTERNAL
CONFIDENTIAL
RESTRICTED
SENSITIVE
```

Model routing and tool permissions can use classification.

This should be implemented only after the core Environment isolation is proven.

---

# 47. Observability

Add V2 metrics.

### Environment

```text
environment_count
active_environment_count
state_update_latency
```

### Prediction

```text
prediction_count
prediction_calibration
prediction_error
```

### Simulation

```text
simulation_count
simulation_latency
branch_count
```

### Decision

```text
decision_count
decision_latency
human_approval_rate
```

### Learning

```text
learning_candidates
learning_promoted
learning_rejected
```

### Sovereignty

```text
local_inference_rate
external_inference_rate
blocked_external_requests
```

---

# 48. Backward Compatibility Contract

V2 is successful only if:

```text
Existing user
     ↓
starts V2
     ↓
existing memories available
existing decisions available
existing agents available
existing policies available
existing API works
existing Studio works
```

No manual migration should be required for the first V2 release.

---

# 49. Git Strategy

Before implementation:

```bash
git checkout -b v2-sovereign-intelligence
git tag v1-pre-sovereign-intelligence
```

Work in small commits.

Recommended commit sequence:

```text
feat(v2): add domain types
feat(v2): add environment compatibility layer
feat(v2): add environment persistence
feat(v2): add knowledge frontier
feat(v2): add prediction service
feat(v2): add simulation sandbox
feat(v2): add strategy model
feat(v2): integrate decision trace
feat(v2): add outcome learning
feat(studio): add sovereign intelligence navigation
feat(studio): add environment workspace
feat(studio): add forecast workspace
feat(studio): add simulation workspace
feat(studio): add decision replay
feat(studio): add learning workspace
```

---

# 50. Do Not Do These Things

## DO NOT

Rewrite the runtime.

Rewrite the memory architecture.

Replace the existing Policy Engine.

Replace the Service Registry.

Replace the existing Decision Trace.

Replace all Behavior Packs.

Replace all agents.

Replace all API routes.

Replace the Studio framework.

Perform a giant database migration.

Rename every existing class.

Move hundreds of files simply to make the architecture look cleaner.

---

# 51. V2 Definition of Done

V2 is considered structurally complete when:

### Architecture

- Environment is first-class.
- Principal and Membership are first-class.
- State is versioned.
- Knowledge and Knowledge Gaps are first-class.
- Goal/Strategy/Plan exist.
- Policy remains governed.
- Prediction exists.
- Simulation is sandboxed.
- Decision integrates all relevant objects.
- Action and Outcome exist.
- Learning feeds back into Knowledge/Memory.

### Governance

- Environment isolation works.
- Policy gates remain authoritative.
- Authority is explicit.
- Simulation cannot create side effects.
- Provenance exists.
- Decision replay works.
- Learning cannot silently modify policy.

### Compatibility

- Existing tests pass.
- Existing API contracts pass.
- Existing memory remains readable.
- Existing agents work.
- Existing Behavior Packs work.
- Existing Studio remains accessible.
- Existing deployments can start without destructive migration.

---

# 52. The Final Architecture

The target architecture is:

```text
                         PERSONAVAULT
                              │
                 SOVEREIGN INTELLIGENCE
                              │
                    PRINCIPAL + ENVIRONMENT
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
       IDENTITY             STATE             MEMBERSHIP
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
     MEMORY                KNOWLEDGE              UNKNOWN
       │                      │                      │
       └──────────────────────┼──────────────────────┘
                              │
                            GOALS
                              │
                          STRATEGY
                              │
                            PLAN
                              │
                   ┌──────────┴──────────┐
                   │                     │
                PREDICT               SIMULATE
                   │                     │
                   └──────────┬──────────┘
                              │
                           OPTIONS
                              │
                           POLICY
                              │
                         AUTHORITY
                              │
                          DECISION
                              │
                           ACTION
                              │
                           OUTCOME
                              │
                          LEARNING
                              │
                  ┌───────────┴───────────┐
                  ↓                       ↓
               MEMORY                 KNOWLEDGE
                  │                       │
                  └───────────┬───────────┘
                              ↓
                         NEXT DECISION
```

---

# 53. The Most Important Design Principle

PersonaVault should not become:

> **an AI that makes decisions for you.**

It should become:

> **the sovereign environment in which intelligence, evidence, prediction, simulation, governance, decisions and learning are continuously connected.**

The model can change.

The agent can change.

The device can change.

The organization can change.

The environment can change.

But the **continuity of intelligence belongs to PersonaVault**.

That is the architectural moat.

---

# 54. Product Architecture in One Sentence

> **PersonaVault provides sovereign intelligence that maintains a persistent model of an Environment, remembers what happened, understands what is known and unknown, predicts what may happen, simulates what could happen, evaluates strategy and policy, supports governed decisions and actions, and learns from outcomes.**

This is the V2 specification.

---

*End of Specification*