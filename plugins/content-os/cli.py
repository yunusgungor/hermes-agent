"""
CLI registration for Content OS v2.4.0.

Full CLI interface: setup, status, audit, new, brief, draft, verify,
scan, score, signal, postmortem, learnings, patterns, search, runs,
context, voice-update, route, archive, extract-brand.
"""

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from content_os_core import ContentOSCore

console = Console()


def register_cli(content_parser, core: ContentOSCore):
    """Build the hermes content argparse tree."""
    subs = content_parser.add_subparsers(dest="content_command")

    # ── System ──
    subs.add_parser("setup", help="Initialize Content OS v2.4.0 directory structure")
    subs.add_parser("status", help="Show state of all active content runs")
    subs.add_parser("audit", help="Full system audit (directories, files, health)")

    # ── Idea Gate ──
    route_parser = subs.add_parser("route", help="Decide 4-route Idea Gate for an idea")
    route_parser.add_argument("idea", nargs="+", help="The content idea")
    route_parser.add_argument("--source", choices=["internal", "external", "existing", "research"],
                              help="Optional source hint for routing")

    # ── Run ──
    new_parser = subs.add_parser("new", help="Start a new content object (with Idea Gate)")
    new_parser.add_argument("idea", nargs="+", help="The initial content idea")
    new_parser.add_argument("--slug", help="Optional custom slug")
    new_parser.add_argument("--source", choices=["internal", "external", "existing", "research"],
                            help="Source hint for Idea Gate routing")

    state_parser = subs.add_parser("state", help="Show or update run state")
    state_parser.add_argument("slug", nargs="?", help="Optional slug to show state")
    state_parser.add_argument("--set", help="New state value (e.g. approved, scheduled)")

    # ── Agent Pipeline ──
    brief_parser = subs.add_parser("brief", help="Start brief generation for a run")
    brief_parser.add_argument("slug", help="Content slug")
    brief_parser.add_argument("--llm", action="store_true", help="Use LLM to auto-generate brief.md")

    draft_parser = subs.add_parser("draft", help="Start draft generation for a run")
    draft_parser.add_argument("slug", help="Content slug")
    draft_parser.add_argument("--llm", action="store_true", help="Use LLM to auto-generate draft")

    verify_parser = subs.add_parser("verify", help="Run verifier on a draft")
    verify_parser.add_argument("slug", help="Content slug")
    verify_parser.add_argument("--llm", action="store_true", help="Use LLM for verification")

    # ── Quality ──
    scan_parser = subs.add_parser("scan", help="Scan a draft for 54 slop patterns")
    scan_parser.add_argument("slug", help="The content slug to scan")

    score_parser = subs.add_parser("score", help="Score a draft against 12-point rubric")
    score_parser.add_argument("slug", help="The content slug to score")

    # ── Signals ──
    signal_parser = subs.add_parser("signal", help="Fetch content signals from a source")
    signal_parser.add_argument("source", nargs="?", choices=["x", "rss"], default="x",
                               help="Signal source")

    # ── Postmortem ──
    postmortem_parser = subs.add_parser("postmortem", help="LLM-based postmortem analysis")
    postmortem_parser.add_argument("slug", help="Content slug")
    postmortem_parser.add_argument("--impressions", type=int, default=0)
    postmortem_parser.add_argument("--bookmarks", type=int, default=0)
    postmortem_parser.add_argument("--likes", type=int, default=0)
    postmortem_parser.add_argument("--retweets", type=int, default=0)

    # ── Learnings ──
    learnings_parser = subs.add_parser("learnings", help="Get learnings from previous runs")
    learnings_parser.add_argument("--topic", help="Optional topic filter")

    patterns_parser = subs.add_parser("patterns", help="Analyze patterns across all runs")

    # ── Search ──
    search_parser = subs.add_parser("search", help="Search runs by content")
    search_parser.add_argument("query", help="Search query")

    # ── List ──
    runs_parser = subs.add_parser("runs", help="List all runs with state, route, status")
    runs_parser.add_argument("--no-archive", action="store_true", help="Exclude archived runs")

    # ── Context ──
    ctx_parser = subs.add_parser("context", help="Show context for a run")
    ctx_parser.add_argument("slug", help="Content slug")

    # ── Voice ──
    subs.add_parser("voice-update", help="Show current voice profile")

    # ── Archive ──
    archive_parser = subs.add_parser("archive", help="Archive a learned run")
    archive_parser.add_argument("slug", help="Content slug to archive")

    # ── Brand Foundation ──
    subs.add_parser("extract-brand", help="Extract brand foundation from raw notes (interactive)")

    # ══════════════════════════════════════════════════════════════
    # HANDLER
    # ══════════════════════════════════════════════════════════════

    def handler(args):
        cmd = args.content_command

        # ── Setup ──
        if cmd == "setup":
            console.print(core.setup())

        # ── Status ──
        elif cmd == "status":
            table = Table(title="Content OS — Active Run States")
            table.add_column("Slug", style="cyan")
            table.add_column("State (14-stage)", style="magenta")
            table.add_column("Route", style="yellow")
            table.add_column("Next Action", style="dim")

            if core.active_runs.exists():
                for d in core.active_runs.iterdir():
                    if d.is_dir():
                        slug = d.name
                        state = core.get_state(slug)
                        route = "?"
                        obj = d / "content-object.md"
                        if obj.exists():
                            m = __import__("re").search(r'route:\s*(\w+)',
                                                         obj.read_text(encoding="utf-8"),
                                                         __import__("re").IGNORECASE)
                            if m:
                                route = m.group(1)
                        actions = core.get_next_actions(slug)
                        next_action = actions[0] if actions else ""
                        table.add_row(slug, state, route, next_action[:40])
            console.print(table)

        # ── Audit ──
        elif cmd == "audit":
            report = core.audit()
            color = "green" if "✅" in report else "red"
            console.print(Panel(report, title="Content OS System Audit", border_style=color))

        # ── Route (Idea Gate) ──
        elif cmd == "route":
            idea = " ".join(args.idea)
            source = getattr(args, "source", "")
            res = core.decide_route(idea, source)
            console.print(Panel(
                f"[bold]Route:[/bold] {res['route']}\n"
                f"[bold]Rationale:[/bold] {res['rationale']}\n"
                f"[bold]Source:[/bold] {res['source_type']}",
                title=f"Idea Gate — {idea[:50]}",
                border_style="blue",
            ))

        # ── New Run ──
        elif cmd == "new":
            idea = " ".join(args.idea)
            slug = getattr(args, "slug", None)
            source = getattr(args, "source", "")
            res = core.create_run(idea, slug, source)
            if res.get("status") == "exists":
                console.print(f"[yellow]Run already exists:[/yellow] {res['slug']}")
            else:
                console.print(f"[bold green]✅ Created new run:[/bold green] {res['slug']}")
                console.print(f"   Route: {res['route']}")
                console.print(f"   Path: {res['path']}")
                if res.get("context_provided"):
                    console.print("[dim]Context from previous runs automatically provided[/dim]")

        # ── State ──
        elif cmd == "state":
            slug = getattr(args, "slug", None)
            new_state = getattr(args, "set", None)

            if new_state and slug:
                console.print(core.update_state(slug, new_state))
            elif slug:
                state = core.get_state(slug)
                actions = core.get_next_actions(slug)
                console.print(f"[bold cyan]{slug}[/bold cyan] — State: [bold]{state}[/bold]")
                console.print("\n[bold]Next actions:[/bold]")
                for i, a in enumerate(actions, 1):
                    console.print(f"  {i}. {a}")
            else:
                # Show all states
                if core.active_runs.exists():
                    table = Table(title="All Run States")
                    table.add_column("Slug", style="cyan")
                    table.add_column("State", style="magenta")
                    for d in core.active_runs.iterdir():
                        if d.is_dir():
                            table.add_row(d.name, core.get_state(d.name))
                    console.print(table)
                else:
                    console.print("[yellow]No active runs[/yellow]")

        # ── Brief ──
        elif cmd == "brief":
            slug = args.slug
            use_llm = getattr(args, "llm", False)
            core.sync_state(slug)
            core.update_state(slug, "brief_ready")
            console.print(f"[bold green]📝 Brief generation triggered for[/bold green] {slug}")
            console.print("State set to: brief_ready")
            if use_llm:
                console.print("[yellow]LLM auto-generation requires async context. "
                             "Use Hermes agent interaction instead.[/yellow]")
            else:
                console.print("Write brief.md in the run folder (see SKILL.md for template).")

        # ── Draft ──
        elif cmd == "draft":
            slug = args.slug
            use_llm = getattr(args, "llm", False)
            console.print(f"[bold green]✍️ Draft generation triggered for[/bold green] {slug}")
            if use_llm:
                console.print("[yellow]LLM auto-generation requires async context. "
                             "Use Hermes agent interaction instead.[/yellow]")
            else:
                console.print("Run Writer Agent: read brief.md + voice-profile.md → draft-package.md")

        # ── Verify ──
        elif cmd == "verify":
            slug = args.slug
            console.print(f"[bold green]🔍 Verification triggered for[/bold green] {slug}")
            l = getattr(args, "llm", False)
            if l:
                console.print("[yellow]LLM verifier requires async context. "
                             "Use Hermes agent interaction instead.[/yellow]")

        # ── Scan (54-pattern slop) ──
        elif cmd == "scan":
            import re as _re
            run_path = (core.active_runs / args.slug).resolve()
            draft_path = run_path / "draft-package.md"
            if not draft_path.exists():
                draft_path_run = run_path / "draft.md"
                if draft_path_run.exists():
                    draft_path = draft_path_run
            if not draft_path.exists():
                console.print(f"[red]Error:[/red] Draft not found for {args.slug}")
                return

            res = core.scan_slop(draft_path.read_text(encoding="utf-8"))
            color = "green" if res["score"] == "PASS" else (
                "yellow" if res["score"] == "REVISE" else "red")
            console.print(f"\n[bold {color}]Score: {res['score']}[/bold {color}]")
            console.print(f"Tier 1 (Critical): {res['tier1_count']}")
            console.print(f"Tier 2 (High): {res['tier2_count']}")
            console.print(f"Tier 3 (Medium): {res['tier3_count']}")
            console.print(f"Bonus (Tone/Noise): {res['bonus_count']}")

            if res["all_findings"]:
                console.print("\n[bold]Detected Patterns:[/bold]")
                for f in res["all_findings"][:15]:
                    console.print(f"  - {f[:80]}")
                if len(res["all_findings"]) > 15:
                    console.print(f"  ... and {len(res['all_findings']) - 15} more")

        # ── Score (Rubric) ──
        elif cmd == "score":
            console.print(f"[cyan]Rubric requires LLM context. "
                         f"Use Hermes agent interaction: 'rubric score {args.slug}'[/cyan]")

        # ── Signal ──
        elif cmd == "signal":
            signals = core.process_signal(args.source)
            table = Table(title=f"Signals from {args.source.upper()}")
            table.add_column("#", style="dim")
            table.add_column("Signal")
            for i, s in enumerate(signals, 1):
                table.add_row(str(i), s[:120])
            console.print(table)

        # ── Postmortem ──
        elif cmd == "postmortem":
            metrics = {
                "impressions": args.impressions,
                "bookmarks": args.bookmarks,
                "likes": args.likes,
                "retweets": args.retweets,
                "engagements": args.likes + args.retweets,
            }
            console.print(f"[cyan]Postmortem requires LLM context. "
                         f"Use Hermes agent interaction: 'run postmortem for {args.slug}'[/cyan]")

        # ── Learnings ──
        elif cmd == "learnings":
            learnings = core.get_learnings_for_brief(
                getattr(args, "topic", None))
            console.print(Panel(learnings, title="Learnings from Previous Runs"))

        # ── Patterns ──
        elif cmd == "patterns":
            patterns = core.analyze_run_patterns()
            if "message" in patterns:
                console.print(f"[yellow]{patterns['message']}[/yellow]")
                return

            table = Table(title="Run Patterns Analysis")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            table.add_row("Total Runs", str(patterns.get("total_runs", 0)))
            table.add_row("Avg Bookmarks", str(patterns.get("avg_bookmarks", 0)))
            table.add_row("Archived", str(patterns.get("archive_count", 0)))
            console.print(table)

            if patterns.get("top_formats"):
                console.print("\n[bold]Top Formats:[/bold]")
                for fmt, count in patterns["top_formats"]:
                    console.print(f"  - {fmt}: {count}")
            if patterns.get("top_pillars"):
                console.print("\n[bold]Top Pillars:[/bold]")
                for pillar, count in patterns["top_pillars"]:
                    console.print(f"  - {pillar}: {count}")
            if patterns.get("state_distribution"):
                console.print("\n[bold]State Distribution:[/bold]")
                for state, count in sorted(patterns["state_distribution"].items()):
                    console.print(f"  - {state}: {count}")

        # ── Search ──
        elif cmd == "search":
            results = core.search_runs(args.query)
            if not results:
                console.print(f"[yellow]No results for '{args.query}'[/yellow]")
                return
            table = Table(title=f"Search Results: '{args.query}'")
            table.add_column("Slug", style="cyan")
            table.add_column("File", style="yellow")
            table.add_column("State", style="magenta")
            for r in results:
                table.add_row(r["slug"], r["file"], r.get("state", "unknown"))
            console.print(table)

        # ── Runs ──
        elif cmd == "runs":
            include_archived = not args.no_archive
            runs = core.get_all_runs(include_archived)
            if not runs:
                console.print("[yellow]No runs found[/yellow]")
                return
            table = Table(title="All Content Runs")
            table.add_column("Slug", style="cyan")
            table.add_column("State", style="magenta")
            table.add_column("Route", style="yellow")
            table.add_column("Status", style="green")
            table.add_column("Files", style="dim")
            for r in runs:
                fc = len(r.get("files", []))
                table.add_row(
                    r["slug"],
                    r.get("state", "?"),
                    r.get("route", "?"),
                    r.get("status", "?"),
                    f"{fc} files",
                )
            console.print(table)

        # ── Context ──
        elif cmd == "context":
            for base in [core.active_runs, core.archive]:
                cf = base / args.slug / "context.md"
                if cf.exists():
                    console.print(Panel(
                        cf.read_text(encoding="utf-8"),
                        title=f"Context for {args.slug}",
                    ))
                    return
            console.print(f"[red]Error:[/red] Run {args.slug} not found")

        # ── Voice Update ──
        elif cmd == "voice-update":
            vf = core.voice / "voice-profile.md"
            if vf.exists():
                console.print(Panel(
                    vf.read_text(encoding="utf-8"),
                    title="Voice Profile (with updates)",
                ))
            else:
                console.print("[yellow]No voice profile found[/yellow]")

        # ── Archive ──
        elif cmd == "archive":
            console.print(core.archive_run(args.slug))

        # ── Extract Brand ──
        elif cmd == "extract-brand":
            console.print(Panel(
                "Brand Foundation Extraction\n\n"
                "Use Hermes agent interaction with the Brand Foundation prompt:\n"
                "1. Share raw notes (what you do, audience, voice)\n"
                "2. Agent will produce 6 artifacts:\n"
                "   - positioning.md\n"
                "   - audience.md\n"
                "   - pillars.md\n"
                "   - voice rules (5 rules + 5 antipatterns)\n"
                "   - voice-profile.md\n"
                "   - proof bank (10 items)\n"
                "3. Files saved to strategy/ and voice/ directories\n",
                title="Content OS — Brand Foundation Extraction",
                border_style="blue",
            ))

        else:
            content_parser.print_help()

    content_parser.set_defaults(func=handler)
