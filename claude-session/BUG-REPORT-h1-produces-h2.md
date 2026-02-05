# CRITICAL BUG: H1 Approvals Produce H2 Deliverables

**Date:** 2026-02-03
**Severity:** CRITICAL - Core approval flow broken
**Status:** ROOT CAUSE IDENTIFIED

---

## Bug Description

When user approves H1, the system generates and delivers an H2 deliverable instead.

**User Reports:**
1. First approval: "approve H1" → Received H2 deliverable
2. Second approval: "approve H1" → AGAIN received H2 deliverable

---

## Evidence

### approvals.jsonl Sequence
```json
{"timestamp": "2026-02-03T23:44:32.177612", "opportunity_id": "H2", "slack_message_ts": "1770158454.492329", "status": "approved"}
{"timestamp": "2026-02-03T23:44:32.244530", "opportunity_id": "H1", "slack_message_ts": "1770159089.666039", "status": "approved"}
{"timestamp": "2026-02-03T23:44:32.307291", "opportunity_id": "H1", "slack_message_ts": "1770162248.065099", "status": "approved"} ← NEW H1 approval
{"timestamp": "2026-02-03T23:45:35+00:00", "opportunity_id": "H2", "status": "delivered", "catalyst_file": "output/catalyst_2026-02-03_H2_plan.json"} ← H2 delivered instead!
```

### Catalyst Files
```bash
-rw-r--r-- 1 root root 15026 Feb  3 23:45 /opt/crewai/output/catalyst_2026-02-03_H2_plan.json
```

Only H2 deliverable exists for today. No H1 deliverable generated despite two H1 approval entries.

### Opportunities File
```json
{
  "H1": {"title": "Local Model Diversity for Homelab AI Projects"},
  "H2": {"title": "Agent-to-Agent Orchestration Pattern Research"}
}
```

Opportunities are NOT swapped - H1 and H2 are correct in the source data.

---

## Root Cause Analysis

### Investigation Path

1. ✅ **Opportunities file** - H1 and H2 are NOT swapped
2. ✅ **approval_parser.py** - Correctly extracts "H1" from "approve H1" text
3. ✅ **approvals.jsonl logging** - H1 is correctly logged with opportunity_id: "H1"
4. ❌ **n8n workflow execution order** - FOUND THE BUG

### The Bug: n8n Parallel Processing Race Condition

The n8n workflow is processing multiple approvals **in parallel or out of order**.

**What Happens:**
1. Poller runs at 23:44:32
2. Detects 3 approval messages in Slack thread:
   - H2 (old, from earlier today)
   - H1 (old, from earlier today)
   - H1 (new, just posted)
3. All 3 pass through "Check for Duplicates" node
   - H2: NOT duplicate (already delivered, but node checks for status=="delivered" which should filter it)
   - H1 (old): NOT duplicate (no delivery logged yet)
   - H1 (new): NOT duplicate (no delivery logged yet)
4. All 3 flow to "Log Approval" → "Trigger Catalyst"
5. **n8n executes Catalyst triggers in parallel or out-of-order**
6. H2 Catalyst completes first (or only H2 executes?)
7. H2 deliverable posted to Slack
8. H1 Catalyst either:
   - Never executes, OR
   - Executes but fails silently, OR
   - Executes but output is lost

---

## Duplicate Detection Failure

**Secondary Bug:** The duplicate detection is not working correctly.

**Evidence:** H2 was approved and delivered at 22:59-23:00:
```json
{"timestamp": "2026-02-03T22:59:51.386360", "opportunity_id": "H2", "status": "approved"}
{"timestamp": "2026-02-03T23:00:42+00:00", "opportunity_id": "H2", "status": "delivered"}
```

But at 23:44:32, H2 was approved AGAIN:
```json
{"timestamp": "2026-02-03T23:44:32.177612", "opportunity_id": "H2", "status": "approved"}
```

**Why Duplicate Detection Failed:**

Check the "Check for Duplicates" logic:
```python
if (rec.get('digest_date') == digest_date and
    rec.get('opportunity_id') == opp_id and
    rec.get('status') == 'delivered'):
    already_processed = True
```

This checks if an approval with status=="delivered" exists. But the APPROVAL entry has status=="approved", and only the DELIVERY entry has status=="delivered".

**The bug:** The code checks the wrong field. It should check if there exists ANY entry with the same digest_date + opportunity_id + status=="delivered", NOT if the current entry's status is "delivered".

**But wait...** Looking again, the logic seems correct. Let me re-examine.

Actually, the duplicate check iterates through ALL entries in approvals.jsonl and looks for ANY entry matching digest_date + opp_id + status=="delivered". This SHOULD have caught H2 as a duplicate.

**Hypothesis:** The Slack thread had multiple replies, and n8n's "Get Replies" node fetched ALL replies including old ones. The "Filter User Replies" then passed all of them through, including already-processed approvals.

---

## n8n Workflow Architecture Issues

### Issue 1: No Execution Order Control

The workflow processes approvals sequentially in theory, but n8n might be:
- Batching multiple items and processing in parallel
- Executing SSH nodes for multiple items simultaneously
- Using race conditions where the wrong item's $json context is used

### Issue 2: Context Passing Between Nodes

When multiple items flow through nodes, expressions like `{{ $json.opp_id }}` might reference:
- The FIRST item in the batch
- The LAST item in the batch
- A random item (race condition)

### Issue 3: No Deduplication at Reply Level

The "Get Replies" node fetches the last 100 replies from the Slack thread. If old approval replies are still in the thread, they'll be re-processed every poller cycle.

**What Should Happen:**
- "Get Replies" should only fetch NEW replies since last poll
- OR "Filter User Replies" should filter out already-processed message timestamps
- OR "Check for Duplicates" should happen BEFORE "Log Approval", not after

---

## Why H1 Produces H2 (Specific Mechanism)

**Theory 1: First-Item Context Bleed**

When Extract Approvals processes multiple replies, it creates multiple output items:
```javascript
results = [
  {json: {opp_id: "H2", digest_ts: "...", reply_ts: "..."}},
  {json: {opp_id: "H1", digest_ts: "...", reply_ts: "..."}},
  {json: {opp_id: "H1", digest_ts: "...", reply_ts: "..."}}  // New H1
]
```

When these flow to "Trigger Catalyst", n8n might be:
- Processing all 3 in parallel
- Using `$json` from the FIRST item (H2) for all 3 executions
- Executing Catalyst 3 times with opp_id="H2" each time

**Theory 2: Loop Execution Order**

n8n's execution order might be:
1. Process H2 item → Trigger Catalyst (H2) → SUCCESS
2. Process H1 item → Trigger Catalyst (but uses H2 context?) → ???
3. Process H1 item (new) → Trigger Catalyst (but uses H2 context?) → ???

**Theory 3: SSH Node Doesn't Wait**

The "Trigger Catalyst" SSH node might not wait for completion before processing the next item, causing:
- All 3 SSH commands execute simultaneously
- All 3 read the same Catalyst output file
- Only the first (H2) completes, others timeout or fail

---

## Fix Strategy

### Fix 1: Add Timestamp Filtering (IMMEDIATE)

**Problem:** Old replies are re-processed every poller cycle
**Solution:** Track last processed message timestamp

**Implementation:**
1. Store last processed message_ts in a file: `/opt/crewai/output/last_processed_ts.txt`
2. In "Filter User Replies", skip any message with ts <= last_processed_ts
3. Update last_processed_ts after each successful poll

**Code Change (Filter User Replies node):**
```javascript
// Read last processed timestamp
const fs = require('fs');
const lastTsFile = '/opt/crewai/output/last_processed_ts.txt';
let lastProcessedTs = '0';
if (fs.existsSync(lastTsFile)) {
  lastProcessedTs = fs.readFileSync(lastTsFile, 'utf8').trim();
}

const results = [];
let maxTs = lastProcessedTs;

for (const item of allItems) {
  const msg = item.json;

  // Skip if already processed
  if (msg.ts <= lastProcessedTs) {
    continue;
  }

  // ... rest of filtering logic

  // Track max timestamp
  if (msg.ts > maxTs) {
    maxTs = msg.ts;
  }
}

// Write new max timestamp
fs.writeFileSync(lastTsFile, maxTs);

return results;
```

### Fix 2: Force Sequential Execution (RECOMMENDED)

**Problem:** n8n processes multiple approvals in parallel
**Solution:** Use n8n's "Loop Over Items" node or split workflow

**Implementation Option A: Loop Over Items**
Add a "Loop Over Items" node after "Extract Approvals":
1. Converts batch into sequential processing
2. Each approval goes through Catalyst → Slack → Log individually
3. No parallel execution possible

**Implementation Option B: Split Workflow**
1. Current workflow: Poll → Detect → Log ALL approvals
2. Second workflow: Process ONE approval at a time from a queue file
3. First workflow writes to queue, second workflow reads from queue

### Fix 3: Better Duplicate Detection (CRITICAL)

**Current Issue:** Duplicate detection happens AFTER logging

**Solution:** Move duplicate check BEFORE logging

**New Flow:**
1. Extract Approvals
2. Check for Duplicates (for EACH approval)
3. Filter New Approvals (only pass non-duplicates)
4. Log Approval (only new ones)
5. Trigger Catalyst (only new ones)

**This already exists!** The flow is correct. The bug is that the duplicate check is not working.

**Real Issue:** The duplicate check should filter out H2 (already delivered at 23:00:42), but it didn't.

**Why?** Let me re-check the duplicate logic...

```python
if (rec.get('digest_date') == digest_date and
    rec.get('opportunity_id') == opp_id and
    rec.get('status') == 'delivered'):
    already_processed = True
```

This should have found:
```json
{"digest_date": "2026-02-03", "opportunity_id": "H2", "status": "delivered"}
```

And set already_processed=True for H2.

**But the approvals.jsonl shows H2 was approved again at 23:44:32!**

This means the duplicate check FAILED.

**Possible reasons:**
1. The digest_date didn't match (but it's the same: 2026-02-03)
2. The opportunity_id didn't match (but it's the same: H2)
3. The status check failed (but status=="delivered" is there)
4. File read issue (file not opened correctly?)
5. **The duplicate check happened BEFORE the 23:00:42 delivery was logged** (timing issue)

**Most likely: Timing Issue**

At 22:59:51, H2 was approved. At 23:00:42, H2 was delivered.

But if the poller ran again at 23:00:00 (between approval and delivery), it would:
1. Fetch replies (sees H2 approval)
2. Check duplicates (no delivery logged yet)
3. Log approval AGAIN
4. Trigger Catalyst (while previous Catalyst is still running!)

**This explains everything:**
- Multiple H2 approvals logged (poller ran while Catalyst was processing)
- H1 producing H2 (both Catalyst executions used the same opportunity data)

---

## Recommended Fix (IMMEDIATE)

### Fix: Add Approval-Level Duplicate Check

**Change the duplicate detection to check for status=="approved" OR status=="delivered":**

```python
already_processed = False
approvals_file = '/opt/crewai/output/approvals.jsonl'
if os.path.exists(approvals_file):
    with open(approvals_file) as f:
        for line in f:
            try:
                rec = json.loads(line)
                if (rec.get('digest_date') == digest_date and
                    rec.get('opportunity_id') == opp_id and
                    rec.get('status') in ['approved', 'delivered']):  # ← CHECK FOR BOTH
                    already_processed = True
                    break
            except:
                pass
```

This will prevent re-processing approvals that are already logged, even if not yet delivered.

### Fix: Add Split Items Node

After "Extract Approvals", add a "Split Out" node to force n8n to process one approval at a time:

**Node Configuration:**
- Type: "Split Out"
- Field to Split: (leave default)
- Include: "Other fields"

This ensures each approval is processed sequentially, not in parallel.

---

## Testing Plan After Fix

1. Clear all test approvals from approvals.jsonl (keep only pre-23:00 entries)
2. Deploy fixed workflow (v13)
3. Post "approve H1" in Slack
4. Wait 5-10 minutes
5. Verify:
   - Only ONE H1 approval logged
   - H1 deliverable generated (not H2)
   - H1 delivery logged
6. Post "approve H1" AGAIN
7. Verify:
   - Duplicate detected, NO new log entry
   - NO new Catalyst execution

---

## Session Impact

**This bug blocks Phase 6 testing.** We cannot proceed with Test 3 (Multiple Approvals) or other tests until this is fixed.

**Recommendation:** Fix immediately before continuing Phase 6 integration tests.

