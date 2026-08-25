# Behavior Pack Architecture

## 1. Overview
A **Behavior Pack** is the canonical unit of domain intelligence in PersonaVault. It is a **portable, versioned, declarative intermediate representation (IR)** that transforms domain-specific behavior into an **executable, auditable decision graph**. It acts as the behavioral layer between a general-purpose Agent Runtime and specific domain logic, ensuring that AI decisions are grounded in verifiable policies.

## 2. Core Abstractions
The Behavior Pack enforces a strict architectural boundary by producing a **Decision Trace** rather than a black-box "Chain of Thought":

| Concept | Purpose |
| :--- | :--- |
| **Ontology** | Defines what exists (entities) and what happens (events) in the domain. |
| **Normalization** | Maps raw, probabilistic world data (LLM output) to a structured "signal" vocabulary. |
| **Policy** | Maps signals and conditions to deterministic decisions and actions. |
| **Autonomy** | Defines human-in-the-loop (HITL) requirements for specific decisions. |
| **Traceability** | Records the verifiable execution path from evidence to outcome. |

## 3. Recommended Schema (v0.1)

```yaml
pack:
  id: [domain-id]
  name: [Domain Name]
  version: 1.0.0
  domain: [domain_category]

entities:
  [entity_name]:
    pattern: [regex_pattern]
    fields: { [field_name]: [type] }

events:
  [event_name]:
    fields: { [field_name]: [type] }

policies:
  - name: [policy_name]
    when:
      signals: [list_of_normalized_signals]
      conditions: [logical_constraints]
    decision:
      type: [decision_type]
      severity: [severity_level]
      reasoning: [human_readable_explanation_template]
    actions:
      - action: [action_name]
        priority: [low|high]
    autonomy:
      level: [observe|suggest|recommend|approve|execute]
    confidence_threshold: [0.0-1.0]

learning:
  observe: [event_list]
  discover: [pattern_types]
  propose:
    minimum_confidence: [float]
```

## 4. The Execution Trace Pipeline
To ensure auditability and decoupling, the system adheres to a verifiable execution pipeline:

```text
┌─────────────────────────────────────────────────────────────┐
│                  USER INPUT / CONTEXT                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    PERCEPTION LAYER                        │
│  - LLM processes raw input                                 │
│  - Extracts entities, intents, signals                     │
│  - Confidence scores attached                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  SIGNAL NORMALIZER                         │
│  - Maps LLM output to canonical signals                    │
│  - Validates against ontology                              │
│  - Creates structured, typed data                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   BEHAVIOR PACK                            │
│  - Domain ontology                                         │
│  - Policies (declarative)                                  │
│  - Decision logic (deterministic)                          │
│  - Action mappings                                         │
│  - Confidence thresholds                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   POLICY ENGINE                            │
│  - Compile-time optimized                                  │
│  - Deterministic evaluation                                │
│  - Policy matching                                         │
│  - Decision production                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   EXECUTION LAYER                          │
│  - Autonomy checks (HITL)                                  │
│  - Action execution                                        │
│  - Outcome tracking                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   PROVENANCE / AUDIT                       │
│  - Complete decision trace                                 │
│  - Verifiable execution                                    │
│  - Human-readable explanation                              │
│  - Queryable, versionable, testable                        │
└─────────────────────────────────────────────────────────────┘
```

## 5. Key Architectural Principles

### Verifiable Execution Trace
Unlike standard "Chain of Thought" (which is often just performative model-generated text), the Behavior Pack produces an **Execution Trace**. This is a reproducible record of the system's observable decision process. If a decision is made, the system can answer "Why?" by pointing to the specific evidence, signals, and policies that triggered it.

### Authoritative vs. Explanatory Reasoning
The system distinguishes between two types of reasoning:
1. **Authoritative Trace**: The machine-readable sequence of `evidence → signal → policy → decision → action`. This is the verifiable truth.
2. **Explanatory Reason**: A human-readable summary generated for clarity. While the explanation is helpful for users, the authoritative trace is what is audited and tested.

### Autonomy Gates (Safety)
Autonomy is a first-class primitive. By defining `autonomy.level`, the runtime enforces safety boundaries (e.g., requiring human approval for high-severity decisions) based on the compiled policy, not the model's whims.

### Auditable Provenance (The "Decision Graph")
Every decision produces a **Decision Graph** containing:
1. **Perception**: What did we think we saw? (with confidence)
2. **Signals**: What canonical facts were extracted?
3. **Evidence**: Which specific data points support the signals?
4. **Policy**: Which specific rule was matched?
5. **Decision**: What was the resulting command?
6. **Action/Outcome**: What happened in the real world?


### Example Decision Trace Structure
The system outputs a typed JSON object representing the authoritative decision trace:

```json
{
  "decision_id": "D-20260825-224538-1984",
  "timestamp": "2026-08-25T22:45:38.966678",
  "agent": "planner",
  "trace": {
    "perception": {
      "source": "raw_input",
      "confidence": 0.85
    },
    "signals": [
      {
        "type": "pattern_match",
        "value": {"trigger": "contract", "weight": 0.8}
      }
    ],
    "policy": {
      "matched": "High Value Case Review",
      "conditions": ["test_entity present", "value > 100"]
    },
    "decision": {
      "type": "review_required",
      "severity": "high",
      "autonomy_level": "recommend"
    },
    "actions": ["notify_executive"]
  },
  "explanation": "The value of this legal case ($2,500,000) exceeds the $1,000,000 threshold."
}
```

## 6. Compiler & Runtime Usage

### Compilation
Packs are written in declarative YAML and compiled into optimized Python for execution.

```bash
# Compile all source packs
python3 compile_packs.py --compile-all

# Compile a specific pack
python3 compile_packs.py --compile legal_intelligence

# List compiled packs
python3 compile_packs.py --list
```

### Testing
You can test a compiled pack directly from the CLI.

```bash
python3 compile_packs.py --test legal_intelligence
```

### Runtime Integration
The `PackExecutor` handles loading and execution of compiled packs.

```python
from runtime.pack_executor import PackExecutor

executor = PackExecutor()
result = await executor.process_with_best_pack(
    raw_input="High value case $2,000,000",
    user_id=1
)
```

