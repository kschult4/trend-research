# Workflow Comparison: v1 vs v2

## TL;DR Answer

**YES - v2 completely replaces v1. You should disable v1 when you activate v2.**

Both workflows trigger the same crew.py execution, but v2 produces a better UX. Running both would:
- Trigger crew.py twice at 6 AM (wasteful, ~$0.50 cost per run)
- Post duplicate content to Slack (confusing)
- Serve no useful purpose

**Recommendation:** Import v2, test it, then disable/delete v1.

---

## Side-by-Side Comparison

| Aspect | v1 (Current/Old) | v2 (New/Phase 2) |
|--------|------------------|------------------|
| **Workflow Name** | "Strategic Intelligence Daily" | "Strategic Intelligence Daily v2" |
| **Trigger** | Schedule only (6 AM) | Schedule + Manual trigger |
| **Executes** | `crew.py` on Container 118 | `crew.py` on Container 118 ✅ SAME |
| **Reads File** | `slack_digest_*.json` | `slack_messages_*.json` |
| **Slack Output** | 1 long message (digest) | 3-5 individual messages |
| **Message Format** | Plain text (slack_message field) | Slack Block Kit (blocks) |
| **Buttons** | ❌ None | ✅ [Develop] [Ignore] per message |
| **Emoji Indicators** | ❌ None | ✅ 🏠 homelab / 💼 work |
| **Scannable** | ❌ Hard to scan | ✅ Easy to scan (<30s) |
| **Error Handling** | ✅ Slack notification | ✅ Slack notification ✅ SAME |
| **Credentials** | Container 118 SSH + Slack token | Container 118 SSH + Slack token ✅ SAME |
| **Channel** | #trend-monitoring | #trend-monitoring ✅ SAME |

---

## What's Identical

Both workflows:
1. **Run the same crew.py** - No difference in AI execution
2. **Use the same credentials** - SSH and Slack tokens
3. **Post to the same channel** - #trend-monitoring
4. **Have error handling** - Notify on crew.py failure
5. **Run at 6 AM** - Same schedule
6. **Cost the same** - ~$0.40-0.50 per execution (Claude API calls)

**The only difference is HOW the output is formatted and displayed in Slack.**

---

## What Changed

### v1 Workflow Output (Old)

**Reads:** `slack_digest_*.json` (old format)

**Parses:**
```javascript
{
  slack_message: "📊 Strategic Intelligence Digest\n_2026-02-04 06:00_\n\n...[LONG STRING]...",
  timestamp: "...",
  sources_count: 5,
  signals_count: 6
}
```

**Posts to Slack:**
```
📊 Strategic Intelligence Digest
_2026-02-04 06:00_
Sources monitored: 5 | Signals analyzed: 6

---
🔍 SCOUT SIGNALS
[First 500 chars]...

---
🧠 ANALYST SYNTHESIS
[First 800 chars]...

---
🏠 HOMELAB OPPORTUNITIES

[H1] Local Audio Generation for Home Automation
_Connects directly to Home Assistant..._
Signal: ACE-Step-1.5 achieving...
Next Steps: 1. Monitor...

[H2] Code Assistant Integration
...

[H3] Agent Sandboxing
...

---
💼 WORK OPPORTUNITIES
_No work opportunities identified today_

---
_Reply: `approve [ID] [type]` to generate deliverable_
_Types: `plan` (homelab), `brief` or `slide` (work)_
_Example: `approve H1, W1 brief`_
```

**Problem:** One very long message, hard to scan, requires thread replies to approve.

---

### v2 Workflow Output (New)

**Reads:** `slack_messages_*.json` (new Phase 2 format)

**Parses:**
```javascript
{
  timestamp: "...",
  sources_count: 5,
  signals_count: 6,
  summary: {
    scout_preview: "...",
    analyst_preview: "..."
  },
  messages: [
    {
      opportunity_id: "H1",
      category: "homelab",
      title: "Local Audio Generation for Home Automation",
      relevance: "...",
      signal: "...",
      next_steps: "...",
      slack_blocks: [ ... Block Kit JSON ... ]
    },
    { opportunity_id: "H2", ... },
    { opportunity_id: "H3", ... }
  ]
}
```

**Posts to Slack (3 separate messages):**

**Message 1:**
```
🏠 [H1] Local Audio Generation for Home Automation

Relevance: Connects directly to Home Assistant (192.168.1.12)...

Signal: ACE-Step-1.5 achieving commercial-quality audio...

Next Steps:
1. Monitor ACE-Step-1.5 community validation...
2. If verified, test deployment on AI Box...

[Develop]  [Ignore]
```

**Message 2:**
```
🏠 [H2] Code Assistant Integration with Active Development Projects

Relevance: Multiple active projects (Guitar Practice App...)...

Signal: Code model commoditization...

Next Steps:
1. Evaluate Qwen3-Coder-Next performance...
2. Test local deployment on AI Box...

[Develop]  [Ignore]
```

**Message 3:**
```
🏠 [H3] Agent Sandboxing for CrewAI Strategic Intelligence

Relevance: This very system (192.168.1.18) uses multi-agent workflows...

Signal: Deno Sandbox infrastructure emergence...

Next Steps:
1. Research Deno Sandbox architecture...
2. Evaluate isolation requirements...

[Develop]  [Ignore]
```

**Benefit:** Scannable individual messages, one-click buttons, visual emoji coding.

---

## crew.py Output Files

**Key insight:** crew.py now generates BOTH formats simultaneously.

After crew.py runs, you'll find:

```
/opt/crewai/output/
├── digest_2026-02-04_06-00-00.md               (Markdown, for archival)
├── slack_digest_2026-02-04_06-00-00.json       (v1 format, OLD)
├── slack_messages_2026-02-04_06-00-00.json     (v2 format, NEW)
└── opportunity_mapping_2026-02-04.json         (For Phase 3 button handlers)
```

**This means:**
- Both workflows can read their respective files
- No conflict between v1 and v2
- But running both would post duplicate content to Slack

---

## Why crew.py Still Generates v1 Format

**Backward compatibility during transition.**

The old format is still generated so that:
1. You can test v2 without breaking v1
2. You can run both workflows side-by-side temporarily
3. You can roll back if v2 has issues

**Once v2 is verified working, we can remove the old format generation in Phase 4 cleanup.**

---

## Migration Strategy

### Option 1: Clean Cutover (Recommended)

**Steps:**
1. Import v2 workflow
2. Test v2 manually (Manual Trigger)
3. Verify individual messages appear correctly
4. **Disable v1** (toggle Active to OFF)
5. **Enable v2** (toggle Active to ON)
6. Next 6 AM: Only v2 runs
7. After 2-3 days: Delete v1 workflow

**Pros:**
- Clean transition
- No duplicate messages
- Clear which workflow is active

**Cons:**
- If v2 fails, no messages until you re-enable v1

---

### Option 2: Parallel Testing (Conservative)

**Steps:**
1. Import v2 workflow
2. Keep v1 active at 6:00 AM
3. Set v2 to 6:05 AM (5 min offset)
4. Compare outputs for 1-2 days
5. Disable v1 when satisfied
6. Change v2 back to 6:00 AM

**Pros:**
- Safety net if v2 fails
- Can compare outputs side-by-side

**Cons:**
- Duplicate content in Slack (confusing)
- crew.py runs twice (double cost ~$1/day)
- More noise in #trend-monitoring

---

### Option 3: Manual Testing Only (Safest)

**Steps:**
1. Import v2 workflow
2. **Don't enable schedule** (leave inactive)
3. Keep v1 running at 6 AM
4. Manually trigger v2 a few times over several days
5. When confident, disable v1 and enable v2

**Pros:**
- No risk to daily operations
- Can test thoroughly before cutover
- No duplicate messages

**Cons:**
- Delayed Phase 2 completion
- Must remember to manually trigger for testing

---

## Recommended Approach

**Go with Option 1 (Clean Cutover):**

1. **Import v2**
2. **Test manually** - Execute Manual Trigger, verify output
3. **If test passes:**
   - Disable v1 (Active: OFF)
   - Enable v2 (Active: ON)
4. **Monitor tomorrow's 6 AM run**
5. **If v2 works:** Delete v1 after 2-3 days
6. **If v2 fails:** Re-enable v1, debug v2

**Why this is safe:**
- v2 is tested code (we validated the JSON structure)
- Both workflows use identical credentials and crew execution
- Only the output formatting changed
- You can re-enable v1 in 30 seconds if needed

---

## Rollback Procedure

**If v2 fails at 6 AM:**

1. Open n8n: http://192.168.1.11:5678
2. Find "Strategic Intelligence Daily" (v1)
3. Toggle "Active" to ON
4. v1 will resume tomorrow at 6 AM
5. Debug v2 in the meantime

**Time to rollback:** <1 minute

---

## Phase 3 Dependency

**Important:** Phase 3 (button action handlers) will ONLY work with v2.

v1 doesn't have buttons, so:
- You must be running v2 before starting Phase 3
- Phase 3 webhooks will expect v2's button action IDs
- v1 will become obsolete after Phase 3

**Timeline:**
- Phase 2: Switch to v2 (now)
- Phase 3: Implement button handlers (next session)
- Phase 4: Delete v1 and old format generation (cleanup)

---

## Credential Verification

Both workflows use the same credentials:

**SSH Credential (ID: 1)**
- Name: "Container 118 SSH"
- Type: SSH Private Key
- Used by: Both v1 and v2

**Slack Credential (ID: 1)**
- Name: "Slack Trend Reporting Token"
- Type: HTTP Header Auth
- Used by: Both v1 and v2

**No credential changes needed.** v2 will automatically use the same credentials.

---

## Final Answer

**YES - v2 completely replaces v1.**

**Action Plan:**
1. ✅ Import `n8n-strategic-intelligence-daily-v2.json`
2. ✅ Test with Manual Trigger
3. ✅ Verify individual Slack messages appear
4. ✅ Disable v1 workflow (Active: OFF)
5. ✅ Enable v2 workflow (Active: ON)
6. ✅ Monitor tomorrow's 6 AM run
7. ✅ Delete v1 after 2-3 successful runs

**Both workflows cannot run simultaneously** without creating duplicate posts. Choose one.

**Recommendation: Use v2.** It's the future of the system and required for Phase 3.

---

*Comparison created: 2026-02-04*
*Recommendation: Clean cutover from v1 to v2*
