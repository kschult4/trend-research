# Empty Digest Notification - Implementation Guide

**Status:** Ready to implement
**Estimated time:** 10-15 minutes
**Risk:** Low (reversible, adds functionality without removing anything)

---

## Overview

This guide adds a fallback Slack notification when the daily brief runs but finds zero actionable opportunities. This way you'll know the system ran successfully even on quiet days.

**Current behavior:**
```
6 AM → Crew runs → 0 opportunities → No Slack messages → User uncertain if system ran
```

**New behavior:**
```
6 AM → Crew runs → 0 opportunities → Fallback Slack message → User knows system ran
```

---

## Implementation Method

**Option 1: Manual UI Update (Recommended)**
- Safest approach
- Visual verification of changes
- Immediate testing in n8n canvas
- Steps provided below

**Option 2: Export/Import**
- Export current workflow as backup
- Import modified version
- More complex, less transparent

**We'll use Option 1** following governance principles (staged evolution, reversibility, verification).

---

## Step-by-Step Instructions

### Step 1: Access n8n Workflow
1. Go to https://n8n.kyle-schultz.com
2. Navigate to **Workflows**
3. Open: **"Strategic Intelligence Daily v2"**

### Step 2: Add "Check if Empty" Node

**Location:** Between "Parse Phase 2 JSON" and "Split Messages Array"

1. Click the **+** button on the connection between:
   - **Parse Phase 2 JSON** → **Split Messages Array**

2. Search for and add: **IF** node

3. Configure the IF node:
   - **Name:** `Check if Empty`
   - **Conditions:**
     - **Value 1:** `{{ $json.messages.length }}` (click "Expression" toggle)
     - **Operation:** `Equal`
     - **Value 2:** `0`

4. Click **Execute Node** to test (should evaluate to true if messages is empty)

### Step 3: Add "Slack Fallback Notification" Node

1. On the **TRUE** output of "Check if Empty", click **+**

2. Add: **HTTP Request** node

3. Configure as follows:

**Name:** `Slack Fallback Notification`

**Authentication:** None (we'll use Bearer token in headers)

**Method:** POST

**URL:** `https://slack.com/api/chat.postMessage`

**Headers:**
- Click "Add Option" → "Add Header"
  - Name: `Authorization`
  - Value: `Bearer xoxb-9570960523936-10431921181313-gdijmNyeLV1yBrVRRxJSOEiF`
- Add another header:
  - Name: `Content-Type`
  - Value: `application/json; charset=utf-8`

**Body:**
- Enable: "Send Body"
- Body Content Type: "JSON"
- Specify Body: "Using JSON"
- JSON:

```json
{
  "channel": "#trend-monitoring",
  "text": "📊 Daily Brief: No actionable opportunities today",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "📊 *Daily Brief: No actionable opportunities today*\n\n• {{ $json.sources_count }} sources checked\n• {{ $json.signals_count }} signals analyzed\n• 0 homelab opportunities\n• 0 work opportunities\n\n_All signals filtered as not actionable. System running normally._"
      }
    }
  ]
}
```

**IMPORTANT:** Make sure to toggle the **Expression** mode for `sources_count` and `signals_count` fields so they use the values from the Parse Phase 2 JSON output.

### Step 4: Reconnect "Split Messages Array" Node

1. On the **FALSE** output of "Check if Empty", connect to **Split Messages Array**

2. Delete the old connection from "Parse Phase 2 JSON" to "Split Messages Array"

**Final flow should be:**
```
Parse Phase 2 JSON
  ↓
Check if Empty (IF node)
  ↓                    ↓
  TRUE                 FALSE
  ↓                    ↓
Slack Fallback         Split Messages Array
Notification           ↓
                       Slack Post Message with Blocks
```

### Step 5: Save and Test

1. Click **Save** (top right)

2. Keep workflow **Active**

3. Test with Manual Trigger:
   - You can test by temporarily modifying the "Check if Empty" condition to always be true
   - Or wait until tomorrow's 6 AM run if today produces no opportunities

---

## Visual Layout Reference

Suggested node positions (x, y):

```
Parse Phase 2 JSON:        (750, 64)
Check if Empty:            (1000, 64)
Slack Fallback:            (1250, 200)
Split Messages Array:      (1250, 64)
Slack Post Message:        (1500, 64)
```

This keeps the main flow horizontal and the fallback branch slightly below.

---

## Verification Checklist

After implementation, verify:

- [ ] "Check if Empty" node condition is `{{ $json.messages.length }} == 0`
- [ ] TRUE output goes to "Slack Fallback Notification"
- [ ] FALSE output goes to "Split Messages Array"
- [ ] Slack Fallback has correct channel: `#trend-monitoring`
- [ ] Slack Fallback has Bearer token in Authorization header
- [ ] Slack Fallback JSON uses expressions for `sources_count` and `signals_count`
- [ ] Old connection from "Parse Phase 2 JSON" → "Split Messages Array" is deleted
- [ ] Workflow is still Active
- [ ] Manual test shows correct routing

---

## Testing Options

### Option A: Wait for Tomorrow's 6 AM Run
- Least invasive
- Requires overnight wait
- Shows real-world behavior

### Option B: Manual Execution
1. Click **Manual Trigger** in n8n
2. Watch execution flow
3. Check which branch it takes (TRUE or FALSE)
4. Verify Slack message appears correctly

### Option C: Force Empty Test
1. Temporarily change "Check if Empty" to always TRUE:
   - Condition: `1 == 1`
2. Run Manual Trigger
3. Verify Slack fallback message appears
4. Change condition back to `{{ $json.messages.length }} == 0`
5. Save again

**Recommended:** Option C (quick verification, immediate feedback)

---

## Rollback Plan

If something goes wrong:

1. **Immediate:** Deactivate workflow (toggle Active to OFF)
2. Delete new nodes: "Check if Empty" and "Slack Fallback Notification"
3. Reconnect "Parse Phase 2 JSON" directly to "Split Messages Array"
4. Save and reactivate

**Backup:** Workflow export file is saved at:
```
/tmp/workflow_backup.json (on your Mac)
```

You can re-import this if needed.

---

## Expected Slack Message Format

When the workflow finds 0 opportunities, you'll see:

```
📊 Daily Brief: No actionable opportunities today

• 12 sources checked
• 19 signals analyzed
• 0 homelab opportunities
• 0 work opportunities

All signals filtered as not actionable. System running normally.
```

This confirms:
- ✅ System ran successfully
- ✅ Sources were checked
- ✅ Signals were found and analyzed
- ✅ Strategists filtered them (not an error)

---

## Post-Implementation

After successful implementation:

1. **Monitor tomorrow's 6 AM run (2026-02-08)**
   - If opportunities exist: Should see individual messages (current behavior)
   - If no opportunities: Should see fallback message (new behavior)

2. **Update documentation:**
   - Mark this implementation as complete in session notes
   - Update Roadmap if needed (this is an enhancement to Phase 3)

3. **Observe for a week:**
   - Track how often fallback message appears
   - Adjust Strategist filtering if needed (too many quiet days vs too much noise)

---

## Questions or Issues?

If you encounter problems:
- n8n won't save: Check all expressions are valid (look for red error highlights)
- Slack message fails: Verify channel name and token are correct
- Wrong branch executes: Check IF condition syntax exactly matches example

---

**This enhancement follows governance principles:**
- ✅ Staged evolution (adds functionality, doesn't remove)
- ✅ Reversibility (easy to rollback)
- ✅ Verification (multiple testing options)
- ✅ Simplicity (2 new nodes, 1 condition change)

**Ready to implement!**
