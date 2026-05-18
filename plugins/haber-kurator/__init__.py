"""
Haber-Kurator Plugin v3.1.0 → MIGRATED TO PRODINAMIK ENGINE

This plugin now acts as a THIN WRAPPER that delegates all calls
to the Prodinamik Engine plugin (prodinamik tool).

Original source code archived at: plugins/archive/haber-kurator/

Migration date: 2026-05-19 (final)
"""

from pathlib import Path
from typing import Any, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)

VERSION = "3.1.0 (migrated → prodinamik-engine)"


def register(ctx: Any) -> None:
    """Register haber-kurator tools → Prodinamik Engine delegation."""

    logger.info(
        "Haber-Kurator v%s — MIGRATED to Prodinamik Engine. "
        "Use 'prodinamik' tool instead. Original code at plugins/archive/haber-kurator/",
        VERSION,
    )

    # ── Tool: haber_kurator_manager → delegates to prodinamik ──
    manager_schema = {
        "name": "haber_kurator_manager",
        "description": (
            "[MIGRATED] Haber Kuratör → now delegates to Prodinamik Engine. "
            "Use 'prodinamik' tool instead with the same actions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "setup", "audit", "list", "sources",
                        "fetch_news", "verify_news", "publish_verified",
                        "cross_verify_story", "search_news",
                        "auto_publish", "hallucination_check",
                        "check_correction", "issue_correction",
                        "update_state", "get_state", "sync_state",
                        "get_next_actions", "scan_slop",
                        "search_runs", "get_all_runs", "archive_run",
                    ],
                },
                "slug": {"type": "string"},
                "state": {"type": "string"},
                "text": {"type": "string"},
                "query": {"type": "string"},
                "search_query": {"type": "string"},
                "max_results": {"type": "integer"},
                "language": {"type": "string"},
                "country": {"type": "string"},
                "include_archived": {"type": "boolean", "default": True},
                "category": {"type": "string"},
                "limit": {"type": "integer"},
                "human_review": {"type": "boolean", "default": True},
                "cluster_data": {"type": "object"},
                "error_description": {"type": "string"},
                "correct_information": {"type": "string"},
                "retract": {"type": "boolean", "default": False},
            },
            "required": ["action"],
        },
    }

    def _proxy_handler(args: dict, **kw) -> str:
        """Delegate haber_kurator_manager call to Prodinamik Engine handle_all."""
        try:
            import sys
            plugin_dir = Path(__file__).parent.parent / "prodinamik-engine"
            if plugin_dir.exists():
                sys.path.insert(0, str(plugin_dir))
                from hermes_bridge import handle_all
                result = handle_all(args)
                return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            logger.warning(f"Prodinamik Engine proxy failed: {e}")
            return json.dumps({"error": f"Haber action '{args.get('action')}' failed. Prodinamik Engine unavailable."}, ensure_ascii=False)

        return json.dumps({"error": "Prodinamik Engine plugin not found"}, ensure_ascii=False)

    ctx.register_tool(
        name="haber_kurator_manager",
        toolset="haber",
        schema=manager_schema,
        handler=_proxy_handler,
        description="[MIGRATED → use prodinamik] Haber Kuratör news verification pipeline",
        is_async=False,
    )

    # ── Tool: haber_kurator_retriever → delegates ──
    retriever_schema = {
        "name": "haber_kurator_retriever",
        "description": "[MIGRATED → use prodinamik] Knowledge retrieval from Haber Kuratör stores.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["sources", "source_summary", "strategy", "voice", "run", "stores", "learnings"],
                },
                "slug": {"type": "string"},
                "topic": {"type": "string"},
            },
            "required": ["category"],
        },
    }

    def _retriever_handler(args: dict, **kw) -> str:
        try:
            import sys
            plugin_dir = Path(__file__).parent.parent / "prodinamik-engine"
            if plugin_dir.exists():
                sys.path.insert(0, str(plugin_dir))
                from hermes_bridge import handle_all
                if args.get("category") == "sources":
                    result = handle_all({"action": "sources"})
                else:
                    result = handle_all({"action": "sources"})
                return json.dumps(result, ensure_ascii=False, default=str)
        except Exception:
            pass
        return json.dumps({"error": "Retriever unavailable"}, ensure_ascii=False)

    ctx.register_tool(
        name="haber_kurator_retriever",
        toolset="haber",
        schema=retriever_schema,
        handler=_retriever_handler,
        description="[MIGRATED] Knowledge retrieval from Haber Kuratör stores.",
    )

    # ── Slash command: /haber → redirect notice ──
    def handle_slash(args: str) -> str:
        return (
            "⚠️ Haber-Kurator is MIGRATED to Prodinamik Engine.\n"
            "   Use these slash commands instead:\n"
            "   • `/run haber <title>` — Create news run\n"
            "   • `/p-status <slug>` — Check status\n\n"
            "   Or use the `prodinamik` tool directly:\n"
            "   `prodinamik action=fetch_news country=turkey`\n"
            "   `prodinamik action=verify_news country=turkey`\n"
            "   `prodinamik action=sources`"
        )

    ctx.register_command(
        "haber",
        handler=handle_slash,
        description="[MIGRATED] Haber Kuratör — use /run and /p-* commands instead",
        args_hint="",
    )

    logger.warning(
        "Haber-Kurator plugin → fully migrated to Prodinamik Engine. "
        "Run 'prodinamik action=...' instead of 'haber_kurator_manager action=...'"
    )
