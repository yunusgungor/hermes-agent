"""Content OS Plugin v2.4.0 — Full Content OS Implementation.

Complete 14-state lifecycle, 54 slop patterns (3 tiers + bonus),
4-route Idea Gate, Writer/Verifier dual-agent pipeline,
LLM-based postmortem with exact-line analysis, signal processing.

Registers tools, hooks, slash commands, and CLI for the Content OS workflow.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import logging

from .content_os_core import ContentOSCore, tool_content_os_manager, tool_content_os_retriever
from .cli import register_cli

logger = logging.getLogger(__name__)

VERSION = "2.4.0"


def register(ctx: Any) -> None:
    root = Path(__file__).parent
    core = ContentOSCore(root)

    # ══════════════════════════════════════════════════════════════
    # TOOL: content_os_manager (24 actions — full lifecycle)
    # ══════════════════════════════════════════════════════════════

    manager_schema = {
        "name": "content_os_manager",
        "description": (
            "Complete Content OS management: setup, idea gate (4 routes), "
            "run lifecycle (14 states), Writer/Verifier agent pipeline, "
            "slop scan (54 patterns), rubric scoring, signal processing, "
            "postmortem (LLM-based exact-line analysis), voice evolution, "
            "cross-run learning, pattern analysis, search, archive."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        # System
                        "setup", "audit", "list",
                        # Idea Gate
                        "decide_route",
                        # Run management
                        "new_run", "update_state", "get_state", "sync_state",
                        "get_next_actions",
                        # Agent Pipeline
                        "generate_brief", "generate_draft", "run_verifier",
                        # Quality
                        "scan_slop", "score",
                        # Signals
                        "signal",
                        # Postmortem
                        "postmortem",
                        # Voice
                        "update_voice",
                        # Learning
                        "get_learnings", "analyze_patterns",
                        # Search
                        "search_runs", "get_all_runs",
                        # Archive
                        "archive_run",
                    ],
                    "description": "Action to perform in the Content OS pipeline",
                },
                "idea": {"type": "string", "description": "Content idea text for new_run or decide_route"},
                "source_hint": {
                    "type": "string",
                    "description": "Hint for Idea Gate routing: 'internal', 'external', 'existing', 'research'",
                },
                "slug": {"type": "string", "description": "Content slug for existing runs"},
                "state": {"type": "string", "description": "New state for update_state (see lifecycle: captured→idea_review→brief_ready→drafting→verification→draft_review→approved→scheduler_ready→scheduled→published→feedback_24h→feedback_72h→learned→archived)"},
                "text": {"type": "string", "description": "Text to scan for slop patterns"},
                "source": {"type": "string", "description": "Signal source: 'x' or 'rss'"},
                "metrics": {"type": "object", "description": "Metrics for postmortem: impressions, bookmarks, likes, retweets"},
                "updates": {"type": "object", "description": "Voice profile updates: new_rules, banned_patterns, insights"},
                "topic": {"type": "string", "description": "Topic filter for learnings"},
                "query": {"type": "string", "description": "Search query for run search"},
                "extra_context": {"type": "string", "description": "Extra context for brief generation"},
                "include_archived": {"type": "boolean", "description": "Include archived runs in results", "default": True},
            },
            "required": ["action"],
        },
    }

    ctx.register_tool(
        name="content_os_manager",
        toolset="content",
        schema=manager_schema,
        handler=lambda args, **kw: tool_content_os_manager(core, args, **kw),
        description="Complete Content OS pipeline management tool.",
        is_async=True,
    )

    # ══════════════════════════════════════════════════════════════
    # TOOL: content_os_retriever
    # ══════════════════════════════════════════════════════════════

    retriever_schema = {
        "name": "content_os_retriever",
        "description": "Retrieve strategy, voice, run data, stores, or learnings from Content OS.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["strategy", "voice", "run", "stores", "learnings"],
                    "description": "Knowledge category to retrieve",
                },
                "slug": {"type": "string", "description": "Slug for run category"},
                "topic": {"type": "string", "description": "Optional topic filter for learnings"},
            },
            "required": ["category"],
        },
    }

    ctx.register_tool(
        name="content_os_retriever",
        toolset="content",
        schema=retriever_schema,
        handler=lambda args, **kw: tool_content_os_retriever(core, args),
        description="Knowledge retrieval from Content OS stores.",
    )

    # ══════════════════════════════════════════════════════════════
    # SLASH COMMAND: /content
    # ══════════════════════════════════════════════════════════════

    def handle_slash(args: str) -> Optional[str]:
        argv = args.strip().split()
        if not argv:
            return (
                "Usage: /content [status|new|brief|draft|verify|scan|score|"
                "audit|setup|signal|postmortem|route|state|archive|"
                "learnings|patterns|runs|context|voice-update]"
            )

        sub = argv[0]

        if sub == "status":
            runs = core.active_runs
            if not runs.exists():
                return "No active runs."
            lines = ["### Active Content Runs", ""]
            for r in runs.iterdir():
                if r.is_dir():
                    state = core.get_state(r.name)
                    lines.append(f"- **{r.name}** — `{state}`")
            return "\n".join(lines)

        if sub == "new":
            idea = " ".join(argv[1:])
            if not idea:
                return "Usage: /content new <idea>"
            res = core.create_run(idea)
            ctx.inject_message(
                f"New content run created: '{idea}' (route: {res['route']}). "
                f"Next: decide the route and write a brief."
            )
            return f"✅ Created run: **{res['slug']}** (Route: {res['route']})"

        if sub == "route":
            idea = " ".join(argv[1:])
            if not idea:
                return "Usage: /content route <idea> [source_hint]"
            source = argv[-1] if argv[-1] in ("internal", "external", "existing", "research") else ""
            if source:
                idea = " ".join(argv[1:-1])
            res = core.decide_route(idea, source)
            return (
                f"### Idea Gate — Route Decision\n"
                f"- **Route:** {res['route']}\n"
                f"- **Rationale:** {res['rationale']}\n"
                f"- **Source:** {res['source_type']}"
            )

        if sub == "state":
            if len(argv) < 2:
                active = list(core.active_runs.iterdir()) if core.active_runs.exists() else []
                lines = ["### All Run States", ""]
                for d in active:
                    if d.is_dir():
                        lines.append(f"- **{d.name}**: {core.get_state(d.name)}")
                return "\n".join(lines)
            slug = argv[1]
            state = core.get_state(slug)
            actions = core.get_next_actions(slug)
            return (
                f"### {slug}\n"
                f"- **State:** {state}\n"
                f"- **Next actions:**\\n"
                + "\n".join(f"  {i+1}. {a}" for i, a in enumerate(actions))
            )

        if sub == "brief":
            if len(argv) < 2:
                return "Usage: /content brief <slug>"
            slug = argv[1]
            core.sync_state(slug)
            core.update_state(slug, "brief_ready")
            ctx.inject_message(
                f"Please write a Writer Context Packet (brief.md) for run: {slug}. "
                f"Use the Content OS Writer Context Packet format. "
                f"Read idea.md and context.md from the run folder."
            )
            return f"📝 Tasked to write brief for **{slug}**."

        if sub == "draft":
            if len(argv) < 2:
                return "Usage: /content draft <slug>"
            slug = argv[1]
            ctx.inject_message(
                f"Please generate the draft for run: {slug}. "
                f"Read brief.md, voice-profile.md, and master-avoid-slop.md. "
                f"Produce a draft-package.md with rubric_self_assessment, "
                f"avoid_slop_pass, open_loops_flagged, and voice_check sections."
            )
            return f"✍️ Tasked to draft **{slug}**."

        if sub == "verify":
            if len(argv) < 2:
                return "Usage: /content verify <slug>"
            slug = argv[1]
            ctx.inject_message(
                f"Please verify the draft for run: {slug}. "
                f"Read brief.md and draft-package.md. "
                f"Run rubric scoring + slop scan. "
                f"Produce verifier-report.md with VERDICT (APPROVE/REVISE/REJECT)."
            )
            return f"🔍 Tasked to verify **{slug}**."

        if sub == "scan":
            if len(argv) < 2:
                return "Usage: /content scan <slug>"
            slug = argv[1]
            path = core.active_runs / slug / "draft-package.md"
            if not path.exists():
                return f"Draft not found for {slug}"
            res = core.scan_slop(path.read_text(encoding="utf-8"))
            return (
                f"### Slop Scan: {slug}\n"
                f"- **Score:** {res['score']}\n"
                f"- **Tier 1 (Critical):** {res['tier1_count']}\n"
                f"- **Tier 2 (High):** {res['tier2_count']}\n"
                f"- **Tier 3 (Medium):** {res['tier3_count']}\n"
                f"- **Bonus (Tone):** {res['bonus_count']}\n"
                f"- **Findings:** {', '.join(res['all_findings'][:8]) or 'None'}"
            )

        if sub == "audit":
            return core.audit()

        if sub == "setup":
            return core.setup()

        if sub == "signal":
            src = argv[1] if len(argv) > 1 else "x"
            signals = core.process_signal(src)
            lines = [f"### Signals from {src.upper()}", ""]
            for i, s in enumerate(signals, 1):
                lines.append(f"{i}. {s}")
            return "\n".join(lines)

        if sub == "postmortem":
            if len(argv) < 2:
                return "Usage: /content postmortem <slug> [--impressions N --bookmarks N]"
            slug = argv[1]
            ctx.inject_message(
                f"Please run postmortem analysis for run: {slug}. "
                f"Read draft-package.md and feedback.md. "
                f"Analyze exact lines that drove bookmarks and engagement."
            )
            return f"📊 Tasked to run postmortem for **{slug}**."

        if sub == "archive":
            if len(argv) < 2:
                return "Usage: /content archive <slug>"
            return core.archive_run(argv[1])

        if sub == "learnings":
            topic = argv[1] if len(argv) > 1 else None
            return core.get_learnings_for_brief(topic)

        if sub == "patterns":
            patterns = core.analyze_run_patterns()
            if "message" in patterns:
                return patterns["message"]
            lines = ["### Run Patterns Analysis", ""]
            lines.append(f"- **Total runs:** {patterns['total_runs']}")
            lines.append(f"- **Avg bookmarks:** {patterns['avg_bookmarks']}")
            lines.append(f"- **Archived:** {patterns.get('archive_count', 0)}")
            if patterns.get("top_formats"):
                lines.append("\n**Top formats:**")
                for f, c in patterns["top_formats"]:
                    lines.append(f"  - {f}: {c}")
            if patterns.get("state_distribution"):
                lines.append("\n**State distribution:**")
                for s, c in sorted(patterns["state_distribution"].items()):
                    lines.append(f"  - {s}: {c}")
            return "\n".join(lines)

        if sub == "runs":
            include_archived = not (len(argv) > 1 and argv[1] == "--active")
            runs = core.get_all_runs(include_archived)
            if not runs:
                return "No runs found."
            lines = ["### All Content Runs", ""]
            for r in runs:
                state = r.get("state", "?")
                route = r.get("route", "?")
                status = r.get("status", "?")
                files = len(r.get("files", []))
                lines.append(f"- **{r['slug']}** — {state} — {route} — {status} ({files} dosya)")
            return "\n".join(lines)

        if sub == "context":
            if len(argv) < 2:
                return "Usage: /content context <slug>"
            slug = argv[1]
            for base in [core.active_runs, core.archive]:
                ctx_file = base / slug / "context.md"
                if ctx_file.exists():
                    return f"### Context for {slug}\n\n{ctx_file.read_text(encoding='utf-8')[:1500]}"
            return f"Run {slug} not found."

        if sub == "voice-update":
            vf = core.voice / "voice-profile.md"
            if vf.exists():
                return f"### Voice Profile\n\n{vf.read_text(encoding='utf-8')[:1000]}"
            return "No voice profile found."

        return f"Unknown subcommand: {sub}. Try: status, new, route, state, brief, draft, verify, scan, score, audit, setup, signal, postmortem, archive, learnings, patterns, runs, context, voice-update"

    ctx.register_command(
        "content",
        handler=handle_slash,
        description="Content OS: full content production pipeline.",
        args_hint="[status|new|route|state|brief|draft|verify|scan|audit|setup|signal|postmortem|archive|learnings|patterns|runs|context|voice-update]",
    )

    # ══════════════════════════════════════════════════════════════
    # CLI COMMAND: hermes content
    # ══════════════════════════════════════════════════════════════

    ctx.register_cli_command(
        name="content",
        help="Content OS v2.4.0 — Full content production management",
        setup_fn=lambda sub: register_cli(sub, core),
        description=(
            "AI-Augmented Content Production System.\n"
            "Complete pipeline: signal → idea → brief → draft → verify → publish → feedback.\n"
            "14-state lifecycle, 54 slop patterns, 4-route Idea Gate."
        ),
    )

    # ══════════════════════════════════════════════════════════════
    # HOOKS
    # ══════════════════════════════════════════════════════════════

    def on_session_start(**kwargs):
        logger.info("Content OS v%s Session Started.", VERSION)

    def post_tool_call(tool_name: str, args: Dict[str, Any], result: str, **kwargs):
        """Observe file writes to auto-update Content OS states.

        Handles both Hermes tool naming conventions:
        - write_file (current Hermes API)
        - write_to_file (legacy)
        """
        from pathlib import Path
        if tool_name not in ("write_file", "write_to_file", "create_file"):
            return

        target_path = args.get("TargetFile", "") or args.get("path", "") or args.get("file_path", "")

        # Check if this targets a run folder
        if target_path and ("runs/active/" in target_path or "runs\\active\\" in target_path):
            path = Path(target_path)
            try:
                slug = path.parent.name
                filename = path.name

                state_map = {
                    "brief.md": "brief_ready",
                    "draft-package.md": "drafting",
                    "verifier-report.md": "verification",
                    "published": "published",
                }

                if filename in state_map:
                    new_state = state_map[filename]
                    try:
                        core.update_state(slug, new_state)
                        logger.info(
                            "Auto-updated %s to %s (via post_tool_call)", slug, new_state
                        )
                    except Exception:
                        pass
            except Exception:
                pass

    ctx.register_hook("on_session_start", on_session_start)
    ctx.register_hook("post_tool_call", post_tool_call)

    # ══════════════════════════════════════════════════════════════
    # SKILL REGISTRATION
    # ══════════════════════════════════════════════════════════════

    skill_path = root / "SKILL.md"
    if skill_path.exists():
        ctx.register_skill(
            "content-os",
            skill_path,
            description="AI-Augmented Content Production System v2.4.0 — Full Content OS pipeline",
        )

    logger.info("Content OS plugin v%s (Full Implementation) registered.", VERSION)
