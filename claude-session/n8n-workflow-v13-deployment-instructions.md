# n8n Workflow v13 - Deployment Instructions

**Version:** 13
**Date:** 2026-02-03
**Purpose:** Fix H1→H2 bug (duplicate detection + sequential processing)

---

## Changes in v13

### Fix 1: Improved Duplicate Detection ✅
**Problem:** Duplicate detection only checked for status=="delivered", causing old approvals to be re-processed if the poller ran between approval and delivery.

**Solution:** Now checks for BOTH status=="approved" AND status=="delivered"

**Code Change (Check for Duplicates node):**
```python
# OLD (v12):
if (rec.get('status') == 'delivered'):
    already_processed = True

# NEW (v13):
if (rec.get('status') in ['approved', 'delivered']):
    already_processed = True
```

This prevents re-processing any approval that has already been logged, even if not yet delivered.

### Fix 2: Sequential Processing ✅
**Problem:** When multiple approvals existed, n8n processed them in parallel or with context bleed, causing H1 approvals to produce H2 deliverables.

**Solution:** Added "Split Out Items" node after "Extract Approvals" to force sequential, one-at-a-time processing.

**New Node:**
- **Name:** Split Out Items
- **Type:** n8n-nodes-base.splitOut
- **Position:** Between "Extract Approvals" and "Validate Opportunity Exists"
- **Effect:** Forces n8n to process each approval individually, preventing context bleed

---

## Deployment Steps

### Step 1: Clear Test Data (CRITICAL)

Before deploying v13, clean up the test approvals to prevent confusion:

```bash
# SSH to Container 118
ssh root@192.168.1.18

# Backup current approvals.jsonl
cp /opt/crewai/output/approvals.jsonl /opt/crewai/output/approvals.jsonl.backup-2026-02-03

# Keep only the first successful H2 approval/delivery (lines 14-16 from today)
# Remove all the test entries from 23:44 onward
head -16 /opt/crewai/output/approvals.jsonl > /opt/crewai/output/approvals.jsonl.clean
mv /opt/crewai/output/approvals.jsonl.clean /opt/crewai/output/approvals.jsonl

# Verify clean log
tail -5 /opt/crewai/output/approvals.jsonl
```

**Expected output (last 3 lines):**
```json
{"timestamp": "2026-02-03T22:59:51.386360", "opportunity_id": "H2", "status": "approved"}
{"timestamp": "2026-02-03T22:59:51.448226", "opportunity_id": "H1", "status": "approved"}
{"timestamp": "2026-02-03T23:00:42+00:00", "opportunity_id": "H2", "status": "delivered"}
```

This leaves H2 as delivered (duplicate detection will work) and H1 as approved (ready for retry).

### Step 2: Import v13 Workflow into n8n

1. **Open n8n UI:**
   - Navigate to: http://192.168.1.11:5678/
   - Or external: https://n8n.kyle-schultz.com/

2. **Deactivate Current Workflow:**
   - Find "Approval Poller and Catalyst Trigger"
   - Click the toggle to deactivate (workflow must be inactive for import)

3. **Import v13:**
   - Click hamburger menu (☰) in top left
   - Select "Import from File"
   - Choose file: `claude-session/n8n-approval-poller-workflow-v13.json`
   - Click "Import"

4. **Verify Import:**
   - Workflow should now show v13 in version field
   - Check for new "Split Out Items" node between "Extract Approvals" and "Validate Opportunity Exists"
   - Visual flow should show: Extract Approvals → Split Out Items → Validate Opportunity Exists

5. **Update Credentials (if needed):**
   - If SSH credential is missing, add it:
     - Node: Any SSH node (like "Parse Approval Syntax")
     - Credential: "Container 118 SSH"
     - Host: 192.168.1.18
     - Username: root
     - Private Key: (your n8n_container118_rsa key)

6. **Activate Workflow:**
   - Click the toggle to activate
   - Workflow will start running every 5 minutes

### Step 3: Test the Fix

**Test 1: H1 Approval (Fresh)**

1. Go to Slack #trend-monitoring
2. Find today's digest thread (6 AM post with H1/H2)
3. Reply: `approve H1`
4. Wait 5-10 minutes (one poller cycle)

**Expected Result:**
- H1 deliverable should post to Slack thread
- Title should be: "Local Model Diversity for Homelab AI Projects"
- approvals.jsonl should show:
  - H1 approved (new entry)
  - H1 delivered (new entry)
- Catalyst file should exist: `/opt/crewai/output/catalyst_2026-02-03_H1_plan.json`

**Verify:**
```bash
ssh root@192.168.1.18 "tail -5 /opt/crewai/output/approvals.jsonl"
ssh root@192.168.1.18 "ls -lt /opt/crewai/output/catalyst_*.json | head -3"
```

**Test 2: Duplicate Detection**

1. Reply to digest thread again: `approve H1`
2. Wait 5-10 minutes

**Expected Result:**
- NO new H1 deliverable (duplicate should be caught)
- NO new approvals.jsonl entry
- Slack should show no new message

**Verify:**
```bash
# Should show same number of lines as before
ssh root@192.168.1.18 "wc -l /opt/crewai/output/approvals.jsonl"
```

**Test 3: Multiple Approvals (Sequential)**

*Note: Need fresh opportunities for this test - wait for tomorrow's digest or manually trigger crew*

1. Reply: `approve H1, H2`
2. Wait 10-15 minutes (may take longer for sequential processing)

**Expected Result:**
- H1 deliverable posted first
- H2 deliverable posted second
- Both logged correctly in approvals.jsonl
- No context bleed (H1 gets H1 data, H2 gets H2 data)

---

## Rollback Plan

If v13 has issues:

1. **Deactivate v13 workflow**
2. **Restore v12:**
   - Import `n8n-approval-poller-workflow.json` (v12)
   - Activate
3. **Restore backup approvals.jsonl:**
   ```bash
   ssh root@192.168.1.18 "cp /opt/crewai/output/approvals.jsonl.backup-2026-02-03 /opt/crewai/output/approvals.jsonl"
   ```

---

## Verification Commands

### Check Workflow Status
```bash
# From local machine or n8n UI
# Workflow should show: Active, v13, last execution time
```

### Check Approvals Log
```bash
ssh root@192.168.1.18 "tail -20 /opt/crewai/output/approvals.jsonl"
```

### Check Catalyst Files
```bash
ssh root@192.168.1.18 "ls -lt /opt/crewai/output/catalyst_*.json | head -5"
```

### Check for Specific Opportunity
```bash
# Check if H1 was processed
ssh root@192.168.1.18 "grep 'H1' /opt/crewai/output/approvals.jsonl"

# Check if H1 deliverable exists
ssh root@192.168.1.18 "ls -lh /opt/crewai/output/catalyst_*H1*.json"
```

---

## Expected Behavior After Fix

### Before Fix (v12) ❌
- User approves H1 → Receives H2 deliverable
- Old approvals re-processed every poller cycle
- Multiple approvals processed with context bleed

### After Fix (v13) ✅
- User approves H1 → Receives H1 deliverable
- Duplicate approvals ignored (checks both approved + delivered)
- Multiple approvals processed sequentially, one at a time
- No context bleed between approvals

---

## Monitoring After Deployment

**First 24 Hours:**
- Check approvals.jsonl daily for any unexpected entries
- Verify no duplicate H1/H2 approvals being logged
- Confirm all Catalyst files match their opportunity IDs

**First Week:**
- Monitor for any context bleed issues
- Verify sequential processing doesn't cause timeouts
- Check that processing time remains < 15 min per approval

**Success Criteria:**
- ✅ H1 approval produces H1 deliverable (not H2)
- ✅ Duplicate approvals are ignored
- ✅ No old approvals re-processed
- ✅ Multiple approvals work correctly
- ✅ Processing time acceptable (< 10 min per approval)

---

## Troubleshooting

### Issue: v13 import fails
**Solution:** Deactivate v12 first, then retry import

### Issue: "Split Out Items" node missing
**Solution:** Manually add it:
1. After "Extract Approvals", click the + button
2. Search for "Split Out"
3. Add "Split Out" node
4. Connect: Extract Approvals → Split Out → Validate Opportunity Exists

### Issue: Duplicate detection still not working
**Solution:** Check Python syntax in "Check for Duplicates" node:
```python
if (rec.get('status') in ['approved', 'delivered']):
```
Make sure it's `in ['approved', 'delivered']` not `== 'delivered'`

### Issue: SSH credentials missing
**Solution:** Re-add Container 118 SSH credential to all SSH nodes

---

## Files Modified

**New Files:**
- `claude-session/n8n-approval-poller-workflow-v13.json` - Fixed workflow
- `claude-session/n8n-workflow-v13-deployment-instructions.md` - This file
- `claude-session/BUG-REPORT-h1-produces-h2.md` - Root cause analysis

**Modified Files (on Container 118 after deployment):**
- `/opt/crewai/output/approvals.jsonl` - Cleaned up test entries

---

## Next Steps After Deployment

Once v13 is deployed and Test 1 passes:

1. **Resume Phase 6 Integration Testing**
   - Test 3: Multiple Approvals (if fresh opportunities available)
   - Test 4: Invalid Syntax
   - Test 5: Duplicate Detection (should now work!)
   - Test 6: Dismiss Flow

2. **Document Results**
   - Update Session-2026-02-03-b-CrewAI-Criterion-5-Phase-6.md
   - Mark bug as resolved
   - Record test results

3. **Update Roadmap**
   - If all tests pass, mark Criterion 5 as COMPLETE
   - Update homelab_system_overview.md with final status

---

**Deployment Date:** 2026-02-03
**Deployed By:** (User)
**Approved By:** Claude (Agent)
**Bug Fix:** H1→H2 context bleed + duplicate detection failure

