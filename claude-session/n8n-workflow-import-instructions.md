# n8n Workflow Import Instructions - Phase 2

## ⚠️ Important: v2 Replaces v1

**This workflow REPLACES the existing "Strategic Intelligence Daily" (v1) workflow.**

Both workflows trigger the same crew.py but format output differently. Running both would:
- Post duplicate content to Slack
- Cost double (~$1/day instead of $0.50)
- Create confusion

**Action Required:** Disable v1 when you activate v2.

**See:** `v1-vs-v2-workflow-comparison.md` for detailed comparison.

---

## Quick Start

**File to Import:** `n8n-strategic-intelligence-daily-v2.json`

**Time Required:** 5 minutes

---

## Step-by-Step Import

### 1. Access n8n

Open: http://192.168.1.11:5678

### 2. Import Workflow

1. Click **"Workflows"** in left sidebar
2. Click **"Add workflow"** dropdown (top right)
3. Select **"Import from File"**
4. Choose file: `n8n-strategic-intelligence-daily-v2.json`
5. Click **"Open"**

The workflow will load with all nodes pre-configured.

### 3. Verify Credentials

The workflow uses two credentials that should already exist in your n8n:

**Credential 1: SSH to Container 118**
- Type: SSH Private Key
- Name: "Container 118 SSH" (ID: 1)
- Used by nodes: "SSH Execute Crew", "SSH Read Phase 2 JSON"

**Credential 2: Slack Bot Token**
- Type: HTTP Header Auth
- Name: "Slack Trend Reporting Token" (ID: 1)
- Used by nodes: "Slack Post Message with Blocks", "Slack Error Notification"

**To verify:**
1. Click on each node that shows a credential badge
2. Ensure the credential dropdown shows your existing credentials
3. If credentials are missing, select the correct ones from dropdown

### 4. Test Workflow Manually

**Before enabling the schedule, test manually:**

1. Click the **"Manual Trigger"** node
2. Click **"Execute Node"** button in top right
3. Watch the execution flow through all nodes
4. Check Slack #trend-monitoring for posted messages

**Expected behavior:**
- SSH Execute Crew runs successfully
- JSON file is read and parsed
- Messages array is extracted (3-5 items if opportunities exist, 0 if none)
- One Slack message per opportunity appears with [Develop] [Ignore] buttons
- If 0 opportunities: No messages posted (normal)

### 5. Disable v1 and Enable v2

Once manual test succeeds:

1. **Disable the old workflow:**
   - Go to Workflows list
   - Find "Strategic Intelligence Daily" (v1)
   - Click to open it
   - Toggle **"Active"** to OFF
   - Save

2. **Enable the new workflow:**
   - Go back to "Strategic Intelligence Daily v2"
   - The Schedule Trigger is configured for **6:00 AM daily** (cron: `0 6 * * *`)
   - Click **"Save"**
   - Toggle **"Active"** to ON

The new workflow will now run automatically at 6 AM every day, replacing the old one.

---

## Workflow Architecture

```
┌─────────────────┐
│  Schedule (6AM) │
│       OR        │  ← Two triggers
│  Manual Trigger │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│  SSH Execute Crew   │  Run crew.py on Container 118
│  (5 min timeout)    │
└────────┬────────────┘
         │
         ├─────────────────────────┐
         │                         │
         ▼                         ▼
┌──────────────────┐    ┌─────────────────────┐
│ SSH Read Phase 2 │    │ Check for Errors    │
│ JSON Output      │    │ (stderr monitoring) │
└────────┬─────────┘    └──────────┬──────────┘
         │                         │
         ▼                         ▼ (if errors)
┌──────────────────┐    ┌─────────────────────┐
│ Parse Phase 2    │    │ Slack Error         │
│ JSON             │    │ Notification        │
└────────┬─────────┘    └─────────────────────┘
         │
         ▼
┌──────────────────┐
│ Extract Messages │  Get messages array
│ Array            │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Split Messages   │  Loop: one per message
│ Array            │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Slack Post       │  POST with blocks
│ Message (Loop)   │  (3-5 times)
└──────────────────┘
```

---

## Node Details

### Schedule Trigger
- **Cron:** `0 6 * * *` (6:00 AM daily)
- **Timezone:** Server timezone (adjust if needed)

### Manual Trigger
- **Purpose:** Testing without waiting for schedule
- **Usage:** Click node → Execute Node

### SSH Execute Crew
- **Command:** `cd /opt/crewai && source venv/bin/activate && python3 crew.py 2>&1 | tail -30`
- **Host:** 192.168.1.18
- **User:** root
- **Output:** Last 30 lines (confirms execution success)

### SSH Read Phase 2 JSON
- **Command:** `cat $(ls -t /opt/crewai/output/slack_messages_*.json | head -1)`
- **Purpose:** Reads most recent Phase 2 output file
- **Output:** Full JSON content via stdout

### Parse Phase 2 JSON
- **Type:** Code (JavaScript)
- **Function:** Parses SSH stdout as JSON
- **Output:** Data object with timestamp, summary, messages array

### Extract Messages Array
- **Type:** Code (JavaScript)
- **Function:** Extracts `messages` array from data
- **Handles:** Empty array (no opportunities) gracefully
- **Output:** Array of message objects (0-5 items)

### Split Messages Array
- **Type:** Split In Batches
- **Batch Size:** 1 (processes one message at a time)
- **Output:** Multiple executions, one per message

### Slack Post Message with Blocks
- **URL:** https://slack.com/api/chat.postMessage
- **Method:** POST
- **Body:**
  ```json
  {
    "channel": "#trend-monitoring",
    "blocks": {{ message.slack_blocks }}
  }
  ```
- **Runs:** Once per message (3-5 times typically)

### Check for Crew Errors
- **Type:** IF condition
- **Condition:** stderr contains "ERROR"
- **True path:** Slack Error Notification
- **False path:** (no action)

### Slack Error Notification
- **Triggered:** Only if crew.py execution fails
- **Message:** Posts error details to #trend-monitoring

---

## Troubleshooting

### Issue: "Credential not found"
**Fix:**
1. Open node showing credential error
2. Click credential dropdown
3. Select correct credential from list
4. Save workflow

### Issue: "No messages posted to Slack"
**Possible causes:**
1. Crew run had 0 opportunities (check crew output)
2. Messages array is empty (normal if no opportunities)
3. Slack blocks malformed (check JSON structure)

**Debug:**
1. Click "SSH Read Phase 2 JSON" node
2. View execution data
3. Check `messages` array length
4. If 0: No opportunities found (expected behavior sometimes)

### Issue: "Slack blocks don't render"
**Possible causes:**
1. JSON body not properly formatted
2. Blocks not valid Block Kit JSON

**Fix:**
1. Check execution data for "Slack Post Message" node
2. Verify `slack_blocks` field is an array
3. Test blocks at: https://app.slack.com/block-kit-builder

### Issue: "Workflow runs but buttons don't work"
**This is expected for Phase 2!**
- Buttons will render but not respond to clicks yet
- Phase 3 will implement button action handlers
- For now, verify buttons appear visually

---

## Validation Checklist

After import and first manual test:

- [ ] Workflow imported successfully
- [ ] All credentials verified
- [ ] Manual trigger executes without errors
- [ ] crew.py runs successfully on Container 118
- [ ] JSON file is read and parsed
- [ ] Messages array extracted (count matches opportunities)
- [ ] Slack messages appear in #trend-monitoring
- [ ] Each message has emoji (🏠 or 💼)
- [ ] Each message shows Relevance, Signal, Next Steps
- [ ] [Develop] button renders (blue)
- [ ] [Ignore] button renders (gray)
- [ ] Schedule enabled for 6 AM daily

---

## Comparison to Old Workflow

**Old Workflow (Strategic Intelligence Daily):**
- Single digest message
- All opportunities in one post
- No buttons
- Thread-based approval

**New Workflow (Strategic Intelligence Daily v2):**
- Individual messages per opportunity
- Scannable in <30 seconds
- [Develop] [Ignore] buttons
- Visual emoji indicators (🏠/💼)
- Prepared for Phase 3 button handlers

---

## Next Steps After Import

1. **Test manually** (use Manual Trigger)
2. **Verify messages in Slack** (should see 3-5 individual posts)
3. **Enable schedule** (activate workflow)
4. **Wait for 6 AM run** (or manually trigger for immediate test)
5. **Mark Phase 2 complete** once verified
6. **Begin Phase 3** (button action handlers)

---

## Files Referenced

**Imported file:**
- `n8n-strategic-intelligence-daily-v2.json`

**Reads from Container 118:**
- `/opt/crewai/output/slack_messages_{timestamp}.json`

**Posts to:**
- Slack #trend-monitoring channel

---

## Support

If workflow fails to import or execute:

1. Check n8n version (workflow tested on n8n 1.x)
2. Verify SSH credentials are configured
3. Verify Slack bot token is valid
4. Check Container 118 is accessible (ping 192.168.1.18)
5. Review execution logs in n8n UI

---

*Import guide created: 2026-02-04*
*Workflow version: v2 (Phase 2 - Individual Messages with Buttons)*
