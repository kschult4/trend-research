# n8n Workflow Creation Guide - Phase 2
**Workflow Name:** Strategic Intelligence Daily v2
**Purpose:** Post individual opportunity messages with buttons to Slack

---

## Prerequisites

1. Access to n8n at http://192.168.1.11:5678
2. Slack Bot Token credential already configured in n8n
3. SSH credential for Container 118 (root@192.168.1.18)

---

## Workflow Overview

```
┌─────────────────┐
│  Schedule       │  Daily at 6:00 AM
│  Trigger        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SSH Execute    │  Run crew.py on Container 118
│  crew.py        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Read JSON      │  SCP file back to n8n
│  Output         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Split Into     │  Loop over messages array
│  Items          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Post to        │  For each message
│  Slack          │  with blocks
└─────────────────┘
```

---

## Node-by-Node Configuration

### Node 1: Schedule Trigger

**Type:** Schedule Trigger
**Name:** Daily 6 AM Trigger

**Settings:**
- Trigger Interval: Cron Expression
- Cron Expression: `0 6 * * *`
- Timezone: America/New_York (or your preferred timezone)

---

### Node 2: SSH Execute crew.py

**Type:** SSH
**Name:** Run CrewAI on Container 118

**Credential:** SSH root@192.168.1.18 (use existing credential)

**Settings:**
- Command:
  ```bash
  cd /opt/crewai && source venv/bin/activate && python3 crew.py 2>&1 | tail -20
  ```
- Timeout: 300000 (5 minutes)

**Output:**
- Will see crew.py execution logs
- Final line should show: "Phase 2 message format saved to: ..."

**Note:** We only need last 20 lines to confirm success. Full output is logged in Container.

---

### Node 3: Read JSON Output

**Type:** SSH
**Name:** Read Phase 2 JSON

**Credential:** SSH root@192.168.1.18

**Settings:**
- Command:
  ```bash
  cat $(ls -t /opt/crewai/output/slack_messages_*.json | head -1)
  ```
- This gets the most recent Phase 2 output file

**Expression to parse JSON:**
- In the next node, you'll reference: `{{JSON.parse($node["Read Phase 2 JSON"].json.stdout)}}`

---

### Node 4: Parse JSON and Extract Messages

**Type:** Code (JavaScript)
**Name:** Parse and Extract Messages

**JavaScript Code:**
```javascript
// Get SSH output
const sshOutput = $input.first().json.stdout;

// Parse JSON
const data = JSON.parse(sshOutput);

// Return the full data object
return [{
  json: data
}];
```

**Output:**
- `json.timestamp`: "2026-02-04 11:01:19"
- `json.sources_count`: 5
- `json.signals_count`: 6
- `json.summary`: { scout_preview, analyst_preview }
- `json.messages`: [ ... array of messages ... ]

---

### Node 5: Split Into Items

**Type:** Split In Batches
**Name:** Split Messages Array

**Settings:**
- Batch Size: 1
- Field Name: `messages`

**How it works:**
- Input: Single item with `messages` array
- Output: Multiple items, one per message

**Each item will have:**
- `opportunity_id`: "H1", "H2", etc.
- `category`: "homelab" or "work"
- `title`: Opportunity title
- `relevance`, `signal`, `next_steps`: Text content
- `slack_blocks`: Array of Slack Block Kit JSON

---

### Node 6: Post to Slack

**Type:** HTTP Request
**Name:** Post Message with Blocks

**URL:** `https://slack.com/api/chat.postMessage`

**Method:** POST

**Authentication:** Generic Credential Type
- Credential Type: Header Auth
- Name: `Authorization`
- Value: `Bearer xoxb-YOUR-BOT-TOKEN` (use credential)

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "channel": "#trend-monitoring",
  "blocks": {{ $json.slack_blocks }}
}
```

**Important:**
- The `$json.slack_blocks` is already an array of block objects
- Don't wrap it in additional quotes or JSON.stringify()
- n8n will handle the serialization

**Expected Response:**
```json
{
  "ok": true,
  "channel": "C...",
  "ts": "1707074400.123456",
  "message": { ... }
}
```

---

### Node 7: Error Handler (Optional)

**Type:** HTTP Request
**Name:** Post Error to Slack

**Trigger:** On Error (configure as error handler for any node)

**URL:** `https://slack.com/api/chat.postMessage`

**Method:** POST

**Body:**
```json
{
  "channel": "#trend-monitoring",
  "text": "⚠️ Strategic Intelligence workflow failed:\n```{{ $json.error.message }}```"
}
```

---

## Testing Strategy

### Test 1: Manual Trigger (No Schedule)
1. Create workflow without schedule trigger
2. Add "Manual Trigger" node at start
3. Click "Execute Node" on Manual Trigger
4. Watch execution flow through nodes
5. Verify JSON is parsed correctly
6. Verify messages array is split
7. Check Slack for posted messages

### Test 2: Verify Slack Rendering
1. Check that messages appear in #trend-monitoring
2. Verify buttons render ([Develop] [Ignore])
3. Click a button (will fail in Phase 2, that's OK)
4. Verify button interaction is received (check n8n logs)

### Test 3: Enable Schedule
1. Add Schedule Trigger node
2. Set to trigger 2 minutes from now (for immediate test)
3. Wait for trigger
4. Verify workflow executes automatically
5. Once confirmed, change to `0 6 * * *`

---

## Debugging Tips

### Issue: JSON parse error
**Symptom:** "Unexpected token" error
**Fix:** Check that SSH output is pure JSON (no extra lines)
**Solution:** Use `cat` without extra output, or add `jq '.'` to validate

### Issue: Messages not splitting
**Symptom:** Only one Slack message appears
**Fix:** Verify "Split In Batches" is configured on `messages` field
**Solution:** Double-check field name matches JSON structure

### Issue: Slack blocks don't render
**Symptom:** Message appears as plain text
**Fix:** Ensure `blocks` parameter is passed as JSON array, not string
**Solution:** Use `{{ $json.slack_blocks }}` not `"{{ $json.slack_blocks }}"`

### Issue: Buttons don't appear
**Symptom:** Message text appears but no buttons
**Fix:** Check Slack Block Kit Builder (https://app.slack.com/block-kit-builder)
**Solution:** Paste `slack_blocks` JSON to validate structure

---

## Validation Checklist

Before marking Phase 2 complete:

- [ ] Workflow executes without errors
- [ ] JSON is parsed successfully
- [ ] Messages array is split correctly
- [ ] One Slack message per opportunity appears
- [ ] Each message has emoji (🏠 or 💼)
- [ ] Each message shows Relevance, Signal, Next Steps
- [ ] [Develop] button renders (blue/primary)
- [ ] [Ignore] button renders (default)
- [ ] Messages appear within 5 minutes of 6 AM trigger
- [ ] No duplicate messages
- [ ] Old single-digest message is replaced

---

## Migration from Old Workflow

### Option 1: Replace Existing Workflow
1. Open "Strategic Intelligence Daily" workflow
2. Disable schedule trigger
3. Rename to "Strategic Intelligence Daily (OLD)"
4. Create new workflow "Strategic Intelligence Daily v2"
5. Test new workflow
6. Once verified, delete old workflow

### Option 2: Run Both (Temporary)
1. Keep old workflow active
2. Create new workflow with different schedule (e.g., 6:05 AM)
3. Compare outputs
4. Once validated, disable old workflow

### Recommended: Option 1 (clean cutover)

---

## Estimated Time

- **Workflow creation:** 15-20 minutes
- **Testing and debugging:** 10-15 minutes
- **Total:** 30 minutes

---

## Files Referenced

**Input:**
- `/opt/crewai/output/slack_messages_{timestamp}.json` (created by crew.py)

**Slack Channel:**
- `#trend-monitoring`

**Credentials Needed:**
- SSH to Container 118 (root@192.168.1.18)
- Slack Bot Token

---

## Success Criteria

Phase 2 workflow is complete when:
1. ✅ Workflow executes at 6 AM daily
2. ✅ crew.py runs successfully
3. ✅ JSON output is read and parsed
4. ✅ Messages array is split into individual items
5. ✅ 3-5 Slack messages appear (one per opportunity)
6. ✅ Each message has [Develop] [Ignore] buttons
7. ✅ Messages are scannable in <30 seconds

---

## Next: Phase 3 (Button Handlers)

After Phase 2 is verified:
1. Create new webhook endpoint in n8n
2. Configure Slack app to send button interactions to webhook
3. Map button clicks to opportunity IDs
4. Trigger Catalyst on [Develop] click
5. Write outputs to `/opt/crewai/homelab-outputs/`

But don't start Phase 3 until Phase 2 messages are posting correctly!

---

*Guide created: 2026-02-04*
*For: CrewAI Strategic Intelligence UX Pivot - Phase 2*
