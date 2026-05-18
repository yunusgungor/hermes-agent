"""
Content-OS Plugin v2.5.0 → MIGRATED TO PRODINAMIK ENGINE

This plugin now acts as a THIN WRAPPER that delegates all calls
to the Prodinamik Engine plugin (prodinamik tool).

Original source code archived at: plugins/archive/content-os/

Migration date: 2026-05-19 (final)
"""

from pathlib import Path
from typing import Any, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)

VERSION = "2.5.0 (migrated → prodinamik-engine)"


def register(ctx: Any) -> None:
    """Register content-os tools → Prodinamik Engine delegation."""

    logger.info(
        "Content-OS v%s — MIGRATED to Prodinamik Engine. "
        "Use 'prodinamik' tool instead. Original code at plugins/archive/content-os/",
        VERSION,
    )

    # ── Tool: content_os_manager → delegates to prodinamik handle_all ──
    manager_schema = {
        "name": "content_os_manager",
        "description": (
            "[MIGRATED] Content OS pipeline → now delegates to Prodinamik Engine. "
            "Use 'prodinamik' tool instead with the same actions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "setup", "audit", "list", "new_run", "decide_route",
                        "generate_brief", "generate_draft", "run_verifier",
                        "scan_slop", "score", "signal", "postmortem",
                        "update_voice", "get_learnings", "analyze_patterns",
                        "search_runs", "get_all_runs", "archive_run",
                        "get_state", "update_state", "sync_state",
                        "get_next_actions",
                        "buffer_setup", "buffer_send", "buffer_status",
                        "run_pipeline", "reload_actions",
                    ],
                },
                "idea": {"type": "string"},
                "source_hint": {"type": "string"},
                "slug": {"type": "string"},
                "state": {"type": "string"},
                "text": {"type": "string"},
                "source": {"type": "string"},
                "metrics": {"type": "object"},
                "updates": {"type": "object"},
                "topic": {"type": "string"},
                "query": {"type": "string"},
                "extra_context": {"type": "string"},
                "include_archived": {"type": "boolean", "default": True},
                "api_key": {"type": "string"},
                "force": {"type": "boolean", "default": False},
            },
            "required": ["action"],
        },
    }

    def _proxy_handler(args: dict, **kw) -> str:
        """Delegate content_os_manager call to Prodinamik Engine handle_all."""
        try:
            import sys
            plugin_dir = Path(__file__).parent.parent / "prodinamik-engine"
            if plugin_dir.exists():
                sys.path.insert(0, str(plugin_dir))
                from hermes_bridge import handle_all
                result = handle_all(args)
                return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            logger.warning(f"Prodinamik Engine proxy failed, using fallback: {e}")
            # Fallback: load original core from archive
            try:
                import importlib.util
                archive_core = Path(__file__).parent.parent / "archive" / "content-os" / "content_os_core.py"
                if archive_core.exists():
                    from plugins.archive.content_os.content_os_core import tool_content_os_manager
                    return tool_content_os_manager(archive_core.parent, args, **kw)
            except Exception:
                pass
            return json.dumps({"error": f"Content action '{args.get('action')}' failed. Prodinamik Engine unavailable."}, ensure_ascii=False)

        return json.dumps({"error": "Prodinamik Engine plugin not found"}, ensure_ascii=False)

    ctx.register_tool(
        name="content_os_manager",
        toolset="content",
        schema=manager_schema,
        handler=_proxy_handler,
        description="[MIGRATED → use prodinamik] Content OS pipeline management",
        is_async=False,
    )

    # ── Tool: content_os_retriever (lightweight, keep native) ──
    retriever_schema = {
        "name": "content_os_retriever",
        "description": "[MIGRATED → use prodinamik] Knowledge retrieval from Content OS stores.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["strategy", "voice", "run", "stores", "learnings"],
                },
                "slug": {"type": "string"},
                "topic": {"type": "string"},
            },
            "required": ["category"],
        },
    }

    def _retriever_handler(args: dict, **kw) -> str:
        """Delegate retriever to Prodinamik Engine."""
        try:
            import sys
            plugin_dir = Path(__file__).parent.parent / "prodinamik-engine"
            if plugin_dir.exists():
                sys.path.insert(0, str(plugin_dir))
                from hermes_bridge import handle_all
                # Map retriever actions to prodinamik actions
                category = args.get("category", "")
                if category in ("strategy", "voice", "run", "stores", "learnings"):
                    result = handle_all({"action": "get_learnings", "topic": args.get("topic", "")})
                    return json.dumps(result, ensure_ascii=False, default=str)
        except Exception:
            pass
        return json.dumps({"error": "Retriever unavailable"}, ensure_ascii=False)

    ctx.register_tool(
        name="content_os_retriever",
        toolset="content",
        schema=retriever_schema,
        handler=_retriever_handler,
        description="[MIGRATED] Knowledge retrieval from Content OS stores.",
    )

    # ── Slash command: /content → redirect notice ──
    def handle_slash(args: str) -> str:
        return (
            "⚠️ Content-OS is MIGRATED to Prodinamik Engine.\n"
            "   Use these slash commands instead:\n"
            "   • `/run content <title>` — Create content run\n"
            "   • `/p-status <slug>` — Check status\n"
            "   • `/p-next <slug>` — Next step\n"
            "   • `/p-approve <slug>` — Approve\n\n"
            "   Or use the `prodinamik` tool directly:\n"
            "   `prodinamik action=scan_slop text=...`"
        )

    ctx.register_command(
        "content",
        handler=handle_slash,
        description="[MIGRATED] Content OS — use /run and /p-* commands instead",
        args_hint="",
    )

    # ── CLI: hermes content → redirect notice ──
    try:
        from cli import register_cli as old_register_cli
        old_register_cli(None, None)
    except Exception:
        pass

    logger.warning(
        "Content-OS plugin → fully migrated to Prodinamik Engine. "
        "Run 'prodinamik action=...' instead of 'content_os_manager action=...'"
    )
