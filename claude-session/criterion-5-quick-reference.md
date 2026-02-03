# Criterion 5: Quick Reference

**Design Complete:** 2026-02-02
**Status:** Ready for Implementation
**Estimated Time:** 12.5 hours (3 sessions)

---

## What We're Building

**Goal:** Kyle can approve opportunities from the daily digest via Slack. Catalyst agent generates deliverables and posts them to the thread.

**How it works:**
1. Daily digest posts with numbered opportunities: `[H1]`, `[H2]`, `[W1]`, `[W2]`
2. Kyle replies: `approve H1` or `approve W1 brief`
3. n8n polls for replies every 5 minutes
4. Catalyst agent generates deliverable (Technical Plan, Leadership Brief, or Client Slide)
5. Deliverable posts to Slack thread
6. All approvals logged to `approvals.jsonl`

---

## Approval Syntax

### Homelab Opportunities
```
approve H1              → Technical Plan
approve H2 plan         → Technical Plan (explicit)
approve H1, H2          → Both get Technical Plans
```

### Work Opportunities
```
approve W1 brief        → Leadership Brief
approve W2 slide        → Client Slide
approve W1 brief, W2 slide → Both (different types)
```

### Dismiss
```
dismiss H1              → Logs rejection, no deliverable
dismiss W2              → Logs rejection, no deliverable
```

### Invalid (will error)
```
approve W1              → ERROR: Must specify 'brief' or 'slide'
approve H1 slide        → ERROR: Homelab only supports 'plan'
```

---

## Deliverable Types

| Type | For | Format | Example Sections |
|------|-----|--------|-----------------|
| **Technical Plan** | Homelab only | Implementation guide | Overview, Implementation Approach, Learning Path, Integration Points, Risks, Next Actions |
| **Leadership Brief** | Work | Strategic memo | Executive Summary, Connection to Priorities, Strategic Implications, Implementation, Recommended Approach, Key Stakeholders |
| **Client Slide** | Work | Single slide text | Slide Title, Key Message, Supporting Points (3-4 bullets), So What? |

---

## Implementation Phases

### Phase 1: Strategist Formatting (1 hour, low risk)
- Update Homelab Strategist task to output `### Opportunity:` headers
- Update Work Strategist task to output `### Opportunity:` headers
- Test crew.py to verify structured output

### Phase 2: Opportunity Parsing (2 hours, low risk)
- Create `tools/opportunity_parser.py`
- Update `tools/slack_formatter.py` to format numbered opportunities
- Update `crew.py` to parse and save opportunity mapping
- Test digest format with numbered IDs

### Phase 3: Catalyst Agent (3 hours, medium risk)
- Create `catalyst.py` with agent definition
- Implement 3 task templates (plan, brief, slide)
- Add CLI argument parsing
- Test with mock opportunities

### Phase 4: Approval Parser (1.5 hours, low risk)
- Create `tools/approval_parser.py`
- Implement syntax validation rules
- Add error message generation
- Run unit tests

### Phase 5: n8n Poller Workflow (3 hours, medium risk)
- Create new workflow "Approval Poller and Catalyst Trigger"
- Add 16 nodes (schedule, Slack API calls, SSH execution, error handling)
- Configure Slack credentials and SSH keys
- Activate workflow

### Phase 6: Integration Testing (2 hours, medium risk)
- Test full cycle: Digest → Approval → Catalyst → Delivery
- Test error scenarios (invalid syntax, duplicates)
- Monitor token costs
- Validate all 3 deliverable types

---

## Key Files

### Created by This Project
```
/opt/crewai/
├── catalyst.py                      # NEW: Standalone Catalyst execution
├── tools/
│   ├── opportunity_parser.py       # NEW: Parse structured opportunities
│   └── approval_parser.py          # NEW: Parse approval syntax
├── output/
│   ├── opportunities_*.json        # NEW: Opportunity mapping per digest
│   ├── catalyst_*.json             # NEW: Deliverable outputs
│   └── approvals.jsonl             # NEW: Append-only approval log
```

### Modified
```
/opt/crewai/
├── crew.py                          # Add opportunity parsing
└── tools/
    └── slack_formatter.py          # Add numbered opportunity formatting
```

---

## n8n Workflows

### Workflow 1: "Strategic Intelligence Daily" (Modified)
- **Change:** Parse opportunities, assign IDs, format digest with numbers
- **Risk:** Low (incremental change)

### Workflow 2: "Approval Poller and Catalyst Trigger" (NEW)
- **Nodes:** 16 total
- **Schedule:** Every 5 minutes
- **Flow:** Check Slack → Parse approvals → Check duplicates → Trigger Catalyst → Post deliverable
- **Risk:** Medium (new workflow, external dependencies)

---

## Testing Checklist

### Phase 1 Tests
- [ ] Homelab Strategist output has `### Opportunity:` headers
- [ ] Work Strategist output has `### Opportunity:` headers
- [ ] Multiple opportunities clearly separated

### Phase 2 Tests
- [ ] Opportunities parsed with H1, H2, W1, W2 IDs
- [ ] `opportunities_YYYY-MM-DD.json` created
- [ ] Digest shows `[H1]`, `[W1]` labels
- [ ] Footer instructions appear

### Phase 3 Tests
- [ ] `catalyst.py --digest-date 2026-02-02 --opportunity H1 --type plan` executes
- [ ] Technical Plan generated for homelab
- [ ] Leadership Brief generated for work
- [ ] Client Slide generated for work
- [ ] JSON output valid

### Phase 4 Tests
- [ ] `approve H1` parses correctly
- [ ] `approve W1 brief` parses correctly
- [ ] `approve W1` returns error
- [ ] `approve H1, W1 brief` parses multiple
- [ ] `dismiss H1` parses correctly

### Phase 5 Tests
- [ ] Workflow triggers every 5 minutes
- [ ] Detects digest message
- [ ] Parses replies correctly
- [ ] Checks for duplicates
- [ ] Triggers Catalyst via SSH
- [ ] Posts deliverable to thread

### Phase 6 Tests
- [ ] Full cycle: approve H1 → Deliverable in thread
- [ ] All 3 deliverable types tested
- [ ] Invalid syntax → Help message
- [ ] Duplicate approval → Ignored
- [ ] Dismiss → Logged only
- [ ] Token costs < $0.40 per deliverable

---

## Slack API Requirements

### Scopes Needed (Verify)
- `conversations.history` (read digest message)
- `conversations.replies` (read replies to digest)
- `chat:write` (post deliverables)

### IDs Needed
- **Channel ID:** #trend-monitoring (e.g., `C01ABC123`)
- **Bot User ID:** Strategic Intelligence bot
- **Kyle's User ID:** For filtering approvals (e.g., `U01XYZ789`)

### API Endpoints Used
1. `conversations.history` - Get today's digest message
2. `conversations.replies` - Get replies to digest
3. `chat.postMessage` - Post deliverable to thread

---

## Monitoring

### Check Approval Log
```bash
ssh root@192.168.1.18
cat /opt/crewai/output/approvals.jsonl | jq -r '.deliverable_type' | sort | uniq -c
```

### Check Deliverables
```bash
ssh root@192.168.1.18
ls -lh /opt/crewai/output/catalyst_*.json
cat $(ls -t /opt/crewai/output/catalyst_*.json | head -1) | jq '.deliverable_content' -r
```

### Check Token Costs
```bash
ssh root@192.168.1.18
cat /opt/crewai/output/catalyst_*.json | jq '.token_usage'
```

---

## Cost Model

| Component | Cost/Run | Frequency | Monthly |
|-----------|----------|-----------|---------|
| **Baseline (Criterion 4)** | $0.40-0.50 | Daily | $12-15 |
| **Catalyst (per approval)** | $0.30 | Variable | Variable |

**Example Scenarios:**
- 1 approval/day: +$9/month = $21-24/month total
- 2 approvals/day: +$18/month = $30-33/month total
- 3 approvals/day: +$27/month = $39-42/month total

**Budget Approved:** ~$18-27/month additional (2-3 approvals/day)

---

## Rollback

### Full Rollback to Criterion 4
```bash
# Deactivate poller workflow in n8n
# Revert crew.py
ssh root@192.168.1.18
cd /opt/crewai
cp crew.py.backup-before-criterion5 crew.py

# Revert slack_formatter.py
cd tools
cp slack_formatter.py.backup-before-criterion5 slack_formatter.py
```

**Time to rollback:** < 5 minutes
**Impact:** Returns to daily digests without approval capability

---

## Next Session Prerequisites

Before starting implementation:
1. [ ] Obtain #trend-monitoring channel ID
2. [ ] Obtain Kyle's Slack user ID
3. [ ] Verify container 118 SSH access from n8n
4. [ ] Review `criterion-5-architecture.md`
5. [ ] Review `criterion-5-implementation-plan.md`
6. [ ] Backup current crew.py and slack_formatter.py

---

## Success Criteria (After 2 Weeks)

- [ ] At least 5 approvals processed successfully
- [ ] All 3 deliverable types tested (plan, brief, slide)
- [ ] Average cost per deliverable < $0.40
- [ ] No duplicate approvals processed
- [ ] Error rate < 10%
- [ ] Processing time < 15 minutes (polling + Catalyst + post)

---

*Quick reference created: 2026-02-02*
*For detailed specs, see: criterion-5-architecture.md*
*For implementation details, see: criterion-5-implementation-plan.md*
