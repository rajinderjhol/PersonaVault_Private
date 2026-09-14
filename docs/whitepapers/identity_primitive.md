# The Identity Primitive

**A technical note on attribution as a substrate capability**

---

## 1. Abstract

A system that governs its own learning must be able to justify why any action was taken, any change was made, or any knowledge was asserted. Not just by reference to rules, but by attribution to an identifiable actor.

Most systems treat identity as an authentication problem: a session token, a user ID, or a device signature. This is a mechanism, not a primitive. The primitive of **identity** is the capability to attribute an event, record, or transition to a specific, distinguishable entity that persists across time, whether that entity is human, machine, or environment.

This paper argues that identity is a distinct architectural primitive, irreducible to the authentication mechanisms that establish it or the roles that govern it. And it argues that in a system built for governed, evolvable memory, the identity layer must be a *full taxonomy* of entities, because different kinds of entities carry different accountability guarantees.

The claim is narrow:

> **Every action, record, and authority in a governed system can be attributed to a specific identifiable entity, such that attribution is stable across time, distinguishable from other entities, and independent of the entity's specific attributes.**

The paper defines the primitive, distinguishes it from authentication mechanisms, states what it guarantees and what it does not, shows why it is irreducible, and demonstrates it through PersonaVault's multi-type identity taxonomy.

---

## 2. The Problem: Identity Without a Model

Consider a system that records actions. It has user IDs in an audit log. It has roles in a database. When an action is taken, the system logs: `User_123 performed Action_A`.

This is the default model of most systems. Identity is a label. It is something added to a log entry to facilitate debugging. It is not an object that the system can reason about, relate to other objects, or govern as a first-class entity.

Three problems follow.

**2.1 Attribution is ambiguous.** "User_123" is a label. Is it a human? A service account? A sub-agent? A device? If the system cannot distinguish the *kind* of entity, it cannot apply categorical governance. It cannot enforce "only humans may perform this" vs "only services may perform that."

**2.2 Identity is not stable.** If an identity is a session-based label, it breaks when the session expires or the user rotates. If the system cannot map the transient label back to a stable identity, the chain of attribution is lost.

**2.3 Actors are not first-class.** If identity is not an object, the system cannot express relationships between identities. It cannot represent "Agent A is acting on behalf of Principal B," or "Device C is authorized to act as Agent A." These relationships are the core of authority, but without first-class identity, they must be reconstructed from context.

A system that solves this by adding an "identity table" is solving it partially. The table says *"this ID belongs to this name"*, but the system cannot *reason* about the identity structure independently of the code that resolves it. Identity as a label is weaker than identity as a primitive.

---

## 3. What Identity Is

We define identity as:

> **A persistent referent for an entity that acts, is accountable, or provides context within the system, with defined identity, a distinct category, and the ability to serve as the subject of attribution.**

Four parts, each required.

**3.1 A referent.** The identity refers to an entity that performs actions, is responsible for knowledge, or acts as a source. Not a session — an entity. Two sessions of the same entity are the same identity; two entities with the same attributes (e.g., two users with the same name) are distinct identities.

**3.2 Stable identity.** The entity's identity is stable across time, sessions, and contexts. It is referable, and this reference resolves to the same entity regardless of whether the entity is currently active, authorized, or even existing.

**3.3 A category.** Every identity belongs to a kind. A human-user is a kind of identity; a service-agent is a different kind. The category is a structural property — the system can determine an entity's category from the identity object itself, allowing for category-specific governance.

**3.4 Subject of attribution.** Every primitive (Transition, Record, Authority, Policy) must be able to relate to an identity as a subject. An action is attributed to an identity; a record is created by an identity; a policy is enforced by an identity.

Remove any and identity collapses:

- Remove the referent → you have a label with no entity.
- Remove stable identity → attribution fails when context changes.
- Remove the category → you have entities without roles or rules.
- Remove the subject → you have identities that cannot act or own.

---

## 4. What Identity Guarantees

Four things, and only four.

**4.1 Attribution.** Every governed operation (Record, Transition, Authority) can be mapped to one or more identity entities. The system knows *who* is responsible, *who* acted, and *who* authorized.

**4.2 Distinguishability.** Distinct entities have distinct identities, even if they have identical attributes (e.g., two service agents with the same role and permissions are still two agents). The system never conflates actors.

**4.3 Categorical integrity.** The system can enforce rules based on the category of the entity (e.g., "only humans may authorize," "only services may perform batch updates").

**4.4 Persistence.** An identity object persists even if the entity is not currently active, allowing historical attribution and post-hoc audit.

---

## 5. What Identity Does Not Guarantee

**5.1 That the identity is authentic.** A record attributed to "User_A" proves that the system *labeled* it "User_A," not that the action was performed by the actual human User_A. Authentication is the mechanism that establishes authenticity; identity is the primitive that stores the result.

**5.2 That the identity is unique to one human.** A single identity could be shared by a team (a "service account"), or one human could possess multiple identities (a "personal" vs "work" account). The primitive manages the entities; what those entities correspond to in the real world is a governance concern.

**5.3 That the identity is trustworthy.** Attributing an action to "User_A" does not establish that User_A is trustworthy. That is a property of the identity's authority and record, not of the identity primitive itself.

**5.4 That the identity's history is complete.** An entity may have performed actions that were never recorded. The identity primitive proves attribution for *recorded* actions; it does not guarantee that the entity didn't act elsewhere.

**5.5 That the identity is permanent.** Identities can be retired, deleted, or merged. The primitive defines how to refer to entities that *have* identity, not that every entity must exist forever.

**5.6 That the system can resolve an identity to a real-world person.** The identity primitive manages the internal referent. Whether that referent maps to a physical human is a question of external trust, not internal architecture.

---

## 6. Why Identity Is Irreducible

An objection: *"Identity is just a database column. Every system has this. Calling it a primitive is a distinction without a difference."*

The answer is that the primitive is not "things have names." It is "the system models entities as objects with persistent identity and category, such that all other primitives can use these objects to ground attribution."

Three reductions to consider, and why each fails:

**Reduction 1 — Identity reduces to record.** No. A record represents a thing. Identity *is* the thing that represents the who. You can have records of things without identities (e.g., a "system event" with no actor), and you can have identities that have performed no actions (e.g., a new user with no history).

**Reduction 2 — Identity reduces to authentication token.** No. A token is a temporary proof of identity. Identity is the persistent object that the token points to. A system with only tokens cannot reason about an actor's history, scope, or relationships — it can only check if the current token is valid.

**Reduction 3 — Identity reduces to policy role.** No. A role is a set of permissions. An identity is the entity that holds that role. One identity can hold many roles; one role can be held by many identities. The relationship between identity and policy is a relationship between two distinct primitives.

Each reduction fails because it captures some properties and misses others. The primitive is what has *all* of them simultaneously.

---

## 7. PersonaVault's Identity Taxonomy

PersonaVault implements the Identity primitive through a *taxonomy* — multiple identity types, each a distinct category of entity, all coexisting in the same system. This section demonstrates the primitive through the taxonomy.

### 7.1 The identity taxonomy

| Identity type | What it refers to | Role |
|---|---|---|
| **User** | A human actor with a specific scope | Primary actor, decision-maker |
| **Principal** | An entity (user or service) that delegates authority | Authority owner |
| **Membership** | A relationship between a User and an Environment | Contextual scope |
| **Agent** | A service or model acting on behalf of a Principal | Autonomous actor |
| **Controlled User** | An admin-managed entity | Restricted actor |
| **Organization** | The overarching authority entity | Source of legitimacy |
| **Device** | A hardware entity with a unique identifier | Trust boundary |

Each is a distinct category. Each has an identity independent of its content. Each is referable as the subject of attribution across its lifecycle.

### 7.2 The identity types in the codebase

**Users — `User`.** A User is the system's referent for "a human who interacts with the system." Every User has a stable ID, a profile, and a history of memberships.

**Principals — `Principal`.** A Principal is the system's referent for "an entity that owns authority." A Principal can be a User or an Agent. The Principal model tracks delegation: how much authority does this principal hold, and what has it delegated to others?

**Memberships — `Membership`.** A Membership is the system's referent for "a User within an Environment with a specific Role." This is the core of context: who is this User *right now*, given the environment they are in?

**Agents — `Agent`.** An Agent is the system's referent for "a service, model, or swarm that acts." An Agent's identity is distinct from the human who authorized it.

**Controlled Users — `ControlledUser`.** A Controlled User is a User whose lifecycle and permissions are managed strictly by an admin/organization. This is a restricted category for sensitive domains.

**Organizations — `Organization`.** An Organization is the root identity. All users, principals, and agents ultimately belong to an Organization, which defines the boundaries of legitimacy.

**Devices — `Device`.** A Device is the system's referent for "a physical hardware entity." Device identity is central to the Sovereign Runtime — the system knows not just *who* is acting, but *where* the action is occurring.

### 7.3 Why the taxonomy matters

The taxonomy is the structure that lets the system apply different rules to different *kinds* of entities. Without it, attribution is a "system did it" blur. With it, the system can say:

- "This human user approved this decision."
- "This service agent carried out the execution."
- "This device authenticated the agent."
- "This environment scoped the agent's actions."

The taxonomy makes identity **governable**.

### 7.4 What the taxonomy demonstrates

The taxonomy is an instance of the Identity primitive in the sense of §3. Each:

- Has a **referent** — the entity (human, machine, environment) it refers to.
- Has **persistent identity** — identities are referable across time.
- Has a **category** — identities are of a definite kind, distinguishable from other kinds.
- Is **the subject of attribution** — every action can be attributed to one of these identities.

### 7.5 What the taxonomy does not claim

The taxonomy does not establish that any specific identity is *authentic*, *trustworthy*, or *uniquely mapped to one human*. It simply establishes that the system can distinguish these identities and attribute actions to them. Authentication and trustworthiness remain properties established by other primitives.

---

## 8. Where Identity Sits in the Substrate

| Primitive | Relationship to Identity |
|---|---|
| **Unit** | Identity is a category of Unit. |
| **Identity** | *The subject of this paper.* |
| **Transition** | Transitions are attributed to an Identity. |
| **Record** | Records have an Identity as an author or subject. |
| **Authority** | Identity is the carrier of authority. |
| **Policy** | Policy constrains actions by Identity. |
| **Attestation** | Attestation proves a transition was authorized by a specific Identity. |
| **Trust anchor** | Trust Anchor authenticates the Identity. |

Identity is the *precondition for Authority*. Without identity, there is no "who" to be authorized. It is the primitive that grounds attribution for all actions, records, and transitions.

---

## 9. Open Questions

**9.1 Identity vs. Role.** Is "Role" a primitive, or a way of grouping Identities? The current model treats Role as an attribute of Membership, not an identity itself. Formalizing the boundary between Identity and Role is an open question.

**9.2 Global vs. Local Identity.** When a user is shared across two PersonaVault instances, is it the same Identity? Or is Identity local to an Environment?

**9.3 Identity of non-human entities.** The taxonomy includes Agents and Devices. What are the minimal criteria for a non-human entity to be an "Identity" in a governed system?

---

## 10. Conclusion

The Identity primitive is the stable referent for an entity that acts, is accountable, or provides context: a referent with persistent identity, a distinct category, and the ability to serve as the subject of attribution. It guarantees attribution, distinguishability, categorical integrity, and persistence. It does not guarantee authenticity, uniqueness, trustworthiness, or real-world mapping.

It is irreducible because:

- It is not derivable from record (§6, reduction 1).
- It is not derivable from authentication mechanism (§6, reduction 2).
- It is not derivable from role (§6, reduction 3).
- It is the anchor for attribution in all other primitives.

PersonaVault implements the primitive through a *taxonomy* of seven identity types: User, Principal, Membership, Agent, ControlledUser, Organization, and Device. This taxonomy allows the system to distinguish different *kinds* of actors and apply appropriate governance to each.

The claim is narrow and checkable:

> **Every action, record, and authority in a governed system can be attributed to a specific identifiable entity, such that attribution is stable across time, distinguishable from other entities, and independent of the entity's specific attributes.**

That is the Identity primitive. Everything else — the specific session tokens, the specific auth flows, the specific role definitions — is implementation.

---

*PersonaVault's identity taxonomy, described in §7, is one instance of the primitive. Other systems may implement Identity differently (OIDC, SAML, decentralized identifiers) and the primitive's guarantees apply to those implementations as well.*
