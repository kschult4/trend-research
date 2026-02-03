# BLOCKER: Slack API Credential Issue

**Status:** Criterion 4 implementation complete, deployment blocked
**Date:** 2026-02-02
**Blocker:** Slack API `missing_scope` error

---

## Problem

n8n workflow execution reaches Slack API successfully but receives error:
```
missing_scope
```

**Required scope:** `chat:write`
**Current token scope:** `commands` only

---

## What Was Attempted (Failed)

1. Added `chat:write` scope to Slack app in Slack API dashboard
2. Reinstalled app to workspace
3. Updated n8n credential with new token
4. Result: Same error persists

---

## Root Cause (Most Likely)

**Wrong token type used.** There are two OAuth token types in Slack:

1. **User OAuth Token** (starts with `xoxp-`)
   - Used for user-level actions
   - Not what we need

2. **Bot User OAuth Token** (starts with `xoxb-`)
   - Used for bot actions (posting messages)
   - This is what n8n needs

**Hypothesis:** The token in n8n is likely a User OAuth Token or an old Bot token without the updated scope.

---

## Resolution Steps for Next Session

### Step 1: Verify Slack App Configuration

1. Go to https://api.slack.com/apps
2. Select your app (likely "Trend Monitoring" or similar)
3. Navigate to **OAuth & Permissions** in sidebar
4. Scroll to **Scopes** section
5. Under **Bot Token Scopes** (NOT User Token Scopes), verify these scopes exist:
   - `chat:write`
   - `commands` (already present)
6. If `chat:write` is missing, click "Add an OAuth Scope" and add it

### Step 2: Reinstall App (if scope was added)

1. Scroll to top of **OAuth & Permissions** page
2. Click **Reinstall to Workspace** button
3. Review permissions and click **Allow**
4. Confirm installation success message

### Step 3: Copy the Correct Token

1. On **OAuth & Permissions** page, scroll to **OAuth Tokens for Your Workspace**
2. Find **Bot User OAuth Token** (NOT User OAuth Token)
3. The token should start with `xoxb-` (not `xoxp-`)
4. Click **Copy** button to copy the full token

### Step 4: Update n8n Credential

1. Open n8n: http://192.168.1.11:5678
2. Go to **Credentials** menu (left sidebar)
3. Find your Slack credential (likely "Slack Trend Monitoring" or similar)
4. Click to edit
5. Replace the **Access Token** field with the Bot token you just copied
6. Click **Save**

### Step 5: Test Workflow

1. Open the "Strategic Intelligence Daily" workflow
2. Click **Execute Workflow** (manual trigger)
3. Wait for execution to complete
4. Check results:
   - SSH Execute Crew should succeed ✅
   - Parse JSON should succeed ✅
   - Slack Post should now succeed ✅
5. Verify message appears in #trend-monitoring channel

### Step 6: Verify Bot Channel Membership (if still failing)

If Step 5 still fails with `missing_scope` or `not_in_channel`:

1. Go to Slack #trend-monitoring channel
2. Click channel name at top
3. Go to **Integrations** tab
4. Click **Add apps**
5. Search for your bot name
6. Click **Add** to invite bot to channel

---

## Verification Checklist

Before testing workflow, confirm:

- [ ] Slack app has `chat:write` in **Bot Token Scopes**
- [ ] App is installed to workspace (shows in Slack app list)
- [ ] Token copied starts with `xoxb-` (not `xoxp-`)
- [ ] Token was copied in full (no truncation)
- [ ] n8n credential updated and saved
- [ ] Bot is member of #trend-monitoring channel

---

## What's Working (Don't Need to Fix)

- ✅ Container 118 SSH access from n8n
- ✅ Crew execution on container 118
- ✅ JSON output generation
- ✅ JSON parsing in n8n
- ✅ HTTP request reaching Slack API

**Only issue:** Token doesn't have required scope

---

## Alternative: Manual Slack Testing (Optional)

To verify the token outside of n8n:

```bash
curl -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer xoxb-YOUR-TOKEN-HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "#trend-monitoring",
    "text": "Test message from curl"
  }'
```

Expected success response:
```json
{
  "ok": true,
  "channel": "C...",
  "ts": "..."
}
```

Expected failure response (if wrong scope):
```json
{
  "ok": false,
  "error": "missing_scope",
  "needed": "chat:write"
}
```

---

## After Resolution

Once Slack posting works:

1. ✅ Mark blocker as resolved
2. ✅ Test workflow execution manually (1-2 times)
3. ✅ Activate workflow schedule (toggle to Active)
4. ✅ Wait for first scheduled run at 6 AM
5. ✅ Monitor for 3-5 days to ensure stability
6. ✅ Update roadmap: Criterion 4 COMPLETE (no longer blocked)
7. ✅ Begin planning Criterion 5 (Approval Flow + Catalyst)

---

## Additional Notes

**Token Security:**
- Bot tokens are sensitive credentials
- Never commit tokens to git
- If token is compromised, revoke in Slack API dashboard and generate new one

**Scope Changes:**
- Any time you add/remove scopes, you must reinstall the app
- Old tokens are not automatically updated
- Always copy the token AFTER reinstalling

**n8n Credential Caching:**
- n8n may cache credentials briefly
- If changes don't take effect, try restarting n8n container
- Or wait 1-2 minutes and retry

---

*Blocker documented: 2026-02-02*
*Next session: Resolve Slack credential, activate schedule*
