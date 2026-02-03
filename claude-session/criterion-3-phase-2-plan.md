# Criterion 3 Phase 2: Work Plan

**Session:** 2026-02-01-b
**Goal:** Complete Context Management via Slack (all handlers)

---

## Current State Analysis

### Existing Implementation (Phase 1)
- n8n workflow "Context Manager" deployed
- Webhook URL: `https://n8n.kyle-schultz.com/webhook/context-manager`
- SSH authentication: n8n (container 111) → container 118 via ed25519 key
- Working commands:
  - `/interests <description>` → appends to `/context/hot_topics.md`
  - `/newproject <name>` → creates `/context/briefs/<name>.md`

### Workflow Architecture
1. Slack slash command → n8n webhook
2. Parse Command (JS code node) → extract command type and parameters
3. Route (switch node) → direct to appropriate handler
4. SSH Execute (SSH node) → execute command on container 118
5. Respond (webhook response) → send confirmation to Slack

---

## Phase 2 Requirements

### 1. Update Brief Command
**Slack format:** `/updatebrief <project-name>: <content>`

**Example:**
```
/updatebrief trend-research: Added new cost estimates for Sonnet 4.5
```

**Behavior:**
- Find existing brief in `/context/briefs/`
- Append content with timestamp
- Create new section or append to existing content area
- Error if project doesn't exist

**Implementation plan:**
- Add `update_brief` case to Parse Command node
- Extract project name and content (split on `:`)
- Add new route path to SSH handler
- SSH command: append content with timestamp to existing file
- Check file exists before appending

---

### 2. Transcript Command
**Slack format:** `/transcript <meeting-name>: <transcript-content>`

**Example:**
```
/transcript weekly-standup: Discussed Q1 priorities, AI strategy review, homelab updates
```

**Behavior:**
- Create new file in `/context/transcripts/`
- Filename format: `YYYY-MM-DD-<meeting-name>.md`
- Include metadata: date, meeting name
- Full transcript content as body

**Implementation plan:**
- Add `transcript` case to Parse Command node
- Extract meeting name and content (split on `:`)
- Add new route path to SSH handler
- SSH command: create file with date prefix
- Template format:
  ```markdown
  # Transcript: <meeting-name>
  **Date:** YYYY-MM-DD

  <content>
  ```

---

### 3. Recall Command
**Slack format:** `/recall <query>`

**Example:**
```
/recall Sonnet 4.5 costs
```

**Behavior:**
- Search across all context files (briefs, transcripts, hot_topics, etc.)
- Return matching lines with file context
- Limit to top 10 results
- Use `grep -r` for simple text search

**Implementation plan:**
- Add `recall` case to Parse Command node
- Extract search query
- Add new route path to SSH handler
- SSH command: `grep -r -i -n "<query>" /context/`
- Format results for Slack (limit output)
- Handle no results gracefully

---

## Task Breakdown

### Task 1: Update Brief Handler (30 min)
1. Modify `context-manager-workflow.json` Parse Command node
2. Add `update_brief` parsing logic
3. Add switch case to Route node
4. Create SSH node for update brief operation
5. Create response node
6. Test with curl

### Task 2: Transcript Handler (30 min)
1. Add `transcript` parsing logic to Parse Command
2. Add switch case to Route node
3. Create SSH node for transcript creation
4. Create response node
5. Test with curl

### Task 3: Recall Handler (30 min)
1. Add `recall` parsing logic to Parse Command
2. Add switch case to Route node
3. Create SSH node for grep search
4. Format results in response node
5. Test with curl

### Task 4: Slack Integration Testing (30 min)
1. Configure new slash commands in Slack app
2. Test each command via Slack
3. Verify file operations on container 118
4. Test error cases (missing brief, no results, etc.)
5. Document command formats

### Task 5: Documentation & Validation (30 min)
1. Update Roadmap progress tracker
2. Update homelab_system_overview.md
3. Document all slash command formats
4. Final end-to-end verification
5. Mark Criterion 3 complete

---

## Risk Assessment

**Low Risk:**
- File operations are append/create only (no deletions)
- SSH operations confined to `/context/` directory
- Reversible (can delete files manually if needed)
- No impact on existing Phase 1 functionality

**Medium Risk:**
- n8n workflow update might temporarily break Phase 1 commands
- Mitigation: Export current workflow before modifying, test in isolation

**Permissions Required:**
- n8n workflow modification (medium risk - requires explicit acknowledgment)
- SSH operations on container 118 (allowed by default - read/write to `/context/`)
- Slack app configuration (medium risk - requires explicit acknowledgment)

---

## Success Criteria

- [ ] `/updatebrief` command works end-to-end via Slack
- [ ] `/transcript` command works end-to-end via Slack
- [ ] `/recall` command works end-to-end via Slack
- [ ] All Phase 1 commands still work (`/interests`, `/newproject`)
- [ ] Error handling tested for each command
- [ ] Documentation updated in Roadmap and System Overview
- [ ] Criterion 3 marked complete in Roadmap

---

## Implementation Strategy

**Approach:** Iterative, incremental
1. Extend existing workflow (don't rebuild)
2. Test each handler with curl before Slack integration
3. Preserve Phase 1 functionality
4. Document as we go

**Rollback plan:** Export current workflow before changes, can re-import if needed
