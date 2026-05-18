# Content OS

> **AI-Augmented Content Production System** — structured pipeline: signal → idea → brief → draft → verify → publish → feedback.
> Hermes Agent plugin. Adapted from [Shann³](https://x.com/shannholmberg)'s methodology (5M impressions / 100K bookmarks).

---

## What It Is

A complete content production system that turns ideas into published posts through a repeatable 14-state lifecycle — with AI assistance at every quality gate.

**Key principle:** The system is an accelerator, not an autopilot. AI drafts, you decide.

## Quick Start

```bash
# Create a new content run (Idea Gate auto-decides the route)
hermes content new "Your content idea here" --source internal

# See all active runs and their states
hermes content status

# Scan a draft against 106 slop patterns
hermes content scan <slug>

# Full pipeline:
hermes content brief <slug>   # Writer Context Packet (LLM)
hermes content draft <slug>   # Draft generation (LLM)
hermes content verify <slug>  # Rubric + slop verification (LLM)

# System health
hermes content audit
```

## Architecture

```
Signal Layer ──▶ Idea Gate (4 routes) ──▶ Run Folder ──▶ Brief ──▶ Draft ──▶ Verify
                                                                                  │
                                                                                  ▼
                                                                           Human Review
                                                                                  │
                                                                                  ▼
                                                                     Publish ──▶ Feedback ──▶ Archive
```

- **14-State Lifecycle**: captured → idea_review → brief_ready → drafting → verification → draft_review → approved → scheduler_ready → scheduled → published → feedback_24h → feedback_72h → learned → archived
- **4-Route Idea Gate**: ORIGINAL / REPURPOSE / REWRITE / RESEARCH+IDEATE
- **107 Slop Patterns** (3 tiers + bonus): regex-based AI-content detection
- **12-Point Bookmarkability Rubric**: LLM-scored quality gate (threshold: 8/12)
- **Writer/Verifier Dual Agents**: LLM-powered brief + draft + verification

## Commands

### CLI (`hermes content ...`)

| Command | Description |
|---------|-------------|
| `new <idea>` | Start a new run (with Idea Gate) |
| `state <slug> [--set]` | View or update state |
| `brief <slug>` | Generate Writer Context Packet |
| `draft <slug>` | Generate draft |
| `verify <slug>` | Run verifier (rubric + slop) |
| `scan <slug>` | Scan for slop patterns |
| `runs` | List all runs |
| `search <query>` | Full-text search across runs |
| `audit` | System health check |
| `archive <slug>` | Archive a completed run |

### Slash (`/content ...`)

`/content new <idea>`, `/content status`, `/content scan <slug>`, `/content audit`, `/content runs`

### Tool Actions (24 total)

`content_os_manager`: setup, new_run, decide_route, generate_brief, generate_draft, run_verifier, scan_slop, score, postmortem, search_runs, archive_run, audit, and more.

## Project Structure

```
├── content_os_core.py    Core engine (14-state, slop, agents)
├── __init__.py           Plugin registration (tools, hooks, CLI, slash)
├── cli.py                CLI command tree
├── SKILL.md              Skill definition
├── USER_GUIDE.md         Comprehensive user guide ↗️
├── strategy/             Positioning, audience, pillars (you fill)
├── voice/                Voice profile + slop patterns (you maintain)
├── stores/               Inbox, ideas, hooks, proof, feedback
├── runs/                 Active + archived content runs
├── workflows/            5 playbook documents
└── references/           6 reference documents
```

## Documentation

| Resource | What's Inside |
|----------|--------------|
| **USER_GUIDE.md** | Full user guide — beginner to advanced (57KB, 10 chapters, 51 sections) |
| **SKILL.md** | Hermes skill — auto-loaded, with exhaustive audit checklist |
| **references/** | Architecture, prompts, rubric template, slop pattern details |
| **workflows/** | Step-by-step playbooks for each pipeline stage |

## Requirements

- Hermes Agent v0.27.0+
- Python 3.11+
- LLM provider configured in Hermes (for brief/draft/verify agents)

## License

MIT — free for personal and commercial use.

---

*Inspired by [Shann³](https://x.com/shannholmberg)'s Content OS system. Adapted as a Hermes Agent plugin.*
