"""Prodinamik Engine — Hermes CLI commands."""


def register_cli(ctx):
    """Register CLI subcommand: hermes prodinamik ..."""
    try:

        def setup_parser(subparser):
            subparser.add_argument("command", nargs="?",
                                   choices=["run", "list", "status", "approve", "next", "transition", "dashboard"],
                                   help="Command to execute")
            subparser.add_argument("args", nargs="*", help="Command arguments")

            subsub = subparser.add_subparsers(dest="subcommand")

            run_parser = subsub.add_parser("run", help="Create a new workflow run")
            run_parser.add_argument("profile", nargs="?", default="software",
                                    help="Profile name (software, content-os, haber-kurator)")
            run_parser.add_argument("title", nargs="+", help="Run title")

            status_parser = subsub.add_parser("status", help="Show engine or run status")
            status_parser.add_argument("slug", nargs="?", default="", help="Run slug")

            approve_parser = subsub.add_parser("approve", help="Approve a pending task")
            approve_parser.add_argument("slug", help="Run slug")

            next_parser = subsub.add_parser("next", help="Show next step")
            next_parser.add_argument("slug", help="Run slug")

            transition_parser = subsub.add_parser("transition", help="Execute state transition")
            transition_parser.add_argument("slug", help="Run slug")
            transition_parser.add_argument("target_state", help="Target state")

        def handler(args):
            from .hermes_bridge import (
                handle_run, handle_list, handle_status, handle_approve,
                handle_next, handle_transition, handle_dashboard,
            )

            import json

            if args.subcommand == "run":
                result = handle_run({"profile": args.profile, "title": " ".join(args.title)})
            elif args.subcommand == "status":
                result = handle_status({"slug": args.slug or ""})
            elif args.subcommand == "approve":
                result = handle_approve({"slug": args.slug})
            elif args.subcommand == "next":
                result = handle_next({"slug": args.slug})
            elif args.subcommand == "transition":
                result = handle_transition({"slug": args.slug, "target_state": args.target_state})
            elif args.command == "list":
                result = handle_list({})
            elif args.command == "dashboard":
                result = handle_dashboard({})
            else:
                return "Commands: run, list, status, approve, next, transition, dashboard"
            return json.dumps(result, ensure_ascii=False, indent=2)

        ctx.register_cli_command(
            name="prodinamik",
            help="Prodinamik Engine management",
            setup_fn=setup_parser,
            handler_fn=handler,
            description="Workflow engine commands",
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"CLI registration skipped: {e}")
