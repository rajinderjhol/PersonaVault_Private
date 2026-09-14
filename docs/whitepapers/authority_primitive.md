# The Authority Primitive

**A technical note on the governed ability to act**

---

## 1. Abstract

A system that acts must be able to justify why the action was permitted. Not just *who* took it, and not just *what rule* allowed it, but the whole chain: the source of authority, the expression of that authority as a rule, the identification of the agent carrying it, and the mechanism that enforces it at the moment of action.

Most systems have *some* of this. They have access control (who can act) or a rules engine (what is permitted) or an approval workflow (when a human must sign off). Almost none have the *complete* stack, and almost none treat it as a single primitive with layered components.

This paper argues that **authority** — the governed ability to act, with defined source, scope, carrier, and enforcement — is a distinct architectural primitive, irreducible to identity (who you are) or policy (what the rules say). And it argues that in a system built for governed, evolvable memory, authority is realized not by one mechanism but by a *layered* set of them, each answering a different question.

The claim is narrow:

> **The ability to act can be modeled as a first-class primitive with defined source, expression, carrier, and enforcement, such that every action is traceable to an authority chain that the system can inspect and a third party can verify.**

The paper defines the primitive, distinguishes it from adjacent concepts, states what it guarantees and what it does not, shows why it is irreducible, and demonstrates it through PersonaVault's four-mechanism authority layer.

---

## 2. The Problem: Authority Without a Model

Consider a system that executes actions — calls tools, writes to storage, sends messages, modifies state. It has users. It has rules. It has logs.

Three questions can be asked of any action:

**Question 1 — Who did it?**
This is an *identity* question. Answerable by the actor's authentication.

**Question 2 — Was it allowed?**
This is a *policy* question. Answerable by evaluating the rule against the action.

**Question 3 — On whose behalf, under what source of legitimacy, and what would have stopped it?**
This is an *authority* question. It is not answered by identity (which says who acted, not who authorized) and not by policy (which says what was permitted, not where the permission came from or what enforces it).

Most systems answer 1 and 2, and treat 3 as implicit. The consequence is that when an action is questioned — by an auditor, a regulator, a court, or a customer — the answer has to be assembled from fragments: the user record, the policy table, the audit log, the code that evaluates the policy. The authority chain is not a first-class object; it is a reconstruction.

Three specific failures follow.

**2.1 The source of legitimacy is unclear.** A policy says "actions above $10,000 require approval." Why? Is the policy derived from a constitutional rule, from a regulatory requirement, or from a configuration change someone made? Without a model of authority sources, the system cannot distinguish "this is how it is" from "this is how we chose to make it."

**2.2 The carrier of authority is implicit.** When an AI agent acts, it acts on behalf of something — a user, a service, a delegation chain. If the delegation is implicit (inferred from a session token, or assumed from context), the system cannot answer *"who authorized this specific action, and with what scope?"*

**2.3 The enforcement point is undefined.** A policy can be *evaluated* in multiple places — at input, at execution, at output. If the system does not declare *where* enforcement happens, then enforcement is everywhere and nowhere. The action may be permitted by one code path and blocked by another, and the record cannot say which.

Authority is the primitive that resolves these. It models the source, scope, carrier, and enforcement of permission as a first-class object, so that every action is traceable to an authority chain the system can inspect.

---

## 3. What Authority Is

We define authority as:

> **The governed ability to act, expressed as a permission with a defined source, a defined scope, a defined carrier, and a defined point of enforcement.**

Four parts, each required.

**3.1 A source.** Where does this permission come from? Authority sources are typically hierarchical: a constitutional rule that cannot be overridden, from which specific policies derive, from which specific actions are permitted. Without a source, a permission is arbitrary; the system cannot distinguish "this is legitimate" from "this is permitted."

**3.2 A scope.** What is permitted, under what conditions? A permission is not absolute — it is bounded. The scope says: this action, for this agent, under these conditions, up to this limit, until this expiry. Scope is where authority becomes concrete; it is the expression of the permission as a rule that can be evaluated.

**3.3 A carrier.** Who exercises the permission? Authority is not exercised by "the system" — it is exercised by a specific agent, acting on behalf of a specific principal. The carrier is the chain from the principal to the agent, with each link's scope declared.

**3.4 A point of enforcement.** Where, in the system's execution, is the permission actually checked? Not "somewhere in the code" — a specific point. The enforcement point determines when the action is stopped, what the system knows at the moment of the check, and what happens if the check fails.

Remove any and authority collapses:

- Remove the source → permission without legitimacy.
- Remove the scope → permission without bounds.
- Remove the carrier → permission without an actor.
- Remove the enforcement → permission without a gate.

---

## 4. What Authority Guarantees

Four things, and only four.

**4.1 Traceability.** Every action that required authority is traceable to the specific permission under which it was taken. Not "was allowed by some rule" — "was allowed by this permission, from this source, with this scope, carried by this agent."

**4.2 Boundedness.** Every permission has a defined scope. Actions cannot be taken outside the scope without a distinct permission. Scope is enforced, not advisory.

**4.3 Carrier identity.** Every permission is carried by a specific agent on behalf of a specific principal. Anonymous authority — "the system did it" — is not possible under a complete authority model.

**4.4 Enforcement determinism.** The point at which authority is checked is defined, not emergent. Given the same permission and the same action, the enforcement point produces the same result.

---

## 5. What Authority Does Not Guarantee

**5.1 That the action was correct.** Authority grants permission; it does not establish that the permitted action is the right action. A permitted action can still be wrong.

**5.2 That the source is legitimate.** An authority source can be a constitution, a regulation, a business rule, or a configuration — all of these are "sources" in the model's sense. Whether a given source *should* be a source is a governance question, not an authority question.

**5.3 That the scope is well-chosen.** A permission with a scope that is too broad or too narrow is still a valid permission. Correctly scoped authority is a design property, not a primitive guarantee.

**5.4 That the carrier is trustworthy.** The carrier is the chain from principal to agent. Whether each link is trustworthy — whether the agent will act in the principal's interest — is a trust problem, not an authority problem.

**5.5 That enforcement is complete.** The primitive guarantees that *the declared enforcement point* is deterministic. It does not guarantee that all enforcement happens at that point. Authority can be circumvented by code paths that do not check.

**5.6 That the permission was needed.** A permission can be exercised unnecessarily — the system can invoke the authority check even when the action would have been permitted trivially. The primitive records the permission; it does not judge whether the permission was worth requesting.

---

## 6. Why Authority Is Irreducible

An objection: *"Authority is just policy plus identity. Policies say what is permitted; identity says who the actor is. Authority is the intersection, not a separate primitive."*

The answer is that authority has a *source* and an *enforcement point* that neither policy nor identity provides.

Three reductions to consider.

**Reduction 1 — Authority reduces to policy.** No. A policy is a rule; authority is the permission to act under that rule. The distinction is the one between *"the rules say X is permitted"* and *"this specific agent is permitted to do X under these specific conditions."* The first is general; the second is specific and traceable. A system with policies but no authority model can say what is permitted, but not who permitted it or under what chain.

**Reduction 2 — Authority reduces to identity.** No. Identity says who you are. Authority says what you may do. A system with identity but no authority model knows the actors but not their permissions — every action would need a separate policy evaluation, with no notion of "this agent's scope" or "this principal's delegation."

**Reduction 3 — Authority reduces to (identity + policy).** Closer, but not the same. The composition of identity and policy can produce a *decision* ("this agent, under this policy, is permitted"), but it does not produce a *permission* — a first-class object with a source, a scope, a carrier, and an enforcement point. The permission is what makes the decision auditable: it names the specific rule, the specific delegation, the specific enforcement point. Without it, the decision is derivable but not attributable.

Each reduction fails because it captures some properties and misses others. The primitive is what has *all* of them simultaneously.

---

## 7. PersonaVault's Authority Layer

PersonaVault implements the Authority primitive through a *layered* set of four mechanisms. These mechanisms are not peers — they operate at different levels and answer different questions.

### 7.1 The four mechanisms

| Mechanism | Question it answers | Level |
|---|---|---|
| **Constitution** | What may never be overridden, and what legitimizes the rest? | Source |
| **Trust Policies** | What is permitted, under what conditions? | Expression |
| **Delegated Principals** | Who may act, on whose behalf? | Carrier |
| **HITL Gates** | What pauses an action that requires judgment? | Enforcement |

The layering matters because each mechanism depends on the one above it. Trust Policies derive their legitimacy from the Constitution. Delegated Principals operate within the scope set by Trust Policies. HITL Gates enforce the scope of Delegated Principals. A break at any level propagates downward.

### 7.2 The four mechanisms in the codebase

**Constitution — `governance_constitution.json`, `ConstitutionEditor`.** The Constitution is the immutable base of authority. It is not edited through normal operations; changes require a governance action with its own authority chain. The Constitution declares what may never be overridden — the constraints that bind all other mechanisms. It also provides the *legitimacy* of Trust Policies: a policy is authoritative because the Constitution permits policy-making, not because someone wrote a rule.

The Constitution's guarantee is **source immutability under governance**: the rules that bind everything else cannot be changed without an authority event that is itself governed.

**Trust Policies — `TrustPolicy`, `policy.py`.** Trust Policies are the concrete expression of permitted action. They translate constitutional principles into operational conditions: "actions above $10,000 require approval," "patterns with confidence below θ_freeze cannot be promoted," "cross-environment transfers require a sanitization check." Each policy has a scope, and each scope is bounded by the Constitution.

Trust Policies' guarantee is **evaluable scope**: at any moment, given an action and an actor, the system can determine whether the action is permitted and under what policy.

**Delegated Principals — `Principal`, `Authority`, `AuthorityService`.** Delegated Principals are the carriers of authority. When an agent acts, it acts on behalf of a specific principal, through a specific delegation chain. Each link in the chain has a defined scope — a principal can delegate less than they hold, but not more. The chain is inspectable: an auditor can traverse from the acting agent back to the original source of authority.

Delegated Principals' guarantee is **non-amplification**: delegation preserves or reduces authority; it never expands. This is the monotonicity invariant that makes chains safe to compose.

**HITL Gates — `HITL`, `PendingAction`, autonomy levels.** HITL Gates are the enforcement of authority at the moment of action. When an action requires human judgment — because it exceeds an autonomy threshold, because it triggers a governance check, because the Validator flagged it — the gate pauses execution and produces a `PendingAction`. The human's response determines whether the action proceeds.

HITL Gates' guarantee is **pause-before-effect**: an action that requires a gate is not executed until the gate resolves. This is where authority becomes enforceable rather than merely declarative.

### 7.3 Why the layering is necessary

The four mechanisms are not interchangeable. Consider what each combination would look like without one of them.

**Without the Constitution**: Trust Policies have no legitimacy. They are rules that someone wrote. The system can evaluate them, but it cannot say *why* they are binding. This is the difference between a rule and a law.

**Without Trust Policies**: The Constitution is abstract principle with no operational meaning. "Actions must be overseen" is not a rule that can be evaluated; it is a value that requires a policy to apply.

**Without Delegated Principals**: Every action is taken by "the system." There is no chain to audit, no principal to hold accountable, no scope to enforce. Authority is a property of the system, not of the actor.

**Without HITL Gates**: Authority is declared but not enforced. The system knows what should happen but does not stop to make sure it does. Authority is advisory.

Each mechanism is necessary, and no mechanism is sufficient. The primitive is the whole stack.

---

## 8. Where Authority Sits in the Substrate

The PersonaVault substrate requires eight primitives:

| Primitive | Relationship to Authority |
|---|---|
| **Unit** | The thing authority is exercised over. |
| **Identity** | Who may hold authority. Identity is the precondition; Authority is the permission built on it. |
| **Transition** | The change that authority permits. |
| **Record** | The persistent trace of the permission and the action it permitted. |
| **Authority** | *The subject of this paper.* |
| **Policy** | A specific expression of authority. Policy is to Authority what an instance is to a class. |
| **Attestation** | The cryptographic binding that makes the authority chain verifiable to a third party. |
| **Trust anchor** | The external reference that makes attestation verifiable. |

Transition is the primitive that Attestation binds. Without Transition, there is nothing for Attestation to attest. Without Attestation, Transition is real but unverifiable outside the system. They are complementary.

The relationship between Transition and Record is worth naming precisely, because it's the one that most often gets conflated: **a transition is an event; a record is a durable representation of an event.** They can diverge — an in-memory transition with no record, a record of a non-transition — and the substrate requires both as distinct primitives.

---

## 9. Open Questions

**9.1 Composition of authority across environments.**
If two environments establish authority chains that interact — say, a pattern transferred from one environment to another — how do the two chains compose? Does the receiving environment recognize the source environment's principals? If so, under what scope?

**9.2 Revocation and the persistence of permitted actions.**
If a principal's authority is revoked, do actions previously permitted by that authority remain valid? The forward answer is "yes, the action occurred under then-valid authority." The governance answer may be "no, actions taken under revoked authority must be re-examined." The primitive does not resolve this; it is a question of what the enforcement point's effect is on the historical record.

**9.3 The boundary between Authority and Policy.**
Is a Trust Policy an *instance of authority* or a *constraint on authority*? The current model treats it as an expression — the policy declares what is permitted, which is what authority grants. But a policy can also constrain — "no action may exceed $10,000" is a limit on what any authority may permit. The distinction between expressive and restrictive policies is not yet formalized.

**9.4 Authority without a human principal.**
If an agent acts on behalf of another agent (a sub-agent delegation), and eventually on behalf of a machine-learned policy rather than a human principal, is the resulting action legitimately authorized? The chain is valid under the primitive's rules, but the question of *who is ultimately responsible* is not answered by the primitive.

---

## 10. Conclusion

The Authority primitive is the governed ability to act, expressed as a permission with defined source, scope, carrier, and enforcement point. It guarantees traceability, boundedness, carrier identity, and enforcement determinism. It does not guarantee correctness, legitimacy of sources, well-chosen scopes, trustworthiness of carriers, completeness of enforcement, or necessity of the permission.

It is irreducible because:

- It is not derivable from policy (§6, reduction 1).
- It is not derivable from identity (§6, reduction 2).
- It is not derivable from the composition of identity and policy (§6, reduction 3).
- It fails in ways distinct from the primitives it is commonly conflated with.

PersonaVault implements the primitive through a *layered* set of four mechanisms — Constitution, Trust Policies, Delegated Principals, and HITL Gates — each answering a different question, each required for the whole to be complete.

The layering is the point. Unlike Transition and Record, which have parallel instances, Authority is realized by mechanisms that compose in a hierarchy. The primitive is not any one mechanism; it is the stack.

The claim is narrow and checkable:

> **The ability to act can be modeled as a first-class primitive with defined source, expression, carrier, and enforcement, such that every action is traceable to an authority chain that the system can inspect and a third party can verify.**

That is the Authority primitive. Everything else — the specific constitution, the specific policies, the specific principals, the specific gates — is implementation.

---

*PersonaVault's four-mechanism authority layer, described in §7, is one instance of the primitive. Other systems may implement Authority differently (capability-based, role-based, attribute-based, or hybrid) and the primitive's guarantees apply to those implementations as well.*
