# Attested Epistemic Transitions

**A technical note on proving what an AI learned, from where, and under what governance — to a third party, without trusting the AI**

---

## 1. Abstract

An AI system that learns changes what it knows. Most systems record the *current state* of that knowledge — a database of patterns, a vector store, a policy table. Some record *where* a given piece of knowledge came from. Almost none can prove to an outside party *that a specific change to the system's understanding occurred, under what authority, from what source, at what time* — without the outside party having to trust the system's own account.

This note argues that this capability is a distinct primitive — **attestation of epistemic transitions** — and that it is required for any AI system whose learning is meant to be legible outside itself.

The claim is narrow:

> **A change to an AI's understanding can be bound to a cryptographic record at the moment of the change, such that a third party verifies what the AI learned, when, from what source, and under what authority — without accessing the AI's systems.**

---

## 2. The Problem: An AI That Can't Prove What It Learned

Consider an AI system that has been running in an organization for two years. It has accumulated patterns, rules, and policies. When asked *"why did you recommend X?"*, it retrieves the pattern that produced X and says: *"because I learned Y at some point."*

Three questions can be asked of that answer, and they are distinct.

**Question 1 — What does the system currently believe?**
This is a *state* question. Answerable by reading the system's memory.

**Question 2 — Where did this belief come from?**
This is a *provenance* question. Answerable by following the record's lineage — if the lineage is complete.

**Question 3 — Can I prove, independently, that this belief entered the system at a specific time, from a specific source, under a specific authority?**
This is an *attestation* question. It is not answerable by reading the system, because the system is being questioned. It requires an external reference the system does not control.

Most AI memory systems answer 1 and gesture at 2. A small number do 2 well. Almost none do 3, because doing 3 requires three capabilities that don't naturally co-occur:

- A model of *transitions* between knowledge states — not just current state.
- A record generated *at* the transition — not reconstructed.
- An external trust anchor — a key the verifier holds, independent of the AI.

Without 3, the answer to *"how do you know?"* is: *"because the system says so."* For an auditor, a regulator, a customer, or a court, that is not an answer.

---

## 3. What an Epistemic Transition Is

PersonaVault models knowledge as a thermodynamic state machine. Patterns exist in three phases:

- **Gas** — raw observations, ephemeral
- **Liquid** — recurring patterns, being tested
- **Ice** — crystallized, verified knowledge

Transitions between phases are the events of learning:

| Transition | Meaning |
|---|---|
| **Crystallize** | Gas → Liquid. A recurring observation becomes a candidate pattern. |
| **Freeze** | Liquid → Ice. A candidate pattern is verified and promoted. |
| **Melt** | Ice → Liquid. A frozen pattern conflicts with new evidence and is demoted. |
| **Evaporate** | Liquid/Ice → Gas. A pattern decays from disuse and is purged. |
| **Synthesize** | Many Ice patterns → one Meta-Pattern. Compounded knowledge. |
| **Infer** | Human corrections → a Policy draft. Implicit rules made explicit. |

Each of these is an *epistemic transition*: a change to what the system knows. This is the unit that attestation must be able to bind to a record.

This is a different unit than an *action*. An action is what an AI does. An epistemic transition is what an AI comes to know. The governance of actions and the governance of knowledge are distinct problems.

---

## 4. What Attestation of an Epistemic Transition Is

We define it as:

> **The binding of an epistemic transition to a cryptographic record, at the moment of the transition, with an external trust anchor that a third party controls.**

Six parts, each required.

**4.1 A unit.**
The pattern, rule, or policy being changed. It must have an identity that persists across the transition — the same unit before and after, now in a different phase.

**4.2 A transition.**
The specific change of phase or status. Not "the pattern exists" but "the pattern moved from Liquid to Ice at time T." Attestation is about the change, not the state.

**4.3 A record.**
The transition is encoded in a form that can be verified — canonicalized, hashed, signed. The encoding must be deterministic: the same transition, described twice, must produce the same hash.

**4.4 A defined point.**
The record is generated *at* the transition — from the event that triggered it, before any downstream system can observe or modify it. Not reconstructed after the fact. In PersonaVault, the point of truth is the thermodynamic transition itself: the moment confidence crosses θ_freeze, or a conflict is detected and Melt fires, or pressure exceeds θ_pressure and Synthesize triggers.

**4.5 An authority.**
The governance that permitted the transition. In PersonaVault this is not a delegation chain, it is a *policy*: the constitution, the trust policy, the HITL gate that approved the promotion. "What rules authorized this pattern to become Ice?"

**4.6 An external trust anchor.**
A public key the verifier holds, obtained through a channel the verifier controls, identifying the signing authority of the AI's governance.

Remove any and attestation collapses:

- Remove the unit → nothing to attest.
- Remove the transition → a snapshot, not an event.
- Remove the record → a log entry with no cryptographic binding.
- Remove the defined point → post-hoc reconstruction.
- Remove the authority → attestation with no governance context.
- Remove the anchor → self-assertion.

---

## 5. What It Guarantees

Four things, and only four.

**5.1 Integrity.** The record of the epistemic transition has not been modified since it was created. Any change invalidates the cryptographic check.

**5.2 Attribution.** The record was produced by a specific governance authority, identified by a key the verifier trusts. Not "the AI" — the *governance layer that authorized the transition*.

**5.3 Point of truth.** The record was generated at the transition, from the event that triggered it. Not reconstructed later. The timestamp reflects when the AI learned, not when someone later wrote down that it had.

**5.4 Verifiability without trust.** A third party checks 5.1–5.3 without accessing the AI's systems and without trusting the AI's operator.

---

## 6. What It Does Not Guarantee

**6.1 That the knowledge is true.** Attestation records that the AI came to believe X under authority Y. It does not establish that X is correct. An AI can be attested to have learned a false pattern.

**6.2 That the source was reliable.** The record identifies where the knowledge came from. It does not establish that the source was trustworthy. That is a provenance-and-trust question, not an attestation question.

**6.3 That the governance was correct.** If the policy that permitted Freeze was misapplied, the attestation records the misapplication faithfully. It does not detect that the policy was wrong.

**6.4 That the pattern was actually useful.** A pattern can be attested to have crystallized and still be worthless. Usefulness is measured by outcomes, not attestation.

**6.5 That all transitions were attested.** The record proves a transition occurred. It does not prove that no unrecorded transitions occurred. Detecting gaps requires an external reference for what should have been attested.

**6.6 That the AI cannot be deceived.** Attestation records what the system came to know. It does not prevent the system from being fed poisoned input that produces a spurious pattern. Preventing that is a defense-in-depth problem, not an attestation problem.

The discipline is in what the primitive does not claim. A system that says *"we can prove what our AI learned, from where, under what authority"* is making a checkable claim. A system that says *"we can prove our AI's knowledge is correct"* is overclaiming by an entire category.

---

## 7. Why This Is Not Just Provenance

An objection: *"PersonaVault already records provenance — `derived_from`, lineage, the ADT. Why is attestation separate?"*

Provenance answers a *chain* question: *this pattern came from that source, through these transformations.* Attestation answers a *boundary* question: *did this transition occur under this authority, and can I check it independently?*

A system with provenance but no attestation can be internally consistent and externally unverifiable. A system with attestation but no provenance can be externally verifiable and internally groundless.

The failure modes are different:

| Failure | Provenance detects | Attestation detects |
|---|---|---|
| A record's lineage is broken | Yes | No |
| A record was modified after creation | No | Yes |
| A pattern was promoted without authority | Partial | Yes |
| A pattern's origin is unknown | Yes | No |
| A transition occurred at an unrecorded time | No | Yes |

Neither subsumes the other. A governed, evolvable memory requires both.

---

## 8. Where It Sits in the Substrate

The PersonaVault substrate requires eight primitives:

| Primitive | PersonaVault expression |
|---|---|
| **Unit** | `SemanticPattern`, `BehaviourEvent`, `Policy` |
| **Identity** | user, environment, membership, principal |
| **Transition** | Freeze / Melt / Evaporate / Synthesize |
| **Record** | `derived_from`, lineage, ADT, `ProvenanceTracker` |
| **Authority** | constitution, trust policy, HITL gates |
| **Policy** | `learning/policy.py`, `policy_inference_service` |
| **Attestation** | *the subject of this paper* |
| **Trust anchor** | *the key the verifier holds* |

Six of these exist in the PersonaVault codebase today. **Attestation and trust anchor are the two that do not.**

*Note: The codebase contains a signature mechanism for pattern packages (`app/services/pattern_exchange.py`), but it uses a shared secret rather than an external trust anchor (public key infrastructure) and is not bound to the thermodynamic transition points themselves. Therefore, it produces authenticated records, not attestations.*

That is the finding this paper documents. PersonaVault can currently record what it learned, from where, under what policy. It cannot prove any of that to a third party without that party trusting PersonaVault's own account.

Adding attestation is not a rewrite. It is the addition of two primitives to an otherwise complete substrate.

---

## 9. A Demonstration (Target State)

PersonaVault's current implementation does not yet produce attested epistemic transitions. The following describes what the target implementation would produce, so that the paper states what "done" looks like.

**The scenario.** A pattern's confidence crosses θ_freeze. The thermodynamic engine promotes it from Liquid to Ice. At the moment of promotion, before any other subsystem observes the new phase, the attestation layer generates a signed record of the transition.

**What the record would carry.**

- **Unit:** the pattern's identity and content hash
- **Transition:** Liquid → Ice, with the triggering condition (`confidence ≥ θ_freeze`)
- **Source:** the evidence that produced the confidence — the observations, corrections, or synthesized inputs that contributed
- **Authority:** the policy or governance event that permitted the promotion
- **Point of truth:** timestamp and event identifier at the moment of transition
- **Proof:** canonical hash, signature (Ed25519), signer public key, optional post-quantum signature

**What verification would check.**

1. Content hash matches the committed value
2. Signature verifies against the signer key
3. Signer is in the trusted governance registry
4. The claimed source exists in provenance
5. The claimed authority exists in governance
6. The timestamp precedes any downstream effect

**The four outcomes.**

| Scenario | Hash | Signature | Governance | Verdict |
|---|---|---|---|---|
| Clean | ✅ | ✅ | ✅ Trusted | **VALID** |
| Record altered | ❌ | ❌ | ✅ Trusted | **INVALID** |
| Signature corrupted | ✅ | ❌ | ✅ Trusted | **INVALID** |
| Untrusted governance | ✅ | ✅ | ❌ Untrusted | **UNTRUSTED** |

The rows are distinct — the checks are independent, and the verifier reports *which* failed.

**What the demonstration would prove.** That a change to the AI's understanding can be bound to a record at the moment of the change, with an external trust anchor, and verified by a third party without accessing the AI's systems.

**What it would not prove.** That the pattern is correct, that the source is reliable, that the governance was sound, or that all transitions were attested. Those remain questions for other primitives.

---

## 10. The Point of Truth in PersonaVault

The property that distinguishes attestation from logging is *when* the record is generated.

In PersonaVault, the point of truth is the thermodynamic transition itself — the moment the state machine advances. Concretely:

- **Crystallize** — the moment the observation counter crosses the crystallization threshold.
- **Freeze** — the moment confidence crosses θ_freeze *and* the guard checks pass.
- **Melt** — the moment a conflict is detected between a frozen pattern and new evidence.
- **Evaporate** — the moment the decay score falls below θ_decay *and* the dependent/critical guards clear.
- **Synthesize** — the moment thermal pressure crosses θ_pressure *and* the cooldown has elapsed.

Each of these is a discrete event in `MemoryThermodynamics`. The attestation layer would subscribe to these events and generate the record synchronously, before the transition is visible to any other subsystem.

This is the architectural requirement: **the record must be produced by the transition, not extracted from its result.** A system that reconstructs the record from state afterwards is producing a log, not an attestation.

---

## 11. Open Questions

Three questions specific to epistemic attestation remain unresolved.

**11.1 Composition across synthesized patterns.**
When many patterns synthesize into a Meta-Pattern, what is attested? The synthesis event? The source patterns? Both? A composition model for chained epistemic attestations is not yet defined.

**11.2 Decay of attested knowledge.**
When a pattern evaporates, does its attestation record survive? Retention policy for epistemic attestations is distinct from retention of the pattern itself — an auditor may need to know *that* a pattern was learned even after it has been forgotten.

**11.3 Privacy of the attested content.**
An attestation record identifies the source and content of what the AI learned. In some contexts, that content is sensitive — a clinical pattern is itself patient-adjacent. Selective disclosure (prove the transition occurred without revealing the content) is theoretically possible via zero-knowledge proofs but practically expensive. The trade-off is not settled.

These are real problems. They define the frontier of the primitive, not the validity of it.

---

## 12. Conclusion

Attestation of epistemic transitions is the binding of a change in an AI's understanding to a cryptographic record, at the moment of the change, under an authority, with an external trust anchor. It guarantees integrity, attribution, point of truth, and independent verifiability. It does not guarantee truth, reliability, correctness, usefulness, or completeness.

It is a primitive because:

- It cannot be derived from the record of current state.
- It cannot be derived from provenance.
- It fails in ways distinct from either.
- It has a defined place in the substrate and a defined demonstration.
- It is a capability, not a technique — signatures are its mechanism, not its definition.

PersonaVault currently implements six of the eight substrate primitives. Attestation and trust anchor are the two that remain. This paper defines the first.

The claim is narrow and checkable:

> **A change to an AI's understanding can be bound to a cryptographic record at the moment of the change, such that a third party verifies what the AI learned, from what source, under what authority — without accessing the AI's systems.**

That is attested epistemic transition. Everything else — the specific signature scheme, the specific canonicalization, the specific registry — is implementation.

---

*The target-state demonstration in §9 describes what "done" looks like. The implementation described is not yet in the codebase.*
