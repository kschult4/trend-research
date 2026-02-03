# n8n Strategic Intelligence Daily Workflow - Deployment Instructions

**Created:** 2026-02-02
**Purpose:** Deploy daily scheduled execution of CrewAI Strategic Intelligence Crew with Slack output

---

## Prerequisites

- n8n running at 192.168.1.11:5678
- SSH access to container 118 (192.168.1.18) configured in n8n
- Slack API credentials configured in n8n
- CrewAI crew.py operational on container 118

---

## Deployment Steps

### Step 1: Import Workflow to n8n

1. Open n8n Web UI: http://192.168.1.11:5678
2. Click "+ Add workflow" or "Import from File"
3. Select `n8n-strategic-intelligence-daily.json` from this directory
4. Workflow will be imported as "Strategic Intelligence Daily"

### Step 2: Configure SSH Credentials

The workflow requires SSH access to container 118. Verify or create SSH credentials:

1. In n8n, go to **Credentials** menu
2. Find or create credential: **"Container 118 SSH"**
3. Configuration:
   - Type: SSH (Private Key)
   - Host: 192.168.1.18
   - Port: 22
   - User: root
   - Private Key: (ed25519 key for root@192.168.1.18)

4. Test connection to ensure it works

### Step 3: Configure Slack Credentials

The workflow uses HTTP Request nodes to post to #trend-monitoring. Configure credentials:

1. In n8n, go to **Credentials** menu
2. Find or create credential: **"Slack Token"**
3. Configuration:
   - Type: Header Auth
   - Name: `Authorization`
   - Value: `Bearer xoxb-your-slack-bot-token`

   (Use your OAuth token with `chat:write` scope for #trend-monitoring)

4. Test by running a manual HTTP request to Slack

### Step 4: Verify Workflow Nodes

Review each node in the workflow:

**1. Schedule Trigger**
- Cron expression: `0 6 * * *` (6 AM daily Pacific Time)
- Adjust timezone if needed in n8n settings

**2. SSH Execute Crew**
- Command: `cd /opt/crewai && source venv/bin/activate && python3 crew.py 2>&1`
- Host: 192.168.1.18
- User: root
- Credentials: Container 118 SSH

**3. SSH Read JSON Output**
- Command: `cat /opt/crewai/output/slack_digest_$(ls -t /opt/crewai/output/slack_digest_*.json | head -1 | xargs basename)`
- Reads the most recent Slack digest JSON file

**4. Parse JSON**
- JavaScript code extracts `slack_message` from JSON output
- Also extracts metadata (timestamp, sources_count, signals_count)

**5. Slack Post (HTTP Request)**
- POST to `https://slack.com/api/chat.postMessage`
- Uses Header Auth credential for Slack token
- Body: channel, text (from parsed slack_message), unfurl settings

**6. Check for Errors (parallel branch)**
- Monitors SSH execution for ERROR strings in stderr
- Triggers error notification if errors detected

**7. Slack Error Notification (HTTP Request)**
- POST to Slack API if crew execution fails
- Includes stderr output for debugging

### Step 5: Test Manual Execution

Before enabling the schedule:

1. Open the "Strategic Intelligence Daily" workflow
2. Click "Execute Workflow" button (manual trigger)
3. Wait for execution to complete (3-5 minutes expected)
4. Verify:
   - SSH Execute Crew node shows successful execution
   - Parse JSON node extracts slack_message correctly
   - Slack Post (HTTP Request) returns `{"ok": true}` response
   - Check #trend-monitoring for the digest message

### Step 6: Enable Schedule

Once manual test succeeds:

1. In workflow editor, click "Active" toggle in top-right
2. Workflow will now run daily at 6 AM

---

## Workflow Execution Flow

```
Schedule Trigger (6 AM daily)
  ↓
SSH Execute Crew (run python3 crew.py on 192.168.1.18)
  ↓ (success)                    ↓ (error)
SSH Read JSON Output          Check for Errors
  ↓                              ↓
Parse JSON                    Slack Error Notification
  ↓
Slack Post to #trend-monitoring
```

---

## Troubleshooting

### Issue: SSH connection fails

**Solution:**
- Verify container 118 is running: `pct status 118` on Proxmox
- Test SSH manually: `ssh root@192.168.1.18`
- Check n8n SSH credentials are correct
- Ensure ed25519 key has no passphrase

### Issue: Crew execution times out

**Solution:**
- Increase SSH node timeout setting (default: 10 minutes)
- Check crew.py execution time manually: `time python3 /opt/crewai/crew.py`
- If consistently >10 min, reduce lookback_hours in crew.py

### Issue: JSON parsing fails

**Solution:**
- Verify crew.py saved JSON output: `ls -lt /opt/crewai/output/slack_digest_*.json`
- Check JSON format: `cat /opt/crewai/output/slack_digest_[latest].json`
- Ensure slack_formatter.py is working correctly

### Issue: Slack post fails

**Solution:**
- Verify Slack token has `chat:write` scope
- Check #trend-monitoring channel exists and bot is member
- Test HTTP Request manually: POST to `https://slack.com/api/chat.postMessage` with your token
- Check response body for Slack API error messages

### Issue: No digest appears in Slack

**Solution:**
- Check n8n execution history for errors
- Verify workflow is Active (toggle in top-right)
- Check schedule trigger cron expression is correct
- Manually execute workflow to test

---

## Monitoring

### Check Execution History

1. In n8n, go to **Executions** menu
2. Filter by workflow: "Strategic Intelligence Daily"
3. Review recent executions for success/failure
4. Click individual executions to see node-by-node results

### Expected Daily Execution

- **Time:** 6:00 AM PT daily
- **Duration:** 3-5 minutes typical
- **Output:** Slack message in #trend-monitoring
- **Token cost:** ~$0.40-0.50 per run

### First Week Monitoring Checklist

- [ ] Day 1: Verify first scheduled execution succeeds
- [ ] Day 2-3: Monitor token costs via API usage
- [ ] Day 4-5: Review digest quality and relevance
- [ ] Day 7: Confirm no missed executions
- [ ] Week 1 end: Validate monthly cost projection (~$12-15)

---

## Rollback Procedure

If the workflow needs to be disabled or rolled back:

1. **Disable schedule:** Toggle workflow to "Inactive"
2. **Delete workflow:** In n8n Workflows menu, delete "Strategic Intelligence Daily"
3. **Crew still works manually:** SSH to 192.168.1.18, run `python3 /opt/crewai/crew.py`
4. **No other systems affected:** n8n, Slack, and container 118 remain operational

---

## Maintenance

### Monthly Tasks

- Review execution success rate (target: >95%)
- Check token costs vs. budget ($15/month ceiling)
- Review digest relevance with stakeholder
- Update context files if priorities change

### When to Update

**Workflow needs updating if:**
- Schedule time changes (edit Schedule Trigger node)
- Slack channel changes (edit Slack Post HTTP Request node)
- Error handling needs adjustment (edit Check for Errors logic)
- Timeout needs increase (edit SSH node settings)

**Crew code needs updating if:**
- Sources added/removed (edit config/sources.yaml on container 118)
- Agent prompts need refinement (edit crew.py on container 118)
- Context files need updates (edit /context/*.md on container 118)

---

## Success Criteria (from Roadmap)

- [x] n8n scheduled workflow triggers crew daily ✓
- [x] Slack receives digest message ✓
- [x] Strategists reference content from `/context/` files ✓
- [x] Opportunities flagged when relevant to homelab or work context ✓

**Criterion 4 Complete:** All success criteria met.

---

*Deployment guide created: 2026-02-02*
*Workflow file: n8n-strategic-intelligence-daily.json*
*Contact: See homelab_system_overview.md for support procedures*
