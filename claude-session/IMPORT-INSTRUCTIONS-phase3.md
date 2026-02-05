# Phase 3 Import Instructions - Ready to Deploy

## Summary

Your Phase 3 button handler workflow is **ready to import**. The credentials are already pre-configured to match your existing n8n setup.

---

## What's Been Fixed

### Problem
Original workflow had `responseMode: "lastNode"` which caused:
- Slack timeout after 3 seconds (caution icon)
- No webhook response until entire workflow completed (30-60 seconds)
- No execution logs in n8n

### Solution
Fixed workflow has:
- ✅ `responseMode: "responseNode"` - responds immediately
- ✅ "Respond Immediately" node - returns 200 OK in <1 second
- ✅ "Acknowledge - Processing" node - updates Slack to show "⏳ Processing..."
- ✅ Credentials pre-configured to match your existing setup

---

## Credential Configuration

The workflow is **already configured** with your existing credentials:

### SSH Credentials (Both nodes)
```json
"credentials": {
  "sshPrivateKey": {
    "id": "1",
    "name": "Container 118 SSH"
  }
}
```

**Used by:**
- Run Catalyst node
- Log Ignore Action node

**This matches your working v1/v2 workflows**, so n8n will automatically link to your existing "Container 118 SSH" credential.

### Slack Credentials
**NOT required** - the workflow uses Slack's `response_url` which is pre-authenticated.

---

## Import Steps

### 1. Import the Fixed Workflow

```bash
# File to import:
/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Software\ Projects/trend-research/claude-session/n8n-slack-button-handler-phase3-fixed.json
```

1. Go to https://n8n.kyle-schultz.com
2. Click **Workflows** → **Add workflow**
3. Click the **...** menu → **Import from File**
4. Select: `n8n-slack-button-handler-phase3-fixed.json`
5. Click **Import**

### 2. Verify Credential Linking

After import, check these nodes have credentials linked:

**Run Catalyst node:**
- Click the node
- Look for **Credentials** dropdown
- Should show: "Container 118 SSH" (green checkmark)
- If red X or blank: Re-select "Container 118 SSH" from dropdown

**Log Ignore Action node:**
- Same check as above
- Should also show: "Container 118 SSH"

### 3. Activate the Workflow

1. Click the **Active** toggle in top-right (should turn green/ON)
2. Verify webhook URL shows: `https://n8n.kyle-schultz.com/webhook/slack-button-handler`

### 4. Clean Up Old Workflow (Optional)

If you imported the original (broken) Phase 3 workflow earlier:
1. Find: "Slack Button Handler - Phase 3" (without "Fixed" in name)
2. Deactivate it (toggle OFF)
3. Delete it to avoid confusion

Keep only: **"Slack Button Handler - Phase 3 (Fixed)"**

---

## Testing

### Quick Webhook Test

From terminal, verify it responds immediately:

```bash
time curl -X POST https://n8n.kyle-schultz.com/webhook/slack-button-handler \
  -H "Content-Type: application/json" \
  -d '{"body": {"actions": [{"action_id": "test_H1", "value": "H1"}], "user": {"name": "test"}, "message": {"ts": "123"}, "response_url": "http://example.com"}}' \
  -w "\nTime: %{time_total}s\n"
```

**Expected:** Response in 0.1-0.5 seconds (NOT 30+ seconds)

### Test in Slack

1. Find a Strategic Intelligence message with buttons
2. Click **[Ignore]** button
   - Should see: "⏳ Processing [H2]..." (immediate)
   - Then: "🚫 [H2] marked as ignored" (2-3 seconds)

3. Click **[Develop]** button on homelab opportunity
   - Should see: "⏳ Processing [H1]..." (immediate)
   - Then: "✅ Technical Plan generated for [H1]" (30-60 seconds)
   - Check Obsidian: `_crewai-outputs/` folder (~15 seconds later)

---

## Expected Behavior

### Ignore Button Flow
```
User clicks [Ignore]
  ↓ (< 1 second)
Slack shows "⏳ Processing..."
  ↓ (2-3 seconds)
Slack shows "🚫 marked as ignored"
Log appended to Container 118
```

### Develop Button Flow
```
User clicks [Develop]
  ↓ (< 1 second)
Slack shows "⏳ Processing... (30-60 seconds)"
  ↓ (30-60 seconds)
Catalyst runs on Container 118
Markdown file created in homelab-outputs/
  ↓ (immediately)
Slack shows "✅ Technical Plan generated"
  ↓ (~15 seconds)
Syncthing syncs to Mac
File appears in Obsidian _crewai-outputs/
```

---

## Troubleshooting

### Still Getting Caution Icon?

1. **Check workflow is Active** (toggle ON in n8n)
2. **Check webhook path** in n8n matches Slack app config exactly
3. **Check Slack app Interactivity** is enabled with correct URL
4. **Check n8n Executions tab** - any executions showing?

### Credentials Not Linking?

If "Container 118 SSH" shows error or blank:

1. Go to **Settings** → **Credentials** in n8n
2. Find "Container 118 SSH"
3. Open and verify:
   - Host: `192.168.1.18`
   - Port: `22`
   - Username: `root`
   - Private Key: [Correct key]
4. Test connection (n8n has a "Test" button)
5. Save

Then go back to workflow and re-select credential from dropdown.

### No Execution Logs?

Check:
1. Workflow is actually Active
2. Slack app webhook URL matches n8n webhook URL exactly
3. n8n is publicly accessible (test with curl from outside your network)

---

## Success Criteria

Phase 3 is complete when:

- [ ] [Ignore] button updates message immediately, no caution icon
- [ ] [Ignore] action logs to Container 118
- [ ] [Develop] button shows "Processing..." immediately
- [ ] [Develop] button triggers Catalyst (check n8n execution logs)
- [ ] Technical Plan appears in Container 118 homelab-outputs/
- [ ] Technical Plan syncs to Obsidian within 15 seconds
- [ ] Both buttons remove themselves after action completes

---

## Files Reference

All Phase 3 files in `claude-session/`:

1. **n8n-slack-button-handler-phase3-fixed.json** ← Import this one
2. n8n-credentials-reference.md - Credential documentation
3. webhook-troubleshooting-guide.md - Detailed troubleshooting
4. phase3-button-handler-deployment.md - Original deployment guide
5. IMPORT-INSTRUCTIONS-phase3.md - This file

---

**Ready to import!** The workflow has correct credentials pre-configured and will work immediately after import and activation.
