# The Unit Primitive

**A technical note on stable reference as a substrate capability**

---

## 1. Abstract

A system that governs its own learning must be able to refer to the things it knows. Not the things themselves — their *referents*. The stable identities that persist across time, permit other primitives to operate on them, and remain distinguishable from each other regardless of how their content changes.

Most systems treat referents implicitly. A pattern is a row; a policy is a document; an event is a log entry. The referent is whatever the storage layer produces when queried. This works until the system must reason *about* its referents — track a pattern's evolution, refer to a policy that governed a decision years ago, distinguish two similar-looking observations.

This paper argues that a **unit** — a stable referent for a thing the system tracks — is a distinct architectural primitive, irreducible to the content it holds or the records that describe it. And it argues that Unit is the substrate's most abstract primitive: it is presupposed by every other primitive and presupposes none of them.

The claim is narrow:

> **A system can maintain stable identity for the things it tracks over time, such that each is referable, versionable, and distinguishable from others — independent of its content.**

The paper defines the primitive, distinguishes it from adjacent concepts, states what it guarantees and what it does not, shows why it is irreducible, and demonstrates it through the unit types PersonaVault maintains.

---

## 2. The Problem: Referents Without Identity

Consider a system that stores knowledge. It has patterns. It has policies. It has events. It has decisions. It has evidence.

Each of these is a thing. But "thing" is not a primitive — it is what the storage layer happens to produce when queried. The system's understanding of "what a pattern is" is the union of all the code that reads and writes patterns. There is no single place where the system can say: *"this is a pattern, this is what it means to be a pattern, this is how a pattern is distinguished from a policy."*

Three problems follow.

**2.1 Similar things become indistinguishable.** Two patterns with similar content are not the same pattern. But if the system identifies patterns by content — by hash, by signature, by embedding — it cannot distinguish "this pattern was updated" from "a new pattern was created." Versioning becomes ambiguous; referential integrity breaks.

**2.2 Things become unreferable.** A pattern derived from an event years ago should still be able to refer to that event. But if the event has no stable referent — if it was stored as a log line whose identity is "the log line at position N" — then the reference is fragile. Any reordering, compaction, or migration breaks it.

**2.3 Categories blur.** A pattern and a policy are different *kinds* of thing. But if both are stored as rows with the same shape, the distinction is by convention. Nothing in the system prevents code from treating a policy as a pattern, or a decision as an event. The categories exist only in the developer's mind, not in the system's model.

A system that solves this by adding a `type` field is solving it partially. The type field says what kind of thing a row represents, but the system cannot *reason* about the type — it cannot enumerate all policies, cannot validate that a policy satisfies the constraints of a policy, cannot enforce that decisions reference policies rather than patterns. Type as metadata is weaker than type as primitive.

---

## 3. What a Unit Is

We define a unit as:

> **A stable referent for a thing the system tracks, with identity that persists across time, a category that distinguishes it from other kinds of things, and independence from the content it currently holds.**

Four parts, each required.

**3.1 A referent.** The unit is the *thing* the system is talking about. Not the thing's current content — the thing itself. Two states of the same unit are the same unit; two units with identical content are distinct units. The primitive is the ability to make this distinction structurally, not by convention.

**3.2 Identity that persists.** The unit's identity is stable across time. It can be referred to before and after any transition, any state change, any content update. Identity is what makes versioning possible: the difference between "this unit was updated" and "a new unit was created" is whether the identity persists.

**3.3 A category.** The unit belongs to a kind. A pattern is a kind of unit; a policy is a different kind. The category is a structural property — the system can determine a unit's kind from the unit itself, not from external schema or convention. This is what allows the system to enforce category-appropriate rules.

**3.4 Content independence.** The unit's identity is independent of its content. A pattern whose confidence changes is the same pattern. A policy that is superseded is the same policy (with a new version). Content can change; identity does not.

Remove any and the unit collapses:

- Remove the referent → the system has content without a subject.
- Remove persistent identity → the system cannot distinguish update from creation.
- Remove the category → the system has instances without types.
- Remove content independence → identity is reducible to content, and any change breaks references.

---

## 4. What a Unit Guarantees

Four things, and only four.

**4.1 Referability.** A unit can be referred to by identity. Not by content, not by position, not by convention — by a stable identifier that resolves to the same unit across time and across contexts.

**4.2 Distinguishability.** Two units are distinguishable even when their content is identical or nearly identical. The system can maintain two similar-looking patterns without collapsing them into one.

**4.3 Categorical integrity.** A unit's category is a structural property. The system can enumerate units by category, enforce category-specific rules, and refuse operations that are invalid for a category.

**4.4 Content independence.** A unit's identity survives changes to its content. Updates, versioning, and state transitions do not create new units; they modify existing ones.

---

## 5. What a Unit Does Not Guarantee

**5.1 That the unit is meaningful.** A unit with an identity is not the same as a unit with a purpose. The system can create units that are meaningless — orphaned records, abandoned patterns, superseded policies. The primitive guarantees reference; it does not guarantee significance.

**5.2 That the unit is unique.** Two units can represent the same underlying thing if the system permits it. Deduplication is a policy, not a primitive guarantee. The unit primitive says "this is a referent"; it does not say "this is the *only* referent for that thing."

**5.3 That the unit's category is correct.** A unit can be categorized incorrectly. The primitive guarantees that the category is a structural property, not that it is the right one.

**5.4 That the unit is complete.** A unit represents something; it does not represent everything about that something. Units are partial by nature — a pattern-unit is not the pattern's full conceptual content, only the system's representation of it.

**5.5 That the unit's content is never confused with another.** A unit's identity is stable, but the system can still conflate units at the code level. The primitive provides the means of distinction; whether the code uses them is an implementation property.

**5.6 That the unit's content is trustworthy.** The unit refers to a thing. Whether the thing's current content reflects reality is a separate question, governed by other primitives.

---

## 6. Why Unit Is Irreducible

An objection: *"A unit is just an object with an ID. Every storage layer has this. Calling it a primitive is a distinction without a difference."*

The answer is that the primitive is not "objects have IDs." It is "the system can refer to things as units — with persistent identity, structural category, and content independence — such that other primitives can operate on units without knowing what they contain."

Three reductions to consider, and why each fails:

**Reduction 1 — Unit reduces to record.** No. A record is a persistent representation of something. A unit is the *something* being represented. They can coincide (a record of a pattern and the pattern-unit are related) but they are distinct: a record can describe a unit without being the unit, and a unit can exist without a record (in-memory referents).

**Reduction 2 — Unit reduces to identity + content.** No. Identity says *whose* — a user, a principal, an environment. Content is *what*. A unit is *the thing itself*. Given only identity and content, the system still cannot distinguish "this content changed" from "a new entity was created" — that requires unit identity, which is distinct from both.

**Reduction 3 — Unit reduces to (record + category).** Closer, but still not the same. A record has category; a unit *is* a category member. A record describes a unit; a unit is what records are about. The distinction matters when the system needs to refer to a thing before it has been recorded, or to distinguish two records that describe the same unit.

Each reduction fails because it captures some properties and misses others. The primitive is the thing that has *all* of them simultaneously.

---

## 7. PersonaVault's Unit Types

PersonaVault implements the Unit primitive through a *taxonomy* — five unit types, each a distinct category of referent, all coexisting in the same system. This section demonstrates the primitive through the taxonomy.

### 7.1 The unit taxonomy

| Unit type | What it refers to | Lifecycle |
|---|---|---|
| **Knowledge unit** | A pattern, rule, or assertion the system has learned | Gas → Liquid → Ice → Deactivated → Evaporated |
| **Event unit** | An observation, correction, or evidence item | Created → Retained |
| **Decision unit** | A choice the system made and its reasoning | Created → Retained |
| **Governance unit** | A policy, trust rule, or constitutional principle | Drafted → Active → Superseded |
| **Provenance unit** | A relationship between other units | Created → Retained |

Each is a distinct category. Each has an identity independent of its content. Each is referable across its lifecycle.

### 7.2 The unit types in the codebase

**Knowledge units — `SemanticPattern`.** A knowledge unit is the system's referent for "a thing the system has learned." It has an identity that persists across all thermodynamic transitions — a pattern that crystallizes, freezes, melts, and re-freezes is the same unit throughout. Its content (the specific pattern, the confidence, the usage count) changes; its identity does not.

Knowledge units are mutable. They have a lifecycle. They can be deactivated (referable, but not active) and evaporated (unreferenced by active systems, but preserved in record).

**Event units — `BehaviourEvent`, `Evidence`.** An event unit is the system's referent for "something that happened." Events are created when observed and never modified. Their content is a snapshot of the observation; their identity is the fact that this observation was made at this time by this source.

Event units are immutable. Their lifecycle is "created → retained." They can be referenced by other units (a pattern derived from an event) but are not themselves modified.

**Decision units — `DecisionTrace`, `DecisionTimeline`, `ReasoningChain`.** A decision unit is the system's referent for "a choice that was made." Decisions are created when the system acts; they preserve the reasoning, the evidence, and the outcome. Their identity persists across audits and replays.

Decision units are immutable. A decision, once made, is a historical fact. Replaying a decision creates a new decision unit — not a modification of the original.

**Governance units — `Policy`, `TrustPolicy`.** A governance unit is the system's referent for "a constraint on behavior." A policy has identity that persists across versions — policy P superseded by policy P' is the same policy in a new version, not two policies. The identity is what allows the system to answer "what policy governs this decision?" with a specific referent.

Governance units are versioned. Their content changes across versions; their identity does not.

**Provenance units — `Lineage`, `MemoryGraph` edges.** A provenance unit is the system's referent for "a relationship between two things." Provenance units are edges: derived-from, caused-by, ordered-before. Each edge is a referent with its own identity, referable by other edges and queryable independently.

Provenance units are immutable. An edge, once created, is a historical fact about a relationship that existed at a moment in time.

### 7.3 Why the taxonomy matters

The five unit types are not a convenience. They are the structure that lets the system maintain referential integrity across different categories of knowledge.

Consider what happens if the system has only one unit type:

- Patterns and policies share a referent. The system cannot enforce that a policy is bounded by a constitution but a pattern is not.
- Events and decisions share a referent. The system cannot distinguish "this happened" from "this was chosen."
- Provenance has no referent. Relationships become implicit and fragile.

The taxonomy is what makes the Unit primitive *usable* — not because referential integrity requires five kinds of referents, but because the system needs to distinguish categories to enforce different rules on different kinds of things.

### 7.4 What the taxonomy demonstrates

The taxonomy is an instance of the Unit primitive in the sense of §3. Each:

- Has a **referent** — the thing the unit refers to.
- Has **persistent identity** — units can be referred to across time.
- Has a **category** — units are of a definite kind, distinguishable from other kinds.
- Is **content-independent** — identity survives content changes.

The taxonomy also demonstrates the primitive's §4 guarantees:

- **Referability** — every unit has an ID and can be referred to by other units.
- **Distinguishability** — two patterns with identical content are still two patterns.
- **Categorical integrity** — the system can enumerate patterns, policies, or decisions as distinct sets.
- **Content independence** — a pattern's identity is stable across all state changes.

### 7.5 What the taxonomy does not claim

The taxonomy does not establish that any unit is *meaningful*, *unique*, *correctly categorized*, *complete*, or *never confused with another at the code level*. Those are properties of how the system uses units, not of the primitive. §5 applies to PersonaVault's unit layer as much as to any other.

---

## 8. Where Unit Sits in the Substrate

The PersonaVault substrate requires eight primitives:

| Primitive | Relationship to Unit |
|---|---|
| **Unit** | *The subject of this paper.* |
| **Identity** | Who may hold authority. Identity is the precondition; Authority is the permission built on it. |
| **Transition** | A change of state on a unit. Requires Unit. |
| **Record** | A persistent representation of a unit. A unit can exist without a record (in-memory); a record always refers to a unit. |
| **Authority** | The ability to act on a unit. Distinct concern. |
| **Policy** | The constraints on behavior, represented as governance records. |
| **Attestation** | The proof that a transition on a unit occurred. Requires Unit. |
| **Trust anchor** | The external reference that makes attestation verifiable. |

Unit is the substrate's *most abstract primitive*. It is presupposed by almost every other primitive: Transition transitions a unit; Record records a unit; Attestation attests to a transition on a unit; Authority grants permission to act on a unit; Policy constrains actions on units.

Unit presupposes none of the others. A system can have units without transitions, without records, without authority — the units exist as referents, even if nothing is done with them. This asymmetry is what makes Unit the substrate's foundational layer: every other primitive depends on the existence of things to operate on.

The relationship between Unit and Record is worth naming precisely, because it's the one that gets conflated: **a unit is *what* a record is about; a record is *how* the unit is persisted.** A system can have units without records (transient referents), but cannot have records without units (there is nothing to represent). The distinction is real, and the substrate requires both as distinct primitives.

---

## 9. Open Questions

**9.1 Unit identity vs. content identity.**
When two units have the same content, should the system treat them as one unit or two? The current model permits both (units are distinct, deduplication is a policy), but the criteria for choosing are not formalized.

**9.2 Unit lifecycle across transitions.**
A knowledge unit's content changes as it moves through thermodynamic phases. Is the unit's identity stable across *all* transitions, or are there transitions that constitute a new unit (e.g., Synthesize produces a Meta-Pattern — is the Meta-Pattern a new unit or a derived unit)? The current model treats Meta-Patterns as new units, but the boundary is not formally stated.

**9.3 Unit category migration.**
Can a unit change category? A draft that was a "proposal" becomes a "policy." Is it the same unit in a new category, or a new unit? The current model treats it as a new unit, but this may not be correct for all cases.

**9.4 Unit ownership across environments.**
When a unit is shared across environments, whose unit is it? The originating environment's, the receiving environment's, or a shared referent? This is distinct from Identity (which is about who may act) — it is about which environment the unit "belongs" to.

---

## 10. Conclusion

The Unit primitive is the stable referent for a thing the system tracks: a thing with identity that persists across time, a category that distinguishes it from other kinds of things, and independence from the content it currently holds. It guarantees referability, distinguishability, categorical integrity, and content independence. It does not guarantee meaning, uniqueness, correctness of category, completeness, or referential integrity at the code level.

It is irreducible because:

- It is not derivable from record (§6, reduction 1).
- It is not derivable from identity + content (§6, reduction 2).
- It is not derivable from (record + category) (§6, reduction 3).
- It is the most abstract of the eight: presupposed by almost every other primitive and presupposing none.

PersonaVault implements the primitive through a *taxonomy* — five unit types, each a distinct category of referent: knowledge units, event units, decision units, governance units, and provenance units. Each has identity that persists across its lifecycle, category that distinguishes it structurally, and content independence.

The claim is narrow and checkable:

> **A system can maintain stable identity for the things it tracks over time, such that each is referable, versionable, and distinguishable from others — independent of its content.**

That is the Unit primitive. Everything else — the specific unit types, the specific identifiers, the specific content model — is implementation.

---

*PersonaVault's five-unit taxonomy, described in §7, is one instance of the primitive. Other systems may implement Unit differently (entity-relationship models, resource-oriented APIs, event-sourced aggregates) and the primitive's guarantees apply to those implementations as well.*
