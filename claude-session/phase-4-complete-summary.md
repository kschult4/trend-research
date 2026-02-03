# Criterion 5 Phase 4: COMPLETE

**Date:** 2026-02-02
**Duration:** ~1.5 hours
**Status:** ✅ COMPLETE

---

## Phase 4 Goal

Create approval parser to extract and validate approval/dismiss commands from Slack replies.

---

## Changes Made

### Files Created

**1. `/opt/crewai/tools/approval_parser.py` (NEW)**
- `parse_approval_syntax(text)` - Parse approval/dismiss commands from text
- `parse_single_approval(item, action)` - Parse individual opportunity approval
- `validate_against_opportunities(approvals, opportunities)` - Validate IDs exist in digest
- `generate_help_message(errors)` - Generate user-friendly error messages
- Comprehensive unit tests with 17 test cases

---

## Approval Syntax Supported

### Homelab Opportunities

**Format:** `approve H[number] [plan]`
- `approve H1` → Technical Plan (default)
- `approve H2 plan` → Technical Plan (explicit)
- Type `plan` is default for homelab opportunities
- Other types (`brief`, `slide`) are rejected with error

### Work Opportunities

**Format:** `approve W[number] <brief|slide>`
- `approve W1 brief` → Leadership Brief
- `approve W2 slide` → Client Slide
- Type MUST be specified explicitly (no default)
- Work opportunities without type are rejected with error

### Multiple Approvals

**Format:** Comma-separated list
- `approve H1, W1 brief` → Plan for H1, Brief for W1
- `approve H1, H2, W1 brief, W2 slide` → Multiple mixed

### Dismiss

**Format:** `dismiss H[number]` or `dismiss W[number]`
- `dismiss H1` → Log rejection, no Catalyst execution
- `dismiss W2` → Log rejection, no Catalyst execution
- Type not required for dismiss

---

## Core Functions

### 1. parse_approval_syntax(text)

**Purpose:** Parse approval/dismiss commands from Slack reply text

**Input:**
```python
text = "approve H1, W1 brief"
```

**Output:**
```python
{
    "valid": True,
    "action": "approve",
    "approvals": [
        {"opp_id": "H1", "type": "plan"},
        {"opp_id": "W1", "type": "brief"}
    ],
    "errors": []
}
```

**Validation Rules:**
- Message must start with "approve" or "dismiss"
- At least one opportunity must be specified
- Homelab IDs (H*) default to "plan" type
- Work IDs (W*) must specify "brief" or "slide"
- Invalid types rejected with descriptive error

### 2. validate_against_opportunities(approvals, opportunities)

**Purpose:** Validate parsed approvals against actual opportunity mapping

**Input:**
```python
approvals = [
    {"opp_id": "H1", "type": "plan"},
    {"opp_id": "W99", "type": "brief"}  # Doesn't exist
]

opportunities = {
    "H1": {"title": "...", "relevance": "..."},
    "W1": {"title": "...", "relevance": "..."}
}
```

**Output:**
```python
{
    "valid": False,
    "validated_approvals": [
        {
            "opp_id": "H1",
            "type": "plan",
            "opportunity_data": {"title": "...", "relevance": "..."}
        }
    ],
    "errors": ["Opportunity W99 not found in digest"]
}
```

**Validation:**
- Checks each opportunity ID exists in mapping file
- Returns enriched approvals with full opportunity data
- Returns errors for non-existent opportunities

### 3. generate_help_message(errors)

**Purpose:** Generate user-friendly error message for invalid syntax

**Output:**
```
⚠️ Invalid approval syntax. Here's how to use it:

*Homelab opportunities:*
  • `approve H1` (generates Technical Plan)

*Work opportunities:*
  • `approve W1 brief` (generates Leadership Brief)
  • `approve W2 slide` (generates Client Slide)

*Multiple approvals:*
  • `approve H1, W1 brief, W2 slide`

*Dismiss:*
  • `dismiss H1` or `dismiss W2`

*Errors detected:*
  • Work opportunities require 'brief' or 'slide' (got: none)
  • Opportunity H99 not found in digest
```

---

## Testing Results

### Unit Tests (All Tests Passing)

**Test Suite:** 17 syntax parsing tests + 6 validation tests

**Syntax Parsing Tests:**
- ✅ Homelab with default type: `approve H1` → plan
- ✅ Homelab lowercase: `approve h2` → H2, plan
- ✅ Homelab with explicit plan: `approve H3 plan` → plan
- ✅ Work with brief: `approve W1 brief` → brief
- ✅ Work with slide: `approve w2 slide` → W2, slide
- ✅ Multiple mixed: `approve H1, W1 brief` → 2 approvals
- ✅ Multiple complex: `approve H1, H2, W1 brief, W2 slide` → 4 approvals
- ✅ Dismiss homelab: `dismiss H1` → type "none"
- ✅ Dismiss work: `dismiss w2` → W2, type "none"
- ✅ Work without type: `approve W1` → FAIL (expected)
- ✅ Homelab with slide: `approve H1 slide` → FAIL (expected)
- ✅ Homelab with brief: `approve H1 brief` → FAIL (expected)
- ✅ Work with plan: `approve W1 plan` → FAIL (expected)
- ✅ Invalid syntax: `random text` → FAIL (expected)
- ✅ No opportunities: `approve` → FAIL (expected)
- ✅ Invalid prefix: `approve X1` → FAIL (expected)
- ✅ Missing number: `approve H` → FAIL (expected)

**Results:** 17/17 tests passed (100%)

**Validation Tests:**
- ✅ Valid homelab opportunity (H1 exists)
- ✅ Valid work opportunity (W1 exists)
- ✅ Multiple valid opportunities
- ✅ Non-existent homelab opportunity (H99) → validation error
- ✅ Non-existent work opportunity (W99) → validation error
- ✅ One valid, one invalid → partial validation

**Results:** 6/6 tests passed (100%)

### Real-World Integration Test

Tested against actual Phase 2 opportunity mapping (`opportunities_2026-02-02.json`):

**Available Opportunities:**
- H1: "Local LLM Fine-tuning with Ollama"
- H2: "Self-hosted Analytics with Plausible"
- W1: "AI-Assisted Code Review Patterns"

**Test Results:**
```
Command: approve H1
  Syntax valid: True
  Opportunities exist: True
  ✅ Ready for Catalyst execution
     - H1 (plan): Local LLM Fine-tuning with Ollama

Command: approve W1 brief
  Syntax valid: True
  Opportunities exist: True
  ✅ Ready for Catalyst execution
     - W1 (brief): AI-Assisted Code Review Patterns

Command: approve W1 slide
  Syntax valid: True
  Opportunities exist: True
  ✅ Ready for Catalyst execution
     - W1 (slide): AI-Assisted Code Review Patterns

Command: approve H1, W1 brief
  Syntax valid: True
  Opportunities exist: True
  ✅ Ready for Catalyst execution
     - H1 (plan): Local LLM Fine-tuning with Ollama
     - W1 (brief): AI-Assisted Code Review Patterns

Command: approve H99
  Syntax valid: True
  Opportunities exist: False
  ❌ Validation failed: ['Opportunity H99 not found in digest']

Command: approve W99 brief
  Syntax valid: True
  Opportunities exist: False
  ❌ Validation failed: ['Opportunity W99 not found in digest']
```

**All tests passed successfully** ✅

---

## Success Criteria Met

- ✅ approval_parser.py created with parsing and validation functions
- ✅ All 17 unit tests pass (syntax parsing)
- ✅ All 6 validation tests pass (opportunity existence checking)
- ✅ Valid approval syntax parsed correctly
- ✅ Invalid syntax returns helpful errors
- ✅ Multiple approvals in one message handled
- ✅ Homelab defaults to 'plan'
- ✅ Work requires explicit 'brief' or 'slide'
- ✅ Dismiss syntax supported (type="none")
- ✅ Case-insensitive parsing (h1 = H1)
- ✅ Validation against real opportunity mapping works
- ✅ Help message generation tested

---

## Key Implementation Details

### Regex Pattern for Opportunity IDs

```python
pattern = r'^([hw])(\d+)(?:\s+(plan|brief|slide))?$'
```

**Components:**
- `([hw])` - Capture H or W (case-insensitive)
- `(\d+)` - Capture one or more digits
- `(?:\s+(plan|brief|slide))?` - Optional whitespace + type

**Examples:**
- `h1` → matches: H, 1, None
- `w2 brief` → matches: W, 2, brief
- `H3 plan` → matches: H, 3, plan

### Type Validation Logic

**Homelab (H*):**
```python
if prefix == 'H':
    if deliverable_type is None or deliverable_type == 'plan':
        result["type"] = "plan"  # Default to plan
        result["valid"] = True
    else:
        result["errors"].append(f"Homelab opportunities only support 'plan'")
```

**Work (W*):**
```python
elif prefix == 'W':
    if deliverable_type in ['brief', 'slide']:
        result["type"] = deliverable_type
        result["valid"] = True
    else:
        result["errors"].append(f"Work opportunities require 'brief' or 'slide'")
```

### Comma Splitting for Multiple Approvals

```python
items = [item.strip() for item in items_text.split(',')]
for item in items:
    parsed_item = parse_single_approval(item, action)
    if parsed_item["valid"]:
        result["approvals"].append(...)
    else:
        result["errors"].extend(parsed_item["errors"])
```

**Behavior:**
- Split on commas
- Trim whitespace from each item
- Parse each individually
- Collect all errors (doesn't fail fast)
- Valid only if all items valid and no errors

### Error Handling Philosophy

**Descriptive Errors:**
- "Work opportunities require 'brief' or 'slide' (got: none)"
- "Opportunity H99 not found in digest"
- "Invalid format: 'x1' (expected: H1, W2 brief, etc.)"

**Help Message:**
- Always includes full syntax examples
- Shows correct format for each opportunity type
- Lists specific errors detected
- Encourages correct retry

---

## What's Ready for Phase 5

Phase 5 will create the n8n workflow to poll Slack for approvals and trigger Catalyst.

**Phase 5 can now:**
- Poll Slack for replies to digest message
- Extract reply text and call `parse_approval_syntax(text)`
- Check if `result["valid"] == True`
- If valid, call `validate_against_opportunities(approvals, opportunities_from_mapping_file)`
- For each validated approval, call Catalyst:
  ```bash
  python3 catalyst.py --digest-date YYYY-MM-DD --opportunity H1 --type plan
  ```
- If invalid, post help message to Slack thread

**n8n workflow will receive:**
```python
{
    "valid": True,
    "action": "approve",
    "approvals": [
        {"opp_id": "H1", "type": "plan"},
        {"opp_id": "W1", "type": "brief"}
    ],
    "errors": []
}
```

**n8n workflow will loop through approvals and trigger Catalyst for each.**

---

## Example n8n Integration

### n8n Code Node (Python)

```python
import sys
sys.path.insert(0, '/opt/crewai')
from tools.approval_parser import parse_approval_syntax, validate_against_opportunities
import json

# Get reply text from Slack API
reply_text = items[0].text  # From Slack conversations.replies

# Parse syntax
parsed = parse_approval_syntax(reply_text)

if not parsed["valid"]:
    # Post help message to Slack
    from tools.approval_parser import generate_help_message
    help_msg = generate_help_message(parsed["errors"])
    # Return help_msg for Slack posting node
    return [{"json": {"error": True, "help_message": help_msg}}]

# Load opportunity mapping
digest_date = "2026-02-02"  # Extract from digest timestamp
with open(f'/opt/crewai/output/opportunities_{digest_date}.json') as f:
    data = json.load(f)
    opportunities = data['opportunities']

# Validate against opportunities
validated = validate_against_opportunities(parsed["approvals"], opportunities)

if not validated["valid"]:
    # Generate error message
    help_msg = generate_help_message(validated["errors"])
    return [{"json": {"error": True, "help_message": help_msg}}]

# Return validated approvals for Catalyst trigger loop
return [{"json": {"approvals": validated["validated_approvals"]}}]
```

---

## Observations from Phase 4

### Parser Robustness

**Case-Insensitive:**
- `approve h1` = `approve H1` = `approve H1`
- User doesn't need to remember exact case

**Whitespace Flexible:**
- `approve H1,W1 brief` works (no space after comma)
- `approve H1, W1 brief` works (space after comma)
- Leading/trailing whitespace ignored

**Comprehensive Error Messages:**
- Each invalid item generates specific error
- Multiple errors collected (doesn't fail on first error)
- Help message provides examples and guidance

### Type Enforcement

**Design Decision Validation:**
- Homelab defaulting to `plan` is intuitive (only one type)
- Work requiring explicit type prevents ambiguity
- Users can't accidentally request wrong deliverable type
- Clear error messages guide correct usage

**Edge Cases Handled:**
- `approve H1 brief` → Rejected (homelab doesn't support brief)
- `approve W1 plan` → Rejected (work doesn't support plan)
- `approve W1` → Rejected (work requires explicit type)
- All edge cases tested and working correctly

### Validation Layer

**Two-Stage Validation:**
1. **Syntax validation:** Is the format correct?
2. **Existence validation:** Does the opportunity exist in the digest?

**Benefits:**
- Syntax errors caught early (no need to load mapping file)
- Existence errors caught before Catalyst execution
- User gets immediate feedback on what went wrong
- n8n workflow can branch on validation result

### Testing Quality

**Comprehensive Coverage:**
- 17 syntax parsing tests (valid + invalid cases)
- 6 opportunity validation tests
- Real-world integration test with Phase 2 data
- All edge cases covered

**Confidence Level:**
- 100% test pass rate
- Real data tested successfully
- Ready for n8n integration

---

## Files Modified Summary

| File | Change | Location | Status |
|------|--------|----------|--------|
| `/opt/crewai/tools/approval_parser.py` | Created (new tool) | Container 118 at 192.168.1.18 | ✅ Complete |
| Unit tests | Embedded in approval_parser.py | Run with `python3 tools/approval_parser.py` | ✅ All passing |

**No backups needed:** New file creation (no existing file modified)

---

## Next Session: Phase 5

**Estimated Time:** 3 hours
**Risk:** Medium
**Goal:** Create n8n workflow to poll Slack for approvals and trigger Catalyst

**Tasks:**
1. Create "Approval Poller and Catalyst Trigger" workflow in n8n
2. Add Schedule Trigger (every 5 minutes)
3. Add Slack API nodes (conversations.history, conversations.replies)
4. Add SSH Exec nodes to call approval_parser.py
5. Add loop to trigger Catalyst for each approval
6. Add Slack posting nodes for deliverables and error messages
7. Test end-to-end approval flow

**Prerequisites:**
- Slack channel ID for #trend-monitoring
- Kyle's Slack user ID (for reply filtering)
- SSH credentials verified in n8n
- Create empty approvals log: `touch /opt/crewai/output/approvals.jsonl`

---

*Phase 4 completed: 2026-02-02 18:00*
*Ready for Phase 5 implementation*
