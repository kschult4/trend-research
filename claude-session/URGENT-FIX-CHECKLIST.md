# URGENT: Fix Auto-Triggering - Action Checklist
**Issue:** Catalyst auto-running without button clicks
**Root Cause:** Old "Approval Poller" workflow still active
**Priority:** HIGH - Stop unintended AI operations

---

## IMMEDIATE ACTION (Do This Now)

### Step 1: Disable the Approval Poller (5 minutes)

1. Open n8n UI: http://192.168.1.11:5678

2. Find workflow named: **"Approval Poller and Catalyst Trigger"**
   - OR search for workflows with "Approval" in name
   - OR look for workflows with schedule trigger (clock icon)

3. Open the workflow

4. Click the **toggle/pause button** to set to INACTIVE
   - Should see "Inactive" or red/grey indicator

5. **VERIFY:** Status bar shows workflow is now inactive

### Step 2: Wait and Watch (10 minutes)

- Wait 10 minutes (2 polling cycles)
- Monitor Slack #trend-monitoring
- **Expected:** NO new auto-generated messages appear
- **If new messages appear:** Workflow may not be disabled, double-check Step 1

---

## NEXT ACTIONS (After Verification)

### Step 3: Verify Phase 3 Workflow is Active

1. In n8n UI, find: **"Slack Button Handler - Phase 3"**
   - OR workflow with webhook trigger (webhook icon)

2. **If workflow exists:**
   - Verify it's ACTIVE (green indicator)
   - Note webhook URL: should be `/webhook/slack-button-handler`

3. **If workflow does NOT exist:**
   - You need to import it first
   - File location: `/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Software Projects/trend-research/claude-session/n8n-slack-button-handler-phase3-fixed.json`
   - Follow import instructions in `IMPORT-INSTRUCTIONS-phase3.md`

### Step 4: Test Phase 3 Buttons (15 minutes)

**Prerequisites:**
- Approval Poller is DISABLED
- Phase 3 workflow is ACTIVE
- You have a recent digest in Slack with buttons

**Test [Ignore] button:**
1. Click [Ignore] on any homelab opportunity
2. Verify message updates to "Processing..." then "Ignored"
3. Check log file: `ssh root@192.168.1.18 "cat /opt/crewai/logs/ignored_opportunities.log"`
4. Should see new entry with timestamp and ID

**Test [Develop] button:**
1. Click [Develop] on a DIFFERENT homelab opportunity
2. Verify message updates to "Processing..." (immediate)
3. Wait 30-60 seconds
4. Verify message updates to "✅ Technical Plan generated"
5. Check Obsidian folder: `_crewai-outputs/` should have new markdown file
6. Open file and verify structure is correct

**Success criteria:**
- Both buttons work correctly
- Only ONE execution per button click (check n8n execution logs)
- No auto-triggering occurs while you wait

### Step 5: Permanent Cleanup (After Testing)

1. **Export Approval Poller as backup:**
   - In n8n UI, open Approval Poller workflow
   - Click "..." menu → "Download"
   - Save as: `BACKUP-approval-poller-deleted-2026-02-05.json`

2. **Delete Approval Poller permanently:**
   - In workflow list, click "..." menu on Approval Poller
   - Select "Delete"
   - Confirm deletion

3. **Verify it's gone:**
   - Workflow no longer appears in n8n workflow list
   - Check execution history - no new executions

---

## What to Report Back

After completing Steps 1-4, please confirm:

1. **Approval Poller status:** Disabled or Deleted?
2. **Auto-triggering stopped:** Did you see any new auto-generated messages in the 10-minute wait?
3. **Phase 3 workflow status:** Active and imported?
4. **Button testing results:**
   - [Ignore] button: Pass / Fail / Not tested
   - [Develop] button: Pass / Fail / Not tested
5. **Any errors or unexpected behavior?**

---

## If Something Goes Wrong

**Problem: Can't find Approval Poller workflow**
- It may already be deleted
- Check workflow list for ANY workflow with schedule trigger
- Check n8n execution history for recent "Approval Poller" runs

**Problem: Phase 3 workflow doesn't exist**
- You need to import it first
- See: `IMPORT-INSTRUCTIONS-phase3.md`
- File: `n8n-slack-button-handler-phase3-fixed.json`

**Problem: Buttons don't work after disabling Poller**
- Check Phase 3 workflow is ACTIVE
- Check webhook URL is configured in Slack app
- Check n8n execution logs for errors
- See full troubleshooting guide: `PHASE3-VERIFICATION-PLAN.md`

**Problem: Still seeing auto-triggers**
- Check if there are OTHER workflows with schedule triggers
- Review all active workflows in n8n
- Check Container 118 for cron jobs: `ssh root@192.168.1.18 "crontab -l"`

---

## Files for Reference

- **Incident report:** `INCIDENT-AUTO-TRIGGER-2026-02-05.md`
- **Verification plan:** `PHASE3-VERIFICATION-PLAN.md`
- **Import instructions:** `IMPORT-INSTRUCTIONS-phase3.md`
- **Session note:** `02_Sessions/Session-2026-02-05.md`

---

**Time estimate:** 30 minutes total
**Priority:** Complete Step 1 immediately, Steps 2-5 within next hour

*Checklist created: 2026-02-05*
