#!/usr/bin/env python3
"""
Test Phase 2 with mock opportunities
"""

import sys
sys.path.append('/opt/crewai')
sys.path.append('/opt/crewai/tools')

from tools.opportunity_parser import parse_opportunities, save_opportunity_mapping, format_opportunity_for_slack
from tools.slack_formatter import format_for_slack_with_opportunities, save_for_n8n_with_opportunities
from datetime import datetime
import json

# Mock Strategist outputs with opportunities
mock_homelab_output = """
No homelab-relevant signals in the main batch, but here are some test opportunities:

### Opportunity: Local LLM Fine-tuning with Ollama
**Relevance:** Connects to AI Box project (192.168.1.204) and local inference goals with Gemma 7B model
**Signal:** New Ollama fine-tuning capabilities for consumer hardware announced with adapter support
**Next Steps:** Research Ollama adapter support documentation and test fine-tuning workflow with sample dataset on AI Box

### Opportunity: Self-hosted Analytics with Plausible
**Relevance:** Could replace Google Analytics dependency for Family Hub dashboard (192.168.1.16) and other local services
**Signal:** Plausible Analytics trending on GitHub with strong privacy focus and simple self-hosting
**Next Steps:** Deploy Plausible test instance on Proxmox container, integrate with Family Hub, compare metrics
"""

mock_work_output = """
After reviewing the signals, here are relevant work opportunities:

### Opportunity: AI-Assisted Code Review Patterns
**Relevance:** Directly relates to velocity improvement goals documented in Project Phoenix brief and development team upskilling
**Signal:** New Claude Code review capabilities with contextual feedback emerging in practitioner adoption across development teams
**Next Steps:** Pilot with one team sprint cycle, document productivity impact metrics, share findings with leadership in next status meeting
"""

print("="*70)
print("TESTING PHASE 2 OPPORTUNITY PARSING")
print("="*70)

# Parse opportunities
print("\n1. Parsing Homelab Opportunities...")
homelab_opportunities = parse_opportunities(mock_homelab_output, 'H')
print(f"   Found {len(homelab_opportunities)} opportunities:")
for opp_id, opp_data in homelab_opportunities.items():
    print(f"   - {opp_id}: {opp_data['title']}")

print("\n2. Parsing Work Opportunities...")
work_opportunities = parse_opportunities(mock_work_output, 'W')
print(f"   Found {len(work_opportunities)} opportunities:")
for opp_id, opp_data in work_opportunities.items():
    print(f"   - {opp_id}: {opp_data['title']}")

# Save opportunity mapping
print("\n3. Saving Opportunity Mapping...")
all_opportunities = {**homelab_opportunities, **work_opportunities}
digest_date = datetime.now().strftime("%Y-%m-%d")
mapping_file = save_opportunity_mapping(all_opportunities, digest_date, "", "/tmp/test_opportunities_phase2.json")
print(f"   Saved to: {mapping_file}")

# Verify saved file
with open(mapping_file, 'r') as f:
    saved_data = json.load(f)
print(f"   Verified: {len(saved_data['opportunities'])} opportunities in mapping file")

# Format Slack message
print("\n4. Formatting Slack Message with Numbered Opportunities...")
mock_metadata = {
    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'sources_count': 5,
    'signals_count': 8
}

slack_message = format_for_slack_with_opportunities(
    "Mock scout output with signals...",
    "Mock analyst synthesis with patterns...",
    homelab_opportunities,
    work_opportunities,
    mock_metadata
)

print("\n" + "="*70)
print("SLACK MESSAGE OUTPUT:")
print("="*70)
print(slack_message)

# Save complete JSON output
print("\n" + "="*70)
print("5. Saving Complete Slack JSON...")
json_file = save_for_n8n_with_opportunities(
    "Mock scout output",
    "Mock analyst synthesis",
    homelab_opportunities,
    work_opportunities,
    mock_metadata,
    "/tmp/test_slack_digest_phase2.json"
)
print(f"   Saved to: {json_file}")

with open(json_file, 'r') as f:
    saved_json = json.load(f)
print(f"   Verified: {len(saved_json['opportunities']['homelab'])} homelab + {len(saved_json['opportunities']['work'])} work opportunities")

print("\n" + "="*70)
print("PHASE 2 TEST COMPLETE ✅")
print("="*70)
print("\nVerify:")
print("1. Opportunity IDs are numbered correctly (H1, H2, W1)")
print("2. Slack message shows [H1], [H2], [W1] formatting")
print("3. Footer includes approval syntax instructions")
print("4. JSON contains opportunities field with parsed data")
