# Webhook Troubleshooting Guide - Phase 3

**Issue:** Slack shows caution icon when clicking buttons, no execution in n8n, no documents in Obsidian

**Root Cause:** The webhook configuration had `responseMode: "lastNode"` which waits for the entire workflow (30-60 seconds) before responding to Slack. Slack times out after 3 seconds.

---

## The Fix

I've created a corrected workflow: `n8n-slack-button-handler-phase3-fixed.json`

**Key changes:**
1. Webhook now uses `responseMode: "responseNode"`
2. Added "Respond Immediately" node that returns empty 200 OK within milliseconds
3. Added "Acknowledge - Processing" node that updates Slack message to show "⏳ Processing..."
4. Workflow continues in background, updates Slack when complete

---

## Step-by-Step Fix Instructions

### 1. Check Current Workflow Status

First, verify the workflow is actually deployed:

1. Go to n8n: https://n8n.kyle-schultz.com
2. Look for workflow: "Slack Button Handler - Phase 3"
3. Check if it's **Active** (toggle should be ON/green)
4. Click **Executions** tab - do you see ANY executions?

**If NO executions appear:** Slack isn't reaching the webhook at all (see Section 2)
**If executions appear but fail:** See Section 3

### 2. Verify Webhook URL Configuration

#### A. Check n8n Webhook URL

1. In n8n, open the workflow
2. Click the **Webhook Trigger** node
3. Copy the **Production URL**
4. Should be: `https://n8n.kyle-schultz.com/webhook/slack-button-handler`

#### B. Check Slack App Configuration

1. Go to https://api.slack.com/apps
2. Select your Strategic Intelligence app
3. Click **Interactivity & Shortcuts**
4. Verify **Request URL** matches n8n webhook URL exactly
5. Verify **Interactivity** is enabled (toggle ON)

#### C. Test Webhook Reachability

From your Mac terminal:

```bash
# Test if webhook is reachable
curl -X POST https://n8n.kyle-schultz.com/webhook/slack-button-handler \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}' \
  -v

# Expected: 200 OK response
# If you get 404: Webhook path is wrong or workflow isn't active
# If you get timeout: Network/firewall issue
```

### 3. Import Fixed Workflow

The original workflow had a critical bug. Import the fixed version:

1. **Deactivate** the old workflow (toggle OFF)
2. Click **Add workflow** → **Import from File**
3. Select: `n8n-slack-button-handler-phase3-fixed.json`
4. Verify nodes imported:
   - Webhook Trigger
   - **Respond Immediately** (NEW - returns 200 OK instantly)
   - Parse Button Action
   - **Acknowledge - Processing** (NEW - updates Slack with "Processing...")
   - Route by Action
   - Run Catalyst (develop path)
   - Parse Catalyst Output
   - Update Slack - Develop Success
   - Log Ignore Action (ignore path)
   - Update Slack - Ignored

5. **Activate** the new workflow
6. **Delete** the old workflow (optional, but recommended to avoid confusion)

### 4. Verify Webhook Credentials

The SSH nodes need credentials to connect to Container 118:

1. In n8n, click on **Run Catalyst** node
2. Check **Credentials** dropdown
3. Should show: "Container 118 SSH"
4. If missing or shows error:
   - Click **Credentials** → **Add New**
   - Type: SSH (Private Key)
   - Name: Container 118 SSH
   - Host: 192.168.1.18
   - Port: 22
   - Username: root
   - Private Key: [Your SSH private key for Container 118]

5. Repeat for **Log Ignore Action** node

### 5. Test the Fixed Workflow

#### Test 1: Check Webhook Immediately Returns

1. From terminal, send test POST:
```bash
time curl -X POST https://n8n.kyle-schultz.com/webhook/slack-button-handler \
  -H "Content-Type: application/json" \
  -d '{"body": {"actions": [{"action_id": "test_H1", "value": "H1"}], "user": {"name": "test"}, "message": {"ts": "123"}, "response_url": "http://example.com"}}' \
  -w "\nTime: %{time_total}s\n"
```

**Expected:** Response within 0.1-0.5 seconds (not 30+ seconds)

#### Test 2: Click [Ignore] Button in Slack

1. Find a Strategic Intelligence message with buttons
2. Click **[Ignore]**
3. **Expected behavior:**
   - Message immediately changes to "⏳ Processing [H2]..." (within 1 second)
   - After 2-3 seconds, changes to "🚫 [H2] marked as ignored"
4. Check n8n Executions tab - should show successful execution

#### Test 3: Click [Develop] Button in Slack

1. Click **[Develop]** on a homelab opportunity (H1, H2, H3)
2. **Expected behavior:**
   - Message immediately changes to "⏳ Processing [H1]..." (within 1 second)
   - After 30-60 seconds, changes to "✅ Technical Plan generated..."
3. Check Obsidian after 15 more seconds:
   ```
   /Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Obsidian/The Good Stuff/Homelab/_crewai-outputs/
   ```
4. Should see new .md file with technical plan

---

## Common Issues

### Issue: Still Getting Caution Icon

**Symptoms:**
- Caution icon still appears
- No execution in n8n

**Diagnosis:**
```bash
# Check if n8n is actually running
curl https://n8n.kyle-schultz.com/

# Check if webhook path exists (should NOT return 404)
curl -I https://n8n.kyle-schultz.com/webhook/slack-button-handler

# Check DNS resolution
nslookup n8n.kyle-schultz.com

# Check if there's a firewall/proxy between Slack and n8n
# Slack's IPs should be whitelisted if you have IP filtering
```

**Possible causes:**
1. Workflow not activated in n8n
2. Wrong webhook path in Slack config
3. SSL certificate issue (Slack requires valid HTTPS)
4. Firewall blocking Slack's IP ranges
5. n8n instance not publicly accessible

### Issue: Execution Starts But Fails

**Symptoms:**
- Execution appears in n8n
- Shows error in execution log

**Check execution details:**
1. Click failed execution
2. Look at which node failed
3. Common failures:
   - **Parse Button Action fails:** Slack payload format changed, check `$input.first().json.body` structure
   - **Run Catalyst fails:** SSH credentials wrong, Container 118 unreachable, or Python venv issues
   - **Parse Catalyst Output fails:** Catalyst didn't output expected JSON markers
   - **Update Slack fails:** response_url expired (only valid 30 minutes)

### Issue: Catalyst Runs But No File in Obsidian

**Symptoms:**
- Workflow completes successfully
- Slack shows "✅ Technical Plan generated"
- No file in Obsidian

**Check Syncthing:**
```bash
# SSH to Container 118
ssh root@192.168.1.18

# Verify markdown file was created
ls -la /opt/crewai/homelab-outputs/*.md

# Check Syncthing status
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8384/rest/system/status | jq .

# Check if folder is syncing
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8384/rest/db/status?folder=qiukt-rurae | jq .

# Force rescan
curl -X POST -H "X-API-Key: YOUR_API_KEY" http://localhost:8384/rest/db/scan?folder=qiukt-rurae
```

**Check Mac Syncthing:**
```bash
# Check Syncthing GUI on Mac
open http://localhost:8384

# Look at folder "homelab-outputs"
# Should show: Synced (100%)

# Check if file exists locally
ls -la "/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Obsidian/The Good Stuff/Homelab/_crewai-outputs/"
```

### Issue: Opportunity Not Found Error

**Symptoms:**
- Slack shows "❌ Error: Opportunity H1 not found"

**Cause:** No opportunities mapping file for today's date

**Fix:**
```bash
# Check what dates have opportunity files
ssh root@192.168.1.18
ls -la /opt/crewai/output/opportunities_*.json

# If testing with old opportunity IDs, modify digest_date in workflow or wait for next daily run
```

---

## Verification Checklist

Before testing again, verify:

- [ ] Fixed workflow imported and activated
- [ ] Old workflow deactivated or deleted
- [ ] Webhook URL in n8n matches Slack app config exactly
- [ ] Interactivity enabled in Slack app settings
- [ ] SSH credentials configured in n8n for Container 118
- [ ] Container 118 reachable from n8n server
- [ ] Catalyst has been modified with markdown output (check `/opt/crewai/catalyst.py`)
- [ ] Directory `/opt/crewai/homelab-outputs/` exists
- [ ] Syncthing folder configured and syncing
- [ ] Obsidian vault folder accessible at expected path

---

## Next Steps After Fix Works

Once buttons are working:

1. Test both [Ignore] and [Develop] buttons thoroughly
2. Verify Technical Plans appear in Obsidian within 15 seconds
3. Update session notes with Phase 3 completion
4. Update roadmap to mark Phase 3 complete
5. Prepare for Phase 4: Work Item Deliverables (W IDs with email delivery)

---

*Generated during Phase 3 webhook debugging*
