# Phase 2: Slack Message Refactor - Work Plan

## Current State Analysis

### Current Architecture
1. **Crew Output:** Single JSON file with all opportunities embedded in `slack_message` string
2. **n8n Workflow:** "Strategic Intelligence Daily" reads JSON, posts single large message to Slack
3. **User Experience:** One long digest in a single message, thread-based approval (`approve H1 plan`)

### Current JSON Structure
```json
{
  "timestamp": "2026-02-04 11:01:19",
  "sources_count": 5,
  "signals_count": 6,
  "slack_message": "[LONG STRING WITH ALL CONTENT]",
  "opportunities": {
    "homelab": {
      "H1": { "title": "...", "relevance": "...", "signal": "...", "next_steps": "..." },
      "H2": { ... },
      "H3": { ... }
    },
    "work": {}
  },
  "raw_outputs": {
    "scout": "...",
    "analyst": "..."
  }
}
```

### Problems to Solve
1. Single message is too long and hard to scan
2. No interactive buttons (approval requires typing in thread)
3. All opportunities mixed together in one UI element

---

## Target State (Phase 2 Complete)

### New Architecture
1. **Crew Output:** JSON with array of individual opportunity objects, each ready for separate message
2. **n8n Workflow:** Iterates over array, posts one Slack message per opportunity
3. **User Experience:** 3-5 individual messages, each with [Develop] [Ignore] buttons

### Target JSON Structure
```json
{
  "timestamp": "2026-02-04 11:01:19",
  "sources_count": 5,
  "signals_count": 6,
  "summary": {
    "scout_preview": "[First 500 chars]",
    "analyst_preview": "[First 800 chars]"
  },
  "messages": [
    {
      "opportunity_id": "H1",
      "category": "homelab",
      "title": "Local Audio Generation for Home Automation",
      "relevance": "Connects directly to Home Assistant...",
      "signal": "ACE-Step-1.5 achieving commercial-quality...",
      "next_steps": "1. Monitor ACE-Step-1.5 community validation...",
      "slack_blocks": [
        {
          "type": "section",
          "text": { "type": "mrkdwn", "text": "*[H1] Local Audio Generation*\n\n**Relevance:** ..." }
        },
        {
          "type": "actions",
          "elements": [
            { "type": "button", "text": "Develop", "value": "H1", "action_id": "develop_H1" },
            { "type": "button", "text": "Ignore", "value": "H1", "action_id": "ignore_H1" }
          ]
        }
      ]
    },
    {
      "opportunity_id": "H2",
      "category": "homelab",
      ...
    }
  ]
}
```

### Target Slack Experience
**Morning at 6 AM:**
1. Scout/Analyst summary (single message, no buttons)
2. Message 1: [H1] Local Audio Generation [Develop] [Ignore]
3. Message 2: [H2] Code Assistant Integration [Develop] [Ignore]
4. Message 3: [H3] Agent Sandboxing [Develop] [Ignore]

Each message is scannable, actionable, and independent.

---

## Implementation Tasks

### Task 1: Create Slack Button Message Formatter
**File:** `/opt/crewai/tools/slack_formatter.py`
**New Function:** `create_opportunity_message_blocks()`

```python
def create_opportunity_message_blocks(
    opportunity_id: str,
    category: str,  # "homelab" or "work"
    title: str,
    relevance: str,
    signal: str,
    next_steps: str
) -> List[Dict]:
    """
    Create Slack Block Kit message for a single opportunity with action buttons

    Returns:
        List of Slack blocks (section + actions)
    """
    # Format text
    text = f"*[{opportunity_id}] {title}*\n\n"
    text += f"**Relevance:** {relevance}\n\n"
    text += f"**Signal:** {signal}\n\n"
    text += f"**Next Steps:**\n{next_steps}"

    # Build blocks
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Develop"
                    },
                    "style": "primary",
                    "value": opportunity_id,
                    "action_id": f"develop_{opportunity_id}"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Ignore"
                    },
                    "value": opportunity_id,
                    "action_id": f"ignore_{opportunity_id}"
                }
            ]
        }
    ]

    return blocks
```

### Task 2: Create New Crew Output Format Function
**File:** `/opt/crewai/tools/slack_formatter.py`
**New Function:** `prepare_opportunity_messages()`

```python
def prepare_opportunity_messages(
    scout_output: str,
    analyst_output: str,
    homelab_opportunities: Dict[str, Dict[str, str]],
    work_opportunities: Dict[str, Dict[str, str]],
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Prepare structured output for n8n to iterate and post individual messages

    Returns:
        {
            "timestamp": "...",
            "summary": { scout_preview, analyst_preview },
            "messages": [ array of opportunity message objects ]
        }
    """
    messages = []

    # Process homelab opportunities
    for opp_id in sorted(homelab_opportunities.keys()):
        opp = homelab_opportunities[opp_id]
        message = {
            "opportunity_id": opp_id,
            "category": "homelab",
            "title": opp["title"],
            "relevance": opp["relevance"],
            "signal": opp["signal"],
            "next_steps": opp["next_steps"],
            "slack_blocks": create_opportunity_message_blocks(
                opp_id, "homelab",
                opp["title"], opp["relevance"], opp["signal"], opp["next_steps"]
            )
        }
        messages.append(message)

    # Process work opportunities
    for opp_id in sorted(work_opportunities.keys()):
        opp = work_opportunities[opp_id]
        message = {
            "opportunity_id": opp_id,
            "category": "work",
            "title": opp["title"],
            "relevance": opp["relevance"],
            "signal": opp["signal"],
            "next_steps": opp["next_steps"],
            "slack_blocks": create_opportunity_message_blocks(
                opp_id, "work",
                opp["title"], opp["relevance"], opp["signal"], opp["next_steps"]
            )
        }
        messages.append(message)

    return {
        "timestamp": metadata.get("timestamp"),
        "sources_count": metadata.get("sources_count"),
        "signals_count": metadata.get("signals_count"),
        "summary": {
            "scout_preview": scout_output[:500] + "..." if len(scout_output) > 500 else scout_output,
            "analyst_preview": analyst_output[:800] + "..." if len(analyst_output) > 800 else analyst_output
        },
        "messages": messages
    }
```

### Task 3: Modify crew.py to Use New Format
**File:** `/opt/crewai/crew.py`
**Changes:**
1. Import new function: `from tools.slack_formatter import prepare_opportunity_messages`
2. After parsing opportunities, call new function:
   ```python
   message_payload = prepare_opportunity_messages(
       scout_output, analyst_output,
       homelab_opportunities, work_opportunities,
       metadata
   )
   ```
3. Save to new file: `output/slack_messages_{timestamp}.json`
4. Keep opportunity mapping file for Phase 3 button handlers

### Task 4: Create n8n Workflow
**Workflow Name:** "Strategic Intelligence Daily v2"
**Trigger:** Schedule (6:00 AM daily)

**Nodes:**
1. **Schedule Trigger** (6:00 AM cron)
2. **SSH to Container 118** - Execute crew.py
3. **Read JSON File** - Load `/opt/crewai/output/slack_messages_*.json`
4. **Split Into Items** - Loop over `messages` array
5. **Post to Slack** - For each item, POST with `blocks` parameter
6. **Error Handler** - Log failures to Slack

**SSH Command:**
```bash
cd /opt/crewai && source venv/bin/activate && python3 crew.py
```

**Slack POST Node Configuration:**
```
URL: https://slack.com/api/chat.postMessage
Method: POST
Headers:
  Authorization: Bearer {{SLACK_BOT_TOKEN}}
  Content-Type: application/json
Body:
{
  "channel": "#trend-monitoring",
  "blocks": {{$json.slack_blocks}}
}
```

### Task 5: Testing Strategy
1. **Local Test:** Run crew.py manually, verify JSON structure
2. **Slack Block Kit Validator:** Test blocks JSON in Slack Block Kit Builder
3. **n8n Test:** Trigger workflow manually, verify messages post correctly
4. **Button Test:** Click buttons, verify interaction payload received (Phase 3)

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Slack Block Kit syntax errors | Medium | Medium | Use Block Kit Builder to validate JSON before deployment |
| n8n loop iteration fails | Low | High | Test loop with small sample JSON first |
| Button clicks not received | Medium | Low | Phase 3 problem, can proceed with Phase 2 completion |
| Too many messages (rate limiting) | Low | Low | Crew typically produces 3-5 opportunities, well under limits |

---

## Success Criteria (Phase 2)

Phase 2 is complete when:

1. ✅ Crew.py outputs new JSON format with `messages` array
2. ✅ Each message includes properly formatted Slack blocks
3. ✅ n8n workflow iterates over messages array successfully
4. ✅ 6 AM run produces 3-5 individual Slack messages (not one digest)
5. ✅ Each message displays [Develop] [Ignore] buttons
6. ✅ Messages are scannable and independent

**Not required for Phase 2:**
- Button clicks actually triggering actions (Phase 3)
- Catalyst integration (Phase 3)
- Email delivery for work items (Phase 3)

---

## Next Session (Phase 3)

After Phase 2 is verified working:
1. Create button interaction webhook in n8n
2. Map button clicks to opportunity IDs
3. Trigger Catalyst for [Develop] clicks
4. Write Technical Plans to `/opt/crewai/homelab-outputs/` (syncs to Obsidian)
5. Handle work item second-level buttons ([Executive Brief] [Sales Slide])
6. Set up email delivery for work deliverables

---

## File Artifacts

**New/Modified Files:**
- `/opt/crewai/tools/slack_formatter.py` (new functions)
- `/opt/crewai/crew.py` (use new output format)
- n8n workflow JSON (new "Strategic Intelligence Daily v2")

**Preserved Files:**
- `/opt/crewai/tools/opportunity_parser.py` (still needed for Phase 3)
- `/opt/crewai/output/opportunity_mapping_*.json` (still needed for button handlers)
