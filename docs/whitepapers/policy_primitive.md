# The Policy Primitive

**A technical note on governed constraints as a first-class substrate capability**

---

## 1. Abstract

A governed system must express what is permitted and what is restricted, not as ad-hoc code checks, but as a formal model that can be evaluated, audited, and reasoned about.

Most systems express rules as fragments scattered across the codebase: `if` statements, hardcoded limits, and database constraints. This is mechanism, not primitive. The primitive of **policy** is the ability to represent constraints as first-class objects, with defined evaluation semantics, scope, and enforcement, such that any action can be traced to the specific rule that permitted or restricted it.

This paper argues that policy is a distinct architectural primitive, irreducible to the authority that grants it or the records that audit it. And it argues that in a system built for governed, evolvable memory, policy is realized through a *layered* approach, where rules derive their legitimacy from a higher-order constitution and constrain the actions of delegated principals.

The claim is narrow:

> **A system can represent permitted and restricted behavior as a first-class object with defined scope, evaluation semantics, and enforcement points — such that any action can be evaluated against the policies that govern it, and any policy can be traced to the authority that issued it.**

The paper defines the primitive, distinguishes it from authority (which grants permission) and transition (which changes state), states what it guarantees and what it does not, shows why it is irreducible, and demonstrates it through PersonaVault's layered policy implementation.

---

## 2. The Problem: Policy Without a Model

Consider a system that executes actions. It has code paths that evaluate: *"Is this agent allowed to do this?"*. This evaluation is scattered: a hardcoded check in the API layer, a database trigger in the storage layer, a config setting in the service layer.

This is the default model of most systems. Policy is an implementation detail. It is not an object that the system can reason about.

Three problems follow.

**2.1 Rules are invisible.** When the system is asked *"What governs this action?"*, there is no single answer. The "policy" is the sum of every check in the codebase. You cannot audit this, you cannot test it comprehensively, and you cannot evolve it safely.

**2.2 Rules are inconsistently applied.** If policy is code, policy consistency is code consistency. One developer might check for a limit in the API layer, another might check in the service layer, and a third might miss it entirely. There is no central point of truth for "what is allowed."

**2.3 Rules are static and brittle.** A change in a rule requires a code change. The policy cannot evolve based on learning, based on context, or based on governance events, because the policy is not a first-class object the system can manipulate.

A system that solves this by adding a "rules engine" is solving it partially. The engine provides a place to put rules, but if the rules are not primitives — if they have no identity, no provenance, no relationship to authority — then the "engine" is just a configuration file in a wrapper.

---

## 3. What Policy Is

We define policy as:

> **The governed expression of permitted or restricted action, with defined scope, evaluation semantics, and enforcement points.**

Four parts, each required.

**3.1 A scope.** What does this policy apply to? A policy is not universal; it is bounded. The scope defines the domain — which units, which actors, which transitions — to which the policy applies.

**3.2 Evaluation semantics.** How is this policy checked? Is it a boolean check? A risk score? A human-in-the-loop requirement? The system must know how to *evaluate* the policy, not just store it.

**3.3 Enforcement points.** Where, in the system's execution, is the policy checked? Not "somewhere in the code" — a specific point. The enforcement point determines when the action is stopped, what the system knows at the moment of the check, and what happens if the check fails.

**3.4 Provenance.** Every policy must be traceable to the authority that issued it. A policy that cannot be linked to the authority chain is arbitrary.

Remove any and policy collapses:

- Remove the scope → policy without bounds.
- Remove evaluation semantics → policy without logic.
- Remove enforcement points → policy without effect.
- Remove provenance → policy without legitimacy.

---

## 4. What Policy Guarantees

Four things, and only four.

**4.1 Evaluability.** Any action can be evaluated against the relevant policies to determine if it is permitted or restricted.

**4.2 Traceability.** Any permitted or restricted action can be traced to the specific policy that governed the outcome.

**4.3 Categorical restriction.** Policies allow the system to enforce rules based on categories (e.g., "all Knowledge units require validation," "all Governance units require human approval").

**4.4 Governance integration.** Policies are linked to the Authority primitive; a policy only exists because an authority permitted it.

---

## 5. What Policy Does Not Guarantee

**5.1 That the policy is correct.** A policy correctly expresses what is permitted; it does not establish that the policy itself is sound or safe.

**5.2 That the policy covers all cases.** A system might have policies for X and Y, but not for Z. The policy primitive does not guarantee completeness.

**5.3 That the enforcement is perfectly implemented.** A policy might declare "action X must be restricted," but if the enforcement point is circumvented, the policy is not followed.

**5.4 That the evaluation is always correct.** A policy's evaluation depends on the data it is given. If the data is faulty, the evaluation may be incorrect.

**5.5 That the policy is permanent.** Policies are versioned, not permanent. The primitive records the version, not the absolute truth.

**5.6 That the policy is useful.** A policy can be valid, traceable, and correctly enforced while being counter-productive or useless.

---

## 6. Why Policy Is Irreducible

An objection: *"Policy is just a set of rules. Why not just store them in a database and query them?"*

The answer is that the primitive is not "things have rules." It is "the system models rules as *objects* with defined scope, evaluation semantics, and enforcement points, such that all other primitives can use these objects to ground governance."

Three reductions to consider, and why each fails:

**Reduction 1 — Policy reduces to Authority.** No. Authority is the power to permit; Policy is the rule that *expresses* that permission. A principal has authority (the "who"); a policy provides the "what". Reducing policy to authority loses the "what" — the specific conditions and limits.

**Reduction 2 — Policy reduces to Unit.** No. A unit is a thing tracked. A policy is a thing that *constrains* the tracking or action on that thing. Reducing policy to unit loses the constraint semantics.

**Reduction 3 — Policy reduces to Code/Config.** No. Code/config is an implementation; policy as a primitive is an architectural object with provenance and lifecycle. Code/config lacks the "governance integration" guarantee — it cannot be easily audited or evolved as a first-class object.

Each reduction fails because it captures some properties and misses others. The primitive is what has *all* of them simultaneously.

---

## 7. PersonaVault's Policy Layer

PersonaVault implements the Policy primitive through a *layered* set of four mechanisms. These mechanisms are not peers — they operate at different levels and answer different questions.

### 7.1 The four mechanisms

| Mechanism | Question it answers | Level |
|---|---|---|
| **Constitution** | What may never be overridden, and what legitimizes the rest? | Source |
| **Trust Policies** | What is permitted, under what conditions? | Expression |
| **Learning Policies** | What constraints apply to evolving patterns? | Evolution |
| **Autonomy Levels** | What pauses an action that requires judgment? | Enforcement |

The layering matters because each mechanism depends on the one above it. Trust Policies derive their legitimacy from the Constitution. Learning Policies are governed by Trust Policies. Autonomy Levels enforce the runtime behavior.

### 7.2 The four mechanisms in the codebase

**Constitution — `governance_constitution.json`, `ConstitutionEditor`.** The Constitution is the immutable base of policy. It declares the invariants that bind all other policies: e.g., "no knowledge pattern may be frozen without a valid audit trace."

**Trust Policies — `TrustPolicy`, `policy.py`.** Trust Policies are the operational rules: "actions above $10,000 require approval." They scope permissions.

**Learning Policies — `policy.py` (learning-specific).** Learning policies govern the *evolution* of the memory: "only crystallize patterns that recur three times," "discard patterns that have not been accessed for 30 days."

**Autonomy Levels — `AutonomyLevel`.** Autonomy Levels are the enforcement points: "Observe" (log only), "Recommend" (ask human), "Approve" (perform with trace), "Execute" (fully autonomous).

### 7.3 Why the layering is necessary

- **Without Constitution**: Policies lack legitimacy; they are just configuration files.
- **Without Trust Policies**: Operational oversight is impossible.
- **Without Learning Policies**: The system evolves blindly, ignoring its own constraints.
- **Without Autonomy Levels**: Governance is binary (allowed/denied) and lacks the nuance of human judgment or risk-based enforcement.

---

## 8. Where Policy Sits in the Substrate

| Primitive | Relationship to Policy |
|---|---|
| **Unit** | Policy constrains actions on Units. |
| **Identity** | Policy evaluates the actor's Identity. |
| **Transition** | Policy governs which Transitions are permitted. |
| **Record** | Policy is persisted as a Governance Record. |
| **Authority** | Policy is the expression of Authority. |
| **Policy** | *The subject of this paper.* |
| **Attestation** | Attestation proves a transition followed the Policy. |
| **Trust anchor** | Trust Anchor verifies the Policy's origin. |

---

## 9. Open Questions

**9.1 Policy conflict resolution.** If two policies have overlapping scopes but conflicting rules, which takes precedence? The current model is ad-hoc (order of evaluation), but this needs formalization.

**9.2 Dynamic policy evolution.** How can policies evolve safely without disrupting the system's governing invariants?

**9.3 Policy as Code vs. Policy as Data.** At what point should a policy be a data-driven model versus a hardcoded logic check?

---

## 10. Conclusion

The Policy primitive is the governed expression of permitted or restricted action, with defined scope, evaluation semantics, and enforcement points. It guarantees evaluability, traceability, categorical restriction, and governance integration.

It is irreducible because:

- It is not derivable from Authority (§6, reduction 1).
- It is not derivable from Unit (§6, reduction 2).
- It is not derivable from Code/Config (§6, reduction 3).

PersonaVault implements the primitive through a *layered* set of four mechanisms — Constitution, Trust Policies, Learning Policies, and Autonomy Levels — each answering a different question, each required for the whole to be complete.

The claim is narrow and checkable:

> **A system can represent permitted and restricted behavior as a first-class object with defined scope, evaluation semantics, and enforcement points — such that any action can be evaluated against the policies that govern it, and any policy can be traced to the authority that issued it.**

That is the Policy primitive. Everything else — the specific rules, the specific database tables, the specific evaluation code — is implementation.

---

*PersonaVault's policy layer, described in §7, is one instance of the primitive. Other systems may implement Policy differently (Rego/OPA, attribute-based access control, hardcoded logic) and the primitive's guarantees apply to those implementations as well.*
