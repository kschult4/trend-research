# Next Session Handoff: Criterion 5 Phase 5-6

**Date:** 2026-02-02
**Progress:** 4 of 6 phases complete (67%)
**Remaining Work:** 5 hours estimated

---

## Quick Context

You are continuing Criterion 5 implementation for the CrewAI Strategic Intelligence Crew project. The approval flow enables users to approve opportunities from the daily digest and receive Catalyst-generated deliverables.

**Project Folder:** `/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Software Projects/trend-research`
**Container:** 118 at 192.168.1.18 (`/opt/crewai`)
**Vault:** `/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Obsidian/The Good Stuff/Homelab/`

---

## What's Complete (Phases 1-4)

### Phase 1: Strategist Formatting ✅
- Strategists output structured opportunities with `### Opportunity:` headers
- Format: Title, Relevance, Signal, Next Steps subsections
- File: `/opt/crewai/crew.py` (modified)

### Phase 2: Opportunity Parsing ✅
- Parser extracts opportunities and assigns numbered IDs (H1, H2, W1, W2)
- Slack digest displays opportunities with `[H1]`, `[W1]` formatting
- Opportunity mapping saved to `output/opportunities_YYYY-MM-DD.json`
- Files: `/opt/crewai/tools/opportunity_parser.py` (new), `tools/slack_formatter.py` (modified)

### Phase 3: Catalyst Agent ✅
- Standalone script generates 3 deliverable types:
  - Technical Plan (homelab opportunities)
  - Leadership Brief (work opportunities)
  - Client Slide (work opportunities)
- CLI: `python3 catalyst.py --digest-date YYYY-MM-DD --opportunity H1 --type plan`
- File: `/opt/crewai/catalyst.py` (new)
- All 3 types tested successfully

### Phase 4: Approval Parser ✅
- Parses approval syntax: `approve H1`, `approve W1 brief`, `approve H1, W2 slide`
- Validates against opportunity mapping
- 23 unit tests (all passing)
- File: `/opt/crewai/tools/approval_parser.py` (new)

---

## What's Next (Phases 5-6)

### Phase 5: n8n Approval Poller Workflow (3 hours)

**Goal:** Create n8n workflow to poll Slack for approvals and trigger Catalyst

**Workflow Name:** "Approval Poller and Catalyst Trigger"

**Key Nodes (16 total):**
1. Schedule Trigger (every 5 minutes)
2. Get Today's Digest (Slack conversations.history)
3. Check Digest Found (IF node)
4. Get Replies (Slack conversations.replies)
5. Parse Approvals (SSH → approval_parser.py)
6. Check for Duplicates (SSH → grep approvals.jsonl)
7. Filter New Approvals (IF node)
8. Log Approval (SSH → append to approvals.jsonl)
9. Trigger Catalyst (SSH → catalyst.py)
10. Parse Catalyst Output (Code node)
11. Check Catalyst Success (IF node)
12. Format Deliverable (Code node)
13. Post to Slack Thread (Slack chat.postMessage)
14. Update Approval Log (SSH → append delivery status)
15-16. Error handlers (invalid syntax, Catalyst failure)

**Reference:** See `/claude-session/criterion-5-implementation-plan.md` lines 997-1100 for detailed node configuration

### Phase 6: Integration Testing (2 hours)

**Goal:** End-to-end validation of approval flow

**Test Scenarios:**
- Approve homelab opportunity (H1) → Technical Plan posted to Slack
- Approve work opportunity with brief (W1 brief) → Leadership Brief posted
- Approve work opportunity with slide (W2 slide) → Client Slide posted
- Multiple approvals (H1, W1 brief) → Both deliverables posted
- Invalid syntax (approve W1) → Help message posted
- Non-existent opportunity (approve H99) → Error message posted
- Duplicate approval → Ignored (no duplicate deliverable)
- Dismiss syntax (dismiss H1) → Logged, no deliverable

---

## Prerequisites Before Starting Phase 5

**Must Gather:**
1. **Slack Channel ID** for #trend-monitoring
   - Get via Slack API or channel URL
   - Format: `C01ABC123`
   - Used in: n8n Slack API nodes

2. **Kyle's Slack User ID**
   - Get via Slack API or profile
   - Format: `U01XYZ789`
   - Used in: Reply filtering (only parse Kyle's replies)

3. **Verify SSH Access**
   - Test: `ssh root@192.168.1.18 "cd /opt/crewai && ls"`
   - Ensure n8n has SSH credentials saved
   - Container IP: 192.168.1.18

4. **Create Approvals Log**
   - Run: `ssh root@192.168.1.18 "touch /opt/crewai/output/approvals.jsonl"`
   - Used for: Duplicate detection

5. **Verify Slack API Token**
   - Scopes needed: `conversations.history`, `conversations.replies`, `chat.postMessage`
   - Credential name in n8n: "Slack Trend Reporting Token"

---

## Key Architecture Decisions (Made in This Session)

1. **Polling (not Events API):** 5-10 min latency acceptable for strategic intelligence
2. **Single Digest (not Threaded):** Opportunities numbered in one message with `[H1]`, `[W1]` IDs
3. **Reply Syntax (not Reactions):** Parse text like `approve H1, W1 brief`
4. **Three Deliverable Types:** Plan (homelab), Brief (work), Slide (work)
5. **Type Enforcement:** Homelab defaults to "plan", Work requires explicit "brief" or "slide"
6. **Cost Ceiling:** $17-26/month additional (validated: average $0.29 per deliverable)

---

## File Locations (Quick Reference)

**Container 118 (`/opt/crewai`):**
- `catalyst.py` - Catalyst agent script (Phase 3)
- `tools/opportunity_parser.py` - Opportunity parsing (Phase 2)
- `tools/approval_parser.py` - Approval parsing (Phase 4)
- `crew.py` - Daily digest with opportunity parsing (Phase 1-2)
- `tools/slack_formatter.py` - Slack formatting with numbered IDs (Phase 2)
- `output/opportunities_YYYY-MM-DD.json` - Opportunity mapping
- `output/approvals.jsonl` - Approval log (create in Phase 5)

**Project Folder:**
- `claude-session/criterion-5-architecture.md` - System design (300+ lines)
- `claude-session/criterion-5-implementation-plan.md` - 6-phase plan (800+ lines)
- `claude-session/phase-1-complete-summary.md` - Phase 1 results
- `claude-session/phase-2-complete-summary.md` - Phase 2 results
- `claude-session/phase-3-complete-summary.md` - Phase 3 results
- `claude-session/phase-4-complete-summary.md` - Phase 4 results

**Vault:**
- `02_Sessions/Session-2026-02-02-b-CrewAI-Criterion-5-Planning.md` - Full session notes

---

## Testing Status

**All Tests Passing:**
- ✅ Phase 1: Strategist format (no-opportunity case validated)
- ✅ Phase 2: Opportunity parsing (mock H1, H2, W1 successful)
- ✅ Phase 3: Catalyst deliverables (3/3 types successful)
- ✅ Phase 4: Approval parser (23/23 unit tests passing)
- ✅ Real-world integration (Phase 2 + 4 with actual opportunities)

**Cost Validation:**
- Technical Plan: ~$0.30-0.35 per deliverable
- Leadership Brief: ~$0.28-0.32 per deliverable
- Client Slide: ~$0.24-0.26 per deliverable
- Average: ~$0.29 (within budget)

---

## Common Commands for Phase 5

**Test Approval Parser:**
```bash
ssh root@192.168.1.18
cd /opt/crewai
python3 tools/approval_parser.py  # Run unit tests
```

**Test Catalyst:**
```bash
ssh root@192.168.1.18
cd /opt/crewai
source venv/bin/activate
python3 catalyst.py --digest-date 2026-02-02 --opportunity H1 --type plan
```

**Check Opportunity Mapping:**
```bash
ssh root@192.168.1.18 "cat /opt/crewai/output/opportunities_2026-02-02.json | jq '.opportunities | keys'"
```

**Create Approvals Log:**
```bash
ssh root@192.168.1.18 "touch /opt/crewai/output/approvals.jsonl"
```

---

## Success Criteria for Phase 5

- ✅ n8n workflow "Approval Poller and Catalyst Trigger" created
- ✅ Schedule trigger runs every 5 minutes
- ✅ Workflow polls Slack for digest message
- ✅ Workflow retrieves replies to digest
- ✅ Approval parser called via SSH
- ✅ Catalyst triggered for valid approvals
- ✅ Deliverables posted to Slack thread
- ✅ Approvals logged to approvals.jsonl
- ✅ Invalid syntax returns help message
- ✅ Non-existent opportunities return error message

---

## Rollback Procedure (If Needed)

**To revert to Criterion 4:**
1. Deactivate "Approval Poller and Catalyst Trigger" workflow in n8n
2. Revert crew.py: `cp crew.py.backup-before-criterion5 crew.py`
3. Revert slack_formatter.py: `cp slack_formatter.py.backup-before-criterion5 slack_formatter.py`
4. Delete new files (optional): `rm catalyst.py tools/opportunity_parser.py tools/approval_parser.py`

**Rollback time:** < 5 minutes

---

## Quick Start for Next Session

1. **Read this handoff document** (you're here!)
2. **Gather prerequisites** (Slack channel ID, user ID)
3. **Read Phase 5 specification** in `criterion-5-implementation-plan.md` (lines 997-1100)
4. **Open n8n** and create new workflow
5. **Follow node-by-node configuration** from implementation plan
6. **Test incrementally** (build workflow step-by-step)
7. **Run Phase 6 testing scenarios** when workflow complete

---

**Estimated Remaining Time:** 5 hours
**Estimated Sessions:** 1-2 sessions
**Current Progress:** 67% complete (4 of 6 phases)

**Good luck with Phase 5!**
