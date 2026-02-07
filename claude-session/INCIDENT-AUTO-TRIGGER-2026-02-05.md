# INCIDENT REPORT: Unintended Auto-Triggering of Catalyst
**Date:** 2026-02-05
**Session:** Session-2026-02-05
**Severity:** HIGH (auto-execution of expensive AI operations)
**Status:** ROOT CAUSE IDENTIFIED, REMEDIATION PENDING

---

## Incident Summary

Technical Plans were automatically generated for opportunities H1 and H2 at 5:01 AM WITHOUT any user interaction (button clicks). This occurred before the daily digest was even delivered at 6 AM, and the user did not click any buttons.

### Observed Behavior
- **Time:** 5:01 AM (approximately)
- **Slack messages posted:**
  - "Technical Plan generated for [H1]... Check Obsidian: _crewai-outputs/"
  - "Technical Plan generated for [H2]... Check Obsidian: _crewai-outputs/"
- **Daily digest posted:** 6:00 AM (scheduled time)
- **User interaction:** NONE - no buttons clicked
- **Expected behavior:** Catalyst should ONLY run when user clicks [Develop] button

### Impact Assessment
- **Cost:** ~$0.40-0.80 in unintended API calls (2 Catalyst runs × Sonnet 4.5)
- **UX:** Confusing - outputs appeared before user could review opportunities
- **Trust:** Undermines new button-based approval flow
- **Data:** Technical Plans generated may not be wanted/relevant
- **Operational:** If unchecked, could trigger on ALL homelab opportunities daily

---

## Root Cause Analysis

### Investigation Timeline

**Step 1: Examined Phase 3 Button Handler Workflow**
- File: `n8n-slack-button-handler-phase3-fixed.json`
- Trigger: Webhook only (`path: "slack-button-handler"`)
- No schedule trigger present
- Validation: Code correctly parses button payload (`payload.actions[0]`)
- **Conclusion:** Phase 3 workflow is NOT the source of auto-triggering

**Step 2: Searched for Other Catalyst Callers**
- Command: `grep -r "catalyst.py" *.json`
- Found 5 workflow files calling Catalyst:
  1. `n8n-slack-button-handler-phase3-fixed.json` (Phase 3, webhook-triggered) ✅
  2. `n8n-slack-button-handler-phase3-v2.json` (older Phase 3 draft)
  3. `n8n-slack-button-handler-phase3.json` (original Phase 3 draft)
  4. `n8n-approval-poller-workflow-v13.json` ⚠️ **HAS SCHEDULE TRIGGER**
  5. `n8n-approval-poller-workflow.json` (earlier version)

**Step 3: Examined Approval Poller Workflow**
- File: `n8n-approval-poller-workflow-v13.json`
- **ROOT CAUSE IDENTIFIED:**

```json
{
  "name": "Approval Poller and Catalyst Trigger",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "cronExpression",
              "expression": "*/5 * * * *"    // RUNS EVERY 5 MINUTES
            }
          ]
        }
      },
      "name": "Every 5 Minutes",
      "type": "n8n-nodes-base.scheduleTrigger",
      // ...
    }
  ]
}
```

### How the Auto-Triggering Happened

1. **5:00 AM:** Approval Poller runs on schedule (every 5 minutes)
2. **Fetch Slack history:** Calls `conversations.history` API for #trend-monitoring
3. **Find digest:** Looks for messages containing "Strategic Intelligence Digest"
4. **Check for replies:** Looks for thread replies (old approval mechanism)
5. **Trigger Catalyst:** If conditions met, SSHs to Container 118 and runs Catalyst
6. **Post to Slack:** Updates message with "Technical Plan generated" confirmation

**Why it triggered at 5:01 AM specifically:**
- The workflow likely found yesterday's or a previous digest message
- OR it's polling logic incorrectly interpreted some message as an approval
- OR the workflow has a bug where it triggers on ALL recent digest messages

**Why this wasn't caught earlier:**
- Approval Poller was created in Criterion 5 Phase 5 (thread-based approval)
- Phase 3 was designed to REPLACE this system with button-based approval
- Roadmap Phase 5 (Cleanup) explicitly lists: "Delete Approval Poller n8n workflow"
- Phase 5 was never executed
- Both systems are now running CONCURRENTLY

---

## Technical Details

### Approval Poller Workflow Architecture

**Trigger:**
- Schedule: Every 5 minutes (`*/5 * * * *`)
- Active 24/7

**Logic Flow:**
1. Get Today's Digest (HTTP Request to Slack API)
   - Endpoint: `conversations.history`
   - Channel: `C0ABUP7MHMM` (#trend-monitoring)
   - Limit: 10 messages
   - Oldest: Last 24 hours
2. Parse Digest Response (Code Node)
   - Filter for bot messages containing "Strategic Intelligence Digest"
   - Prefer messages with replies (`reply_count > 0`)
3. Check Digest Found (If Node)
   - If true → continue
   - If false → stop
4. Prepare Get Replies (Code Node)
   - Extract `digest_ts` and `digest_date`
5. Get Replies (HTTP Request)
   - Endpoint: `conversations.replies`
   - Fetch thread replies
6. Parse Approvals (Code Node)
   - Look for messages like "approve H1" or "approve W2 brief"
   - Extract opportunity ID and deliverable type
7. Run Catalyst (SSH Node)
   - SSH to 192.168.1.18
   - Execute: `python3 catalyst.py --digest-date {date} --opportunity {id} --type {type}`
8. Update Slack (HTTP Request)
   - Post success message to thread

### Why This Conflicts with Phase 3

**Phase 3 Design (Button-Based):**
- User sees individual messages with buttons
- Clicks [Develop] → webhook triggers
- Catalyst runs on-demand

**Approval Poller Design (Thread-Based):**
- User replies in thread: "approve H1"
- Poller detects reply every 5 minutes
- Catalyst runs automatically

**Conflict:**
- Both systems active simultaneously
- Approval Poller may be triggering on false positives
- OR Poller is running Catalyst for ALL H IDs by default
- Phase 3 button clicks would also trigger (correct behavior)
- Result: Double execution or unintended execution

---

## Immediate Remediation Plan

### Action 1: DISABLE Approval Poller Workflow (URGENT)

**Priority:** IMMEDIATE - Stop further auto-triggering

**Steps:**
1. Log into n8n UI: http://192.168.1.11:5678
2. Navigate to "Workflows" tab
3. Find workflow: "Approval Poller and Catalyst Trigger"
4. Click workflow to open
5. Toggle workflow to INACTIVE (pause button)
6. Verify status shows "Inactive" indicator

**Validation:**
- Wait 10 minutes (2 polling cycles)
- Check Slack #trend-monitoring for new auto-generated messages
- Should see NO new messages from this workflow

**Risk:** LOW - Disabling stops unwanted behavior, no data loss

---

### Action 2: Verify Phase 3 Workflow is Active

**Steps:**
1. In n8n UI, find workflow: "Slack Button Handler - Phase 3"
2. Verify workflow is ACTIVE (green indicator)
3. Verify webhook URL: `https://n8n.kyle-schultz.com/webhook/slack-button-handler`
4. Check webhook is configured in Slack app settings

**If Phase 3 workflow is NOT imported:**
- Import from file: `n8n-slack-button-handler-phase3-fixed.json`
- Follow instructions in: `IMPORT-INSTRUCTIONS-phase3.md`
- Activate workflow after import

---

### Action 3: Test Phase 3 Button Flow (After Disabling Poller)

**Purpose:** Confirm button-based flow works correctly in isolation

**Steps:**
1. Wait for next daily digest at 6 AM (or trigger manually)
2. Click [Ignore] button on one opportunity → Verify CSV log
3. Click [Develop] button on different opportunity → Verify Technical Plan syncs
4. Check n8n execution logs for Phase 3 workflow only (no Approval Poller)

**Expected outcome:**
- Only Phase 3 webhook workflow executes
- Catalyst runs only for clicked button
- No auto-triggering occurs

---

### Action 4: Delete Approval Poller Workflow (After Testing)

**Priority:** MEDIUM - Permanent cleanup after Phase 3 verified

**Steps:**
1. Export Approval Poller workflow as backup (JSON)
2. Save to: `/Users/.../claude-session/BACKUP-approval-poller-deleted-2026-02-05.json`
3. In n8n UI, delete workflow permanently
4. Verify workflow no longer appears in workflow list

**Rationale:**
- Workflow is superseded by Phase 3 button system
- Keeping it risks future accidental activation
- Backup ensures recovery if needed

---

### Action 5: Update Roadmap Phase 5 Status

**Steps:**
1. Open: `CrewAI-Strategic-Intelligence-UX-Pivot.md`
2. Update Phase 5 (Cleanup) section:
   - Mark "Delete Approval Poller n8n workflow" as COMPLETE
   - Add incident reference and date
   - Update status from "READY TO START" to "IN PROGRESS" or "PARTIAL"

---

## Long-Term Prevention Measures

### Recommendation 1: Workflow Naming Convention

**Problem:** Multiple workflows with similar names/purposes

**Solution:**
- Prefix deprecated workflows with `[DEPRECATED]` or `[OLD]`
- Archive old workflow files in subfolder: `claude-session/deprecated/`
- Document active vs deprecated in project README

### Recommendation 2: n8n Workflow Audit

**Action:** Review all active workflows in n8n
- List all workflows with their trigger types
- Identify any schedule-triggered workflows calling sensitive operations
- Verify each workflow has clear purpose and ownership
- Disable any workflows not documented in Roadmap

### Recommendation 3: Phase 5 Becomes Mandatory

**Lesson:** Cleanup is not optional when replacing systems

**Update Roadmap:**
- Phase 5 should be executed IMMEDIATELY after Phase 3 verification
- Deprecation of old workflows is PART OF Phase 3 success criteria
- Never leave two approval systems running concurrently

### Recommendation 4: n8n Workflow Tagging

**Action:** Use n8n tags to track workflow lineage
- Tag Phase 3 workflows: `ux-pivot`, `button-handler`, `active`
- Tag deprecated workflows: `deprecated`, `criterion-5`, `inactive`
- Makes visual identification easier in n8n UI

---

## Cost Analysis

### Actual Cost (This Incident)
- 2 unintended Catalyst runs (H1, H2)
- Each run: ~$0.20-0.40 (Sonnet 4.5 API)
- **Total:** ~$0.40-0.80

### Potential Cost (If Undetected)
- Approval Poller runs every 5 minutes
- If it triggers ALL H IDs daily: 3-5 opportunities × $0.30 = $0.90-1.50/day
- Monthly: ~$27-45 in unintended costs
- Plus user confusion and incorrect outputs

**Impact:** Early detection saved significant cost and UX degradation

---

## Timeline

| Time | Event |
|------|-------|
| 2026-02-04 | Phase 3 code complete, workflow created |
| 2026-02-04 | Session marked "Phases 1-3 Complete" |
| 2026-02-04 | Phase 5 cleanup NOT executed |
| 2026-02-05 5:01 AM | Auto-trigger: H1 and H2 Technical Plans generated |
| 2026-02-05 6:00 AM | Daily digest delivered to Slack |
| 2026-02-05 (session) | User reports issue, investigation begins |
| 2026-02-05 (session) | Root cause identified: Approval Poller still active |

---

## Lessons Learned

1. **Cleanup is part of completion:** Phase 5 should not be deferred
2. **Test in isolation:** New workflows should be tested with old workflows DISABLED first
3. **Concurrent systems are risky:** Never run two approval mechanisms simultaneously
4. **Verify deactivation:** Assume old workflows are still active until proven otherwise
5. **Schedule triggers are powerful:** Any workflow with `*/5 * * * *` needs extra scrutiny

---

## Remediation Checklist

- [ ] Disable Approval Poller workflow in n8n UI
- [ ] Wait 10 minutes and verify no new auto-triggers
- [ ] Verify Phase 3 workflow is active and configured
- [ ] Test Phase 3 button flow (Ignore and Develop)
- [ ] Confirm no double execution or auto-triggering
- [ ] Export Approval Poller as backup JSON
- [ ] Delete Approval Poller workflow permanently
- [ ] Update Roadmap Phase 5 status
- [ ] Archive old workflow files in `deprecated/` folder
- [ ] Audit all active n8n workflows
- [ ] Document active workflows in project README
- [ ] Mark incident as RESOLVED in session note

---

## References

- **Session:** Session-2026-02-05.md
- **Roadmap:** CrewAI-Strategic-Intelligence-UX-Pivot.md
- **Workflow files:**
  - `n8n-approval-poller-workflow-v13.json` (problematic)
  - `n8n-slack-button-handler-phase3-fixed.json` (correct)
- **Prior session:** Session-2026-02-04-c-Phase3-Complete.md

---

*Incident Report Created: 2026-02-05*
*Next Action: User must disable Approval Poller workflow in n8n UI*
