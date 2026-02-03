# Criterion 5: Implementation Plan

**Date:** 2026-02-02
**Architecture:** See `criterion-5-architecture.md`
**Estimated Total Time:** 12.5 hours (2-3 sessions)

---

## Implementation Order and Dependencies

```
Phase 1: Strategist Formatting
    ↓ (enables)
Phase 2: Opportunity Parsing
    ↓ (enables)
Phase 3: Catalyst Agent
    ↓ (parallel with)
Phase 4: Approval Parser
    ↓ (both required for)
Phase 5: n8n Approval Poller
    ↓ (validates)
Phase 6: Integration Testing
```

---

## Phase 1: Strategist Output Formatting

**Duration:** 1 hour
**Risk:** Low
**Dependencies:** None

### Files to Modify
1. `/opt/crewai/crew.py` - Update Strategist task descriptions

### Changes Required

#### Homelab Strategist Task Update
```python
homelab_strategist_task = Task(
    description=f"""Evaluate the Analyst's synthesis for homelab relevance...

    OUTPUT REQUIREMENTS:
    For each opportunity you identify, use this EXACT structure:

    ### Opportunity: [Clear Title]
    **Relevance:** [Why this matters to Kyle's homelab context]
    **Signal:** [What specific development/trend triggered this]
    **Next Steps:** [What could be explored/implemented]

    Each opportunity must be separated by the ### Opportunity: header.
    Be selective - only flag opportunities that are genuinely actionable.
    """,
    agent=homelab_strategist,
    expected_output="Structured opportunities with clear titles, relevance, signal, and next steps"
)
```

#### Work Strategist Task Update
```python
work_strategist_task = Task(
    description=f"""Evaluate the Analyst's synthesis for work relevance...

    OUTPUT REQUIREMENTS:
    For each opportunity you identify, use this EXACT structure:

    ### Opportunity: [Clear Title]
    **Relevance:** [Why this matters to Kyle's work context]
    **Signal:** [What specific development/trend triggered this]
    **Next Steps:** [What could be explored/piloted/advocated]

    Each opportunity must be separated by the ### Opportunity: header.
    Be selective - only flag opportunities that are genuinely actionable.
    """,
    agent=work_strategist,
    expected_output="Structured opportunities with clear titles, relevance, signal, and next steps"
)
```

### Testing
```bash
# SSH to container 118
ssh root@192.168.1.18

# Activate venv
cd /opt/crewai
source venv/bin/activate

# Run crew manually
python3 crew.py

# Check output format
ls -la output/
cat output/digest_*.md  # Verify Strategist sections have ### Opportunity: headers
```

### Success Criteria
- ✅ Homelab Strategist output contains `### Opportunity:` headers
- ✅ Work Strategist output contains `### Opportunity:` headers
- ✅ Each opportunity has Relevance, Signal, Next Steps subsections
- ✅ Multiple opportunities clearly separated

### Rollback
- Revert crew.py to backup: `cp crew.py.backup-before-criterion4 crew.py`

---

## Phase 2: Opportunity Parsing and Digest Formatting

**Duration:** 2 hours
**Risk:** Low
**Dependencies:** Phase 1 complete

### Files to Create
1. `/opt/crewai/tools/opportunity_parser.py` (new)

### Files to Modify
1. `/opt/crewai/tools/slack_formatter.py` (modify)
2. `/opt/crewai/crew.py` (modify)

### Implementation: `tools/opportunity_parser.py`

```python
#!/usr/bin/env python3
"""
Opportunity Parser
Extracts and numbers opportunities from Strategist outputs
"""

import re
from typing import List, Dict, Any

def parse_opportunities(text: str, prefix: str) -> Dict[str, Dict[str, str]]:
    """
    Parse structured opportunities from Strategist output

    Args:
        text: Strategist output text
        prefix: 'H' for homelab, 'W' for work

    Returns:
        Dict mapping IDs to opportunity data
        Example: {"H1": {"title": "...", "text": "...", "relevance": "...", "signal": "...", "next_steps": "..."}}
    """
    opportunities = {}

    # Split by ### Opportunity: headers
    sections = re.split(r'###\s+Opportunity:\s+', text)

    # Skip first section (text before first opportunity)
    for idx, section in enumerate(sections[1:], start=1):
        opp_id = f"{prefix}{idx}"

        # Extract title (first line)
        lines = section.strip().split('\n')
        title = lines[0].strip()

        # Extract subsections
        relevance = extract_subsection(section, 'Relevance')
        signal = extract_subsection(section, 'Signal')
        next_steps = extract_subsection(section, 'Next Steps')

        opportunities[opp_id] = {
            "title": title,
            "full_text": section.strip(),
            "relevance": relevance,
            "signal": signal,
            "next_steps": next_steps
        }

    return opportunities

def extract_subsection(text: str, subsection_name: str) -> str:
    """Extract content from **Subsection:** pattern"""
    pattern = rf'\*\*{subsection_name}:\*\*\s*(.+?)(?=\*\*|\Z)'
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""

def format_opportunity_for_slack(opp_id: str, opp_data: Dict[str, str]) -> str:
    """
    Format single opportunity for Slack digest

    Args:
        opp_id: e.g., "H1", "W2"
        opp_data: Opportunity dict with title, relevance, signal, next_steps

    Returns:
        Formatted text for Slack
    """
    lines = [
        f"*[{opp_id}] {opp_data['title']}*",
        f"_{opp_data['relevance']}_",
        f"Signal: {opp_data['signal']}",
        f"Next Steps: {opp_data['next_steps']}",
        ""
    ]
    return "\n".join(lines)

def save_opportunity_mapping(
    opportunities: Dict[str, Dict[str, str]],
    digest_date: str,
    digest_message_ts: str = "",
    output_file: str = None
) -> str:
    """
    Save opportunity mapping to JSON file for Catalyst reference

    Args:
        opportunities: Combined dict of all opportunities (H* and W*)
        digest_date: YYYY-MM-DD
        digest_message_ts: Slack message timestamp (filled in later by n8n)
        output_file: Path to save (default: output/opportunities_{date}.json)

    Returns:
        Path to saved file
    """
    import json
    from datetime import datetime

    if output_file is None:
        output_file = f"output/opportunities_{digest_date}.json"

    payload = {
        "digest_date": digest_date,
        "digest_message_ts": digest_message_ts,
        "created_at": datetime.now().isoformat(),
        "opportunities": opportunities
    }

    with open(output_file, 'w') as f:
        json.dump(payload, f, indent=2)

    return output_file

# Unit tests
if __name__ == "__main__":
    test_text = """
    Some preamble text...

    ### Opportunity: Local LLM Fine-tuning
    **Relevance:** This connects to your AI Box project
    **Signal:** New quantization techniques for consumer hardware
    **Next Steps:** Research Ollama fine-tuning capabilities

    ### Opportunity: Self-hosted Analytics
    **Relevance:** Replace Google Analytics with local option
    **Signal:** Plausible Analytics trending on GitHub
    **Next Steps:** Deploy test instance on Proxmox
    """

    opps = parse_opportunities(test_text, 'H')
    print("Parsed opportunities:")
    for opp_id, opp_data in opps.items():
        print(f"\n{opp_id}: {opp_data['title']}")
        print(f"  Relevance: {opp_data['relevance'][:50]}...")
        print(f"  Signal: {opp_data['signal'][:50]}...")

    # Test formatting
    print("\n--- Slack Format ---")
    for opp_id, opp_data in opps.items():
        print(format_opportunity_for_slack(opp_id, opp_data))
```

### Implementation: Update `tools/slack_formatter.py`

Add new function:
```python
def format_for_slack_with_opportunities(
    scout_output: str,
    analyst_output: str,
    homelab_opportunities: Dict[str, Dict[str, str]],
    work_opportunities: Dict[str, Dict[str, str]],
    metadata: Dict[str, Any]
) -> str:
    """
    Format digest with numbered opportunities

    Args:
        scout_output: Scout agent output
        analyst_output: Analyst synthesis
        homelab_opportunities: Dict of H* opportunities
        work_opportunities: Dict of W* opportunities
        metadata: Sources count, signals count, timestamp

    Returns:
        Formatted Slack message
    """
    from tools.opportunity_parser import format_opportunity_for_slack

    lines = []

    # Header
    lines.append("📊 *Strategic Intelligence Digest*")
    lines.append(f"_{metadata.get('timestamp', '')}_")
    lines.append(f"Sources: {metadata.get('sources_count', 'N/A')} | Signals: {metadata.get('signals_count', 'N/A')}")
    lines.append("")

    # Scout Section (condensed preview)
    lines.append("---")
    lines.append("*🔍 SCOUT SIGNALS*")
    lines.append("")
    scout_preview = scout_output[:500] + "..." if len(scout_output) > 500 else scout_output
    lines.append(scout_preview)
    lines.append("")

    # Analyst Section (condensed preview)
    lines.append("---")
    lines.append("*🧠 ANALYST SYNTHESIS*")
    lines.append("")
    analyst_preview = analyst_output[:800] + "..." if len(analyst_output) > 800 else analyst_output
    lines.append(analyst_preview)
    lines.append("")

    # Homelab Opportunities (numbered)
    lines.append("---")
    lines.append("*🏠 HOMELAB OPPORTUNITIES*")
    lines.append("")
    if homelab_opportunities:
        for opp_id in sorted(homelab_opportunities.keys()):
            opp_text = format_opportunity_for_slack(opp_id, homelab_opportunities[opp_id])
            lines.append(opp_text)
    else:
        lines.append("_No homelab opportunities identified today_")
    lines.append("")

    # Work Opportunities (numbered)
    lines.append("---")
    lines.append("*💼 WORK OPPORTUNITIES*")
    lines.append("")
    if work_opportunities:
        for opp_id in sorted(work_opportunities.keys()):
            opp_text = format_opportunity_for_slack(opp_id, work_opportunities[opp_id])
            lines.append(opp_text)
    else:
        lines.append("_No work opportunities identified today_")
    lines.append("")

    # Footer with instructions
    lines.append("---")
    lines.append("_Reply: `approve [ID] [type]` to generate deliverable_")
    lines.append("_Types: `plan` (homelab), `brief` or `slide` (work)_")
    lines.append("_Example: `approve H1, W1 brief`_")

    return "\n".join(lines)
```

Update `save_for_n8n()`:
```python
def save_for_n8n_with_opportunities(
    scout_output: str,
    analyst_output: str,
    homelab_opportunities: Dict[str, Dict[str, str]],
    work_opportunities: Dict[str, Dict[str, str]],
    metadata: Dict[str, Any],
    output_file: str = None
) -> str:
    """Save formatted output with numbered opportunities"""
    from datetime import datetime

    if output_file is None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = f"output/slack_digest_{timestamp}.json"

    # Format for Slack
    slack_message = format_for_slack_with_opportunities(
        scout_output, analyst_output,
        homelab_opportunities, work_opportunities,
        metadata
    )

    # Create payload
    payload = {
        "timestamp": metadata.get('timestamp', datetime.now().isoformat()),
        "sources_count": metadata.get('sources_count', 0),
        "signals_count": metadata.get('signals_count', 0),
        "slack_message": slack_message,
        "opportunities": {
            "homelab": homelab_opportunities,
            "work": work_opportunities
        },
        "raw_outputs": {
            "scout": scout_output,
            "analyst": analyst_output
        }
    }

    # Save to file
    with open(output_file, 'w') as f:
        json.dump(payload, f, indent=2)

    return output_file
```

### Implementation: Update `crew.py`

Add opportunity parsing after Strategist tasks:
```python
# After crew execution
scout_output = scout_task.output.raw if hasattr(scout_task, 'output') else ""
analyst_output = analyst_task.output.raw if hasattr(analyst_task, 'output') else ""
homelab_output = homelab_strategist_task.output.raw if hasattr(homelab_strategist_task, 'output') else ""
work_output = work_strategist_task.output.raw if hasattr(work_strategist_task, 'output') else ""

# Parse opportunities
from tools.opportunity_parser import parse_opportunities, save_opportunity_mapping

homelab_opportunities = parse_opportunities(homelab_output, 'H')
work_opportunities = parse_opportunities(work_output, 'W')

print(f"[Crew] Parsed {len(homelab_opportunities)} homelab opportunities")
print(f"[Crew] Parsed {len(work_opportunities)} work opportunities")

# Combine for mapping file
all_opportunities = {**homelab_opportunities, **work_opportunities}

# Save opportunity mapping
digest_date = datetime.now().strftime("%Y-%m-%d")
opp_mapping_file = save_opportunity_mapping(all_opportunities, digest_date)
print(f"[Crew] Opportunity mapping saved: {opp_mapping_file}")

# Save for n8n (with numbered opportunities)
from tools.slack_formatter import save_for_n8n_with_opportunities

metadata = {
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "sources_count": len([s for s in config['sources'] if s['active']]),
    "signals_count": len(all_entries)
}

slack_file = save_for_n8n_with_opportunities(
    scout_output, analyst_output,
    homelab_opportunities, work_opportunities,
    metadata
)
print(f"[Crew] Slack digest saved: {slack_file}")
```

### Testing
```bash
# SSH to container
ssh root@192.168.1.18
cd /opt/crewai
source venv/bin/activate

# Test opportunity parser
python3 tools/opportunity_parser.py

# Run full crew
python3 crew.py

# Verify outputs
cat output/opportunities_*.json  # Should have H1, H2, W1, W2 etc.
cat output/slack_digest_*.json   # Should have numbered opportunities in slack_message field
```

### Success Criteria
- ✅ Opportunities parsed correctly (H1, H2, W1, W2)
- ✅ `opportunities_YYYY-MM-DD.json` created with all opportunity data
- ✅ `slack_digest_*.json` contains formatted message with `[H1]`, `[W1]` labels
- ✅ Approval syntax instructions appear in footer

### Rollback
- Revert changes to crew.py, slack_formatter.py
- Delete opportunity_parser.py
- System falls back to Criterion 4 format

---

## Phase 3: Catalyst Agent and Execution Script

**Duration:** 3 hours
**Risk:** Medium
**Dependencies:** Phase 2 complete

### Files to Create
1. `/opt/crewai/catalyst.py` (new standalone script)

### Implementation: `catalyst.py`

```python
#!/usr/bin/env python3
"""
Catalyst Deliverable Generator
Generates technical plans, leadership briefs, or client slides for approved opportunities
"""

import os
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from tools.context_loader import load_homelab_context, load_work_context

# Load environment variables
load_dotenv('config/.env')

# === CATALYST AGENT ===
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

def load_opportunity(digest_date, opportunity_id):
    """Load opportunity data from mapping file"""
    mapping_file = f"output/opportunities_{digest_date}.json"

    if not os.path.exists(mapping_file):
        raise FileNotFoundError(f"Opportunity mapping not found: {mapping_file}")

    with open(mapping_file, 'r') as f:
        data = json.load(f)

    if opportunity_id not in data['opportunities']:
        raise ValueError(f"Opportunity {opportunity_id} not found in mapping")

    return data['opportunities'][opportunity_id]

def create_plan_task(opportunity_data, context_data):
    """Create Technical Plan task for homelab opportunities"""
    return Task(
        description=f"""Generate a Technical Plan for the following homelab opportunity.

OPPORTUNITY:
Title: {opportunity_data['title']}
Relevance: {opportunity_data['relevance']}
Signal: {opportunity_data['signal']}
Next Steps: {opportunity_data['next_steps']}

RELEVANT CONTEXT:
{context_data}

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

def create_brief_task(opportunity_data, context_data):
    """Create Leadership Brief task for work opportunities"""
    return Task(
        description=f"""Generate a Leadership Brief for the following work opportunity.

OPPORTUNITY:
Title: {opportunity_data['title']}
Relevance: {opportunity_data['relevance']}
Signal: {opportunity_data['signal']}
Next Steps: {opportunity_data['next_steps']}

RELEVANT CONTEXT:
{context_data}

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

def create_slide_task(opportunity_data, context_data):
    """Create Client Slide task for work opportunities"""
    return Task(
        description=f"""Generate a Client Slide (text format) for the following work opportunity.

OPPORTUNITY:
Title: {opportunity_data['title']}
Relevance: {opportunity_data['relevance']}
Signal: {opportunity_data['signal']}

RELEVANT CONTEXT:
{context_data}

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

def main():
    parser = argparse.ArgumentParser(description='Generate Catalyst deliverable')
    parser.add_argument('--digest-date', required=True, help='Digest date (YYYY-MM-DD)')
    parser.add_argument('--opportunity', required=True, help='Opportunity ID (e.g., H1, W2)')
    parser.add_argument('--type', required=True, choices=['plan', 'brief', 'slide'], help='Deliverable type')

    args = parser.parse_args()

    try:
        # Load opportunity
        print(f"[Catalyst] Loading opportunity {args.opportunity} from {args.digest_date}...")
        opportunity_data = load_opportunity(args.digest_date, args.opportunity)

        # Load context
        print(f"[Catalyst] Loading context files...")
        if args.opportunity.startswith('H'):
            context_data = load_homelab_context()
        else:
            context_data = load_work_context()

        # Create task
        print(f"[Catalyst] Creating {args.type} task...")
        if args.type == 'plan':
            task = create_plan_task(opportunity_data, context_data)
        elif args.type == 'brief':
            task = create_brief_task(opportunity_data, context_data)
        else:  # slide
            task = create_slide_task(opportunity_data, context_data)

        # Execute
        print(f"[Catalyst] Executing Catalyst agent...")
        crew = Crew(
            agents=[catalyst],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()
        deliverable_content = str(result)

        # Save output
        output_file = f"output/catalyst_{args.digest_date}_{args.opportunity}_{args.type}.json"
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "digest_date": args.digest_date,
            "opportunity_id": args.opportunity,
            "deliverable_type": args.type,
            "opportunity_data": opportunity_data,
            "deliverable_content": deliverable_content,
            "context_used": {
                "type": "homelab" if args.opportunity.startswith('H') else "work"
            }
        }

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        # Print JSON output for n8n to capture
        result_json = {
            "success": True,
            "deliverable_file": output_file,
            "deliverable_content": deliverable_content,
            "opportunity_title": opportunity_data['title']
        }

        print("\n[Catalyst] === OUTPUT START ===")
        print(json.dumps(result_json, indent=2))
        print("[Catalyst] === OUTPUT END ===")

    except Exception as e:
        error_json = {
            "success": False,
            "error": str(e),
            "digest_date": args.digest_date,
            "opportunity_id": args.opportunity,
            "deliverable_type": args.type
        }
        print("\n[Catalyst] === OUTPUT START ===")
        print(json.dumps(error_json, indent=2))
        print("[Catalyst] === OUTPUT END ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Testing
```bash
# SSH to container
ssh root@192.168.1.18
cd /opt/crewai
source venv/bin/activate

# Run crew to generate opportunities first
python3 crew.py

# Test Catalyst with mock approval
python3 catalyst.py --digest-date 2026-02-02 --opportunity H1 --type plan

# Verify output
cat output/catalyst_2026-02-02_H1_plan.json
```

### Success Criteria
- ✅ Catalyst agent executes without errors
- ✅ Technical Plan generated for homelab opportunity
- ✅ Leadership Brief generated for work opportunity
- ✅ Client Slide generated for work opportunity
- ✅ Output JSON contains deliverable_content field
- ✅ Token usage reasonable (~45k input, 8k output)

### Rollback
- Delete catalyst.py
- No impact on existing crew.py functionality

---

## Phase 4: Approval Parsing Tool

**Duration:** 1.5 hours
**Risk:** Low
**Dependencies:** None (can be done in parallel with Phase 3)

### Files to Create
1. `/opt/crewai/tools/approval_parser.py` (new)

### Implementation

```python
#!/usr/bin/env python3
"""
Approval Parser
Parses approval/dismiss syntax from Slack replies
"""

import re
from typing import List, Dict, Any

def parse_approval_syntax(text: str) -> Dict[str, Any]:
    """
    Parse approval or dismiss syntax from user reply

    Supported formats:
    - approve H1
    - approve W1 brief
    - approve W2 slide
    - approve H1, W1 brief, W2 slide
    - dismiss H1
    - dismiss W2

    Args:
        text: User's reply text

    Returns:
        {
            "valid": bool,
            "action": "approve" | "dismiss",
            "approvals": [{"opp_id": "H1", "type": "plan"}, ...],
            "errors": [str, ...]
        }
    """
    text = text.strip().lower()

    result = {
        "valid": False,
        "action": None,
        "approvals": [],
        "errors": []
    }

    # Check for approve or dismiss keyword
    if text.startswith('approve'):
        result["action"] = "approve"
        items_text = text[7:].strip()  # Remove 'approve'
    elif text.startswith('dismiss'):
        result["action"] = "dismiss"
        items_text = text[7:].strip()  # Remove 'dismiss'
    else:
        result["errors"].append("Message must start with 'approve' or 'dismiss'")
        return result

    if not items_text:
        result["errors"].append("No opportunities specified")
        return result

    # Split by commas for multiple approvals
    items = [item.strip() for item in items_text.split(',')]

    for item in items:
        parsed_item = parse_single_approval(item, result["action"])
        if parsed_item["valid"]:
            result["approvals"].append({
                "opp_id": parsed_item["opp_id"],
                "type": parsed_item["type"]
            })
        else:
            result["errors"].extend(parsed_item["errors"])

    result["valid"] = len(result["approvals"]) > 0 and len(result["errors"]) == 0

    return result

def parse_single_approval(item: str, action: str) -> Dict[str, Any]:
    """
    Parse single approval item

    Args:
        item: e.g., "h1", "w1 brief", "w2 slide"
        action: "approve" or "dismiss"

    Returns:
        {"valid": bool, "opp_id": str, "type": str, "errors": []}
    """
    result = {
        "valid": False,
        "opp_id": None,
        "type": None,
        "errors": []
    }

    # Pattern: [H|W][0-9]+ optional [plan|brief|slide]
    pattern = r'^([hw])(\d+)(?:\s+(plan|brief|slide))?$'
    match = re.match(pattern, item.lower())

    if not match:
        result["errors"].append(f"Invalid format: '{item}' (expected: H1, W2 brief, etc.)")
        return result

    prefix = match.group(1).upper()
    number = match.group(2)
    deliverable_type = match.group(3)

    opp_id = f"{prefix}{number}"
    result["opp_id"] = opp_id

    # For dismiss, type is not required
    if action == "dismiss":
        result["type"] = "none"
        result["valid"] = True
        return result

    # For approve, validate deliverable type
    if prefix == 'H':
        # Homelab: defaults to 'plan', no other types allowed
        if deliverable_type is None or deliverable_type == 'plan':
            result["type"] = "plan"
            result["valid"] = True
        else:
            result["errors"].append(f"Homelab opportunities only support 'plan' (got: {deliverable_type})")

    elif prefix == 'W':
        # Work: MUST specify 'brief' or 'slide'
        if deliverable_type in ['brief', 'slide']:
            result["type"] = deliverable_type
            result["valid"] = True
        else:
            result["errors"].append(f"Work opportunities require 'brief' or 'slide' (got: {deliverable_type or 'none'})")

    return result

def generate_help_message(errors: List[str]) -> str:
    """Generate helpful error message for invalid syntax"""
    lines = [
        "⚠️ Invalid approval syntax. Here's how to use it:",
        "",
        "*Homelab opportunities:*",
        "  • `approve H1` (generates Technical Plan)",
        "",
        "*Work opportunities:*",
        "  • `approve W1 brief` (generates Leadership Brief)",
        "  • `approve W2 slide` (generates Client Slide)",
        "",
        "*Multiple approvals:*",
        "  • `approve H1, W1 brief, W2 slide`",
        "",
        "*Dismiss:*",
        "  • `dismiss H1` or `dismiss W2`",
        "",
        "*Errors detected:*"
    ]

    for error in errors:
        lines.append(f"  • {error}")

    return "\n".join(lines)

# Unit tests
if __name__ == "__main__":
    test_cases = [
        ("approve H1", True, [{"opp_id": "H1", "type": "plan"}]),
        ("approve h2", True, [{"opp_id": "H2", "type": "plan"}]),
        ("approve W1 brief", True, [{"opp_id": "W1", "type": "brief"}]),
        ("approve w2 slide", True, [{"opp_id": "W2", "type": "slide"}]),
        ("approve H1, W1 brief", True, [{"opp_id": "H1", "type": "plan"}, {"opp_id": "W1", "type": "brief"}]),
        ("dismiss H1", True, [{"opp_id": "H1", "type": "none"}]),
        ("approve W1", False, []),  # Missing type for work
        ("approve H1 slide", False, []),  # Invalid type for homelab
        ("random text", False, []),  # Invalid syntax
    ]

    print("Running approval parser tests...\n")
    for text, expected_valid, expected_approvals in test_cases:
        result = parse_approval_syntax(text)
        status = "✅" if result["valid"] == expected_valid else "❌"
        print(f"{status} '{text}'")
        print(f"   Valid: {result['valid']}, Approvals: {result['approvals']}")
        if result["errors"]:
            print(f"   Errors: {result['errors']}")
        print()
```

### Testing
```bash
# SSH to container
ssh root@192.168.1.18
cd /opt/crewai

# Run unit tests
python3 tools/approval_parser.py
```

### Success Criteria
- ✅ All unit tests pass
- ✅ Valid approval syntax parsed correctly
- ✅ Invalid syntax returns helpful errors
- ✅ Multiple approvals in one message handled
- ✅ Homelab defaults to 'plan'
- ✅ Work requires explicit 'brief' or 'slide'

### Rollback
- Delete approval_parser.py (no dependencies)

---

## Phase 5: n8n Approval Poller Workflow

**Duration:** 3 hours
**Risk:** Medium
**Dependencies:** Phases 2, 3, 4 complete

### Prerequisites
1. Verify Slack API token has `conversations.history` and `conversations.replies` scopes
2. Verify SSH credentials for container 118 in n8n
3. Create `approvals.jsonl` file on container: `touch /opt/crewai/output/approvals.jsonl`

### Workflow Creation Steps

1. **Create New Workflow in n8n**
   - Name: "Approval Poller and Catalyst Trigger"
   - Description: "Polls Slack for approvals and triggers Catalyst deliverables"

2. **Add Schedule Trigger Node**
   - Cron Expression: `*/5 * * * *` (every 5 minutes)
   - Timezone: America/Chicago (or user's timezone)

3. **Add "Get Today's Digest" HTTP Request Node**
   - Method: POST
   - URL: `https://slack.com/api/conversations.history`
   - Authentication: Use existing "Slack Trend Reporting Token" credential
   - Body (JSON):
     ```json
     {
       "channel": "C01ABC123",  // #trend-monitoring channel ID
       "limit": 10,
       "oldest": "{{ $now.minus(24, 'hours').toSeconds() }}"
     }
     ```
   - Post-processing (Code node):
     ```javascript
     // Find most recent message from bot
     const messages = $input.first().json.messages;
     const botMessages = messages.filter(m =>
       m.text && m.text.includes('Strategic Intelligence Digest')
     );

     if (botMessages.length === 0) {
       return { digest_found: false };
     }

     const digest = botMessages[0];
     return {
       digest_found: true,
       digest_ts: digest.ts,
       digest_date: new Date(digest.ts * 1000).toISOString().split('T')[0]
     };
     ```

4. **Add "Check Digest Found" IF Node**
   - Condition: `{{ $json.digest_found }} === true`
   - If false → END
   - If true → Continue

5. **Add "Get Replies" HTTP Request Node**
   - Method: POST
   - URL: `https://slack.com/api/conversations.replies`
   - Body:
     ```json
     {
       "channel": "C01ABC123",
       "ts": "={{ $json.digest_ts }}",
       "limit": 100
     }
     ```

6. **Add "Parse Approvals" Code Node**
   ```javascript
   // Filter replies from Kyle (not bot)
   const replies = $input.first().json.messages;
   const kyleUserId = "U01XYZ789";  // Kyle's Slack user ID

   const userReplies = replies.filter(r => r.user === kyleUserId);

   if (userReplies.length === 0) {
     return { has_approvals: false };
   }

   // Call approval parser via SSH (will implement in next node)
   return {
     has_approvals: true,
     digest_date: $('Get Today\'s Digest').first().json.digest_date,
     digest_ts: $('Get Today\'s Digest').first().json.digest_ts,
     replies: userReplies
   };
   ```

7. **Add "Parse Each Reply" SSH Node** (loop over replies)
   - Host: 192.168.1.18
   - Command:
     ```bash
     cd /opt/crewai && python3 -c "
     from tools.approval_parser import parse_approval_syntax
     import json
     text = '''{{ $json.text }}'''
     result = parse_approval_syntax(text)
     print(json.dumps(result))
     "
     ```
   - Captures parsed approvals as JSON

8. **Add "Check for Duplicates" SSH Node**
   - Host: 192.168.1.18
   - Command:
     ```bash
     digest_date="{{ $json.digest_date }}"
     opp_id="{{ $json.opp_id }}"

     # Check if already processed
     if grep -q "\"digest_date\": \"$digest_date\".*\"opportunity_id\": \"$opp_id\"" /opt/crewai/output/approvals.jsonl; then
       echo '{"already_processed": true}'
     else
       echo '{"already_processed": false}'
     fi
     ```

9. **Add "Filter New Approvals" IF Node**
   - Condition: `{{ $json.already_processed }} === false`
   - If true (already processed) → END
   - If false (new approval) → Continue

10. **Add "Log Approval" SSH Node**
    - Host: 192.168.1.18
    - Command:
      ```bash
      cd /opt/crewai

      cat >> output/approvals.jsonl << 'EOF'
      {"timestamp": "$(date -Iseconds)", "digest_date": "{{ $json.digest_date }}", "opportunity_id": "{{ $json.opp_id }}", "deliverable_type": "{{ $json.type }}", "status": "approved", "slack_user": "{{ $json.user_id }}", "slack_message_ts": "{{ $json.message_ts }}"}
      EOF
      ```

11. **Add "Trigger Catalyst" SSH Node**
    - Host: 192.168.1.18
    - Command:
      ```bash
      cd /opt/crewai
      source venv/bin/activate
      python3 catalyst.py --digest-date "{{ $json.digest_date }}" --opportunity "{{ $json.opp_id }}" --type "{{ $json.type }}" 2>&1
      ```
    - Timeout: 300000 ms (5 minutes)

12. **Add "Parse Catalyst Output" Code Node**
    ```javascript
    const stdout = $input.first().json.stdout;

    // Extract JSON between markers
    const startMarker = '[Catalyst] === OUTPUT START ===';
    const endMarker = '[Catalyst] === OUTPUT END ===';

    const startIdx = stdout.indexOf(startMarker);
    const endIdx = stdout.indexOf(endMarker);

    if (startIdx === -1 || endIdx === -1) {
      return {
        success: false,
        error: "Could not parse Catalyst output"
      };
    }

    const jsonStr = stdout.substring(startIdx + startMarker.length, endIdx).trim();
    const result = JSON.parse(jsonStr);

    return {
      ...result,
      digest_ts: $('Get Today\'s Digest').first().json.digest_ts
    };
    ```

13. **Add "Check Catalyst Success" IF Node**
    - Condition: `{{ $json.success }} === true`
    - If false → Post error to Slack → END
    - If true → Continue

14. **Add "Format Deliverable for Slack" Code Node**
    ```javascript
    const deliverable = $input.first().json.deliverable_content;
    const oppTitle = $input.first().json.opportunity_title;
    const oppId = $input.first().json.opportunity_id;
    const type = $input.first().json.deliverable_type;

    const typeLabel = {
      'plan': '🔧 Technical Plan',
      'brief': '📋 Leadership Brief',
      'slide': '📊 Client Slide'
    }[type];

    const message = `${typeLabel} for *[${oppId}] ${oppTitle}*\n\n${deliverable}`;

    return {
      message: message,
      thread_ts: $input.first().json.digest_ts
    };
    ```

15. **Add "Post to Slack Thread" HTTP Request Node**
    - Method: POST
    - URL: `https://slack.com/api/chat.postMessage`
    - Body:
      ```json
      {
        "channel": "C01ABC123",
        "thread_ts": "={{ $json.thread_ts }}",
        "text": "={{ $json.message }}"
      }
      ```

16. **Add "Update Approval Log (Delivered)" SSH Node**
    - Host: 192.168.1.18
    - Command:
      ```bash
      cd /opt/crewai

      cat >> output/approvals.jsonl << 'EOF'
      {"timestamp": "$(date -Iseconds)", "digest_date": "{{ $json.digest_date }}", "opportunity_id": "{{ $json.opp_id }}", "deliverable_type": "{{ $json.type }}", "status": "delivered", "catalyst_file": "{{ $json.deliverable_file }}"}
      EOF
      ```

17. **Add Error Handler Nodes** (parallel branches for failures)
    - Post error message to Slack
    - Log failure to approvals.jsonl with status "failed"

18. **Activate Workflow**
    - Toggle "Active" switch
    - First poll will occur within 5 minutes

### Testing Plan

1. **Manual Trigger Test**
   - Post test digest to Slack manually
   - Reply "approve H1"
   - Wait 5 minutes (or manually execute workflow)
   - Verify deliverable appears in thread

2. **Multiple Approvals Test**
   - Reply "approve H1, W1 brief"
   - Verify both deliverables generated

3. **Invalid Syntax Test**
   - Reply "approve W1" (missing type)
   - Verify help message appears

4. **Duplicate Approval Test**
   - Reply "approve H1" twice
   - Verify only one deliverable generated

5. **Dismiss Test**
   - Reply "dismiss W2"
   - Verify logged but no deliverable

### Success Criteria
- ✅ Workflow triggers every 5 minutes
- ✅ Detects approvals from Kyle's replies
- ✅ Parses approval syntax correctly
- ✅ Prevents duplicate processing
- ✅ Triggers Catalyst successfully
- ✅ Posts deliverable to thread
- ✅ Logs approval + delivery to approvals.jsonl
- ✅ Error handling works (invalid syntax, Catalyst failure)

### Rollback
- Deactivate workflow (toggle inactive)
- No impact on daily digest workflow
- No files modified on container

---

## Phase 6: Integration Testing and Monitoring

**Duration:** 2 hours
**Risk:** Medium
**Dependencies:** Phase 5 complete

### Testing Scenarios

#### Test 1: Full Happy Path
1. Wait for next daily digest (6 AM) or manually trigger
2. Reply "approve H1"
3. Observe:
   - Approval logged to approvals.jsonl
   - Catalyst executes (check SSH to container, monitor process)
   - Deliverable posts to thread within 5-10 min
   - Delivery logged to approvals.jsonl

#### Test 2: Work Opportunities (Both Types)
1. Reply "approve W1 brief"
2. Verify Leadership Brief generated
3. Reply "approve W2 slide"
4. Verify Client Slide generated
5. Compare outputs (different formats)

#### Test 3: Multiple Approvals
1. Reply "approve H1, W1 brief, W2 slide"
2. Verify all 3 deliverables generated
3. Check approvals.jsonl has 3 entries
4. Verify no race conditions (all complete)

#### Test 4: Invalid Syntax
1. Reply "approve W1" (missing type)
2. Verify help message appears
3. Verify NOT logged to approvals.jsonl

#### Test 5: Duplicate Detection
1. Reply "approve H1"
2. Wait for deliverable
3. Reply "approve H1" again
4. Verify second attempt ignored (no duplicate deliverable)

#### Test 6: Dismiss
1. Reply "dismiss H2"
2. Verify logged to approvals.jsonl with status "dismissed"
3. Verify no Catalyst triggered

#### Test 7: Catalyst Failure Handling
1. Manually break catalyst.py (introduce syntax error)
2. Reply "approve H1"
3. Verify error message posted to Slack
4. Verify logged as "failed" in approvals.jsonl
5. Fix catalyst.py
6. Retry approval (should work)

### Monitoring Setup

#### Daily Checks (First Week)
- Check approvals.jsonl daily
- Verify token costs in Claude API dashboard
- Compare actual cost vs estimate ($0.30 per deliverable)
- Collect user feedback on deliverable quality

#### Metrics to Track
```bash
# SSH to container 118
ssh root@192.168.1.18

# Count approvals by type
cat /opt/crewai/output/approvals.jsonl | jq -r '.deliverable_type' | sort | uniq -c

# Count by status
cat /opt/crewai/output/approvals.jsonl | jq -r '.status' | sort | uniq -c

# List all deliverable files
ls -lh /opt/crewai/output/catalyst_*.json

# Check latest deliverable
cat $(ls -t /opt/crewai/output/catalyst_*.json | head -1) | jq '.deliverable_content' -r
```

#### n8n Monitoring
- Check workflow execution history
- Verify no errors in poller runs
- Monitor execution time (should be < 5 min per approval)

### Success Criteria (After 2 Weeks)
- ✅ At least 5 approvals processed
- ✅ All 3 deliverable types tested (plan, brief, slide)
- ✅ Average cost per deliverable < $0.40
- ✅ No duplicate approvals
- ✅ Error rate < 10%
- ✅ Processing time < 15 minutes

### Operational Documentation
Update these files:
1. `homelab_system_overview.md` - Add Criterion 5 description
2. `README.md` - Add approval flow section
3. Create quick reference card for approval syntax

---

## Post-Implementation: Documentation Updates

### Update `homelab_system_overview.md`

Add to CrewAI Strategic Intelligence section:
```markdown
- **Approval Flow (Criterion 5):** Slack-based approval of opportunities
  - Reply to digest with `approve [ID] [type]` syntax
  - Catalyst agent generates deliverables (Technical Plans, Leadership Briefs, Client Slides)
  - Deliverables posted to Slack thread
  - All approvals logged to `/opt/crewai/output/approvals.jsonl`
- **n8n Workflow:** "Approval Poller and Catalyst Trigger" (every 5 min)
- **Catalyst Cost:** ~$0.30 per deliverable (monitored)
```

### Update Roadmap Progress Tracker

Mark Criterion 5 as COMPLETE once all tests pass:
```markdown
| **Criterion 5: Approval Flow + Catalyst** | ✅ Complete | YYYY-MM-DD | Approval syntax operational, Catalyst generating deliverables, 3 types tested |
```

---

## Risk Mitigation Summary

| Risk | Mitigation Strategy |
|------|---------------------|
| **Cost overrun** | Monitor daily costs first week; add approval limit if needed |
| **Polling latency** | Set expectations (5-10 min); can upgrade to Events API if needed |
| **Invalid syntax** | Clear help messages; examples in digest footer |
| **Catalyst failures** | Error handling posts to Slack; log failures; user can retry |
| **Duplicate approvals** | Check approvals.jsonl before each Catalyst trigger |
| **Strategist output unparseable** | Fallback to manual numbering if parser fails; strict format requirements |

---

*Implementation plan complete: 2026-02-02*
*Ready to begin Phase 1*
