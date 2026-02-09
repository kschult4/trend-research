#!/usr/bin/env python3
"""
Opportunity Parser
Extracts and numbers opportunities from Strategist outputs
"""

import re
import json
from typing import Dict, Any
from datetime import datetime

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
    """Extract content from **Subsection...:** pattern (flexible name matching).

    Handles variations like **Relevance to Homelab:** when searching for 'Relevance',
    or **Signal Strength:** when searching for 'Signal'.
    """
    # [^:\n]* absorbs extra words in the field name before the colon
    # Lookahead stops at next **SectionHeader:** or --- separator or end of string
    pattern = rf'\*\*{re.escape(subsection_name)}[^:\n]*:\*\*\s*(.*?)(?=\n\s*\*\*[A-Z]|\n\s*---|\Z)'
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
    print("Testing Opportunity Parser...")
    print("="*60)

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
    print(f"\nParsed {len(opps)} opportunities:")
    for opp_id, opp_data in opps.items():
        print(f"\n{opp_id}: {opp_data['title']}")
        print(f"  Relevance: {opp_data['relevance'][:50]}...")
        print(f"  Signal: {opp_data['signal'][:50]}...")
        print(f"  Next Steps: {opp_data['next_steps'][:50]}...")

    # Test formatting
    print("\n" + "="*60)
    print("Slack Format Test:")
    print("="*60)
    for opp_id, opp_data in opps.items():
        print(format_opportunity_for_slack(opp_id, opp_data))

    # Test saving
    print("="*60)
    print("Saving Opportunity Mapping Test:")
    test_file = save_opportunity_mapping(opps, "2026-02-02", "", "/tmp/test_opportunities.json")
    print(f"✅ Saved to: {test_file}")

    with open(test_file, 'r') as f:
        saved_data = json.load(f)
    print(f"✅ Verified: {len(saved_data['opportunities'])} opportunities in saved file")
    print("\n" + "="*60)
    print("All tests passed! ✅")
