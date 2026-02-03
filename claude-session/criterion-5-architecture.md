# Criterion 5: Approval Flow and Catalyst - Architecture Design

**Date:** 2026-02-02
**Status:** Design Phase
**Session:** Session-2026-02-02-b-CrewAI-Criterion-5-Planning.md

---

## Design Decisions (Approved)

1. **Approval Detection:** Polling Slack API every 5-10 minutes (acceptable latency)
2. **Message Structure:** Single digest with numbered IDs `[H1]`, `[H2]`, `[W1]`, `[W2]` (NOT threaded)
3. **Deliverable Types:**
   - **Technical Plan** - Homelab opportunities only
   - **Leadership Brief** - Work opportunities
   - **Client Slide** - Work opportunities (alternative to Leadership Brief)
4. **Cost Ceiling:** ~$18-27/month additional approved
5. **Approval Method:** Reply to digest with approval syntax

---

## System Architecture

### Information Flow

```
Daily Digest (6 AM)
    ↓
Post to Slack (#trend-monitoring)
    with numbered opportunities [H1], [H2], [W1], [W2]
    ↓
Polling Workflow (every 5 min)
    ↓
Check for replies matching approval syntax
    ↓
Parse: opportunity ID + deliverable type
    ↓
Trigger Catalyst SSH execution
    ↓
Catalyst generates deliverable
    ↓
Post deliverable to Slack thread
    ↓
Log approval + deliverable to tracking file
```

---

## Approval Syntax

User replies to digest message with one of these formats:

### Homelab Opportunities (Technical Plan only)
```
approve H1
approve h2 plan
approve H1, H2
```

### Work Opportunities (Leadership Brief or Client Slide)
```
approve W1 brief
approve w2 slide
approve W1 brief, W2 slide
```

**Syntax Rules:**
- Case-insensitive (`h1` = `H1`, `brief` = `Brief`)
- Comma-separated for multiple approvals in one message
- Deliverable type defaults:
  - Homelab (`H*`) → Always `plan` (only one type)
  - Work (`W*`) → MUST specify `brief` or `slide` (no default to avoid ambiguity)
- Invalid syntax = ignored + error message

**Examples:**
- ✅ `approve H1` → Technical Plan for opportunity H1
- ✅ `approve W1 brief` → Leadership Brief for W1
- ✅ `approve W2 slide` → Client Slide for W2
- ✅ `approve H1, W1 brief, W2 slide` → Multiple deliverables
- ❌ `approve W1` → ERROR: Must specify `brief` or `slide` for Work opportunities
- ❌ `approve H1 slide` → ERROR: Homelab only supports `plan`

---

## Dismiss Syntax

User can explicitly dismiss opportunities (logs rejection, no Catalyst):

```
dismiss H1
dismiss W2
dismiss H1, W2
```

**Behavior:**
- Log dismissal to tracking file with timestamp
- No Catalyst execution
- Helps track "what Kyle evaluated but rejected" for future learning

---

## Digest Message Format Changes

### Current Format (Criterion 4)
```markdown
📊 *Strategic Intelligence Digest*
_2026-02-02 06:00_

---
*🔍 SCOUT SIGNALS*
[preview of scout output...]

---
*🧠 ANALYST SYNTHESIS*
[preview of analyst output...]

---
*🏠 HOMELAB OPPORTUNITIES*
[full homelab strategist output...]

---
*💼 WORK OPPORTUNITIES*
[full work strategist output...]
```

### New Format (Criterion 5)
```markdown
📊 *Strategic Intelligence Digest*
_2026-02-02 06:00_
Sources: 5 | Signals: 12

---
*🔍 SCOUT SIGNALS*
[preview of scout output...]

---
*🧠 ANALYST SYNTHESIS*
[preview of analyst output...]

---
*🏠 HOMELAB OPPORTUNITIES*

*[H1] Local LLM Fine-tuning Workflow*
[opportunity description from Homelab Strategist...]

*[H2] Self-hosted Analytics Alternative*
[opportunity description from Homelab Strategist...]

---
*💼 WORK OPPORTUNITIES*

*[W1] AI-Assisted Code Review Patterns*
[opportunity description from Work Strategist...]

*[W2] Team Prototyping Framework*
[opportunity description from Work Strategist...]

---
_Reply with: `approve [ID] [type]` to generate deliverable_
_Types: `plan` (homelab), `brief` or `slide` (work)_
_Example: `approve H1, W1 brief`_
```

**Key Changes:**
1. Opportunities are numbered with bold IDs: `*[H1]*`, `*[W1]*`
2. Footer instructions explain approval syntax
3. Each opportunity has a clear title (extracted from Strategist output)

---

## Strategist Output Format Changes

**Current:** Strategists output free-form prose about opportunities

**New Requirement:** Strategists must structure output as:

```markdown
### Opportunity: [Clear Title]
**Relevance:** [Why this matters to context]
**Signal:** [What triggered this]
**Next Steps:** [What could be done]
```

This structured format enables:
- Clean extraction of opportunity titles for `[H1]`, `[H2]` labels
- Clear boundary detection between multiple opportunities
- Better context for Catalyst agent

**Implementation:** Update Strategist task descriptions and expected_output specifications

---

## Catalyst Agent Specification

### Agent Definition

```python
catalyst = Agent(
    role='Catalyst Deliverable Generator',
    goal='Create actionable deliverables (technical plans, leadership briefs, client slides) for approved opportunities',
    backstory="""You are a strategic deliverable writer who excels at translating
    trend signals into concrete, actionable outputs. You understand how to bridge
    between abstract opportunities and practical next steps.

    For Technical Plans (homelab), you focus on:
    - Implementation approach (what needs to be built/configured)
    - Learning path (what Kyle needs to learn first)
    - Risks and rollback strategy
    - Integration with existing homelab architecture

    For Leadership Briefs (work), you focus on:
    - Connection to active work projects/priorities
    - Strategic pitch (why this matters to the organization)
    - Implementation considerations for a team
    - Potential blockers or prerequisites

    For Client Slides (work), you focus on:
    - Clear, concise explanation of the concept
    - Value proposition for business stakeholders
    - Real-world use cases and examples
    - "So what?" framing (why should they care)

    You write with clarity, pragmatism, and actionability.""",
    verbose=True,
    allow_delegation=False,
    llm='claude-sonnet-4-5-20250929'
)
```

### Task Templates

#### Technical Plan Task
```python
catalyst_task_plan = Task(
    description=f"""Generate a Technical Plan for the following homelab opportunity.

    OPPORTUNITY:
    {opportunity_text}

    RELEVANT CONTEXT:
    - Homelab Architecture: {homelab_context}
    - Active Projects: {relevant_briefs}
    - Known Constraints: {known_constraints}

    OUTPUT REQUIREMENTS:
    Create a technical plan with these sections:

    ## Overview
    [2-3 sentences: What is this and why consider it?]

    ## Implementation Approach
    [Step-by-step: How would this be built/deployed in the homelab?]

    ## Learning Path
    [What skills/knowledge needed? Resources to study first?]

    ## Integration Points
    [How does this connect to existing homelab systems?]

    ## Risks and Rollback
    [What could go wrong? How to undo changes?]

    ## Next Actions
    [Concrete first steps to validate/prototype]
    """,
    agent=catalyst,
    expected_output="Well-structured technical plan with clear implementation steps"
)
```

#### Leadership Brief Task
```python
catalyst_task_brief = Task(
    description=f"""Generate a Leadership Brief for the following work opportunity.

    OPPORTUNITY:
    {opportunity_text}

    RELEVANT CONTEXT:
    - Work Role: {work_role}
    - Active Projects: {relevant_briefs}
    - Hot Topics: {hot_topics}
    - Recent Transcripts: {relevant_transcripts}

    OUTPUT REQUIREMENTS:
    Create a leadership brief with these sections:

    ## Executive Summary
    [2-3 sentences: What is this and why does it matter?]

    ## Connection to Current Priorities
    [How does this relate to active work projects/themes?]

    ## Strategic Implications
    [What are the broader implications for the team/org?]

    ## Implementation Considerations
    [What would it take to pilot/adopt this? Team readiness?]

    ## Recommended Approach
    [Concrete next steps: experiment, advocate, pilot, or watch]

    ## Key Stakeholders
    [Who should be involved in this conversation?]
    """,
    agent=catalyst,
    expected_output="Well-structured leadership brief with strategic framing"
)
```

#### Client Slide Task
```python
catalyst_task_slide = Task(
    description=f"""Generate a Client Slide (text format) for the following work opportunity.

    OPPORTUNITY:
    {opportunity_text}

    RELEVANT CONTEXT:
    - Work Role: {work_role}
    - Active Projects: {relevant_briefs}

    OUTPUT REQUIREMENTS:
    Create text content for a single explanatory slide with these sections:

    ## Slide Title
    [Clear, compelling headline]

    ## Key Message (1-2 sentences)
    [The main point in business-friendly language]

    ## Supporting Points (3-4 bullets)
    - [Benefit 1]
    - [Benefit 2]
    - [Use case or example]
    - [Implementation consideration]

    ## So What? (1 sentence)
    [Why should a business stakeholder care about this?]

    TONE: Clear, non-technical, value-focused
    AUDIENCE: Business stakeholders / clients (not engineers)
    """,
    agent=catalyst,
    expected_output="Single-slide content with clear business value framing"
)
```

---

## Data Flow and File Artifacts

### Directory Structure

```
/opt/crewai/
├── crew.py                          # Main crew (Scout, Analyst, Strategists)
├── catalyst.py                      # NEW: Catalyst execution script
├── output/
│   ├── slack_digest_*.json         # Daily digest (existing)
│   ├── catalyst_*.json             # NEW: Catalyst deliverables
│   └── approvals.jsonl             # NEW: Append-only approval log
├── config/
│   ├── .env                        # API keys
│   └── sources.yaml                # RSS sources
└── tools/
    ├── source_fetcher.py           # RSS fetching
    ├── context_loader.py           # Context file loading
    ├── slack_formatter.py          # Slack message formatting
    ├── opportunity_parser.py       # NEW: Parse numbered opportunities
    └── approval_parser.py          # NEW: Parse approval syntax
```

### File Specifications

#### `output/approvals.jsonl` (Append-only log)
```json
{"timestamp": "2026-02-02T08:15:00Z", "digest_date": "2026-02-02", "opportunity_id": "H1", "deliverable_type": "plan", "status": "approved", "slack_user": "U01ABC123", "slack_message_ts": "1706864100.123456"}
{"timestamp": "2026-02-02T08:15:00Z", "digest_date": "2026-02-02", "opportunity_id": "W1", "deliverable_type": "brief", "status": "approved", "slack_user": "U01ABC123", "slack_message_ts": "1706864100.123456"}
{"timestamp": "2026-02-02T09:22:00Z", "digest_date": "2026-02-02", "opportunity_id": "W2", "deliverable_type": "none", "status": "dismissed", "slack_user": "U01ABC123", "slack_message_ts": "1706868120.789012"}
{"timestamp": "2026-02-02T09:30:00Z", "digest_date": "2026-02-02", "opportunity_id": "H1", "deliverable_type": "plan", "status": "delivered", "catalyst_file": "output/catalyst_2026-02-02_H1_plan.json"}
```

#### `output/catalyst_2026-02-02_H1_plan.json`
```json
{
  "timestamp": "2026-02-02T09:30:00Z",
  "digest_date": "2026-02-02",
  "opportunity_id": "H1",
  "deliverable_type": "plan",
  "opportunity_text": "[Full opportunity description from Homelab Strategist]",
  "deliverable_content": "[Full Technical Plan from Catalyst]",
  "context_used": {
    "homelab_architecture": true,
    "briefs": ["project-a.md"],
    "hot_topics": true
  },
  "token_usage": {
    "input_tokens": 45000,
    "output_tokens": 8000,
    "estimated_cost": 0.28
  }
}
```

---

## n8n Workflow Architecture

### Workflow 1: Enhanced "Strategic Intelligence Daily" (Modified)

**Changes from Criterion 4:**
1. After Strategist outputs, parse opportunities and assign IDs
2. Format digest with numbered opportunities `[H1]`, `[H2]`, `[W1]`, `[W2]`
3. Include approval syntax instructions in footer
4. Save opportunity mapping to file: `output/opportunities_2026-02-02.json`

**New Python Tool:** `tools/opportunity_parser.py`
- Parses Homelab Strategist output → extracts opportunities → assigns H1, H2, H3...
- Parses Work Strategist output → extracts opportunities → assigns W1, W2, W3...
- Returns mapping: `{"H1": {"title": "...", "text": "..."}, "W1": {...}}`

**Opportunity Mapping File:** `output/opportunities_2026-02-02.json`
```json
{
  "digest_date": "2026-02-02",
  "digest_message_ts": "1706864400.123456",
  "opportunities": {
    "H1": {
      "title": "Local LLM Fine-tuning Workflow",
      "full_text": "[complete opportunity description]",
      "source": "homelab_strategist"
    },
    "H2": {
      "title": "Self-hosted Analytics Alternative",
      "full_text": "[complete opportunity description]",
      "source": "homelab_strategist"
    },
    "W1": {
      "title": "AI-Assisted Code Review Patterns",
      "full_text": "[complete opportunity description]",
      "source": "work_strategist"
    }
  }
}
```

### Workflow 2: NEW "Approval Poller and Catalyst Trigger"

**Trigger:** Schedule every 5 minutes (cron: `*/5 * * * *`)

**Nodes:**

1. **Schedule Trigger** (every 5 min)
   ↓
2. **Get Today's Digest Message** (HTTP Request to Slack API)
   - Endpoint: `conversations.history`
   - Channel: `#trend-monitoring`
   - Filter: Messages from bot user in last 24 hours
   - Extract: Most recent digest message_ts
   ↓
3. **Get Replies to Digest** (HTTP Request to Slack API)
   - Endpoint: `conversations.replies`
   - parent_message_ts: `{{ digest_message_ts }}`
   - Filter: Replies from Kyle (user_id match)
   ↓
4. **Parse Approval Syntax** (Code node)
   - Parse reply text for approval/dismiss syntax
   - Extract: opportunity IDs + deliverable types
   - Check against `approvals.jsonl` for duplicates
   ↓
5. **Filter New Approvals** (IF node)
   - If no new approvals → End
   - If new approvals → Continue
   ↓
6. **Log Approval** (SSH to 118, append to approvals.jsonl)
   ↓
7. **Trigger Catalyst** (SSH to 118, run catalyst.py)
   - Pass: opportunity_id, deliverable_type, digest_date
   ↓
8. **Read Catalyst Output** (SSH to 118, cat catalyst_*.json)
   ↓
9. **Post to Slack Thread** (HTTP Request to Slack API)
   - Endpoint: `chat.postMessage`
   - thread_ts: `{{ digest_message_ts }}` (reply in thread)
   - text: Formatted deliverable content
   ↓
10. **Update Approval Log** (SSH to 118, append delivery status)

**Error Handling:**
- If Catalyst fails → Post error to thread + log failure
- If duplicate approval → Ignore silently (already processed)
- If invalid syntax → Reply with help message

---

## Catalyst Execution Script

**File:** `/opt/crewai/catalyst.py`

**Purpose:** Standalone script to generate single deliverable on-demand

**Invocation:**
```bash
python3 catalyst.py --digest-date 2026-02-02 --opportunity H1 --type plan
python3 catalyst.py --digest-date 2026-02-02 --opportunity W1 --type brief
python3 catalyst.py --digest-date 2026-02-02 --opportunity W2 --type slide
```

**Behavior:**
1. Load opportunity text from `output/opportunities_{digest_date}.json`
2. Load relevant context files based on opportunity source
3. Select task template (plan/brief/slide)
4. Execute Catalyst agent with single task
5. Save output to `output/catalyst_{digest_date}_{opp_id}_{type}.json`
6. Print JSON output to stdout for n8n to capture

**Output Format (stdout):**
```json
{
  "success": true,
  "deliverable_file": "output/catalyst_2026-02-02_H1_plan.json",
  "deliverable_content": "[Full Technical Plan text]",
  "token_usage": {"input": 45000, "output": 8000, "cost": 0.28}
}
```

---

## State Machine

```
[Digest Posted]
    ↓
[User Replies] → Parse Syntax
    ↓
    ├─ Valid Approval → [Approved] → Check Duplicate → [Processing]
    │                                      ↓
    │                                  Already Processed → [Ignore]
    ↓
[Processing] → Trigger Catalyst → [Generating]
    ↓
    ├─ Success → [Delivered] → Post to Thread → [Complete]
    ↓
    └─ Failure → [Failed] → Post Error → [Complete]

[User Dismisses] → [Dismissed] → Log Only → [Complete]
```

---

## Implementation Phases

### Phase 1: Strategist Output Formatting (Low Risk)
**Goal:** Make Strategist outputs structured with clear opportunity boundaries

**Tasks:**
1. Update Homelab Strategist task description (add structure requirement)
2. Update Work Strategist task description (add structure requirement)
3. Test crew.py with new task descriptions
4. Verify output is parseable

**Validation:** Manual run of crew.py produces structured opportunities

**Estimated Time:** 1 hour

---

### Phase 2: Opportunity Parsing and Digest Formatting (Low Risk)
**Goal:** Parse Strategist outputs into numbered opportunities in Slack digest

**Tasks:**
1. Create `tools/opportunity_parser.py`
   - Function: `parse_homelab_opportunities(text)` → `[{title, text}, ...]`
   - Function: `parse_work_opportunities(text)` → `[{title, text}, ...]`
   - Function: `assign_ids(homelab_opps, work_opps)` → `{H1: {...}, W1: {...}}`
2. Update `tools/slack_formatter.py`
   - Add `format_numbered_opportunities()` function
   - Add footer with approval syntax instructions
3. Update crew.py to call opportunity_parser and save mapping file
4. Test digest formatting locally

**Validation:** Digest shows `[H1]`, `[W2]` etc. with clear instructions

**Estimated Time:** 2 hours

---

### Phase 3: Catalyst Agent and Execution Script (Medium Risk)
**Goal:** Create standalone catalyst.py that generates deliverables

**Tasks:**
1. Create `catalyst.py` with Agent definition
2. Implement task templates (plan, brief, slide)
3. Add command-line argument parsing
4. Add context loading (read from opportunity mapping + context files)
5. Add JSON output formatting
6. Test with mock opportunity data

**Validation:**
```bash
python3 catalyst.py --digest-date 2026-02-02 --opportunity H1 --type plan
```
Produces valid JSON output with deliverable content

**Estimated Time:** 3 hours

---

### Phase 4: Approval Parsing Tool (Low Risk)
**Goal:** Parse approval/dismiss syntax from Slack replies

**Tasks:**
1. Create `tools/approval_parser.py`
   - Function: `parse_approval_syntax(text)` → `[{opp_id, type, action}, ...]`
   - Regex patterns for approval/dismiss
   - Validation (W* must have type, H* defaults to plan)
2. Unit tests for various syntax formats
3. Error message generation for invalid syntax

**Validation:** Parser correctly handles all syntax examples from spec

**Estimated Time:** 1.5 hours

---

### Phase 5: Approval Poller n8n Workflow (Medium Risk)
**Goal:** Create n8n workflow that polls for approvals and triggers Catalyst

**Tasks:**
1. Create new workflow "Approval Poller and Catalyst Trigger"
2. Configure Schedule Trigger (every 5 min)
3. Add Slack API nodes (conversations.history, conversations.replies)
4. Add Code node for approval parsing
5. Add SSH nodes for Catalyst execution
6. Add Slack post node for deliverable
7. Add error handling nodes
8. Test with manual approval in Slack

**Validation:** Reply "approve H1" to digest → Deliverable appears in thread within 5 min

**Estimated Time:** 3 hours

---

### Phase 6: Integration Testing and Monitoring (Medium Risk)
**Goal:** Validate end-to-end flow and establish monitoring

**Tasks:**
1. Run full cycle: Digest → Approval → Catalyst → Delivery
2. Test error scenarios (invalid syntax, duplicate approval, Catalyst failure)
3. Monitor first week token costs
4. Add approval metrics to tracking
5. Document operational procedures

**Validation:** 3-5 successful approvals with deliverables posted

**Estimated Time:** 2 hours

---

## Total Estimated Implementation Time: 12.5 hours
**Suggested Breakdown:** 2-3 sessions of 4-5 hours each

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Strategist output not parseable** | Medium | High | Start with strict format requirements; add fallback to manual numbering |
| **Approval polling misses replies** | Low | Medium | Test Slack API pagination; add duplicate detection |
| **Catalyst token cost exceeds estimate** | Medium | Medium | Monitor first 5 approvals closely; add cost logging |
| **n8n workflow timeout (Catalyst slow)** | Medium | Medium | Run Catalyst via SSH background job; poll for completion |
| **Duplicate approvals processed** | Medium | Low | Check approvals.jsonl before each Catalyst trigger |
| **Invalid approval syntax causes errors** | High | Low | Graceful error handling + help message |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **User confusion about syntax** | High | Low | Clear instructions in digest footer; examples in first digest |
| **Deliverable quality below expectations** | Medium | Medium | Iterate on Catalyst task descriptions; collect feedback |
| **Polling latency frustrating** | Low | Medium | Set expectations (5-10 min); can upgrade to Events API later |
| **Cost ceiling exceeded** | Low | High | Monitor daily; can disable poller or add daily approval limit |

---

## Monitoring and Success Metrics

### Key Metrics to Track

1. **Approval Rate:** % of digests that receive at least one approval
2. **Deliverable Distribution:** Count by type (plan / brief / slide)
3. **Token Costs:** Actual cost per deliverable type (compare to $0.30 estimate)
4. **Processing Time:** Time from approval to deliverable posted
5. **Error Rate:** % of approvals that fail Catalyst execution

### Success Criteria (After 2 Weeks)

- ✅ At least 5 approvals processed successfully
- ✅ All 3 deliverable types tested
- ✅ Average cost per deliverable < $0.40
- ✅ No duplicate approvals processed
- ✅ Error rate < 10%
- ✅ Processing time < 15 minutes (polling + Catalyst + post)

---

## Rollback Procedures

### Rollback to Criterion 4

**If Criterion 5 causes issues:**

1. Disable "Approval Poller" workflow in n8n (toggle inactive)
2. Revert crew.py to Criterion 4 version (backup exists: `crew.py.backup-before-criterion5`)
3. Revert slack_formatter.py to simple format (no numbered opportunities)
4. Keep approvals.jsonl for historical record

**Impact:** System returns to daily digests without approval capability

**Recovery Time:** < 5 minutes

### Partial Rollback

**If Catalyst works but approval detection is problematic:**

1. Disable automated polling
2. Add manual Catalyst trigger via Slack command: `/catalyst H1 plan`
3. Keep opportunity numbering in digests (still useful for reference)

---

## Future Enhancements (Out of Scope for Criterion 5)

1. **Slack Events API** - Real-time reactions instead of polling
2. **Approval Analytics** - Dashboard showing approval patterns over time
3. **Learning Loop** - Use approval/dismiss history to improve Strategist relevance filtering
4. **Notebook LM Integration** - Escalate complex deliverables to Notebook LM for deep research
5. **Multi-format Deliverables** - Export as PDF, Markdown, or Notion page
6. **Approval Limits** - Daily quota (e.g., max 3 approvals/day) to control costs
7. **Feedback Collection** - Rate deliverable quality to tune Catalyst prompts

---

*Architecture design complete: 2026-02-02*
*Ready for implementation approval*
