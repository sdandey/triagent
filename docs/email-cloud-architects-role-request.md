# Email to Cloud Architects

---

**To:** Dimitri Apostola (dapostola@deloitte.com), Krisztian Racz (usa-cracz@deloitte.com)
**Subject:** Request: Data Plane Permissions for AI Agents POC - Sandbox Subscription

---

Team,

I have a sandbox subscription provisioned **"US-AZSUB-AME-AA-ODATAOPENAI-SBX"** (ID: `5eefdd74-582a-411a-9168-6a3b7ac1de4c`) for one of the POC projects related to AI Agents development.

The agent I'm building requires sandbox environment and access to AI Foundry models and Azure Container Apps Dynamic Sessions. I have Contributor-level access to the subscription. However, I do not have access to leverage these services at the data plane level.

Based on my analysis:

---

## My Current Access on This Subscription

| Group Membership | Role Assigned | Scope |
|------------------|---------------|-------|
| SG-US Audit Cortex Architect | **Deloitte Custom Contributor** | Subscription |
| SG-US Omnia Data Cloud Architects Elevated | Reader | Subscription |

---

## Current Data Plane Actions (Deloitte Custom Contributor)

| Section | Current Value |
|---------|---------------|
| `dataActions` | `[]` (empty) |
| `notDataActions` | `[]` (empty) |

**Status:** No data plane permissions are currently configured for any services.

---

## Proposed Changes to Deloitte Custom Contributor Role

### ADD the following dataActions:

| # | dataAction to ADD | Service | Purpose |
|---|-------------------|---------|---------|
| 1 | `Microsoft.App/sessionPools/*/read` | Container Apps | Read session pool information |
| 2 | `Microsoft.App/sessionPools/interpreters/execute/action` | Container Apps | Execute code in dynamic sessions |
| 3 | `Microsoft.App/sessionPools/interpreters/read` | Container Apps | Read interpreter configuration |
| 4 | `Microsoft.App/sessionPools/executions/*` | Container Apps | Manage code execution lifecycle |
| 5 | `Microsoft.App/sessionPools/files/*` | Container Apps | File operations in sessions |
| 6 | `Microsoft.CognitiveServices/*` | AI Foundry / OpenAI | OpenAI APIs, AI Agents, Speech, Vision |

### JSON Format:

```json
"dataActions": [
  "Microsoft.App/sessionPools/*/read",
  "Microsoft.App/sessionPools/interpreters/execute/action",
  "Microsoft.App/sessionPools/interpreters/read",
  "Microsoft.App/sessionPools/executions/*",
  "Microsoft.App/sessionPools/files/*",
  "Microsoft.CognitiveServices/*"
]
```

---

## Summary of Changes

| Section | Current | Action | Proposed |
|---------|---------|--------|----------|
| `dataActions` | `[]` (empty - 0 items) | **ADD** | 6 new dataActions |
| `notDataActions` | `[]` (empty) | No change | `[]` (empty) |

---

## Precedent

This follows the same pattern as **Deloitte Veeam Contributor** which includes dataActions for KeyVault and Storage:

```json
"dataActions": [
  "Microsoft.KeyVault/vaults/keys/decrypt/action",
  "Microsoft.KeyVault/vaults/keys/encrypt/action",
  "Microsoft.KeyVault/vaults/keys/read",
  "Microsoft.Storage/storageAccounts/queueServices/queues/messages/delete",
  "Microsoft.Storage/storageAccounts/queueServices/queues/messages/read",
  "Microsoft.Storage/storageAccounts/queueServices/queues/messages/write"
]
```

---

Please let me know if you need any additional information or would like to discuss.

Thank you,
Santosh Dandey
