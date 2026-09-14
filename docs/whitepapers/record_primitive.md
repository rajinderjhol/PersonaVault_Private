# The Record Primitive

**A technical note on persistent representation as a first-class substrate capability**

---

## 1. Abstract

A system that learns must be able to represent what it knows, what it observed, what it did, and what it derived — and it must be able to distinguish these categories, because each carries different guarantees and fails in different ways.

Most systems have one kind of record: a row, a document, a log entry. Everything is stored in the same shape, and the differences between a pattern and an observation, between a decision and the policy that governed it, between a derivation and the thing it was derived from, are expressed informally — in metadata, in convention, or not at all.

This paper argues that a **record** — a persistent representation of something the system knows, observed, did, or derived — is a distinct architectural primitive, irreducible to the transitions it stores or the state it holds. And it argues that a substrate for governed, evolvable memory requires not one record type but a *taxonomy* of them, because different kinds of persistent representation carry different guarantees.

The claim is narrow:

> **A persistent representation can be modeled as a first-class primitive with defined identity, immutability rules, and provenance, such that the system can distinguish what it knows from what it observed from what it did from what it derived — and can reason about each independently.**

The paper defines the primitive, states what it guarantees and what it does not, shows why it cannot be reduced to the other substrate primitives, and demonstrates it through PersonaVault's five-variant record layer.

---

## 2. The Problem: When Everything Is a Row

Consider a system that stores everything it knows and everything that happens in a single record type — a table, a document store, a log. Every entry has the same shape: an ID, a payload, a timestamp, maybe a type field.

This is the default model of most systems. Records are uniform. The differences between a knowledge assertion and an observed event, between a decision and the policy that governed it, between a derivation and the thing it was derived from — all of these are collapsed into a single representation, distinguished only by convention.

Three consequences follow.

**2.1 Guarantees cannot be distinguished.** A record of an observation should be immutable — you cannot un-observe something. A record of a pattern should be mutable — the pattern's confidence changes over time. If both are stored as the same record type, the system cannot enforce immutability on one without freezing the other. The guarantees a record provides are determined by what *kind* of record it is; uniform records cannot provide differentiated guarantees.

**2.2 Relationships cannot be expressed natively.** A derivation is not a record — it is a relationship between records. A lineage edge, a "derived from," a policy applied to a decision — these are second-order structures. If the system has only one record type, relationships must be encoded as fields, as foreign keys, or as duplicated content. The relationships become implicit, and implicit relationships are the ones that get lost.

**2.3 Provenance cannot be reconstructed.** When the system is asked *"why do you believe X?"*, the answer must be reconstructible from the record layer. If the records are uniform, the answer requires external knowledge — a schema, a convention, a code path — that is not itself in the records. The system knows X, but cannot prove *how* it came to know X from the records alone.

A system that solves this by adding a schema is only partially solving the problem. The schema says *"this field means observation"*, but the record layer cannot enforce it, cannot check it, cannot reason about it independently of the code that reads it.

---

## 3. What a Record Is

We define a record as:

> **A persistent representation of something the system knows, observed, did, or derived, with defined identity, a temporal anchor, and a stated relationship to the system's other records.**

Five parts, each required.

**3.1 A subject.** The thing the record represents. Not the record's content — the *referent*. What is this record *about*? A pattern is about a piece of knowledge. An event is about something that happened. A decision is about a choice that was made.

**3.2 Identity.** The record has a stable identity across time. It can be referred to, linked to, and reasoned about by its identity, independent of its current content. Without identity, records are data; with identity, they are *things*.

**3.3 A temporal anchor.** Every record is anchored in time — not as metadata, but as a property. When did this knowledge come into existence? When was this event observed? When was this decision made? Time is what makes records orderable, comparable, and contextualizable.

**3.4 A defined immutability rule.** Every record type declares whether it is mutable or immutable. An observation is immutable — it happened. A pattern is mutable — its confidence changes. A policy is immutable in its historical form, but superseded by a new version rather than modified. The immutability rule is a property of the record type, not of the record instance.

**3.5 A stated relationship to other records.** Records are not isolated. A pattern was derived from observations. A decision was governed by a policy. A lineage edge connects two things. Every record declares how it relates to the others — not by convention, but as a structural property.

Remove any and the record collapses into data:

- Remove the subject → you have a payload with no referent.
- Remove identity → the record cannot be referred to.
- Remove the temporal anchor → the record cannot be placed in history.
- Remove the immutability rule → the record's guarantees are undefined.
- Remove the relationship → the record is an island, and provenance is lost.

---

## 4. What a Record Guarantees

A record does not guarantee one thing. It guarantees a *set* of properties determined by its variant — but four guarantees are common to all record types that qualify as records under §3.

**4.1 Persistence.** The record survives the process that created it. Not necessarily forever — retention is a policy — but beyond the immediate transaction. A record that is not persistent is a value, not a record.

**4.2 Referencability.** The record can be referred to by identity, from other records, from code, from external queries. Referencability is what turns a record from a value into a thing.

**4.3 Temporal placement.** The record is locatable in time — its own time (when it was created), and, if it represents an event or observation, its *referent's* time (when the thing it records happened). The distinction matters: a log entry created at 10:05 recording an event that occurred at 10:03 has two times, and both are meaningful.

**4.4 Categorical distinction.** The record's type is a structural property, not a convention. The system can distinguish records of different kinds by inspecting the record itself, without external knowledge of schema or convention. This is what allows different record types to carry different guarantees.

The fourth guarantee is the one most systems lack. They have records, they have persistence, they have identity and time — but they do not have *categorical distinction as a structural property*. And without it, the guarantees of §4.1–4.3 cannot be differentiated across record types.

---

## 5. What a Record Does Not Guarantee

**5.1 That the record reflects reality.** A record of an observation records that the system observed something — not that the thing observed is true. A record of a pattern records that the system has a pattern — not that the pattern is correct. The record is faithful to what the system represents; the correspondence to reality is a separate question.

**5.2 That the record is complete.** A record represents *something*. It does not guarantee that it represents *everything* relevant. Detecting gaps requires an external reference for what should have been recorded.

**5.3 That the record is consistent with other records.** Two records can contradict each other. A pattern can conflict with another pattern. A decision can violate a policy. The record layer stores the contradiction; it does not resolve it. Consistency is enforced by other primitives — policy, governance, attestation — not by the record itself.

**5.4 That the record is authoritative.** A record can be overwritten, superseded, or revoked by a higher-authority record. The record's authority depends on the record type and the governance context.

**5.5 That the record is immutable in the cryptographic sense.** Immutability, as used here, is a property of the record type — whether the system's rules allow modification. Cryptographic immutability — whether the record can be proven unmodified to a third party — is attestation's concern, not the record's.

**5.6 That relationships are transitive.** A record can reference another record, which references a third. Whether the reference chain is transitively usable depends on the semantics of the relationship, which the record layer does not enforce.

---

## 6. Why Record Is Irreducible

An objection: *"A record is just persisted state. Any system that stores anything has records. Calling them a primitive is a distinction without a difference."*

The answer is that the primitive is not "the system persists things." It is "the system persists things *as records* — with identity, temporal anchors, immutability rules, and stated relationships — such that different *kinds* of persistent representation carry different guarantees."

Three reductions to consider, and why each fails:

**Reduction 1 — Record reduces to state.** No. State is a snapshot of what is currently the case. A record is a *thing* the system can refer to, reason about, and relate to other records. State has no identity, no temporal anchor beyond "now", no categorical distinction. Reducing records to state loses all four of these.

**Reduction 2 — Record reduces to transition.** No. A transition is an event — a change of state. A record is a persistent representation. They can be co-present (a transition that produces a record), but they are distinct: a record can represent a non-transition (an observation, a fact), and a transition can occur without producing a record (an in-memory state change that was never persisted). They are related but distinct.

**Reduction 3 — Record reduces to (state + event log).** Closer, but still not the same. An event log records events; a state store records state. Neither provides categorical distinction as a structural property, and neither provides the *relationships between records* as first-class structures. Records are persistent representations; they have their own identity and their own relationships, independent of whether they correspond to events or state.

Each reduction fails because it captures some of the properties and misses others. The primitive is the thing that has *all* of them: subject, identity, temporal anchor, immutability rule, stated relationships.

---

## 7. PersonaVault's Record Layer

PersonaVault implements the Record primitive through a *taxonomy* — five record variants, each carrying different guarantees, all coexisting in the same system. This section demonstrates the primitive through the taxonomy.

### 7.1 The five variants

| Variant | Subject | Immutability | Primary guarantees |
|---|---|---|---|
| **Knowledge record** | A unit of knowledge | Mutable | Identity, semantic integrity, versioning |
| **Event record** | Something that happened | Immutable | Temporal anchoring, source attribution |
| **Decision record** | A choice the system made | Immutable | Causal linkage, reproducibility |
| **Governance record** | A constraint on behavior | Immutable (versioned) | Authority attribution, scope |
| **Provenance record** | A relationship between records | Immutable | Directionality, graph integrity |

Each variant is a distinct instantiation of the Record primitive. Each satisfies the five requirements of §3. Each carries a guarantee set that is *appropriate to its kind* — the system does not enforce immutability on mutable records, and does not allow modification of immutable ones.

### 7.2 The five variants in the codebase

**Knowledge records — `SemanticPattern`, `Pattern`.** These represent units of knowledge. A pattern has an identity, a current state (Gas/Liquid/Ice/Deactivated), a confidence score, a usage count, a provenance chain, and a history of transitions. Knowledge records are mutable: the pattern's state changes over time. The record's identity is stable; its content is not.

The guarantee this variant provides is **versioned mutability**: the pattern can be updated, but its history is preserved. An observer can query not just "what does this pattern currently assert?" but "how has this pattern's confidence changed over time?" and "what transitions has this pattern undergone?"

**Event records — `BehaviourEvent`, `Evidence`.** These represent things that happened — observations, incidents, corrections, evidence introduced into the system. An event record is immutable: once recorded, the event is a historical fact and cannot be altered. Its temporal anchor is the moment of observation. Its source attribution identifies where the observation came from.

The guarantee this variant provides is **immutable observation**: an event record cannot be modified after creation. If new information arrives that contradicts a prior observation, that arrival is a *new* event, not a modification of the old one. This is the correct model for observation — you cannot un-observe something.

**Decision records — `DecisionTrace`, `DecisionTimeline`, `ReasoningChain`.** These represent choices the system made and the reasoning that led to them. A decision record captures the decision itself, the evidence that supported it, the policy that governed it, and the chain of reasoning that produced it. Decision records are immutable — a decision, once made, is a historical fact.

The guarantee this variant provides is **reproducibility**: from the decision record alone, an observer can reconstruct what the system decided and why. This is what makes decision records auditable — the "why" is not external to the record; it is in the record.

**Governance records — `Policy`, `TrustPolicy`.** These represent constraints on behavior — what is permitted, under what conditions, by what authority. Governance records are immutable in their historical form: a policy is not modified; it is superseded by a new version rather than modified. The identity of the policy persists; the specific constraint it expresses is versioned.

The guarantee this variant provides is **authority attribution with versioned scope**: an observer can determine which policy was in effect at a given time, who authorized it, and what it constrained.

**Provenance records — `Lineage`, `MemoryGraph`, `VectorClock`.** These represent relationships between other records — derivation, causality, ordering across distributed events. A provenance record is not the derived thing or the source thing; it is the *edge between them*. Provenance records are immutable.

The guarantee this variant provides is **navigable derivation**: from any record, the system can determine its sources, and from any source, the system can determine what was derived from it. The graph is traversable in both directions.

### 7.3 Why the taxonomy matters

The five variants are not a convenience. They are the structure that lets the record layer provide *differentiated guarantees*.

Consider what happens if the system has only one record type:

- Observations and patterns share a record. The system cannot enforce immutability on observations without freezing patterns.
- Decisions and events share a record. The system cannot distinguish "what happened" from "what was decided about it."
- Policies and evidence share a record. The system cannot distinguish "this is a constraint" from "this is an input."
- Derivations have no record. The relationships between records are implicit.

The taxonomy is what makes the record layer *governable* — not because governance requires five tables, but because governance requires that the system can enforce different rules on different kinds of persistent representation.

### 7.4 What the taxonomy demonstrates

The taxonomy is an instance of the Record primitive in the sense of §3. Each variant:

- Has a **subject** — knowledge, observation, decision, constraint, relationship.
- Has **identity** — records are referable by ID.
- Has a **temporal anchor** — creation time, referent time, or both.
- Has a **defined immutability rule** — mutable for knowledge; immutable for the others.
- Has **stated relationships** — knowledge cites observations, decisions cite policies, provenance records cite both endpoints.

The taxonomy also demonstrates the primitive's §4 guarantees:

- **Persistence** — all records survive process restarts.
- **Referencability** — records can be referred to by ID, by other records, and by external queries.
- **Temporal placement** — records are queryable by time.
- **Categorical distinction** — the record's variant is a structural property, not a metadata convention. The system can enforce variant-appropriate rules because it can determine a record's variant from the record itself.

### 7.5 What the taxonomy does not claim

The taxonomy does not establish that any specific record is *true*, *complete*, *consistent*, or *authoritative*. Those are properties of the record's subject and its governance, not of the record primitive. §5 applies to PersonaVault's record layer as much as to any other.

The taxonomy is also not claimed to be exhaustive. A system with these five variants is well-specified for governance, but not necessarily for every purpose. Attestation (§8) is the clear case of a record type that PersonaVault lacks.

---

## 8. Where Record Sits in the Substrate

The PersonaVault substrate requires eight primitives:

| Primitive | Relationship to Record |
|---|---|
| **Unit** | The subject of a record. Records represent units. |
| **Identity** | Whose record it is. Distinct concern. |
| **Transition** | The event a record may represent. Records can represent transitions, but also non-transitions. |
| **Record** | *The subject of this paper.* |
| **Authority** | Who may create, modify, or revoke a record. Enforced by record-type rules and governance. |
| **Policy** | The constraints on behavior, represented as governance records. |
| **Attestation** | The cryptographic binding of the transition to a verifiable record. Requires Record. |
| **Trust anchor** | The external reference that makes attestation verifiable. |

Transition is the primitive that Attestation binds. Without Transition, there is nothing for Attestation to attest. Without Attestation, Transition is real but unverifiable outside the system. They are complementary.

The relationship between Transition and Record is worth naming precisely, because it's the one that most often gets conflated: **a transition is an event; a record is a durable representation of an event.** They can diverge — an in-memory transition with no record, a record of a non-transition — and the substrate requires both as distinct primitives.

---

## 9. Open Questions

**9.1 The boundary between record and unit.**
A `SemanticPattern` is both a unit (a thing that can be transitioned) and a record (a persistent representation of knowledge). Is this a conflation, or are unit and record legitimately the same object viewed differently? The current model treats them as the same object; whether this is correct or an accident is an open question.

**9.2 Record identity across versions.**
A governance record (a Policy) is immutable in its historical form but superseded by a new version. Does the policy have one identity or many? When the system asks "what policy governs this decision?", does it query the version that was in effect, or the version that is current? The answer determines how policy-bound decisions are audited.

**9.3 The record of a record.**
Provenance records reference other records. But provenance records are themselves records. Is there a meta-level where the system records the creation of a provenance record? The current model does not have this; the question is whether it should.

**9.4 Record retention and the interaction with evaporation.**
When a pattern evaporates, its record is removed from the active model. But the record of the *evaporation* — the transition that removed it — is preserved. Should the pattern's record itself be preserved for audit, or is the transition record sufficient? This interacts with the Evaporate transition's guarantees and with retention policy.

---

## 10. Conclusion

The Record primitive is the persistent representation of something the system knows, observed, did, or derived — with identity, a temporal anchor, an immutability rule, and stated relationships. It guarantees persistence, referencability, temporal placement, and categorical distinction. It does not guarantee truth, completeness, consistency, authority, or cryptographic immutability.

It is irreducible because:

- It is not derivable from state (§6, reduction 1).
- It is not derivable from transition (§6, reduction 2).
- It is not derivable from (state + event log) (§6, reduction 3).
- It fails in ways distinct from the primitives it is commonly conflated with.

PersonaVault implements the primitive through a *taxonomy* — five record variants, each with its own guarantees: knowledge records (mutable, versioned), event records (immutable, temporal), decision records (immutable, reproducible), governance records (immutable, versioned), and provenance records (immutable, directional).

The taxonomy is the point. A system with only one record type cannot provide differentiated guarantees; a system with a taxonomy can. And it is the taxonomy, not the individual record, that makes the record layer *governable* — not because governance requires five tables, but because governance requires that the system can enforce different rules on different kinds of persistent representation.

The claim is narrow and checkable:

> **A persistent representation can be modeled as a first-class primitive with defined identity, immutability rules, and provenance, such that the system can distinguish what it knows from what it observed from what it did from what it derived — and can reason about each independently.**

That is the Record primitive. Everything else — the specific schema, the specific tables, the specific queries — is implementation.

---

*PersonaVault's five-variant record layer, described in §7, is one instance of the primitive. Other systems may implement Record differently (event sourcing with distinct event and snapshot stores, CQRS with separate read and write models, append-only logs with structural variants) and the primitive's guarantees apply to those implementations as well.*
