# Phase 3: Button Handler Deployment Guide

**Created:** 2026-02-04
**Status:** Ready for deployment

---

## Overview

This guide covers deploying the Slack button handler workflow that processes [Develop] and [Ignore] button clicks from Strategic Intelligence messages.

## Architecture

```
Slack Button Click
  ↓
n8n Webhook (slack-button-handler)
  ↓
Parse Action (develop_H1 → {action: develop, id: H1})
  ↓
Route by Action Type
  ↓                    ↓
[Develop]          [Ignore]
  ↓                    ↓
SSH: Run Catalyst   SSH: Append Log
  ↓                    ↓
Parse Output        Update Slack
  ↓                    ↓
Update Slack        (dismissed)
  ↓
Obsidian Sync
(via Syncthing)
```

## Step 1: Import Workflow into n8n

1. Open n8n web UI: `https://n8n.kyle-schultz.com`

2. Click **Workflows** → **Add workflow** → **Import from File**

3. Select file: `n8n-slack-button-handler-phase3.json`

4. Verify imported nodes:
   - Webhook Trigger
   - Parse Button Action (Code)
   - Route by Action (Switch)
   - Run Catalyst (SSH)
   - Parse Catalyst Output (Code)
   - Update Slack - Develop Success (HTTP Request)
   - Log Ignore Action (SSH)
   - Update Slack - Ignored (HTTP Request)
   - Error Handler (HTTP Request)
   - Respond to Slack (Respond to Webhook)

5. **Activate** the workflow

## Step 2: Get Webhook URL

1. Click on the **Webhook Trigger** node

2. Copy the **Production URL**, should be:
   ```
   https://n8n.kyle-schultz.com/webhook/slack-button-handler
   ```

3. Keep this URL for next step

## Step 3: Configure Slack App

1. Go to https://api.slack.com/apps

2. Select your **Strategic Intelligence** app

3. Navigate to **Interactivity & Shortcuts**

4. Enable **Interactivity**

5. Set **Request URL** to:
   ```
   https://n8n.kyle-schultz.com/webhook/slack-button-handler
   ```

6. Click **Save Changes**

## Step 4: Verify Container 118 Prerequisites

SSH to Container 118 and verify:

```bash
ssh root@192.168.1.18

# 1. Verify Catalyst has been modified with markdown output
grep -A 5 "homelab-outputs" /opt/crewai/catalyst.py

# 2. Verify homelab-outputs directory exists
ls -la /opt/crewai/homelab-outputs/

# 3. Verify opportunities mapping exists for today
ls -la /opt/crewai/output/opportunities_$(date +%Y-%m-%d).json

# 4. Verify ignored_opportunities.log location
mkdir -p /opt/crewai/logs/
touch /opt/crewai/logs/ignored_opportunities.log
```

## Step 5: Test [Ignore] Button

1. In Slack, find a Strategic Intelligence message with buttons

2. Click **[Ignore]** on any opportunity (e.g., H2)

3. **Expected behavior:**
   - Slack message immediately shows "Processing..."
   - Within 2-3 seconds, message updates to:
     ```
     🚫 [H2] marked as ignored
     No further action will be taken.
     ```
   - Original buttons are removed

4. **Verify log file:**
   ```bash
   ssh root@192.168.1.18
   tail /opt/crewai/logs/ignored_opportunities.log

   # Should show:
   # 2026-02-04T10:30:45.123Z,H2,kyle.schultz
   ```

## Step 6: Test [Develop] Button

1. In Slack, click **[Develop]** on a homelab opportunity (e.g., H1)

2. **Expected behavior:**
   - Slack message immediately shows "Processing..."
   - Catalyst runs (30-60 seconds)
   - Message updates to:
     ```
     ✅ Technical Plan generated for [H1]

     [Opportunity Title]

     📁 Check Obsidian: `_crewai-outputs/`

     File will sync within ~15 seconds.
     ```

3. **Monitor n8n execution:**
   - Open n8n → Executions
   - Click the running execution
   - Watch nodes turn green as they complete
   - Verify SSH output contains `[Catalyst] === OUTPUT START ===`

4. **Verify Catalyst JSON output:**
   ```bash
   ssh root@192.168.1.18
   ls -la /opt/crewai/output/catalyst_$(date +%Y-%m-%d)_H1_plan.json
   cat /opt/crewai/output/catalyst_$(date +%Y-%m-%d)_H1_plan.json | jq .
   ```

5. **Verify markdown file created:**
   ```bash
   ls -la /opt/crewai/homelab-outputs/*.md
   cat /opt/crewai/homelab-outputs/[filename]-technical-plan.md
   ```

6. **Verify Syncthing sync:**
   - Wait 15 seconds
   - Open Obsidian vault folder on Mac:
     ```
     /Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Obsidian/The Good Stuff/Homelab/_crewai-outputs/
     ```
   - Verify markdown file appears
   - Open in Obsidian to verify formatting

## Error Scenarios

### Error: Opportunity Not Found

**Symptom:** Slack shows "❌ Error: Opportunity H1 not found in mapping"

**Cause:** No opportunities file for the digest date

**Fix:**
```bash
# Check what dates have opportunity files
ls -la /opt/crewai/output/opportunities_*.json

# Either use an opportunity from an existing date, or wait for next daily run
```

### Error: Catalyst Timeout

**Symptom:** n8n execution shows SSH node stuck for >120 seconds

**Cause:** Catalyst agent taking too long

**Fix:**
- Check Container 118 CPU/memory usage
- Review Catalyst logs: `ssh root@192.168.1.18 "tail -100 /opt/crewai/logs/*.log"`
- Consider increasing n8n SSH node timeout

### Error: File Not Syncing to Obsidian

**Symptom:** Markdown file exists on Container 118 but not appearing in Obsidian

**Cause:** Syncthing sync issue

**Fix:**
```bash
# 1. Check Syncthing status on Container 118
curl -H "X-API-Key: YOUR_API_KEY" http://192.168.1.18:8384/rest/system/status | jq .

# 2. Check Syncthing status on Mac
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8384/rest/system/status | jq .

# 3. Force rescan
curl -X POST -H "X-API-Key: YOUR_API_KEY" http://192.168.1.18:8384/rest/db/scan?folder=qiukt-rurae
```

## Phase 3 Completion Checklist

- [ ] Workflow imported and activated in n8n
- [ ] Slack app configured with webhook URL
- [ ] Container 118 prerequisites verified
- [ ] [Ignore] button tested successfully
- [ ] [Develop] button tested successfully
- [ ] Technical Plan appears in Obsidian
- [ ] Session notes updated
- [ ] Roadmap updated with Phase 3 completion

## Next Phase: Work Item Deliverables

Once Phase 3 is verified, the roadmap includes:

**Phase 4: Work Item Handlers**
- Implement [Develop] button for W IDs (work opportunities)
- Generate Leadership Brief or Client Slide
- Email deliverable instead of Syncthing
- Configure email credentials and templates

---

*Generated as part of CrewAI Strategic Intelligence UX Pivot - Phase 3*
