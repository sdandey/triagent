# Azure Dev Tunnel Setup Guide

**Last Updated:** 2026-01-02
**Document Version:** 1.0

## Overview

This guide explains how to set up Azure Dev Tunnels for local development with MSAL authentication. Corporate policy restricts localhost redirect URIs in Azure AD app registrations, so dev tunnels are required to test the Web UI locally.

---

## Prerequisites

- **Azure AD account** with access to the Deloitte tenant
- **macOS** (for Homebrew installation) or Windows/Linux (see alternative installation)
- **Python 3.11+** with the project virtual environment set up

---

## One-Time Setup

### Step 1: Install Dev Tunnel CLI

**macOS (Homebrew):**
```bash
brew install --cask devtunnel
```

**Windows:**
```powershell
winget install Microsoft.devtunnel
```

**Linux:**
```bash
curl -sL https://aka.ms/DevTunnelCliInstall | bash
```

### Step 2: Login with Azure AD

```bash
devtunnel user login
```

This opens a browser window for Azure AD authentication. Sign in with your Deloitte account.

Verify login:
```bash
devtunnel user show
```

Expected output:
```
Logged in as sdandey@deloitte.com (Deloitte (O365D))
```

### Step 3: Use the Team Tunnel

The team already has a shared tunnel configured. You don't need to create a new one.

| Property | Value |
|----------|-------|
| **Tunnel Name** | `triagent-team` |
| **Tunnel URL** | `https://4m2mfr3p-8080.use2.devtunnels.ms` |
| **Port** | 8080 |

Verify the tunnel exists:
```bash
devtunnel show triagent-team
```

> **Note:** If you need to create a new tunnel for personal use, see the [Creating a New Tunnel](#creating-a-new-tunnel) section.

---

## Environment Configuration

### Update `.env` File

Ensure your `.env` file contains these settings:

```bash
# Dev Tunnel Configuration
CHAINLIT_URL=https://4m2mfr3p-8080.use2.devtunnels.ms
CHAINLIT_COOKIE_SAMESITE=none

# Azure AD OAuth Configuration
OAUTH_AZURE_AD_CLIENT_ID=57b5437c-ad58-4520-8b1b-a102ad2d9049
OAUTH_AZURE_AD_CLIENT_SECRET=<your-client-secret>
OAUTH_AZURE_AD_TENANT_ID=36da45f1-dd2c-4d1f-af13-5abe46b99921
OAUTH_AZURE_AD_ENABLE_SINGLE_TENANT=true
```

### Key Settings Explained

| Setting | Purpose |
|---------|---------|
| `CHAINLIT_URL` | The public URL where Chainlit is accessible. Used for OAuth redirect. |
| `CHAINLIT_COOKIE_SAMESITE=none` | Required for cross-domain OAuth cookies through the dev tunnel. |

---

## Daily Development Workflow

### Terminal 1: Start Dev Tunnel

```bash
devtunnel host triagent-team
```

Leave this running. You should see:
```
Hosting port 8080 at https://4m2mfr3p-8080.use2.devtunnels.ms
```

### Terminal 2: Start Chainlit

```bash
cd ~/Documents/code/triagent-web-ui
source .venv/bin/activate
python start_chainlit.py
```

The browser automatically opens to `https://4m2mfr3p-8080.use2.devtunnels.ms`.

---

## Troubleshooting

### "oauth state does not correspond" Error

**Cause:** Stale cookies from previous sessions.

**Fix:**
1. Open an incognito/private browser window
2. Navigate to the dev tunnel URL
3. Try signing in again

### Tunnel Not Found

**Symptom:** `devtunnel host triagent-team` fails with "tunnel not found"

**Fix:** The tunnel may have expired (30-day limit). Contact the team lead to recreate the tunnel, or create your own:

```bash
devtunnel create my-tunnel --allow-anonymous
devtunnel port create my-tunnel --port-number 8080
```

Then update your `.env` with the new URL.

### Port 8080 Already in Use

**Fix:**
```bash
lsof -ti:8080 | xargs kill -9
```

### Azure AD Redirect Error

**Symptom:** AADSTS50011 - redirect URI mismatch

**Fix:** Ensure the redirect URI is registered in Azure AD:
- Go to Azure Portal > App registrations > US TRIAGENT NONPROD
- Navigate to Authentication > Web platform
- Add: `https://4m2mfr3p-8080.use2.devtunnels.ms/auth/oauth/azure-ad/callback`

---

## Creating a New Tunnel

If you need to create a personal tunnel:

```bash
# Create tunnel with anonymous access
devtunnel create my-personal-tunnel --allow-anonymous

# Add port forwarding for Chainlit
devtunnel port create my-personal-tunnel --port-number 8080

# Get the tunnel URL
devtunnel show my-personal-tunnel
```

Then:
1. Update your `.env` with the new `CHAINLIT_URL`
2. Add the new redirect URI to the Azure AD app registration

---

## Azure AD App Registration

The Web UI uses the following Azure AD app:

| Property | Value |
|----------|-------|
| **App Name** | US TRIAGENT NONPROD |
| **Client ID** | `57b5437c-ad58-4520-8b1b-a102ad2d9049` |
| **Tenant ID** | `36da45f1-dd2c-4d1f-af13-5abe46b99921` |
| **Redirect URI** | `https://4m2mfr3p-8080.use2.devtunnels.ms/auth/oauth/azure-ad/callback` |

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `devtunnel user login` | Login to Azure AD |
| `devtunnel user show` | Show current login |
| `devtunnel list` | List your tunnels |
| `devtunnel show triagent-team` | Show tunnel details |
| `devtunnel host triagent-team` | Start hosting the tunnel |
| `devtunnel delete <name>` | Delete a tunnel |
