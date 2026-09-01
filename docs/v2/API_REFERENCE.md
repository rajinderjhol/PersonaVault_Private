# V2 API Reference

This document provides a summary of the V2 API endpoints implemented for the PersonaVault Sovereign Intelligence platform.

## Base URL
`/v2/environments`

---

## 🌍 Environments

### Create Environment
`POST /v2/environments/`

Creates a new sovereign intelligence environment.

**Request Body:**
```json
{
  "name": "string",
  "owner_principal_id": "string",
  "type": "string" 
}
```

### List Environments
`GET /v2/environments/`

Lists all active environments.

### Get Environment
`GET /v2/environments/{env_id}`

Retrieves details for a specific environment.

---

## 📦 Intelligence Packs

### List Adapted Packs
`GET /v2/environments/{env_id}/packs/`

Lists V2 Intelligence Packs, dynamically adapted from existing V1 Behavior Packs.

---

## 🛡️ Governance

### Add Member
`POST /v2/environments/{env_id}/members/`

Adds a Principal to the environment with a specific role and permissions.

### List Members
`GET /v2/environments/{env_id}/members/`

Lists all members of the environment.

### Grant Authority
`POST /v2/environments/{env_id}/authorities/`

Grants a specific capability to a Principal within the environment.
