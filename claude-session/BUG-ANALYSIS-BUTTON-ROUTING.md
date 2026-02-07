# BUG ANALYSIS: Both Buttons Execute Develop Path

**Reported:** 2026-02-05
**Symptom:** Both [Ignore] and [Develop] buttons show Obsidian message
**Expected:** [Ignore] should only log to CSV, no Catalyst execution

---

## Root Cause Analysis

### Workflow Structure Review

The n8n workflow JSON shows correct structure:

1. **Parse Button Action** (lines 30-39):
   - Extracts `action_id` (e.g., "develop_H1" or "ignore_H2")
   - Splits on `_` to get action_type: "develop" or "ignore"
   - ✅ Logic is correct

2. **Route by Action** Switch Node (lines 64-92):
   - Output 0: action_type == "develop" → Run Catalyst
   - Output 1: (implicit fallback) → Log Ignore Action
   - ✅ Structure is correct

3. **Connections** (lines 235-251):
   ```json
   "Route by Action": {
     "main": [
       [ { "node": "Run Catalyst" } ],      // Output 0
       [ { "node": "Log Ignore Action" } ]  // Output 1
     ]
   }
   ```
   - ✅ Connections are correct

### Hypothesis: The Switch Node is Routing BOTH Paths

**Possible causes:**

1. **n8n Switch node bug:** Both outputs executing instead of one
2. **Action type parsing error:** `action_type` not being set correctly
3. **Button action_id mismatch:** Buttons created with wrong action_id format
4. **Workflow imported incorrectly:** Node configuration lost during import

---

## Diagnostic Steps

### Step 1: Check n8n Execution Log

**User action needed:**
1. Open n8n UI: http://192.168.1.11:5678
2. Go to "Executions" tab
3. Find most recent execution (should be from the button test)
4. Open execution details

**Check these nodes:**

**"Parse Button Action" node:**
- Look at output data
- Verify `action_type` field value
- Should be "develop" or "ignore" (lowercase)

**"Route by Action" node:**
- Check which output path was taken
- Output 0 = develop path
- Output 1 = ignore path
- **CRITICAL:** Check if BOTH outputs executed (this would be the bug)

**"Acknowledge - Processing" node:**
- This runs BEFORE the switch
- Both buttons will execute this (expected)
- Message shows "Processing..." for both actions (this is CORRECT)

### Step 2: Verify Button Action IDs

The issue might be in how buttons are created in the daily digest.

**Check Slack message source:**
1. In Slack, find a digest message with buttons
2. Click "..." menu on message → "Copy link"
3. Use Slack API or inspect network traffic to see button configuration

**Expected button structure:**
```json
{
  "type": "actions",
  "elements": [
    {
      "type": "button",
      "text": { "type": "plain_text", "text": "Develop" },
      "action_id": "develop_H1",   // <- CRITICAL: Must start with "develop"
      "value": "H1"
    },
    {
      "type": "button",
      "text": { "type": "plain_text", "text": "Ignore" },
      "action_id": "ignore_H1",    // <- CRITICAL: Must start with "ignore"
      "value": "H1"
    }
  ]
}
```

---

## Most Likely Root Cause

Based on symptoms, the most likely issue is:

### **The workflow is imported but the Switch node lost its configuration**

n8n Switch nodes are sensitive to import/export. The condition might not have been imported correctly.

**Fix:** Re-configure the Switch node in n8n UI:

1. Open workflow in n8n
2. Click "Route by Action" switch node
3. Verify conditions:
   - **Condition 1 (Output 0):** `{{ $json.action_type }}` equals `develop`
   - **No Condition 2** (Output 1 is fallback/default)
4. Make sure "strict type validation" is enabled
5. Save workflow
6. Re-test buttons

---

## Alternative: Check if Both Nodes Are Executing

**Theory:** The Switch node might be configured to run ALL paths instead of choosing one.

**Check in n8n execution log:**
- If you see BOTH "Run Catalyst" AND "Log Ignore Action" executed → Switch node is broken
- If you see ONLY "Run Catalyst" executed → Button action_id is wrong (both buttons have "develop" prefix)

---

## Quick Fix: Updated Switch Node Configuration

If the Switch node configuration is lost, here's the correct configuration:

```json
{
  "parameters": {
    "conditions": {
      "options": {
        "caseSensitive": true,
        "leftValue": "",
        "typeValidation": "strict"
      },
      "conditions": [
        {
          "id": "route-develop",
          "leftValue": "={{ $json.action_type }}",
          "rightValue": "develop",
          "operator": {
            "type": "string",
            "operation": "equals",
            "singleValue": true
          }
        }
      ],
      "combinator": "and"
    },
    "options": {
      "allMatchingOutputs": false,  // <- CRITICAL: Only ONE output should execute
      "looseTypeValidation": false
    }
  },
  "name": "Route by Action",
  "type": "n8n-nodes-base.switch",
  "typeVersion": 3
}
```

**Key setting:** `"allMatchingOutputs": false` ensures only ONE path executes.

---

## Action Plan for User

### Immediate Diagnostic:

1. **Check n8n execution log for the Ignore button test:**
   - Did "Log Ignore Action" execute? (should be YES)
   - Did "Run Catalyst" execute? (should be NO)
   - Did "Parse Catalyst Output" execute? (should be NO)
   - Did "Update Slack - Develop Success" execute? (should be NO)

2. **If ALL nodes executed:**
   - Switch node is configured to run all paths
   - Fix: Edit Switch node → Set "Mode" to "Run Once for First Match"

3. **If only Develop path executed:**
   - Button action_ids are wrong (both start with "develop")
   - Need to check how buttons are created in Phase 2 code on Container 118

### Report Back:

Which nodes executed when you clicked [Ignore]?
- [ ] Parse Button Action
- [ ] Acknowledge - Processing
- [ ] Route by Action
- [ ] Run Catalyst (should be NO)
- [ ] Parse Catalyst Output (should be NO)
- [ ] Update Slack - Develop Success (should be NO)
- [ ] Log Ignore Action (should be YES)
- [ ] Update Slack - Ignored (should be YES)

---

*Bug Analysis Created: 2026-02-05*
*Awaiting n8n execution log review*
