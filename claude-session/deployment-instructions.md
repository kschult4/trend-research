# Criterion 3 Phase 2: Deployment Instructions

**Status:** Ready for n8n deployment and Slack configuration
**Created:** 2026-02-01

---

## What's Been Completed

### 1. Workflow Design ✅
- Created enhanced workflow: `context-manager-workflow-phase2.json`
- Backed up Phase 1 workflow: `context-manager-workflow-phase1-backup.json`
- All 5 handlers implemented:
  - `/interests` (Phase 1)
  - `/newproject` (Phase 1)
  - `/updatebrief` (Phase 2 - NEW)
  - `/transcript` (Phase 2 - NEW)
  - `/recall` (Phase 2 - NEW)

### 2. Test Data Preparation ✅
- Created test project brief on container 118: `/context/briefs/test-project.md`
- Container 118 ready to receive operations
- SSH authentication already configured

---

## Deployment Steps Required

### Step 1: Deploy Workflow to n8n (Manual - UI Required)

**Important:** The n8n API does not properly register webhooks for workflows created/updated via REST API. We must use the Web UI.

1. **Access n8n:**
   - URL: http://192.168.1.11:5678 (internal) OR https://n8n.kyle-schultz.com (external)
   - Login with credentials

2. **Open Existing Workflow:**
   - Navigate to "Context Manager" workflow
   - Click "..." menu → "Export Workflow" (optional second backup)

3. **Import Enhanced Workflow:**
   - Click "..." menu → "Import from File"
   - Select: `/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Software Projects/trend-research/claude-session/context-manager-workflow-phase2.json`
   - Choose: "Replace current workflow" (NOT create new)
   - This preserves the webhook URL

4. **Verify Workflow:**
   - Check all nodes are connected properly
   - Verify SSH credential "Container 118 SSH" is linked to all SSH nodes
   - Ensure webhook path remains "context-manager"

5. **Activate Workflow:**
   - Toggle workflow to "Active" (if not already)
   - This registers the webhook endpoint

---

### Step 2: Configure New Slack Slash Commands

**Access Slack App Configuration:**
- URL: https://api.slack.com/apps
- Find app: "Trend Monitoring"

**Add Three New Slash Commands:**

1. **Update Brief Command:**
   - Command: `/updatebrief`
   - Request URL: `https://n8n.kyle-schultz.com/webhook/context-manager`
   - Short Description: "Update an existing project brief"
   - Usage Hint: `project-name: update content`

2. **Transcript Command:**
   - Command: `/transcript`
   - Request URL: `https://n8n.kyle-schultz.com/webhook/context-manager`
   - Short Description: "Save a meeting transcript"
   - Usage Hint: `meeting-name: transcript content`

3. **Recall Command:**
   - Command: `/recall`
   - Request URL: `https://n8n.kyle-schultz.com/webhook/context-manager`
   - Short Description: "Search across context files"
   - Usage Hint: `search query`

**Reinstall App (if needed):**
- If commands don't appear in Slack, reinstall the app to workspace
- Settings → Install App → Reinstall to Workspace

---

## Testing Plan

### Phase 1: Local Curl Tests (Optional Pre-Check)

Test webhook directly before Slack integration:

```bash
# Test Update Brief
curl -X POST https://n8n.kyle-schultz.com/webhook/context-manager \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "command=/updatebrief&text=test-project: Added deployment instructions&user_name=kyle"

# Verify on container 118
ssh root@192.168.1.18 "cat /context/briefs/test-project.md"

# Test Transcript
curl -X POST https://n8n.kyle-schultz.com/webhook/context-manager \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "command=/transcript&text=team-standup: Discussed Criterion 3 completion&user_name=kyle"

# Verify on container 118
ssh root@192.168.1.18 "ls -la /context/transcripts/ && cat /context/transcripts/2026-02-01-team-standup.md"

# Test Recall
curl -X POST https://n8n.kyle-schultz.com/webhook/context-manager \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "command=/recall&text=deployment&user_name=kyle"
```

### Phase 2: Slack End-to-End Tests

Test each command from Slack channel:

1. **Test Update Brief:**
   ```
   /updatebrief test-project: Testing from Slack interface
   ```
   - Expected: Confirmation message in Slack
   - Verify: `ssh root@192.168.1.18 "cat /context/briefs/test-project.md"`

2. **Test Transcript:**
   ```
   /transcript weekly-sync: Reviewed progress on Criterion 3, discussed next steps for Criterion 4
   ```
   - Expected: Confirmation message in Slack
   - Verify: `ssh root@192.168.1.18 "ls /context/transcripts/"`

3. **Test Recall:**
   ```
   /recall Criterion
   ```
   - Expected: Search results in Slack (formatted code block)
   - Should find matches in briefs and transcripts

4. **Test Phase 1 Commands (Regression):**
   ```
   /interests Testing Phase 2 deployment
   /newproject criterion-4-prep
   ```
   - Expected: Both commands still work
   - Verify no regressions

5. **Test Error Handling:**
   ```
   /updatebrief nonexistent-project: This should fail
   ```
   - Expected: Error message about project not found
   - Verify graceful error handling

---

## Rollback Plan

If issues occur:

1. **Rollback n8n Workflow:**
   - Import `context-manager-workflow-phase1-backup.json`
   - Replace current workflow
   - Reactivate

2. **Remove Slack Commands:**
   - Delete `/updatebrief`, `/transcript`, `/recall` from Slack app
   - Phase 1 commands continue working

---

## Success Criteria Checklist

- [ ] Workflow deployed to n8n
- [ ] Webhook registered and active
- [ ] Three new Slack commands configured
- [ ] `/updatebrief` works end-to-end
- [ ] `/transcript` works end-to-end
- [ ] `/recall` works end-to-end
- [ ] Phase 1 commands still work (no regression)
- [ ] Error handling validated
- [ ] Documentation updated

---

## Next Session Tasks (After Deployment)

Once deployed and tested:
1. Update Session note with verification results
2. Update Roadmap progress tracker (mark Criterion 3 complete)
3. Update `homelab_system_overview.md` with all 5 commands
4. Document command reference in Roadmap
5. Session reconciliation and closure
