# Troubleshooting Report: Slack Slash Commands Not Working

**Date:** 2026-02-01
**Issue:** `/interests` and `/newproject` slash commands not responding in Slack

---

## Diagnostic Results

### ✅ Workflow Status
- **Workflow ID:** WXCmcegHUvwDpu4o
- **Name:** Context Manager (Trend Monitoring)
- **Active (per API):** True
- **Nodes:** 8 configured
- **Webhook Path:** `context-manager`
- **HTTP Method:** POST

### ❌ Webhook Registration
**Test Command:**
```bash
curl -X POST http://192.168.1.11:5678/webhook/context-manager \
  -d "command=/interests&text=test"
```

**Result:** 404 Error
```json
{
  "code": 404,
  "message": "The requested webhook 'POST context-manager' is not registered.",
  "hint": "The workflow must be active for a production URL to run successfully..."
}
```

**Root Cause:** n8n webhooks don't auto-register when workflows are created/updated via REST API. The workflow is marked "active" in the database, but the webhook listener isn't registered in n8n's runtime.

### ❌ Execution History
- **Executions:** 0 (zero)
- **Conclusion:** No Slack requests have reached the workflow

### ⚠️ SSH Credential Mismatch
- **Current:** Workflow uses "AI Box SSH" credential
- **AI Box SSH Points To:** 192.168.1.204 (AI Box server)
- **Should Point To:** 192.168.1.18 (container 118 - CrewAI)

**Impact:** Even if webhook worked, SSH commands would execute on wrong server.

---

## Required Fixes (In Order)

### Fix 1: Register Webhook (CRITICAL)
**Method:** Manual activation in n8n Web UI

**Steps:**
1. Open n8n: http://192.168.1.11:5678
2. Find workflow: "Context Manager (Trend Monitoring)"
3. Open the workflow (click on it)
4. You'll see it's marked as "Active" (green toggle)
5. Toggle it OFF (inactive)
6. Wait 2 seconds
7. Toggle it ON (active)
8. This re-registers the webhook

**Why:** This is the ONLY way to register webhooks in n8n when workflows are created/updated via API.

**Verification:**
```bash
curl -X POST http://192.168.1.11:5678/webhook/context-manager \
  -d "command=/interests&text=test&user_name=testuser&channel_name=test"
```
Should return JSON instead of 404.

---

### Fix 2: Update SSH Credentials
**Problem:** "AI Box SSH" credential points to 192.168.1.204, but we need 192.168.1.18

**Option A - Update Existing Credential (Recommended):**
1. In n8n Web UI, go to "Credentials" (left sidebar)
2. Find "AI Box SSH" credential
3. Edit it:
   - Host: Change from `192.168.1.204` to `192.168.1.18`
   - Test connection
   - Save

**Option B - Create New Credential:**
1. In n8n Web UI, go to "Credentials"
2. Create new "SSH" credential:
   - Name: "Container 118 SSH"
   - Host: `192.168.1.18`
   - Port: `22`
   - Username: `root`
   - Authentication: Private Key (from n8n container: `/root/.ssh/id_rsa`)
3. Save credential
4. Open "Context Manager (Trend Monitoring)" workflow
5. Click each SSH node ("Add Interest", "Create New Project")
6. Change credential from "AI Box SSH" to "Container 118 SSH"
7. Save workflow

**Note:** Option A is simpler if "AI Box SSH" isn't being used by other workflows. Check first!

---

## Verification Steps

### After Fix 1 (Webhook Registration):

**Test 1: Direct cURL**
```bash
curl -X POST http://192.168.1.11:5678/webhook/context-manager \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "command=/interests&text=Manual+test&user_name=testuser&channel_name=test"
```

**Expected Response:**
```json
{"text": "✅ Added interest to /context/hot_topics.md", "response_type": "ephemeral"}
```

**Test 2: Verify File Created**
```bash
ssh root@192.168.1.18 "cat /context/hot_topics.md"
```

**Expected:** File should contain the test entry.

---

### After Fix 2 (SSH Credentials):

**Test `/newproject`:**
```bash
curl -X POST http://192.168.1.11:5678/webhook/context-manager \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "command=/newproject&text=Test+Project%0ASummary+goes+here&user_name=testuser&channel_name=test"
```

**Verify:**
```bash
ssh root@192.168.1.18 "ls -la /context/briefs/"
ssh root@192.168.1.18 "cat /context/briefs/test-project.md"
```

**Expected:** File `/context/briefs/test-project.md` should exist with template content.

---

## Slack Configuration

Once both fixes are complete, configure Slack slash commands:

**In Slack App Settings:**

### `/interests` Command
- **Request URL:** `http://192.168.1.11:5678/webhook/context-manager`
- **Short Description:** "Add an interest or hot topic"
- **Usage Hint:** `[description]`

### `/newproject` Command
- **Request URL:** `http://192.168.1.11:5678/webhook/context-manager`
- **Short Description:** "Create a new project brief"
- **Usage Hint:** `[project name]`

**Note:** Both commands use the SAME webhook URL. The workflow routes based on the `command` field in the payload.

---

## Alternative: Manual Workflow Creation

If webhook registration continues to fail, the workflow can be recreated manually in n8n Web UI:

**Workflow JSON Available At:**
```
/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Software Projects/trend-research/claude-session/slash-command-fixed.json
```

**Import Steps:**
1. In n8n, click "Create Workflow"
2. Click "⋮" menu → Import from File
3. Select the JSON file above
4. Update SSH credential to point to 192.168.1.18
5. Save and activate

---

## Summary

**Issue Root Causes:**
1. ❌ Webhook not registered (n8n API limitation)
2. ❌ SSH credential points to wrong server

**Required Actions:**
1. ✅ Toggle workflow inactive→active in n8n Web UI (Fix 1)
2. ✅ Update SSH credential to use 192.168.1.18 (Fix 2)
3. ✅ Configure Slack slash commands with webhook URL
4. ✅ Test with cURL
5. ✅ Test in Slack channel

**Estimated Time:** 5-10 minutes

---

**Next Steps:** Please perform Fix 1 and Fix 2 in n8n Web UI, then test with the verification commands above.
