# Migration Rules

This document contains the hard rules for protecting the existing codebase.

## DO NOT

- Rename `DecisionState` → `EnvironmentState`
- Replace existing `PolicyEngine`

## DO

- Create `EnvironmentState` and use an adapter.
- Use `PolicyEngine` via a V2 Policy adapter.

All migrations MUST be additive:

```sql
ADD TABLE
ADD COLUMN NULL
ADD INDEX
ADD VIEW
```
