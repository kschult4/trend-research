# Phase 3 Verification Testing Plan
**Session:** 2026-02-05
**Purpose:** Verify CrewAI UX Pivot Phase 3 (Button Action Handlers) is fully operational

---

## Pre-Verification Checklist

Before beginning verification tests, confirm these prerequisites are met:

### 1. n8n Workflow Import Status
- [ ] Workflow `n8n-slack-button-handler-phase3-fixed.json` imported into n8n
- [ ] Webhook URL configured: `https://n8n.kyle-schultz.com/webhook/slack-button-handler`
- [ ] Workflow is ACTIVE (not paused)
- [ ] SSH credentials "Container 118 SSH" (ID=1) are configured and working

**How to check:**
```bash
# Access n8n UI
open http://192.168.1.11:5678

# Look for workflow named "Slack Button Handler - Phase 3"
# Status should show green "Active" indicator
```

### 2. Container 118 State
- [ ] Container running and accessible
- [ ] Catalyst modified with markdown output (backup exists)
- [ ] Directory `/opt/crewai/homelab-outputs/` exists
- [ ] Directory `/opt/crewai/logs/` exists for ignore log

**How to check:**
```bash
# From Proxmox host
pct status 118

# Via SSH (if configured)
ssh root@192.168.1.18 "ls -la /opt/crewai/homelab-outputs/"
ssh root@192.168.1.18 "ls -la /opt/crewai/logs/"
```

### 3. Syncthing Sync Status
- [ ] Syncthing running on Container 118
- [ ] Syncthing running on Mac
- [ ] Folder `homelab-outputs/` sync configured and "Up to Date"

**How to check:**
```bash
# Container 118 Syncthing Web UI
open http://192.168.1.18:8384

# Mac Syncthing Web UI
open http://localhost:8384

# Check folder qiukt-rurae shows "Up to Date" on both sides
```

### 4. Daily Digest Available
- [ ] Today's or recent digest posted to Slack #trend-monitoring
- [ ] Messages have [Develop] and [Ignore] buttons
- [ ] At least one H ID (homelab opportunity) is present

**Note:** If no recent digest exists, you may need to wait for tomorrow's 6 AM run or trigger manually.

---

## Test 1: [Ignore] Button Verification

**Goal:** Confirm [Ignore] button logs to CSV and updates Slack message

### Test Steps

1. **Identify test opportunity**
   - Navigate to Slack #trend-monitoring
   - Find a homelab opportunity (H ID) you want to test with
   - Note the opportunity ID (e.g., "H1")

2. **Click [Ignore] button**
   - Click the [Ignore] button on the Slack message
   - Observe Slack message behavior

3. **Expected immediate behavior (< 3 seconds):**
   - Message updates to show "⏳ Processing..."
   - No timeout or caution icon appears

4. **Expected completion behavior (3-5 seconds):**
   - Message updates to show "🚫 Opportunity marked as ignored"
   - OR similar dismissal message
   - Original opportunity details may be replaced or hidden

5. **Verify log file created**
   ```bash
   # Via SSH to Container 118
   ssh root@192.168.1.18 "cat /opt/crewai/logs/ignored_opportunities.log"

   # Expected output format:
   # 2026-02-05T10:30:45.123Z,H1,U01ABC123
   # (timestamp, opportunity_id, slack_user_id)
   ```

6. **Check n8n execution log**
   - Open n8n UI: http://192.168.1.11:5678
   - Navigate to "Executions" tab
   - Find most recent execution of "Slack Button Handler - Phase 3"
   - Verify execution shows SUCCESS status
   - Review execution data to confirm [Ignore] path was taken

### Success Criteria
- ✅ Slack message updates without timeout
- ✅ Message shows dismissal confirmation
- ✅ Log file contains new entry with correct timestamp and ID
- ✅ n8n execution log shows successful completion

### Troubleshooting
- **Slack shows caution icon:** Webhook took >3 seconds to respond
  - Check n8n workflow uses `responseMode: "responseNode"`
  - Check "Respond Immediately" node is first after webhook
- **No n8n execution log:** Webhook URL may be incorrect
  - Verify Slack app webhook configuration
  - Check n8n webhook node URL matches
- **Log file not created:** SSH command or permissions issue
  - Check SSH credentials in n8n are correct
  - Check directory `/opt/crewai/logs/` exists and is writable

---

## Test 2: [Develop] Button Verification

**Goal:** Confirm [Develop] button triggers Catalyst and syncs Technical Plan to Obsidian

### Test Steps

1. **Identify test opportunity**
   - Navigate to Slack #trend-monitoring
   - Find a DIFFERENT homelab opportunity (H ID) than Test 1
   - Note the opportunity ID (e.g., "H2")
   - Note the opportunity title for file matching

2. **Pre-check Obsidian outputs folder**
   ```bash
   # Check current contents
   ls -la "/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Obsidian/The Good Stuff/Homelab/_crewai-outputs/"

   # Note file count and names before test
   ```

3. **Click [Develop] button**
   - Click the [Develop] button on the Slack message
   - Observe Slack message behavior

4. **Expected immediate behavior (< 3 seconds):**
   - Message updates to show "⏳ Processing..."
   - No timeout or caution icon appears

5. **Expected processing behavior (30-60 seconds):**
   - Message continues to show "Processing..." status
   - Wait patiently for Catalyst to complete

6. **Expected completion behavior (after 30-60 seconds):**
   - Message updates to show "✅ Technical Plan generated"
   - OR similar success confirmation message
   - Message may include link or reference to output

7. **Verify Catalyst execution**
   ```bash
   # Via SSH to Container 118
   ssh root@192.168.1.18 "ls -lt /opt/crewai/homelab-outputs/ | head -5"

   # Expected: New markdown file with today's timestamp
   # Filename format: {sanitized-title}-technical-plan.md
   ```

8. **Verify opportunities mapping file**
   ```bash
   # Check today's opportunities file exists
   ssh root@192.168.1.18 "ls -la /opt/crewai/output/opportunities_*.json | tail -1"

   # This file should contain the opportunity data Catalyst needs
   ```

9. **Verify Syncthing sync (wait 15-30 seconds)**
   ```bash
   # Check Obsidian outputs folder
   ls -lt "/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Obsidian/The Good Stuff/Homelab/_crewai-outputs/" | head -5

   # Expected: Same markdown file from step 7 now appears in Obsidian
   ```

10. **Open and inspect Technical Plan**
    - Open the new markdown file in Obsidian
    - Verify file structure matches expected format:
      ```markdown
      # {Opportunity Title}
      **Generated:** 2026-02-05 HH:MM
      **Opportunity ID:** H2
      **Type:** Technical Plan
      ---
      {Technical Plan content from Catalyst}
      ---
      *Generated by Catalyst from Strategic Intelligence Digest YYYY-MM-DD*
      ```
    - Verify content is relevant to the opportunity selected
    - Verify no JSON artifacts or parsing errors

11. **Check n8n execution log**
    - Open n8n UI: http://192.168.1.11:5678
    - Navigate to "Executions" tab
    - Find most recent execution of "Slack Button Handler - Phase 3"
    - Verify execution shows SUCCESS status
    - Review execution data:
      - Confirm [Develop] path was taken
      - Confirm Catalyst SSH command executed
      - Confirm JSON parsing step succeeded
      - Confirm Slack update step succeeded

### Success Criteria
- ✅ Slack message updates without timeout
- ✅ Processing acknowledgment appears immediately
- ✅ Success confirmation appears after 30-60 seconds
- ✅ Markdown file created in `/opt/crewai/homelab-outputs/`
- ✅ File syncs to Obsidian `_crewai-outputs/` within 30 seconds
- ✅ Markdown file has correct structure and metadata
- ✅ Content is relevant and properly formatted
- ✅ n8n execution log shows successful completion

### Troubleshooting

**Slack timeout or caution icon:**
- Webhook response too slow
- Check `responseMode: "responseNode"` in n8n workflow
- Check "Respond Immediately" node exists and is positioned correctly

**Processing never completes:**
- Catalyst may have crashed or hung
- Check n8n execution log for SSH command errors
- SSH to Container 118 and check Catalyst manually:
  ```bash
  ssh root@192.168.1.18
  cd /opt/crewai
  source venv/bin/activate

  # Find today's digest date
  ls -lt output/opportunities_*.json | head -1

  # Run Catalyst manually
  python3 catalyst.py --digest-date 2026-02-05 --opportunity H2 --type plan
  ```

**Markdown file not created:**
- Check Catalyst code has Phase 3 modifications
- Verify backup exists: `/opt/crewai/catalyst.py.backup-before-phase3`
- Check file permissions on `homelab-outputs/` directory
- Review Catalyst output for errors

**File created but not syncing to Obsidian:**
- Check Syncthing status on both sides (Container 118 and Mac)
- Verify folder `qiukt-rurae` shows "Up to Date"
- Check Syncthing logs for sync errors
- Verify folder path configuration matches:
  - Container: `/opt/crewai/homelab-outputs/`
  - Mac: `_crewai-outputs/` in Obsidian vault
- Try creating test file manually and verify it syncs

**Markdown file malformed or has JSON artifacts:**
- Catalyst JSON parsing may have failed
- Check n8n execution log "Parse Catalyst Output" node
- Verify Catalyst uses JSON markers: `=== OUTPUT START ===` and `=== OUTPUT END ===`
- Inspect Catalyst stdout for parsing issues

**n8n execution failed:**
- Check SSH credentials are correct (ID=1, "Container 118 SSH")
- Verify Container 118 is accessible on 192.168.1.18
- Check opportunities file exists for today's date
- Review execution error details in n8n UI

---

## Test 3: End-to-End Flow Verification

**Goal:** Confirm complete workflow from daily digest to deliverable in Obsidian

### Test Steps

1. **Wait for or trigger daily digest**
   - If testing today, wait for 6 AM scheduled run
   - OR trigger manually via n8n "Strategic Intelligence Daily v2" workflow

2. **Verify digest posts to Slack**
   - Multiple individual messages (not one giant digest)
   - Each message has opportunity title, description, relevance
   - Buttons [Develop] and [Ignore] present on all messages
   - Homelab opportunities marked with H IDs

3. **Perform both button actions**
   - Pick one H ID → Click [Ignore] → Verify Test 1 criteria
   - Pick different H ID → Click [Develop] → Verify Test 2 criteria

4. **Verify no workflow conflicts**
   - Both workflows should complete successfully
   - n8n execution logs show no errors
   - No orphaned processes or hung executions

5. **Verify operational capture**
   - Ignored opportunities logged to CSV
   - Technical Plans delivered to Obsidian
   - All files have correct timestamps and IDs
   - Syncthing sync completes without conflicts

### Success Criteria
- ✅ Daily digest produces clean, readable individual messages
- ✅ Both [Ignore] and [Develop] buttons work independently
- ✅ Multiple button clicks don't interfere with each other
- ✅ All artifacts (logs, markdown files) are captured correctly
- ✅ Syncthing sync remains stable throughout testing
- ✅ No manual intervention required at any step

---

## Post-Verification Checklist

After completing all tests, confirm these outcomes:

### Phase 3 Completion Evidence
- [ ] Test 1 passed: [Ignore] button logs to CSV and updates Slack
- [ ] Test 2 passed: [Develop] button triggers Catalyst and syncs to Obsidian
- [ ] Test 3 passed: End-to-end flow works without manual intervention
- [ ] All n8n execution logs show SUCCESS status
- [ ] No Slack timeout or caution icons observed
- [ ] Technical Plans are readable and properly formatted in Obsidian
- [ ] Syncthing sync completes within 30 seconds consistently

### Documentation Updates Required
- [ ] Update roadmap Phase 3 status from "pending verification" to "COMPLETE"
- [ ] Update session note with verification results
- [ ] Capture any unexpected issues or edge cases discovered
- [ ] Document actual timing measurements (Catalyst runtime, sync time)

### Blockers or Issues Found
If any tests FAILED, document:
- Which test failed and at what step
- Error messages or unexpected behavior observed
- Troubleshooting steps attempted
- Whether issue is blocking or minor

---

## Phase 4 Preview (If Phase 3 Verified)

If all Phase 3 tests pass, Phase 4 can begin. Here's what Phase 4 entails:

### Phase 4 Scope: Work Item Deliverables

**Goal:** Enable work opportunities (W IDs) to generate deliverables sent via email

**Key Changes:**
1. **Second button interaction for work items**
   - Click [Develop] on W ID → Show new buttons: [Executive Brief] [Sales Slide]
   - Instead of immediate Catalyst execution, user chooses deliverable type

2. **Email delivery setup**
   - Configure SMTP credentials in n8n (Gmail, SendGrid, or similar)
   - Modify webhook workflow to send email instead of writing to Obsidian
   - Email subject: "Work Opportunity: {title} - {deliverable type}"
   - Email body: Formatted markdown or HTML from Catalyst output

3. **Catalyst deliverable types**
   - "brief" → Executive Brief (business context, strategic implications)
   - "slide" → Sales Slide (single-slide deck content, visual layout suggestions)
   - Work items do NOT use "plan" type (reserved for homelab H IDs)

4. **Workflow modifications**
   - Add conditional logic: If opportunity starts with "W" → show deliverable buttons
   - Add email sending node after Catalyst execution for work items
   - Keep homelab path unchanged (H IDs still write to Obsidian)

**Estimated effort:** 2-3 hours (email setup, workflow modification, testing)

**Prerequisites:**
- Phase 3 fully verified and stable
- Email credentials available (SMTP host, port, username, password)
- Test email address for verification
- Work opportunities appearing in daily digest (W IDs present)

**Risks:**
- Email deliverability issues (spam filters, authentication)
- SMTP credentials security (must be stored safely in n8n)
- Second button interaction may complicate Slack UX (needs testing)

**Decision needed:** Proceed with Phase 4 implementation or defer?

---

## Next Steps

**If Phase 3 verification PASSES:**
1. Update roadmap to mark Phase 3 as COMPLETE ✅
2. Update session note with verification evidence
3. Present Phase 4 scope to user for approval
4. If approved, begin Phase 4 implementation
5. If deferred, proceed to Phase 5 cleanup

**If Phase 3 verification FAILS:**
1. Document specific failures and error messages
2. Troubleshoot issues using guides in `claude-session/`
3. Fix blockers and re-test
4. Update session note with blocker details
5. Mark session status as BLOCKED with clear next steps

---

*Testing Plan Created: 2026-02-05*
*Roadmap: CrewAI-Strategic-Intelligence-UX-Pivot.md*
*Session: Session-2026-02-05.md*
