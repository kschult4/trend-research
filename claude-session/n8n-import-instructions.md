# n8n Workflow Import Instructions

**File to Import:** `n8n-approval-poller-workflow.json`

---

## Step 1: Import the Workflow

1. Open n8n at http://192.168.1.11:5678
2. Click **"Workflows"** in the left sidebar
3. Click **"Add Workflow"** button (top-right)
4. Click the **three dots menu** (⋮) in the top-right
5. Select **"Import from File"**
6. Browse to: `/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Software Projects/trend-research/claude-session/n8n-approval-poller-workflow.json`
7. Click **Open**

The workflow will be imported with all 25 nodes pre-configured!

---

## Step 2: Update Credential References

After import, you need to update the credential IDs (n8n can't import credential references directly).

### For Slack Nodes (5 nodes need this):
1. **Get Today's Digest** node
2. **Get Replies** node
3. **Post to Slack Thread** node
4. **Post Invalid Syntax Help** node
5. **Post Opportunity Not Found** node
6. **Post Catalyst Error** node

For each node:
- Click the node
- In the "Credential for Slack OAuth2 API" dropdown
- Select: **"Slack Trend Reporting Token"**
- Click **"Execute Node"** to test (optional)

### For SSH Nodes (7 nodes need this):
1. **Parse Approval Syntax** node
2. **Validate Opportunity Exists** node
3. **Check for Duplicates** node
4. **Log Approval** node
5. **Trigger Catalyst** node
6. **Update Approval Log - Delivered** node

For each node:
- Click the node
- In the "Credential for SSH" dropdown
- Select: **"Container 118 SSH"**
- Click **"Execute Node"** to test (optional)

---

## Step 3: Verify Configuration

### Check These Key Values:

1. **Slack Channel ID (should be C0ABUP7MHMM):**
   - "Get Today's Digest" node → Body → channel field
   - "Get Replies" node → Body → channel field
   - All "Post to Slack" nodes → Body → channel field

2. **Kyle's User ID (should be U09GDG5LACR):**
   - "Filter User Replies" node → Code → `kyleUserId` variable

3. **Container 118 IP (should be 192.168.1.18):**
   - Verify SSH credential points to correct host
   - Check: Credentials → Container 118 SSH → Host

---

## Step 4: Test Individual Nodes (Before Activating)

### Test 1: Get Today's Digest
1. Click "Get Today's Digest" node
2. Click **"Execute Node"** button
3. Should return recent messages from #trend-monitoring
4. Verify `messages` array exists in output

### Test 2: Parse Digest Response
1. Click "Parse Digest Response" node
2. Click **"Execute Node"**
3. Should output:
   ```json
   {
     "digest_found": true,
     "digest_ts": "1234567890.123456",
     "digest_date": "2026-02-02"
   }
   ```

### Test 3: Parse Approval Syntax (Manual Test)
1. Go to Slack #trend-monitoring
2. Find today's digest
3. Reply with: `approve H1`
4. In n8n, click "Parse Approval Syntax" node
5. Click **"Execute Node"**
6. Should parse the approval correctly

---

## Step 5: Activate the Workflow

Once all credentials are configured:

1. Click **"Save"** button (top-right)
2. Toggle the **"Active"** switch to ON (top-right)
3. The workflow will now poll every 5 minutes

---

## Step 6: Test End-to-End

### Quick Test:
1. Wait for next daily digest (or use existing one from today)
2. Reply to digest with: `approve H1`
3. Wait up to 5 minutes for next poll
4. Verify:
   - Approval logged to `/opt/crewai/output/approvals.jsonl`
   - Catalyst executed
   - Deliverable posted to Slack thread

### Check Execution History:
1. Click **"Executions"** tab (top)
2. View recent runs
3. Click any execution to see detailed flow
4. Green nodes = success, Red nodes = error

---

## Troubleshooting

### Issue: "Invalid credentials"
- **Fix:** Re-select credentials in all nodes (Step 2 above)

### Issue: "SSH connection failed"
- **Fix:** Verify Container 118 SSH credential
  - Host: 192.168.1.18
  - Port: 22
  - User: root
  - Auth method: Key-based or password

### Issue: "Slack API error: invalid_auth"
- **Fix:** Verify Slack token has correct scopes
  - Required: `chat:write`, `channels:history` (or `groups:history`)

### Issue: "No digest found"
- **Fix:** Normal if no digest posted in last 24 hours
  - Workflow will check again in 5 minutes
  - Manually trigger daily digest workflow to test

### Issue: "Catalyst timeout"
- **Fix:** Increase SSH timeout
  - Click "Trigger Catalyst" node
  - Expand "Options"
  - Set timeout to 300000ms (already configured)

---

## Monitoring Commands

After activation, monitor with these commands:

```bash
# Check workflow execution history (in n8n UI)
# Navigate to: Executions tab

# Check approvals log
ssh root@192.168.1.18 "cat /opt/crewai/output/approvals.jsonl | jq -s '.'"

# Count approvals by status
ssh root@192.168.1.18 "cat /opt/crewai/output/approvals.jsonl | jq -r '.status' | sort | uniq -c"

# View latest deliverable
ssh root@192.168.1.18 "ls -t /opt/crewai/output/catalyst_*.json | head -1 | xargs cat | jq '.deliverable_content' -r"

# Check if workflow is running (in n8n UI)
# Look for: Active toggle = ON, Cron icon in trigger node
```

---

## Expected Behavior

**Normal Operation:**
- Workflow runs every 5 minutes automatically
- Polls Slack for new replies to digest
- Parses approvals and triggers Catalyst
- Posts deliverables to Slack thread
- Logs all approvals to approvals.jsonl

**Error Handling:**
- Invalid syntax → Help message posted to Slack
- Non-existent opportunity → Error message posted to Slack
- Catalyst failure → Error message posted to Slack
- Duplicate approval → Silently skipped (no action)

---

## Next Steps After Import

1. Import workflow (Step 1)
2. Configure credentials (Step 2)
3. Test individual nodes (Step 4)
4. Activate workflow (Step 5)
5. Test with real approval (Step 6)
6. Proceed to Phase 6 integration testing

---

*Import ready: 2026-02-02*
*25 nodes, 3 error handlers, full approval flow*
