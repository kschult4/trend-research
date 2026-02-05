# Workflow Fix: Split Node Issue

## Problem Identified

The workflow went down the "Loop" path instead of posting to Slack because the **wrong split node type** was used.

### Original (Broken) Configuration

**Node:** "Split Messages Array"
- **Type:** `splitInBatches` (WRONG)
- **Issue:** This node is designed for pagination/batching, not array splitting
- **Result:** Tried to loop/batch instead of splitting the array into items

**Extra Node:** "Extract Messages Array"
- **Type:** `code`
- **Issue:** This was a workaround that actually made things worse
- **Result:** Pre-split the array, confusing the splitInBatches node

### What Happened

1. Parse Phase 2 JSON → Returns `{ messages: [...] }`
2. Extract Messages Array → Converts to `[{msg1}, {msg2}, {msg3}]` (already split!)
3. Split Messages Array (splitInBatches) → Expects to split `messages` field, but receives already-split items
4. Goes into "Loop" mode instead of posting to Slack

---

## Solution

### Fixed Configuration

**Node:** "Split Messages Array"
- **Type:** `splitOut` (CORRECT)
- **Parameter:** `fieldToSplitOut: "messages"`
- **Function:** Takes object with `messages` array, outputs one item per message

**Removed:** "Extract Messages Array" node (no longer needed)

### How It Works Now

1. Parse Phase 2 JSON → Returns `{ messages: [{msg1}, {msg2}, {msg3}] }`
2. Split Messages Array (splitOut) → Splits `messages` field into 3 items
3. For each item → Slack Post Message with Blocks
4. Result: 3 individual Slack messages

---

## Key Differences: splitOut vs splitInBatches

### splitOut (What We Need)
- **Purpose:** Split an array field into individual items
- **Input:** `{ messages: [item1, item2, item3] }`
- **Output:** 3 items (one per array element)
- **Use case:** Process each array element separately
- **What we use it for:** Split messages array so each message gets its own Slack post

### splitInBatches (What We Had)
- **Purpose:** Process items in batches/chunks (pagination)
- **Input:** Stream of items
- **Output:** Batches with loop-back for pagination
- **Use case:** Process large datasets in chunks
- **Why it failed:** We don't need batching, we need array splitting

---

## Changes Made

### Removed Node
```json
{
  "id": "extract-messages",
  "name": "Extract Messages Array",
  "type": "n8n-nodes-base.code"
}
```
**Reason:** Unnecessary - splitOut handles this directly

### Modified Node
```json
{
  "id": "split-messages",
  "name": "Split Messages Array",
  "type": "n8n-nodes-base.splitOut",  // Changed from splitInBatches
  "parameters": {
    "fieldToSplitOut": "messages",     // Added parameter
    "options": {}
  }
}
```

### Removed Connection
- Parse Phase 2 JSON → Extract Messages Array (DELETED)

### Added Connection
- Parse Phase 2 JSON → Split Messages Array (DIRECT)

---

## Testing the Fix

**Expected Flow:**

1. **SSH Execute Crew** → Runs crew.py
2. **SSH Read Phase 2 JSON** → Reads `slack_messages_*.json`
3. **Parse Phase 2 JSON** → Parses JSON:
   ```json
   {
     "timestamp": "...",
     "messages": [
       { "opportunity_id": "H1", "slack_blocks": [...] },
       { "opportunity_id": "H2", "slack_blocks": [...] }
     ]
   }
   ```
4. **Split Messages Array** → Splits into 2 items
5. **Slack Post Message with Blocks** → Executes twice (once per item)
6. **Result:** 2 Slack messages appear

**What to Check:**
- ✅ Workflow should NOT go into "Loop" mode
- ✅ "Split Messages Array" should output N items (where N = number of opportunities)
- ✅ "Slack Post Message with Blocks" should execute N times
- ✅ Each execution should post one message to Slack
- ✅ Each message should have correct `slack_blocks`

---

## Re-Import Instructions

### Option 1: Update Existing Workflow (Recommended)

1. Open n8n
2. Go to "Strategic Intelligence Daily v2" workflow
3. Delete "Extract Messages Array" node
4. Click "Split Messages Array" node
5. Change type from "Split In Batches" to "Split Out"
6. Set parameter: Field to split out: `messages`
7. Reconnect: Parse Phase 2 JSON → Split Messages Array
8. Save and test

### Option 2: Delete and Re-Import

1. Open n8n
2. Delete "Strategic Intelligence Daily v2" workflow
3. Import → Choose file: `n8n-strategic-intelligence-daily-v2.json` (updated)
4. Verify credentials
5. Test with Manual Trigger

---

## File Updated

**Updated file:** `claude-session/n8n-strategic-intelligence-daily-v2.json`

**Version:** 2.1 (updated from 2.0)

**Changes:**
- Removed "Extract Messages Array" node
- Changed "Split Messages Array" from `splitInBatches` to `splitOut`
- Removed intermediate connection
- Direct connection: Parse → Split → Slack

---

## Why This Happened

**Initial workflow design mistake:**
- I used `splitInBatches` thinking it would split the array
- Realized it needed help, so added "Extract Messages Array"
- But this created a double-split situation
- The correct approach is just `splitOut` directly on the messages field

**Lesson learned:**
- `splitOut` = array field splitting (what we need)
- `splitInBatches` = pagination/batching (not what we need)

---

*Fix applied: 2026-02-04 23:30 UTC*
*Ready for re-import and testing*
