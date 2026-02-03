# BLOCKER: n8n Workflow Context Passing Issue

**Date:** 2026-02-02
**Phase:** Criterion 5, Phase 5 (n8n Approval Poller Workflow)
**Status:** BLOCKED

## Problem Summary

The n8n workflow runs through all nodes successfully and posts to Slack, but the output shows:
```
Deliverable for [] Unknown
```

This indicates that `opp_id`, `opportunity_title`, and `deliverable_content` are empty/undefined by the time they reach the "Format Deliverable for Slack" node.

## What Works

1. **Catalyst agent works correctly** when run manually:
   ```bash
   ssh root@192.168.1.18 "cd /opt/crewai && source venv/bin/activate && python3 catalyst.py --digest-date 2026-02-02 --opportunity H1 --type plan"
   ```
   This produces full output with proper JSON between `[Catalyst] === OUTPUT START ===` and `=== OUTPUT END ===` markers.

2. **Approval parser works correctly:**
   ```bash
   ssh root@192.168.1.18 "cd /opt/crewai && python3 -c \"from tools.approval_parser import parse_approval_syntax; import json; print(json.dumps(parse_approval_syntax('approve H1')))\""
   ```
   Output: `{"valid": true, "action": "approve", "approvals": [{"opp_id": "H1", "type": "plan"}], "errors": []}`

3. **Slack API calls work** - messages are being posted to threads.

4. **SSH connectivity works** - commands execute on container 118.

5. **Opportunities file exists:**
   ```
   /opt/crewai/output/opportunities_2026-02-02.json
   ```
   Contains: H1, H2, W1

## What Doesn't Work

Context (digest_date, opp_id, deliverable_type, etc.) is being lost somewhere in the n8n node chain. The `approvals.jsonl` log showed entries with all empty values:
```json
{"timestamp": "...", "digest_date": "", "opportunity_id": "", "deliverable_type": "", "status": "delivered", "catalyst_file": ""}
```

## Attempted Fixes

1. **Updated catalyst.py** to include `digest_date`, `opp_id`, `deliverable_type` in its JSON output
2. **Modified SSH nodes** to pass context through stdout by including all fields in JSON output
3. **Changed Trigger Catalyst** to use `$('Extract Approvals').first().json.X` syntax to get values directly from earlier node
4. **Changed Parse Catalyst Output** to use `$('Extract Approvals').first().json.digest_ts`
5. **Cleared approvals.jsonl** to avoid duplicate detection

## Suspected Root Cause

The context is being lost early in the pipeline, likely in one of:
1. **Filter User Replies** - may not be extracting `digest_date` from Parse Digest Response correctly
2. **Parse Approval Syntax** (SSH) - the n8n template `{{ $json.X }}` values may be undefined
3. **Extract Approvals** - may be returning the debug object without proper fields

## Debugging Steps for Tomorrow

1. **Check Extract Approvals output** - Click on this node after running workflow and examine the output JSON
   - If it shows `DEBUG_NO_APPROVALS: true`, the approval parsing failed
   - If it shows proper fields, the issue is downstream

2. **Check Parse Approval Syntax output** - Examine `stdout` field
   - Should contain JSON with `valid`, `approvals`, `digest_date`, etc.

3. **Check Filter User Replies output** - Verify it has `digest_date`, `digest_ts` from digest

4. **Add explicit logging** - Could add a Slack post at each stage to see values

5. **Simplify the workflow** - Consider reducing number of SSH nodes and doing more in JavaScript Code nodes

## Files Involved

- `/Users/kyleschultz/.../claude-session/n8n-approval-poller-workflow.json` - Main workflow file
- `/opt/crewai/catalyst.py` - Catalyst agent (updated to include context in output)
- `/opt/crewai/tools/approval_parser.py` - Approval parser (works correctly)
- `/opt/crewai/output/opportunities_2026-02-02.json` - Today's opportunities
- `/opt/crewai/output/approvals.jsonl` - Approval log (cleared)

## Slack Channel

- Channel ID: `C0ABUP7MHMM`
- Bot Token: Embedded in workflow HTTP Request nodes

## SSH Access

- Container 118: `192.168.1.18`
- SSH Key: `~/.ssh/n8n_container118_rsa`
