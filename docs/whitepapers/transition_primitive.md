# The Transition Primitive

**A technical note on state change as a first-class architectural event**

---

## 1. Abstract

A system that governs its own learning must be able to observe, order, and justify its changes of state. Most systems record the *result* of a change — the new value, the updated record — and treat the change itself as an implementation detail. This paper argues that a **transition** — the discrete event of moving from one state to another — is a distinct architectural primitive, irreducible to the state it produces or the record that persists it, and required for any system whose evolution is meant to be governed.

The claim is narrow:

> **A state change can be modeled as a first-class event with a defined from-state, to-state, trigger, and guard, such that the change is observable, orderable, and governable — independently of the state it produces.**

The paper defines the primitive, distinguishes it from adjacent concepts (state, mutation, event log), states what it guarantees and what it does not, shows why it cannot be reduced to the other substrate primitives, and demonstrates it through PersonaVault's thermodynamic model — eight transitions that instantiate the primitive in a governed, evolvable memory system.

---

## 2. The Problem: Systems That Record State, Not Change

Consider a database that stores the current value of some entity. An update occurs. The row is overwritten. The old value is gone. The fact that a change happened is invisible.

This is the default model of most systems. State is primary. Change is a mechanism for producing the current state. Once the write completes, the transition that produced it is no longer a thing the system can observe, reason about, or govern.

Three consequences follow.

**2.1 Causality is lost.** When the current state is X, the system cannot say *how* it became X — only that it is X. The chain of transitions that produced X is not representable. This makes provenance impossible to establish from state alone.

**2.2 Ordering is lost.** If two changes happen in sequence, the system cannot say which came first unless it has a separate timestamp mechanism. And timestamps are a proxy for order, not the same thing.

**2.3 Governance becomes a state filter.** If transitions are not first-class, then governance can only operate on states. "Is this state permitted?" replaces "is this change permitted?" These are different questions. A state may be legitimate but the transition that produced it illegitimate — for example, a valid pattern promoted without authority. If governance can only see the state, it cannot detect the illegitimate transition.

Systems that solve this by adding an audit log are only solving 2.1 partially. The audit log records *that* a change happened, but unless the log is itself an event in the state model, it is a parallel record, not a first-class transition.

---

## 3. What a Transition Is

We define a transition as:

> **A discrete, identifiable event that moves a unit from one defined state to another, under a trigger and a guard, at a specific point in time.**

Six parts, each required.

**3.1 A unit.** The thing being changed. It must persist across the transition — the same unit before and after, now in a different state. A transition without a persistent subject is not a change of state; it is a creation or destruction.

**3.2 A from-state.** The state the unit is in when the transition begins. Not implicit — explicit. The transition is only valid if the unit is actually in the from-state at the moment the transition fires. This is a precondition, not an assumption.

**3.3 A to-state.** The state the unit is in after the transition completes. Also explicit, also defined in advance. A transition that produces an undefined state is not a transition; it is a mutation.

**3.4 A trigger.** The event that causes the transition to fire. Not "the system decides to transition" — the specific external or internal condition that, when met, initiates the change. Triggers are observable and testable.

**3.5 A guard.** The condition that must hold for the transition to be permitted. Distinct from the trigger: a trigger says *when* a transition is attempted; a guard says *whether* it is allowed. A transition can fire its trigger and fail its guard, and this is a meaningful event — a *rejected* transition, not a non-event.

**3.6 A point in time.** The moment the transition occurs. Not when it was recorded, not when it was observed, but when the change took effect. This is the anchor for ordering and for attestation.

Remove any and the primitive collapses:

- Remove the unit → nothing changes.
- Remove the from-state → no precondition, the transition can fire from anywhere.
- Remove the to-state → not a defined change.
- Remove the trigger → the transition is not causally anchored.
- Remove the guard → the transition is not governed, only mechanical.
- Remove the point in time → the transition cannot be ordered or attested.

---

## 4. What a Transition Guarantees

Four things, and only four.

**4.1 Observability.** The transition is a first-class event. It can be queried, listed, and reasoned about independently of the state it produces. An observer can see not only "the unit is now Ice" but "the unit transitioned to Ice at time T, via the Freeze transition."

**4.2 Ordering.** Transitions are totally ordered per unit. For any two transitions on the same unit, the system can determine which came first. This gives causality, history, and the ability to reconstruct any prior state.

**4.3 Atomicity.** Each transition is either completed or not. No partial states. If the transition fails partway, the unit remains in the from-state. This makes the state model consistent under failure.

**4.4 Governability.** Because the transition carries a guard, the system can *reject* transitions as well as permit them. A rejected transition is itself an event — an attempt that did not succeed — and this is distinct from a transition that never occurred.

---

## 5. What a Transition Does Not Guarantee

**5.1 That the new state is correct.** A transition moves a unit from S1 to S2. It does not establish that S2 is the *right* state. Correctness is a property of the transition's guard, not of the primitive.

**5.2 That the transition was necessary.** A transition can fire legitimately and still be superfluous. The primitive records the event; it does not judge whether the event was worth firing.

**5.3 That the trigger reflects reality.** A trigger can fire on stale data, on mistaken input, or on a sensor error. The transition is correct given its trigger; the trigger's truth is a separate question.

**5.4 That no transitions were missed.** The primitive guarantees that *recorded* transitions are observable and ordered. It does not guarantee that all attempted transitions were recorded. Detecting gaps requires an external reference — an expected-event source the primitive does not provide.

**5.5 That the guard was correctly evaluated.** If a guard is misapplied — if it permits what should have been rejected, or vice versa — the transition fires faithfully on the misapplied guard. Correctness of the guard is the guard's problem, not the primitive's.

**5.6 That the transition is irreversible.** A transition is the *event* of changing state. Whether the change can be undone depends on whether the reverse transition exists and whether it is allowed. The primitive guarantees the forward transition; reverse transitions are separate events with their own guards.

---

## 6. Why Transition Is Irreducible

An objection: *"A transition is just a state change with extra steps. Any system that changes state has transitions; calling them a primitive is a distinction without a difference."*

The answer is that the primitive is not "state changes happen" — it is "state changes are first-class events with defined from-states, to-states, triggers, and guards." Most systems change state without representing those changes as events. The distinction is between *the change occurring* and *the change being a thing the system can name, order, and govern*.

Three reductions to consider, and why each fails:

**Reduction 1 — Transition reduces to state.** No. State is a snapshot; transition is a differential. A system with only state has no way to express "this unit was in state A and is now in state B." Adding a "previous_state" field is not the same — it represents two states, not the transition between them. The transition carries the trigger, the guard, and the point in time; state carries none of these.

**Reduction 2 — Transition reduces to record.** No. A record is a persistent trace. A transition is an event. You can have records of non-transitions (an observation that changed nothing) and transitions with no persistent record (an in-memory state change that was never persisted). They are related but distinct.

**Reduction 3 — Transition reduces to a timestamped state log.** Closer, but still not the same. A timestamped state log records states in order. A transition is the *operation* that produces a new state from an old one, with a trigger and a guard. The log has the states but not the causal machinery. You can reconstruct the transitions from the log if the log is complete and the state space is fully enumerated — but the reconstruction is inference, not representation.

Each reduction fails because it captures some of the transition's properties and misses others. The primitive is the thing that has *all* of them simultaneously: unit, from-state, to-state, trigger, guard, point in time.

---

## 7. PersonaVault's Transition Model

PersonaVault implements the Transition primitive in a governed memory system organized as a thermodynamic state machine. Patterns exist in phases; transitions between phases are the events of learning. This section demonstrates the primitive through eight transitions that the system actually performs.

### 7.1 The state space

```
                ┌──────────────┐
                │   Gas        │  raw observations, ephemeral
                └──────┬───────┘
                       │ Crystallize
                       ▼
                ┌──────────────┐
        ┌──────►│   Liquid     │  candidate patterns, under test
        │       └──────┬───────┘
        │              │ Freeze
        │ Melt         ▼
        │       ┌──────────────┐
        └───────│   Ice        │  verified, active knowledge
                └──────┬───────┘
                       │ Deactivate
                       ▼
                ┌──────────────┐
                │ Deactivated  │  retired, preserved for audit
                └──────┬───────┘
                       │ Re-Activate
                       └───────────────
```

Gas can also be reached by Evaporate from Liquid or Ice. Liquid can be reached from Ice via Melt. Liquid can be re-promoted to Ice via Re-Freeze.

### 7.2 The eight transitions

| # | Transition | From → To | Trigger | Guard |
|---|---|---|---|---|
| 1 | **Crystallize** | Gas → Liquid | Recurrence threshold reached | Deduplication check passes |
| 2 | **Freeze** | Liquid → Ice | Confidence ≥ θ_freeze AND M successes | No open conflicts; guard checks pass |
| 3 | **Melt** | Ice → Liquid | New evidence conflicts with frozen pattern | Scoped to conflicting clause |
| 4 | **Re-Freeze** | Liquid → Ice | Re-validation succeeds after Melt | Prior Melt recorded in `history`; no recurring conflict within memory window |
| 5 | **Evaporate** | Liquid/Ice → Gas | Decay score < θ_decay | No dependents; not critical-tagged |
| 6 | **Synthesize** | Many Ice → Meta-Pattern | Thermal pressure ≥ θ_pressure | Redundancy ≥ θ_r; cooldown elapsed; no open PendingAction |
| 7 | **Deactivate** | Ice → Deactivated | Governance decision | Pattern is in Ice; decision recorded |
| 8 | **Re-Activate** | Deactivated → Ice | Governance decision | Pattern is in Deactivated; decision recorded |

Each is a transition in the sense defined in §3: a unit (the pattern), a defined from-state and to-state, an observable trigger, an explicit guard, and a point in time.

### 7.3 What each transition demonstrates about the primitive

**Crystallize** shows the primitive applied to creation. The transition is not "a new pattern appears" — it is "an observation cluster crosses a recurrence threshold and becomes a candidate pattern." The from-state (Gas) and to-state (Liquid) are explicit. The trigger is the threshold crossing. The guard is deduplication.

**Freeze** shows the primitive applied to promotion. The from-state is Liquid — a precondition, not an assumption. The to-state is Ice. The trigger is confidence plus success count. The guard is that no open conflicts exist. A Freeze attempt that fails the guard is a rejected transition, not a non-event, and the system records it as such.

**Melt** shows the primitive applied to demotion. It is the most important transition in the model because it is the mechanism by which the system *unlearns*. A frozen pattern that conflicts with new evidence is demoted back to Liquid for re-testing. Without Melt, the Ice layer would ossify; with Melt, it remains revisable.

**Re-Freeze** shows the primitive applied to re-validation. This is a distinct transition from Freeze because the unit carries a *history* — the pattern was once Ice, was demoted via Melt, and is now being re-promoted. The transition is scoped by the presence of a prior Melt event in the pattern's `history` field. This is a worked instance of the primitive's "ordering" guarantee: the system can distinguish a first Freeze from a Re-Freeze *because it can see the transitions that came before*.

**Evaporate** shows the primitive applied to forgetting. The trigger is a decay score (a function of usage and staleness). The guard is that the pattern has no dependents and is not critical-tagged. Evaporation is not deletion — the pattern's raw observations remain in Gas — but it is removal from the active model.

**Synthesize** shows the primitive applied to compounding. The from-state is many Ice patterns; the to-state is a single Meta-Pattern. The trigger is thermal pressure (density plus redundancy above a threshold); the guard includes a cooldown, an idempotency check, and human approval via `PendingAction`. Synthesize is the transition that makes the system's knowledge *compress*, and it is the transition that most clearly requires a guard — without one, the system would synthesize constantly.

**Deactivate** shows the primitive applied to governance. The from-state is Ice; the to-state is Deactivated. The trigger is a governance decision — human or policy. The guard is that the pattern is actually in Ice. The transition does not delete the pattern — it removes it from the active inference pool while preserving provenance. This is the transition an auditor most needs to be able to see.

**Re-Activate** shows the primitive's symmetry requirement. If Deactivate exists, Re-Activate must exist — otherwise governance can only remove patterns, never restore them. The from-state is Deactivated; the to-state is Ice. The guard is a governance decision. Re-Activate is not the same as Re-Freeze: Re-Freeze re-validates a *melted* pattern through evidence; Re-Activate restores a *retired* pattern through governance. They are different transitions because they are triggered by different things.

### 7.4 What the model demonstrates

The eight transitions are not just state changes. They are *governed* state changes, each with a from-state, a to-state, a trigger, and a guard, each ordered per unit, each observable, each atomic. They instantiate the Transition primitive in the sense of §3.

The model also demonstrates the primitive's guarantees:

- **Observability** — every transition is recorded in the pattern's `history` and is queryable.
- **Ordering** — the history field is ordered; the system can reconstruct which transitions happened in which order.
- **Atomicity** — the TransitionService ensures that either a transition completes or the unit remains in its prior state.
- **Governability** — every transition has a guard, and rejected transitions are recorded as such.

### 7.5 What the model does not claim

The eight transitions do not establish that a pattern's current state is *correct*, that a transition was *necessary*, that a trigger's underlying data was *accurate*, or that no transitions were *missed*. Those are properties of the transition's guard or trigger, not of the primitive. §5 applies to PersonaVault's model as much as to any other.

---

## 8. Where Transition Sits in the Substrate

The PersonaVault substrate requires eight primitives:

| Primitive | Relationship to Transition |
|---|---|
| **Unit** | The subject of the transition. Transition requires a unit; Unit does not require Transition. |
| **Identity** | Whose unit is being transitioned. Distinct concern. |
| **Transition** | *The subject of this paper.* |
| **Record** | The persistent trace of the transition. Transition can occur without a record (in-memory); Record can exist without a transition (an observation). |
| **Authority** | Who may transition. Enforced by the guard. |
| **Policy** | What is permitted under what conditions. Enforced by the guard. |
| **Attestation** | The cryptographic binding of the transition to a verifiable record. Requires Transition. |
| **Trust anchor** | The external reference that makes attestation verifiable. |

Transition is the primitive that Attestation binds. Without Transition, there is nothing for Attestation to attest. Without Attestation, Transition is real but unverifiable outside the system. They are complementary.

The relationship between Transition and Record is worth naming precisely, because it's the one that most often gets conflated: **a transition is an event; a record is a durable representation of an event.** They can diverge — an in-memory transition with no record, a record of a non-transition — and the substrate requires both as distinct primitives.

---

## 9. Open Questions

**9.1 Composition across systems.**
If system A performs a transition and system B consumes the result, how do the two transition histories compose? A federated transition model — where transitions in one system can trigger transitions in another, with verifiable ordering across the boundary — is not yet formalized.

**9.2 Transition semantics under distributed execution.**
If two systems transition the same unit concurrently, what is the correct resolution? PersonaVault's transitions are per-environment, so this is not yet a problem in practice. It becomes one when patterns cross environments.

**9.3 The boundary between Transition and Unit-Creation.**
Synthesize produces a Meta-Pattern — a *new* unit from many existing Ice patterns. Is this a Transition (because the Ice patterns changed phase), a Unit-Creation (because a new pattern appeared), or both? The current model treats it as a Transition on the source patterns plus a Unit-Creation of the Meta-Pattern. Whether these should be unified is an open design question.

**9.4 Reversibility and its guarantees.**
Deactivate and Re-Activate are a symmetric pair. Melt and Re-Freeze are a symmetric pair. But Crystallize has no reverse (an observation cannot un-crystallize), and Evaporate has no reverse (a pattern that has evaporated is gone). The model is symmetric where symmetry is meaningful and asymmetric where it isn't — but the criteria for when a reverse transition is required are not yet formally stated.

---

## 10. Conclusion

The Transition primitive is the modeling of a state change as a first-class event: a unit moving from a defined from-state to a defined to-state, under a trigger and a guard, at a specific point in time. It guarantees observability, ordering, atomicity, and governability. It does not guarantee correctness, necessity, trigger accuracy, or completeness.

It is irreducible because:

- It is not derivable from state (§6, reduction 1).
- It is not derivable from record (§6, reduction 2).
- It is not derivable from a timestamped state log (§6, reduction 3).
- It fails in ways distinct from the primitives it is commonly conflated with.

PersonaVault implements the primitive through eight transitions — Crystallize, Freeze, Melt, Re-Freeze, Evaporate, Synthesize, Deactivate, Re-Activate — each with a defined from-state, to-state, trigger, and guard, each ordered per unit, each observable, each governable.

The claim is narrow and checkable:

> **A state change can be modeled as a first-class event with a defined from-state, to-state, trigger, and guard, such that the change is observable, orderable, and governable — independently of the state it produces.**

That is the Transition primitive. Everything else — the specific state machine, the specific triggers, the specific guards — is implementation.

---

*PersonaVault's thermodynamic model, described in §7, is one instance of the primitive. Other systems may implement Transition differently (event sourcing, CQRS, actor models) and the primitive's guarantees apply to those implementations as well.*
