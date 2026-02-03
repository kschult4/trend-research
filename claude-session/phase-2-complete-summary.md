# Criterion 5 Phase 2: COMPLETE

**Date:** 2026-02-02
**Duration:** ~2 hours
**Status:** ✅ COMPLETE

---

## Phase 2 Goal

Create opportunity parser and update digest formatting with numbered IDs ([H1], [H2], [W1], [W2]). Save opportunity mapping to JSON for approval poller reference.

---

## Changes Made

### Files Created

**1. `/opt/crewai/tools/opportunity_parser.py` (NEW)**
- `parse_opportunities(text, prefix)` - Parse `### Opportunity:` headers from Strategist output
- `extract_subsection(text, subsection_name)` - Extract Relevance, Signal, Next Steps subsections
- `format_opportunity_for_slack(opp_id, opp_data)` - Format single opportunity with numbered ID for Slack
- `save_opportunity_mapping(opportunities, digest_date, ...)` - Save opportunity mapping JSON file
- Includes unit tests with mock data

### Files Modified

**2. `/opt/crewai/tools/slack_formatter.py` (MODIFIED)**
- Added `format_for_slack_with_opportunities()` - New function for numbered opportunity formatting
- Added `save_for_n8n_with_opportunities()` - Save JSON with opportunities field
- Kept original functions for backward compatibility
- Updated footer to include approval syntax instructions

**3. `/opt/crewai/crew.py` (MODIFIED)**
- Added imports: `opportunity_parser`, `save_for_n8n_with_opportunities`
- Added opportunity parsing after Strategist outputs
- Parse homelab_output → `parse_opportunities(text, 'H')`
- Parse work_output → `parse_opportunities(text, 'W')`
- Save opportunity mapping: `output/opportunities_YYYY-MM-DD.json`
- Updated to use `save_for_n8n_with_opportunities()` instead of `save_for_n8n()`
- Updated phase marker to "CRITERION 5 PHASE 2 (OPPORTUNITY PARSING)"

### Backups Created
- `/opt/crewai/tools/slack_formatter.py.backup-before-criterion5`
- `/opt/crewai/crew.py.backup-before-criterion5` (from Phase 1)

---

## How It Works

### 1. Strategist Output (Phase 1)
```markdown
### Opportunity: Local LLM Fine-tuning
**Relevance:** Connects to AI Box project
**Signal:** New Ollama capabilities announced
**Next Steps:** Research fine-tuning workflow
```

### 2. Parsing (Phase 2)
```python
homelab_opportunities = parse_opportunities(homelab_output, 'H')
# Returns: {"H1": {"title": "...", "relevance": "...", "signal": "...", "next_steps": "..."}}
```

### 3. Slack Formatting (Phase 2)
```markdown
*[H1] Local LLM Fine-tuning*
_Connects to AI Box project_
Signal: New Ollama capabilities announced
Next Steps: Research fine-tuning workflow
```

### 4. Opportunity Mapping File (Phase 2)
```json
{
  "digest_date": "2026-02-02",
  "created_at": "2026-02-02T16:37:25.278759",
  "opportunities": {
    "H1": {
      "title": "Local LLM Fine-tuning",
      "full_text": "### Opportunity: Local LLM...",
      "relevance": "Connects to AI Box project",
      "signal": "New Ollama capabilities announced",
      "next_steps": "Research fine-tuning workflow"
    }
  }
}
```

---

## Testing Results

### Test 1: Actual Crew Run (No Opportunities)
- **Date:** 2026-02-02 16:36:34
- **Sources:** 5, Signals: 2
- **Homelab Opportunities:** 0
- **Work Opportunities:** 0
- **Result:** ✅ Correctly handled no opportunities case
- **Slack Message:** "_No homelab opportunities identified today_"
- **JSON Structure:** `{"opportunities": {"homelab": {}, "work": {}}}`

### Test 2: Mock Opportunities
- **Homelab:** 2 opportunities (H1, H2)
- **Work:** 1 opportunity (W1)
- **Result:** ✅ All opportunities parsed and numbered correctly
- **Slack Message:** Shows `[H1]`, `[H2]`, `[W1]` formatting
- **Mapping File:** All 3 opportunities saved with full data
- **Footer:** Approval syntax instructions included

---

## Success Criteria Met

- ✅ `opportunity_parser.py` created with parsing functions
- ✅ `slack_formatter.py` updated with numbered opportunity formatting
- ✅ `crew.py` integrated parser and calls new formatter function
- ✅ Opportunity IDs assigned sequentially (H1, H2, H3... for homelab)
- ✅ Slack digest shows `[H1]`, `[W1]` numbered format
- ✅ Opportunity mapping saved to `output/opportunities_{date}.json`
- ✅ JSON includes opportunities field with parsed data
- ✅ Footer includes approval syntax instructions
- ✅ Handles no-opportunity case gracefully

---

## Output Files Created

| File | Purpose | Example |
|------|---------|---------|
| `/opt/crewai/output/opportunities_2026-02-02.json` | Maps opportunity IDs to full data for Catalyst | `{"H1": {...}, "W1": {...}}` |
| `/opt/crewai/output/slack_digest_2026-02-02_*.json` | n8n workflow consumption | Contains `opportunities` field + `slack_message` |
| `/opt/crewai/output/digest_2026-02-02_*.md` | Human-readable markdown | Full digest with Strategist outputs |

---

## Format Examples

### Slack Message with Opportunities
```
📊 *Strategic Intelligence Digest*
_2026-02-02 16:37:25_
Sources: 5 | Signals: 8

---
*🔍 SCOUT SIGNALS*
[preview...]

---
*🧠 ANALYST SYNTHESIS*
[preview...]

---
*🏠 HOMELAB OPPORTUNITIES*

*[H1] Local LLM Fine-tuning with Ollama*
_Connects to AI Box project (192.168.1.204) and local inference goals_
Signal: New Ollama fine-tuning capabilities announced
Next Steps: Research Ollama adapter support

*[H2] Self-hosted Analytics with Plausible*
_Could replace Google Analytics dependency for Family Hub_
Signal: Plausible Analytics trending on GitHub
Next Steps: Deploy test instance on Proxmox

---
*💼 WORK OPPORTUNITIES*

*[W1] AI-Assisted Code Review Patterns*
_Directly relates to velocity improvement goals_
Signal: Claude Code review capabilities emerging
Next Steps: Pilot with one team sprint

---
_Reply: `approve [ID] [type]` to generate deliverable_
_Types: `plan` (homelab), `brief` or `slide` (work)_
_Example: `approve H1, W1 brief`_
```

### Slack Message without Opportunities
```
📊 *Strategic Intelligence Digest*
[header...]

---
*🏠 HOMELAB OPPORTUNITIES*

_No homelab opportunities identified today_

---
*💼 WORK OPPORTUNITIES*

_No work opportunities identified today_

---
_Reply: `approve [ID] [type]` to generate deliverable_
_Types: `plan` (homelab), `brief` or `slide` (work)_
_Example: `approve H1, W1 brief`_
```

---

## Key Implementation Details

### Regex Parsing
- Split text by `### Opportunity:` headers
- Extract title from first line after header
- Extract subsections using `**Subsection:**` pattern
- Handle both opportunities and "No opportunities" statements

### ID Assignment
- Homelab: H1, H2, H3... (sequential)
- Work: W1, W2, W3... (sequential)
- IDs assigned in order of appearance in Strategist output

### Error Handling
- Empty opportunities → Returns empty dict `{}`
- No `### Opportunity:` headers found → Returns empty dict
- Missing subsections → Returns empty string for that subsection
- Parser never crashes, always returns valid dict structure

---

## What's Ready for Phase 3

Phase 3 will build the Catalyst agent that generates deliverables for approved opportunities.

**Phase 3 can now:**
- Read opportunity mapping file: `output/opportunities_{date}.json`
- Extract full opportunity data by ID (e.g., "H1")
- Load relevant context (homelab for H*, work for W*)
- Generate deliverable based on type (plan/brief/slide)

**Catalyst will receive:**
```python
opportunity_data = {
    "title": "Local LLM Fine-tuning",
    "full_text": "### Opportunity: Local LLM...",  # Complete original text
    "relevance": "Connects to AI Box project...",
    "signal": "New Ollama capabilities...",
    "next_steps": "Research fine-tuning workflow..."
}
```

---

## Observations from Phase 2

### Parser Robustness
- Handles both "opportunity exists" and "no opportunities" cases
- Gracefully handles missing subsections
- Regex pattern is flexible (allows whitespace variations)
- Never crashes, always returns valid structure

### Format Consistency
- Numbered IDs make approval syntax unambiguous
- Footer instructions guide user on correct syntax
- Approval poller (Phase 5) will easily identify `[H1]` vs `[W1]`

### JSON Structure
- Opportunity mapping file is decoupled from Slack digest
- Catalyst can run hours/days after digest (uses mapping file)
- Easy to test Catalyst with mock opportunity data
- Clear separation: parse once, use multiple times

---

## Files Modified Summary

| File | Change | Status |
|------|--------|--------|
| `/opt/crewai/tools/opportunity_parser.py` | Created (new tool) | ✅ Complete |
| `/opt/crewai/tools/slack_formatter.py` | Added numbered opportunity functions | ✅ Complete |
| `/opt/crewai/crew.py` | Integrated parser, updated formatter calls | ✅ Complete |
| Backups | slack_formatter.py and crew.py backed up | ✅ Complete |

---

## Next Session: Phase 3

**Estimated Time:** 3 hours
**Risk:** Medium
**Goal:** Create Catalyst agent script to generate deliverables

**Tasks:**
1. Create `catalyst.py` standalone script
2. Implement 3 task templates (Technical Plan, Leadership Brief, Client Slide)
3. Add CLI argument parsing (--digest-date, --opportunity, --type)
4. Test with mock opportunity from Phase 2

---

*Phase 2 completed: 2026-02-02 16:40*
*Ready for Phase 3 implementation*
