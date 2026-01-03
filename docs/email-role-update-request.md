# Email: Deloitte Custom Contributor Role Update Request

---

**To:** Dimitri Apostola (dapostola@deloitte.com), Krisztian Racz (usa-cracz@deloitte.com)
**Cc:** [Your Manager]
**Subject:** Request: Add Data Plane Permissions to Deloitte Custom Contributor Role for AI Foundry & Container Apps

---

Hi Dimitri and Krisztian,

I'm reaching out to request an update to the **Deloitte Custom Contributor** role to add data plane permissions for Azure AI Foundry and Azure Container Apps Dynamic Sessions.

## Current Issue

The Deloitte Custom Contributor role currently has:
- **Control Plane**: `actions: ["*"]` - Full resource management ✅
- **Data Plane**: `dataActions: []` - **Empty** ❌

This means we can create and manage resources, but **cannot use/execute them**. Specifically, I'm encountering this error when accessing AI Foundry:

```json
{
  "error": {
    "code": "PermissionDenied",
    "message": "The principal 'usa-sdandey@deloitte.com' lacks the required data action
    'Microsoft.CognitiveServices/accounts/AIServices/agents/read' to perform
    'GET /api/projects/{projectName}/assistants' operation."
  }
}
```

## Requested Changes

Please add the following `dataActions` to the Deloitte Custom Contributor role:

```json
"dataActions": [
  // ============================================
  // 1. Azure Container Apps Dynamic Sessions
  // ============================================
  // Required for: Code execution in session pools (Triagent Web UI)
  "Microsoft.App/sessionPools/*/read",
  "Microsoft.App/sessionPools/interpreters/execute/action",
  "Microsoft.App/sessionPools/interpreters/read",
  "Microsoft.App/sessionPools/executions/*",
  "Microsoft.App/sessionPools/files/*",

  // ============================================
  // 2. Cognitive Services (OpenAI, AI Foundry, etc.)
  // ============================================
  // Required for: Azure OpenAI chat/embeddings, AI Foundry Agents
  // This wildcard covers all Cognitive Services data operations:
  //   - OpenAI (chat completions, embeddings, assistants)
  //   - AIServices/agents (AI Foundry Agents feature)
  //   - Speech, Vision, Language services
  "Microsoft.CognitiveServices/*"
]
```

## Justification

### Pattern Consistency
The **Deloitte Veeam Contributor** role already follows this pattern with dataActions for KeyVault and Storage:
```json
"dataActions": [
  "Microsoft.KeyVault/vaults/keys/decrypt/action",
  "Microsoft.KeyVault/vaults/keys/encrypt/action",
  "Microsoft.Storage/storageAccounts/queueServices/queues/messages/*"
]
```

### Alignment with Azure Built-in Roles
| Azure Built-in Role | dataActions | Our Request |
|---------------------|-------------|-------------|
| Azure ContainerApps Session Executor | `Microsoft.App/sessionPools/*` | Same |
| Azure AI User | `Microsoft.CognitiveServices/*` | Same |
| Cognitive Services OpenAI Contributor | `Microsoft.CognitiveServices/accounts/OpenAI/*` | Covered |

### Specific Permissions Being Requested

#### Container Apps Session Pools
| Permission | Purpose |
|------------|---------|
| `sessionPools/interpreters/execute/action` | Execute Python code in dynamic sessions |
| `sessionPools/executions/*` | Manage code execution lifecycle |
| `sessionPools/files/*` | Upload/download files to sessions |

#### Cognitive Services (AI Foundry + OpenAI)
| Permission | Purpose |
|------------|---------|
| `accounts/OpenAI/deployments/chat/completions/action` | Chat with GPT models |
| `accounts/OpenAI/deployments/embeddings/action` | Generate embeddings |
| `accounts/OpenAI/assistants/*` | Use OpenAI Assistants API |
| `accounts/AIServices/agents/*` | Use AI Foundry Agents |
| `accounts/ContentSafety/*` | Content moderation |

## Security Considerations

1. **No Authorization Changes** - Cannot manage role assignments (already blocked in notActions)
2. **Data Plane Only** - Only grants usage permissions, not resource management
3. **Scoped Access** - Limited to specific Azure service namespaces
4. **Audit Trail** - All operations logged in Azure Activity Log

## Implementation

To update the role, you can use:

```bash
# 1. Export current role definition
az role definition list --name "Deloitte Custom Contributor" -o json > deloitte-custom-contributor.json

# 2. Add the dataActions array (see above)

# 3. Update the role
az role definition update --role-definition @deloitte-custom-contributor.json
```

## Alternative: Immediate Workaround

While waiting for the role update, you could assign these built-in roles to our App Service managed identity:

```bash
# For Dynamic Sessions
az role assignment create \
  --assignee "e97bd84b-7e26-4975-9173-34c4c014fd1e" \
  --role "Azure ContainerApps Session Executor" \
  --scope "/subscriptions/5eefdd74-582a-411a-9168-6a3b7ac1de4c/resourceGroups/triagent-sandbox-rg/providers/Microsoft.App/sessionPools/triagent-sandbox-session-pool"
```

## Summary

| Service | Data Action Needed | Impact |
|---------|-------------------|--------|
| Container Apps Sessions | `Microsoft.App/sessionPools/*` | Enable code execution |
| Azure OpenAI | `Microsoft.CognitiveServices/accounts/OpenAI/*` | Enable AI chat/embeddings |
| AI Foundry Agents | `Microsoft.CognitiveServices/accounts/AIServices/*` | Enable AI agents |
| All Cognitive Services | `Microsoft.CognitiveServices/*` | Full AI capability |

Please let me know if you need any additional information or if you'd like to discuss this request.

Thank you for your help!

Best regards,
Santosh Dandey
sdandey@deloitte.com

---

## Appendix: Complete dataActions Array

```json
{
  "dataActions": [
    "Microsoft.App/sessionPools/*/read",
    "Microsoft.App/sessionPools/interpreters/execute/action",
    "Microsoft.App/sessionPools/interpreters/read",
    "Microsoft.App/sessionPools/executions/*",
    "Microsoft.App/sessionPools/files/*",
    "Microsoft.CognitiveServices/*"
  ]
}
```

This provides equivalent access to:
- Azure ContainerApps Session Executor
- Azure AI User / Azure AI Owner (data plane only)
