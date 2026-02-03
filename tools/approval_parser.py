#!/usr/bin/env python3
"""
Approval Parser
Parses approval/dismiss syntax from Slack replies for Criterion 5
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

def validate_against_opportunities(approvals: List[Dict[str, str]], opportunities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate parsed approvals against actual opportunity mapping

    Args:
        approvals: List of {"opp_id": "H1", "type": "plan"} from parse_approval_syntax
        opportunities: Dict of opportunities from opportunities_{date}.json

    Returns:
        {
            "valid": bool,
            "validated_approvals": [{"opp_id": "H1", "type": "plan", "opportunity_data": {...}}, ...],
            "errors": [str, ...]
        }
    """
    result = {
        "valid": True,
        "validated_approvals": [],
        "errors": []
    }

    for approval in approvals:
        opp_id = approval["opp_id"]

        if opp_id not in opportunities:
            result["errors"].append(f"Opportunity {opp_id} not found in digest")
            result["valid"] = False
        else:
            # Add opportunity data to validated approval
            result["validated_approvals"].append({
                "opp_id": opp_id,
                "type": approval["type"],
                "opportunity_data": opportunities[opp_id]
            })

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
        ("approve H1", True, [{"opp_id": "H1", "type": "plan"}], "Homelab with default type"),
        ("approve h2", True, [{"opp_id": "H2", "type": "plan"}], "Homelab lowercase"),
        ("approve H3 plan", True, [{"opp_id": "H3", "type": "plan"}], "Homelab with explicit plan"),
        ("approve W1 brief", True, [{"opp_id": "W1", "type": "brief"}], "Work with brief"),
        ("approve w2 slide", True, [{"opp_id": "W2", "type": "slide"}], "Work with slide lowercase"),
        ("approve H1, W1 brief", True, [{"opp_id": "H1", "type": "plan"}, {"opp_id": "W1", "type": "brief"}], "Multiple mixed"),
        ("approve H1, H2, W1 brief, W2 slide", True, [
            {"opp_id": "H1", "type": "plan"},
            {"opp_id": "H2", "type": "plan"},
            {"opp_id": "W1", "type": "brief"},
            {"opp_id": "W2", "type": "slide"}
        ], "Multiple complex"),
        ("dismiss H1", True, [{"opp_id": "H1", "type": "none"}], "Dismiss homelab"),
        ("dismiss w2", True, [{"opp_id": "W2", "type": "none"}], "Dismiss work"),
        ("approve W1", False, [], "Work without type (should fail)"),
        ("approve H1 slide", False, [], "Homelab with invalid type (should fail)"),
        ("approve H1 brief", False, [], "Homelab with brief (should fail)"),
        ("approve W1 plan", False, [], "Work with plan (should fail)"),
        ("random text", False, [], "Invalid syntax (should fail)"),
        ("approve", False, [], "No opportunities specified (should fail)"),
        ("approve X1", False, [], "Invalid prefix (should fail)"),
        ("approve H", False, [], "Missing number (should fail)"),
    ]

    print("=" * 70)
    print("APPROVAL PARSER UNIT TESTS")
    print("=" * 70)
    print()

    passed = 0
    failed = 0

    for text, expected_valid, expected_approvals, description in test_cases:
        result = parse_approval_syntax(text)

        # Check if valid matches
        valid_match = result["valid"] == expected_valid

        # Check if approvals match (for valid cases)
        approvals_match = True
        if expected_valid and result["valid"]:
            if len(result["approvals"]) != len(expected_approvals):
                approvals_match = False
            else:
                for expected, actual in zip(expected_approvals, result["approvals"]):
                    if expected["opp_id"] != actual["opp_id"] or expected["type"] != actual["type"]:
                        approvals_match = False
                        break

        test_passed = valid_match and approvals_match

        if test_passed:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1

        print(f"{status} | {description}")
        print(f"   Input: '{text}'")
        print(f"   Expected: valid={expected_valid}, approvals={expected_approvals}")
        print(f"   Got:      valid={result['valid']}, approvals={result['approvals']}")

        if result["errors"]:
            print(f"   Errors: {result['errors']}")

        print()

    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    print()

    # Test validation against opportunities
    print("=" * 70)
    print("OPPORTUNITY VALIDATION TESTS")
    print("=" * 70)
    print()

    mock_opportunities = {
        "H1": {"title": "Local LLM Fine-tuning", "relevance": "AI Box project"},
        "W1": {"title": "Code Review Patterns", "relevance": "Team velocity"}
    }

    validation_tests = [
        ([{"opp_id": "H1", "type": "plan"}], True, "Valid homelab opportunity"),
        ([{"opp_id": "W1", "type": "brief"}], True, "Valid work opportunity"),
        ([{"opp_id": "H1", "type": "plan"}, {"opp_id": "W1", "type": "brief"}], True, "Multiple valid"),
        ([{"opp_id": "H99", "type": "plan"}], False, "Non-existent homelab opportunity"),
        ([{"opp_id": "W99", "type": "brief"}], False, "Non-existent work opportunity"),
        ([{"opp_id": "H1", "type": "plan"}, {"opp_id": "W99", "type": "brief"}], False, "One valid, one invalid"),
    ]

    for approvals, expected_valid, description in validation_tests:
        result = validate_against_opportunities(approvals, mock_opportunities)

        test_passed = result["valid"] == expected_valid

        if test_passed:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"

        print(f"{status} | {description}")
        print(f"   Approvals: {approvals}")
        print(f"   Expected valid: {expected_valid}")
        print(f"   Got valid: {result['valid']}")

        if result["errors"]:
            print(f"   Errors: {result['errors']}")

        if result["validated_approvals"]:
            print(f"   Validated: {len(result['validated_approvals'])} approvals")

        print()

    print("=" * 70)
    print()

    # Test help message generation
    print("=" * 70)
    print("HELP MESSAGE GENERATION TEST")
    print("=" * 70)
    print()

    sample_errors = [
        "Work opportunities require 'brief' or 'slide' (got: none)",
        "Opportunity H99 not found in digest"
    ]

    help_msg = generate_help_message(sample_errors)
    print(help_msg)
    print()
    print("=" * 70)
