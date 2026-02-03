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
