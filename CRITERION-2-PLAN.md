# Criterion 2: Minimal Viable Crew - Planning Document

**Date:** 2026-01-31
**Status:** Planning Phase
**Prerequisites:** Criterion 1 Complete ✅

---

## Criterion 2 Overview

**Primary Outcome:**
Scout agent monitors 3-5 sources, tags by significance. Analyst agent synthesizes across Scout output. Manual trigger produces output to local file.

**Evidence Required:**
- Running `python3 crew.py` produces structured output
- Output contains tagged signals (🔴/🟡/⚪)
- Output contains synthesis (not just summaries)
- Token usage logged and within estimates

**Reproducibility Check:**
- Fresh run produces consistent output format
- Different source content produces different synthesis (not templated)

**Operational Capture:**
- Document crew.py location and invocation
- Document expected output format
- Log first week of token costs

**Explicit Non-Goals:**
- No Strategist agents yet
- No Slack output yet
- No n8n trigger yet
- No context file integration yet

---

## Architecture Design

### Agent Structure

#### Scout Agent
- **Model:** Claude Haiku (cost-effective, fast)
- **Role:** Monitor sources, filter, tag by significance
- **Input:** 3-5 curated sources (RSS/web content)
- **Output:** Tagged signals with significance levels
- **Token Estimate:** ~50k in, 5k out (~$0.02/run)

#### Analyst Agent
- **Model:** Claude Sonnet (deeper reasoning)
- **Role:** Synthesize patterns across Scout signals
- **Input:** Scout's tagged output
- **Output:** Synthesized insights, pattern recognition
- **Token Estimate:** ~20k in, 3k out (~$0.10/run)

### Information Flow

```
Sources (3-5) → Scout Agent → Tagged Signals → Analyst Agent → Synthesis Report → Local File
```

---

## Source Selection (3-5 from 20 available)

### Recommended Initial Set (5 sources)

**Rationale:** Cover multiple interest areas, diverse content types, reliable signal quality

1. **Simon Willison's Blog** (Agent-Assisted Coding)
   - RSS: https://simonwillison.net/atom/everything/
   - Why: Concrete LLM workflow examples, practical signal
   - Update frequency: High (multiple per week)

2. **Anthropic Developer Blog** (AI Tooling Patterns)
   - RSS: https://www.anthropic.com/news (or scraped)
   - Why: Claude-specific workflows, MCP evolution
   - Update frequency: Medium (1-2 per week)

3. **Latent Space** (Agent-Assisted Coding)
   - Substack RSS: https://www.latent.space/feed
   - Why: Deep dives on agent workflows, interviews
   - Update frequency: Medium (weekly podcast + posts)

4. **LocalLLaMA Community** (Local LLMs)
   - Reddit RSS: https://www.reddit.com/r/LocalLLaMA/.rss
   - Why: Homelab-relevant, practical hardware insights
   - Update frequency: Very high (filter to top posts)

5. **Import AI** (Frontier Models)
   - Substack/Newsletter: https://jack-clark.net/
   - Why: Weekly curated developments, thoughtful filtering
   - Update frequency: Weekly

### Alternative Sources (if adjustments needed)

- **Stratechery** (Marketing in AI Search) - Ben Thompson's analysis
- **Hacker News "Show HN"** (Open Source Automation) - Filtered submissions
- **Thoughts on AI** (Ethan Mollick) - Team adaptation patterns

---

## Implementation Plan

### Step 1: Environment Setup
- [x] Container 118 created and accessible
- [x] Python 3.11.2 + CrewAI 1.9.3 installed
- [ ] Anthropic API key configured
- [ ] Test API connectivity

### Step 2: Source Integration
- [ ] Implement RSS feed reader (feedparser library)
- [ ] Implement web scraper for non-RSS sources (optional Phase 1)
- [ ] Create source configuration file (`sources.yaml`)
- [ ] Test source fetching (manual run)

### Step 3: Scout Agent Implementation
- [ ] Define Scout agent role and goal
- [ ] Create Scout task: "Monitor and tag signals"
- [ ] Implement significance tagging logic (🔴/🟡/⚪)
- [ ] Define Scout output schema (JSON/Markdown)
- [ ] Test Scout standalone

### Step 4: Analyst Agent Implementation
- [ ] Define Analyst agent role and goal
- [ ] Create Analyst task: "Synthesize patterns"
- [ ] Implement pattern detection prompts
- [ ] Define Analyst output schema
- [ ] Test Analyst standalone (with mock Scout data)

### Step 5: Crew Orchestration
- [ ] Create `crew.py` main script
- [ ] Wire Scout → Analyst task chain
- [ ] Implement output to local file (`/opt/crewai/output/`)
- [ ] Add token usage logging
- [ ] Test full crew run

### Step 6: Verification
- [ ] Run crew 3 times with different source content
- [ ] Verify output format consistency
- [ ] Verify synthesis varies with content (not templated)
- [ ] Log token costs for each run
- [ ] Document findings

---

## File Structure

```
/opt/crewai/
├── venv/                      # Python virtual environment
├── crew.py                    # Main crew orchestration script
├── agents/
│   ├── scout.py              # Scout agent definition
│   └── analyst.py            # Analyst agent definition
├── tasks/
│   ├── monitor_sources.py    # Scout task
│   └── synthesize.py         # Analyst task
├── tools/
│   └── source_fetcher.py     # RSS/web content fetcher
├── config/
│   ├── sources.yaml          # Source list configuration
│   └── .env                  # API keys (gitignored)
├── output/                    # Generated reports
│   └── [timestamp].md        # Daily synthesis reports
└── logs/
    └── token_usage.log       # Cost tracking
```

---

## API Key Requirements

### Anthropic API Key

**Required for:** Claude Haiku (Scout) and Claude Sonnet (Analyst)

**Setup Steps:**
1. Obtain API key from console.anthropic.com
2. Store in `/opt/crewai/config/.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```
3. Load in crew.py using `python-dotenv`

**Security:**
- Ensure `.env` has 600 permissions (read/write owner only)
- Add `.env` to `.gitignore` if versioning crew code

---

## Output Format Specification

### Expected Output Structure

```markdown
# Strategic Intelligence Digest
**Generated:** [timestamp]
**Sources Monitored:** 5
**Signals Detected:** [count]

---

## 🔴 Milestone Signals

[Scout-tagged milestone items with context]

---

## 🟡 Movement Signals

[Scout-tagged movement items]

---

## 💡 Synthesis

[Analyst's cross-signal pattern analysis]

### Emerging Patterns
- [Pattern 1]
- [Pattern 2]

### Implications
- [Implication 1]

### Open Questions
- [Question 1]

---

**Token Usage:**
- Scout: [input/output tokens]
- Analyst: [input/output tokens]
- Total Cost: ~$[cost]
```

---

## Risk Assessment

**Risk Level:** Low-Medium

**Low Risk:**
- Local Python script execution
- File writes to `/opt/crewai/output/`
- RSS feed reading (read-only)

**Medium Risk:**
- API key configuration (requires secure handling)
- API cost monitoring (need to track spend)

**Mitigation:**
- Set API rate limits if available
- Log all token usage
- Start with small source set (3-5, not all 20)
- Manual trigger only (no automated runs yet)

**Cost Ceiling:** ~$0.12 per run × 7 test runs = ~$0.84 for validation week

---

## Success Criteria

Before declaring Criterion 2 complete:

1. **Functional Evidence**
   - [ ] `python3 crew.py` executes without errors
   - [ ] Output file created in `/opt/crewai/output/`
   - [ ] Output contains 🔴/🟡/⚪ tagged signals
   - [ ] Output contains Analyst synthesis (not just Scout summary)

2. **Quality Evidence**
   - [ ] Run crew with identical sources twice → format consistent
   - [ ] Run crew with different sources → synthesis changes
   - [ ] Manual review: synthesis shows pattern recognition, not templating

3. **Operational Evidence**
   - [ ] Token usage logged for each run
   - [ ] Costs within estimate (Scout ~$0.02, Analyst ~$0.10)
   - [ ] Documentation created: crew.py usage, output format, troubleshooting

4. **Reproducibility Evidence**
   - [ ] Fresh environment test (stop/start container, re-run crew)
   - [ ] No hidden dependencies or manual config steps

---

## Dependencies to Install

```bash
# SSH to container
ssh root@192.168.1.18

# Activate venv
cd /opt/crewai
source venv/bin/activate

# Install additional dependencies
pip install feedparser python-dotenv pyyaml

# Verify installations
pip list | grep -E 'feedparser|python-dotenv|pyyaml'
```

**Packages:**
- `feedparser` - RSS feed parsing
- `python-dotenv` - Environment variable loading
- `pyyaml` - YAML config file parsing

---

## Next Session Planning

**Session Goal:** Implement and verify Criterion 2 (Minimal Viable Crew)

**Time Estimate:** 2-3 hours (implementation + testing)

**Blockers to Address:**
- Obtain Anthropic API key (user action required)
- Verify RSS feed URLs are accessible from container

**Prepare Before Session:**
- Have API key ready
- Review source selection (confirm 3-5 sources)
- Decide on initial test topic/timeframe

---

## Open Questions

1. **Source Selection:** Confirm initial 5 sources or adjust based on preferences?
2. **Output Location:** `/opt/crewai/output/` acceptable or prefer different path?
3. **Scheduling:** Manual trigger only for Phase 2, or add simple cron for testing?
4. **Significance Criteria:** Use default significance rules from roadmap or customize?

---

## References

- **Roadmap:** `01_Roadmap/CrewAI-Strategic-Intelligence-Crew.md`
- **Session Notes:** `02_Sessions/Session-2026-01-31-CrewAI-Strategic-Intelligence-Criterion-1.md`
- **CrewAI Docs:** https://docs.crewai.com/
- **Anthropic API Docs:** https://docs.anthropic.com/

---

*Planning document created: 2026-01-31*
*Ready for implementation in next session*
