"""Prodinamik Engine Plugin v1.8.0

Product-Agnostic Pipeline Engine — Hermes Agent Plugin.

State machine, multi-tier validation, event sourcing, Raft consensus,
AI Grid agent runtime, plugin ecosystem, and AI-native drift detection.

Profiles:
  - software (dev-cycle): Yazılım geliştirme lifecycle
  - content (content-os):  İçerik üretim pipeline (eski Content-OS)
  - haber (haber-kurator): Haber doğrulama pipeline (eski Haber-Kurator)
  - research:              Araştırma pipeline
  - design:                Tasarım pipeline
"""

from pathlib import Path
from typing import Any, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)

VERSION = "1.8.0"

# Plugin root
_PLUGIN_ROOT = Path(__file__).parent


def register(ctx: Any) -> None:
    """Register Prodinamik Engine plugin with Hermes Agent."""
    logger.info(f"Prodinamik Engine v{VERSION} loading...")

    # ══════════════════════════════════════════════════════════════
    # TOOL: prodinamik (26 actions — core + content)
    # ══════════════════════════════════════════════════════════════

    tool_schema = {
        "name": "prodinamik",
        "description": (
            "Prodinamik Engine — workflow management. "
            "34 actions: core (run, list, status, approve, reject, next, "
            "transition, dashboard, budget) + "
            "content (setup, audit, decide_route, scan_slop, score, signal, "
            "search_runs, archive_run, buffer_setup, buffer_send, buffer_status, "
            "update_voice, analyze_patterns, get_learnings, reload_actions) + "
            "haber (fetch_news, verify_news, publish_verified, cross_verify_story, "
            "search_news, auto_publish, hallucination_check, issue_correction, "
            "check_correction, sources) + Content-OS & Haber legacy aliases"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        # Core
                        "run", "list", "status", "approve", "reject",
                        "next", "transition", "dashboard", "budget",
                        # Content-OS actions
                        "setup", "audit", "decide_route", "scan_slop", "score",
                        "signal", "search_runs", "archive_run",
                        "buffer_setup", "buffer_send", "buffer_status",
                        "update_voice", "analyze_patterns", "get_learnings",
                        "reload_actions",
                        # Haber-Kurator actions
                        "fetch_news", "verify_news", "publish_verified",
                        "cross_verify_story", "search_news", "auto_publish",
                        "hallucination_check", "issue_correction",
                        "check_correction", "sources",
                        # Legacy alias
                        "new_run", "get_state", "get_all_runs",
                        "update_state", "get_next_actions",
                    ],
                    "description": "Action to perform in the pipeline (core + content + haber)",
                },
                "profile": {"type": "string", "description": "Profile name: software, content, haber, research, design"},
                "title": {"type": "string", "description": "Run title (for 'run' action)"},
                "slug": {"type": "string", "description": "Run slug"},
                "target_state": {"type": "string", "description": "Target state for transition"},
                "user_id": {"type": "string", "description": "User ID for approval"},
                "include_archived": {"type": "boolean", "description": "Include archived runs", "default": False},
                # Content-specific
                "idea": {"type": "string", "description": "Content idea / text"},
                "source_hint": {"type": "string", "description": "Source hint: internal, external, existing, research"},
                "text": {"type": "string", "description": "Text to scan for slop patterns"},
                "source": {"type": "string", "description": "Signal source: 'x' or 'rss'"},
                "topic": {"type": "string", "description": "Topic filter"},
                "query": {"type": "string", "description": "Search query"},
                "api_key": {"type": "string", "description": "Buffer API key"},
                "updates": {"type": "object", "description": "Voice profile updates"},
                "metrics": {"type": "object", "description": "Postmortem metrics"},
                # Haber-specific
                "search_query": {"type": "string", "description": "News search query"},
                "max_results": {"type": "integer", "description": "Max search results (default: 20)"},
                "language": {"type": "string", "description": "News language filter (default: 'tr')"},
                "country": {"type": "string", "description": "Country filter: 'turkey', 'global'"},
                "category": {"type": "string", "description": "News category: news, technology, business, science"},
                "human_review": {"type": "boolean", "description": "Require human review (default: true)"},
                "cluster_data": {"type": "object", "description": "Story cluster data for cross_verify_story"},
                "error_description": {"type": "string", "description": "Error description for issue_correction"},
                "correct_information": {"type": "string", "description": "Correct information for issue_correction"},
                "retract": {"type": "boolean", "description": "Retract the story entirely (vs correction)", "default": False},
            },
            "required": ["action"],
        },
    }

    ctx.register_tool(
        name="prodinamik",
        toolset="prodinamik",
        schema=tool_schema,
        handler=lambda args, **kw: _handle_tool(args, ctx),
        description="Prodinamik Engine: 26 actions — run pipelines, manage content workflow",
        is_async=False,
    )

    # ══════════════════════════════════════════════════════════════
    # SLASH COMMANDS
    # ══════════════════════════════════════════════════════════════

    ctx.register_command(
        name="/run",
        handler=lambda raw, **kw: _handle_slash_run(raw, ctx),
        description="Create a new workflow run. Usage: /run <profile> <title>",
        args_hint="<profile> <title>",
    )

    ctx.register_command(
        name="/p-approve",
        handler=lambda raw, **kw: _handle_slash_approve(raw, ctx),
        description="Approve a pending task. Usage: /p-approve <slug>",
        args_hint="<slug>",
    )

    ctx.register_command(
        name="/p-next",
        handler=lambda raw, **kw: _handle_slash_next(raw, ctx),
        description="Show next step for a run. Usage: /p-next <slug>",
        args_hint="<slug>",
    )

    ctx.register_command(
        name="/p-status",
        handler=lambda raw, **kw: _handle_slash_status(raw, ctx),
        description="Show engine or run status. Usage: /p-status [slug]",
        args_hint="[slug]",
    )

    # ══════════════════════════════════════════════════════════════
    # CLI: hermes prodinamik ...
    # ══════════════════════════════════════════════════════════════

    try:
        from .cli import register_cli
        register_cli(ctx)
    except ImportError as e:
        logger.warning(f"CLI registration failed: {e}")

    # ══════════════════════════════════════════════════════════════
    # HOOK: Event → Telegram push
    # ══════════════════════════════════════════════════════════════

    ctx.register_hook(
        hook_name="post_tool_call",
        callback=lambda **kw: _hook_post_tool(_ctx=ctx, **kw),
    )

    logger.info(f"Prodinamik Engine v{VERSION} loaded with 34 actions (9 core + 15 content + 10 haber)")


# ═══════════════════════════════════════════════════════════════════
# Tool Handler
# ═══════════════════════════════════════════════════════════════════

def _handle_tool(args: Dict[str, Any], ctx: Any) -> str:
    """Main tool handler — dispatches to hermes_bridge.handle_all."""
    from .hermes_bridge import handle_all

    action = args.get("action", "")
    if not action:
        return json.dumps({"error": "action is required"}, ensure_ascii=False)

    try:
        result = handle_all(args)
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        logger.error(f"Action '{action}' failed: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════════
# Slash Command Handlers (raw_args: str → str)
# ═══════════════════════════════════════════════════════════════════

def _handle_slash_run(raw_args: str, ctx: Any) -> str:
    """/run <profile> <title>"""
    parts = raw_args.strip().split(maxsplit=1)
    if len(parts) < 2:
        return ("Usage: /run <profile> <title>\n"
                "Profiles: software, content, haber, research, design")

    profile, title = parts[0], parts[1]
    result = _handle_tool({"action": "run", "profile": profile, "title": title}, ctx)
    data = json.loads(result)
    if "error" in data:
        return f"❌ {data['error']}"
    return (f"✅ Run oluşturuldu: `{data['slug']}`\n"
            f"   Profile: {data.get('profile', profile)}\n"
            f"   State: {data.get('state', 'captured')}\n"
            f"   Sonraki: /p-next {data['slug']}")


def _handle_slash_approve(raw_args: str, ctx: Any) -> str:
    """/p-approve <slug>"""
    slug = raw_args.strip()
    if not slug:
        return "Usage: /p-approve <slug>"
    result = _handle_tool({"action": "approve", "slug": slug, "user_id": "telegram"}, ctx)
    data = json.loads(result)
    if "error" in data:
        return f"❌ {data['error']}"
    return f"✅ `{slug}` onaylandı → {data.get('state', 'release')}"


def _handle_slash_next(raw_args: str, ctx: Any) -> str:
    """/p-next <slug>"""
    slug = raw_args.strip()
    if not slug:
        return "Usage: /p-next <slug>"
    result = _handle_tool({"action": "next", "slug": slug}, ctx)
    data = json.loads(result)
    if "error" in data:
        return f"❌ {data['error']}"

    msg = f"📋 **{slug}** — Sıradaki adım: **{data.get('next_state', '?')}**\n"
    msg += f"   Mevcut: {data.get('current_state', '?')}\n"
    if available := data.get("available_states"):
        msg += f"   Seçenekler: {' → '.join(available)}\n"
    return msg


def _handle_slash_status(raw_args: str, ctx: Any) -> str:
    """/p-status [slug]"""
    slug = raw_args.strip()
    result = _handle_tool({"action": "status", "slug": slug}, ctx)
    data = json.loads(result)
    if "error" in data:
        return f"❌ {data['error']}"

    if slug:
        msg = f"📊 **{slug}**\n"
        msg += f"   State: {data.get('state', '?')}\n"
        msg += f"   Profile: {data.get('profile', '?')}\n"
        msg += f"   Süre: {data.get('elapsed', 0)}s\n"
        if avail := data.get("available_states"):
            msg += f"   Geçilebilir: {' → '.join(avail)}\n"
    else:
        msg = "🏭 **Prodinamik Engine**\n"
        msg += f"   Aktif run: {data.get('active_runs', 0)}\n"
        msg += f"   Sağlık: %{data.get('health_score', 0)*100:.0f}\n"
        msg += f"   Profiller: {', '.join(data.get('profiles', []))}\n"
    return msg


# ═══════════════════════════════════════════════════════════════════
# Hook: Event → Telegram Push
# ═══════════════════════════════════════════════════════════════════

def _hook_post_tool(**kw):
    """Post-tool hook — engine event'lerini Telegram'a push'la."""
    ctx = kw.get("_ctx")
    tool_name = kw.get("tool_name", "")
    args = kw.get("args", {})
    result = kw.get("result", "")

    if tool_name != "prodinamik":
        return

    action = args.get("action", "")
    slug = args.get("slug", "")

    if action not in ("transition", "approve", "reject", "run"):
        return

    try:
        data = json.loads(result) if isinstance(result, str) else result
        state = data.get("state", data.get("current_state", ""))
        emoji = {"run": "🆕", "approve": "✅", "reject": "❌", "transition": "🔔"}
        msg = f"{emoji.get(action, '🔔')} `{slug}` → **{state}**"

        try:
            from run_agent import AIAgent
            agent = AIAgent()
            agent.send_message("telegram", msg)
        except Exception:
            pass
    except Exception:
        pass
