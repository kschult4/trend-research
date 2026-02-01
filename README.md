# CrewAI Strategic Intelligence Crew

Multi-agent system for monitoring trends in AI, automation, and homelab technology, connecting signals to Kyle's actual context.

**Status:** Criterion 1 Complete (Infrastructure Ready)
**Container:** 118 (crewai-strategist)
**IP Address:** 192.168.1.18
**Project Start:** 2026-01-31

---

## Overview

This project implements a CrewAI-based multi-agent system that:
- Monitors 20+ curated sources for AI/automation/homelab trends
- Tags signals by significance (🔴 Milestone / 🟡 Movement / ⚪ Noise)
- Synthesizes patterns across signals
- Evaluates relevance to homelab architecture and work projects
- Creates actionable deliverables on approval

**Core Value Proposition:** Surface connections Kyle wouldn't make because he's too close to both worlds.

---

## Infrastructure

### Container Specifications

- **Container ID:** 118 (LXC on Proxmox)
- **Hostname:** crewai-strategist
- **IP Address:** 192.168.1.18 (static)
- **OS:** Debian 12.12 (bookworm)
- **Memory:** 2048 MB
- **Cores:** 2
- **Storage:** 20 GB (local-lvm)
- **Network:** vmbr0 bridge, gateway 192.168.1.1
- **DNS:** 192.168.1.13 (PiHole)
- **Authentication:** SSH key-based (Proxmox host keys)
- **Type:** Unprivileged with nesting enabled

### Python Environment

- **Python Version:** 3.11.2
- **pip Version:** 26.0 (within venv)
- **Virtual Environment:** `/opt/crewai/venv`
- **CrewAI Version:** 1.9.3
- **CrewAI Tools Version:** 1.9.3

**Note:** Uses Python virtual environment to comply with Debian 12 PEP 668 externally-managed environment policy.

### Context File Structure

```
/context/
├── briefs/                    # Project briefs (work)
│   └── [project-name].md
├── transcripts/               # Meeting transcripts
│   └── [date]-[meeting].md
├── hot_topics.md              # Leadership concerns, themes
├── homelab_architecture.md    # Current lab state
├── interest_areas.md          # Topics Scout monitors
└── work_role.md               # Kyle's role, boundaries
```

---

## Quick Reference

### Container Management

```bash
# List containers
ssh root@192.168.1.200 "pct list"

# Start container
ssh root@192.168.1.200 "pct start 118"

# Stop container
ssh root@192.168.1.200 "pct stop 118"

# Restart container
ssh root@192.168.1.200 "pct reboot 118"

# Container console
ssh root@192.168.1.200 "pct enter 118"

# SSH to container
ssh root@192.168.1.18
```

### Python Environment

```bash
# SSH to container
ssh root@192.168.1.18

# Activate virtual environment
cd /opt/crewai
source venv/bin/activate

# Verify CrewAI installation
pip show crewai

# Deactivate venv
deactivate
```

### Context Management

```bash
# List context files
ssh root@192.168.1.18 "ls -la /context/"

# View context structure
ssh root@192.168.1.18 "tree /context/"

# Add project brief (manual)
ssh root@192.168.1.18
cat > /context/briefs/example-project.md << 'EOF'
# Project: Example Project
...
EOF
```

---

## Project Phases

### Phase 1: Infrastructure Ready ✅ COMPLETE

**Completion Date:** 2026-01-31

**Evidence:**
- Container 118 running at 192.168.1.18
- Python 3.11.2 installed
- CrewAI 1.9.3 installed in virtual environment
- /context/ directory structure created

**Session Notes:** `02_Sessions/Session-2026-01-31-CrewAI-Strategic-Intelligence-Criterion-1.md`

### Phase 2: Minimal Viable Crew (Pending)

**Goal:** Scout agent + Analyst agent producing tagged and synthesized output to local file

**Requirements:**
- Scout agent monitoring 3-5 sources
- Analyst agent synthesizing across Scout output
- Manual trigger via `python3 crew.py`
- Structured output with significance tags

### Phase 3: Context Management via Slack (Pending)

**Goal:** n8n workflow bridging Slack to filesystem for context management

### Phase 4: Full Crew with Slack Output (Pending)

**Goal:** All 5 agents operational with daily n8n-triggered runs

### Phase 5: Approval Flow and Catalyst (Pending)

**Goal:** Slack-based approval flow with Catalyst deliverables

---

## Crew Structure (Planned)

| Agent | Role | Model | Status |
|-------|------|-------|--------|
| **Scout** | Monitor sources, tag by significance | Haiku | Pending |
| **Analyst** | Synthesize signals, identify patterns | Sonnet | Pending |
| **Homelab Strategist** | Evaluate homelab relevance | Sonnet | Pending |
| **Work Strategist** | Evaluate work relevance | Sonnet | Pending |
| **Catalyst** | Create deliverables on approval | Sonnet | Pending |

---

## Cost Model (Estimated)

| Agent | Model | Est. Cost/Run |
|-------|-------|---------------|
| Scout | Haiku | ~$0.02 |
| Analyst | Sonnet | ~$0.10 |
| Homelab Strategist | Sonnet | ~$0.15 |
| Work Strategist | Sonnet | ~$0.15 |
| Catalyst | Sonnet | ~$0.30 |

**Daily baseline:** ~$0.40-0.50
**Monthly baseline:** ~$12-15
**Catalyst deliverables:** +$0.30 each

**Cost ceiling:** ~$15/month (monitored after first week)

---

## Rollback Strategy

If the project needs to be rolled back:

1. Stop the container: `ssh root@192.168.1.200 "pct stop 118"`
2. Destroy the container: `ssh root@192.168.1.200 "pct destroy 118"`
3. Remove from Uptime Kuma monitoring (when added)
4. Remove from `homelab_system_overview.md` (when added)

**Data Impact:** All data in container is expendable (no critical data)

**Cost Impact:** Minimal (container resources, no ongoing API costs until agents deployed)

---

## Related Documentation

- **Roadmap:** `01_Roadmap/CrewAI-Strategic-Intelligence-Crew.md`
- **Session Notes:** `02_Sessions/Session-2026-01-31-CrewAI-Strategic-Intelligence-Criterion-1.md`
- **System Overview:** `_Background/homelab_system_overview.md`
- **Governance:** `_Background/Execution-Governance-Addendum.md`

---

## Verification Commands

Run these commands to verify Criterion 1 completion:

```bash
# 1. Verify container running
ssh root@192.168.1.200 "pct list | grep 118"
# Expected: "118        running                 crewai-strategist"

# 2. Verify SSH access
ssh root@192.168.1.18 "hostname"
# Expected: "crewai-strategist"

# 3. Verify Python version
ssh root@192.168.1.18 "python3 --version"
# Expected: "Python 3.11.2"

# 4. Verify CrewAI installation
ssh root@192.168.1.18 "cd /opt/crewai && source venv/bin/activate && pip show crewai"
# Expected: "Name: crewai" and "Version: 1.9.3"

# 5. Verify context directory structure
ssh root@192.168.1.18 "ls /context/"
# Expected: "briefs  homelab_architecture.md  hot_topics.md  interest_areas.md  transcripts  work_role.md"
```

---

*Documentation created: 2026-01-31*
*Last updated: 2026-01-31*
