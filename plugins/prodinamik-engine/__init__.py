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
import sys

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
            "51 actions: core (run, list, status, approve, reject, next, "
            "transition, resume, dashboard, budget) + "
            "content (setup, audit, decide_route, scan_slop, score, signal, "
            "search_runs, archive_run, buffer_setup, buffer_send, buffer_status, "
            "update_voice, analyze_patterns, get_learnings, reload_actions) + "
            "haber (fetch_news, verify_news, publish_verified, cross_verify_story, "
            "search_news, auto_publish, hallucination_check, issue_correction, "
            "check_correction, sources) + "
            "AI (ai_detect, ai_predict, ai_recommend, ai_status) + "
            "observability (audit_query, metrics, alert_send) + "
            "management (auth_create, auth_list, auth_revoke, "
            "raft_status, plugin_list, plugin_info) + "
            "debug + config + "
            "legacy aliases.\n\n"
            "HITL (Human-In-The-Loop): transition action'ı PAUSE state'e geçince "
            "awaiting_input=True + questions döndürür. Agent bu durumda clarify "
            "ile kullanıcıya sormalı, sonra resume action'ı ile cevabı iletmelidir."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        # Core
                        "run", "list", "status", "approve", "reject",
                        "next", "transition", "resume", "dashboard", "budget",
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
                        # AI features (NEW — Phase 1)
                        "ai_detect", "ai_predict", "ai_recommend", "ai_status",
                        # Skill emergence — C2: AI Grid (NEW)
                        "generate_skills", "drift_emergence",
                        # Warm Agent — C3 (NEW)
                        "agent_status", "agent_queue",
                        # Observability (NEW — Phase 1)
                        "audit_query", "metrics", "alert_send",
                        # Management (NEW — Phase 2)
                        "auth_create", "auth_list", "auth_revoke",
                        "raft_status", "plugin_list", "plugin_info",
                        # Debug + Config (NEW — Phase 3)
                        "debug", "config",
                        # Legacy alias
                        "new_run", "get_state", "get_all_runs",
                        "update_state", "get_next_actions",
                    ],
                    "description": "Action to perform (core + content + haber + ai + observability)",
                },
                "profile": {"type": "string", "description": "Profile name: software, content, haber, research, design"},
                "title": {"type": "string", "description": "Run title (for 'run' action)"},
                "slug": {"type": "string", "description": "Run slug"},
                "target_state": {"type": "string", "description": "Target state for transition"},
                "answers": {"type": "object", "description": "HITL: User answers dict for resume action (e.g. {\"answer\": \"yes\"}). Resume için kullanılır."},
                "hitl": {"type": "boolean", "description": "HITL kontrolü yapılsın mı? (default: true). false ise direkt state geçişi yapar, PAUSE kontrolü atlanır.", "default": True},
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
                # AI feature params (NEW)
                "verbose": {"type": "boolean", "description": "Verbose output (include AI analysis text)", "default": False},
                "horizon": {"type": "integer", "description": "Forecast horizon in minutes (default: 60)"},
                "metric": {"type": "string", "description": "Single metric name to filter (predict/metrics)"},
                "from_state": {"type": "string", "description": "Source state for recommendation"},
                # Observability params (NEW)
                "since": {"type": "string", "description": "Audit query start time (ISO format)"},
                "until": {"type": "string", "description": "Audit query end time (ISO format)"},
                "level": {"type": "string", "description": "Alert level: info, warning, critical"},
                "message": {"type": "string", "description": "Alert message text"},
                "value": {"type": "number", "description": "Numeric value for metric/alert"},
                # Management params (NEW — Phase 2)
                "role": {"type": "string", "description": "Role for auth create: admin, user, readonly"},
                "key_id": {"type": "string", "description": "API key ID for auth_revoke"},
                "plugin_id": {"type": "string", "description": "Plugin ID for plugin_info"},
                "expires_in_days": {"type": "integer", "description": "API key expiry in days (auth_create)"},
                # Debug params (NEW — Phase 3)
                "command": {"type": "string", "description": "Debug command: timeline, event, state, why, cost, health, budget, summary (default)"},
            },
            "required": ["action"],
        },
    }

    ctx.register_tool(
        name="prodinamik",
        toolset="prodinamik",
        schema=tool_schema,
        handler=lambda args, **kw: _handle_tool(args, ctx),
        description="Prodinamik Engine: 45 actions — run pipelines, AI, observability, management, debug",
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

    ctx.register_command(
        name="/p-resume",
        handler=lambda raw, **kw: _handle_slash_resume(raw, ctx),
        description="Resume a paused run with answer. Usage: /p-resume <slug> <yes|no|answer>",
        args_hint="<slug> <answer>",
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
    from . import hermes_bridge
    from .hermes_bridge import handle_all

    action = args.get("action", "")

    # Special: force-reload engine (clear singleton cache + reload bridge)
    if action == "_reload_engine":
        try:
            import importlib
            # Step 1: Clear engine singleton on old module
            hermes_bridge._engine = None
            # Step 2: Reload engine sub-modules so config defaults are refreshed
            for mod_name in list(sys.modules.keys()):
                if mod_name.startswith("engine.") and mod_name != "engine":
                    sys.modules.pop(mod_name, None)
                if mod_name.startswith("profiles.") or mod_name == "profiles":
                    sys.modules.pop(mod_name, None)
            for key in ["engine.config", "engine.engine", "engine.runtime"]:
                sys.modules.pop(key, None)
            # Step 3: Clear profile modules too (HITL updates)
            for key in ["profiles.content", "profiles.software", "profiles.design",
                        "profiles.research", "profiles.haber", "profiles"]:
                sys.modules.pop(key, None)
            # Step 3: Reload bridge module so code changes take effect
            bridge_name = hermes_bridge.__name__
            sys.modules.pop(bridge_name, None)
            importlib.invalidate_caches()
            # Step 4: Re-import bridge + re-init engine with fresh config
            from . import hermes_bridge as hb
            eng = hb._get_engine()
            return json.dumps({
                "message": "Engine + bridge reloaded",
                "profiles": list(eng.health_snapshot.get("profiles", [])),
                "active_runs": eng.health_snapshot.get("active_runs", 0),
                "health_score": eng.health_snapshot.get("health_score", 0),
                "status": "ok",
            }, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Engine reload failed: {e}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)
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
        msg += f"   State: **{data.get('state', '?')}**\n"
        msg += f"   Profile: {data.get('profile', '?')}\n"
        msg += f"   Süre: {data.get('elapsed', 0)}s\n"
        if data.get("awaiting_input"):
            msg += f"   ⏸️ **Kullanıcı girdisi bekliyor!**\n"
            for i, q in enumerate(data.get("questions", []), 1):
                choices = ""
                if q.get('choices'):
                    choices = "\n       ".join(f"`{c}`" for c in q['choices'])
                    choices = f"\n       ├─ {choices}"
                msg += f"\n   **❓ Soru {i}:** {q['question']}"
                msg += f"\n   Tip: `{q['type']}`"
                if choices:
                    msg += f"\n   Seçenekler:{choices}"
            msg += f"\n\n   💡 `/p-resume {slug} <cevap>`"
        else:
            if avail := data.get("available_states"):
                msg += f"   Geçilebilir: {' → '.join(avail)}\n"
    else:
        msg = "🏭 **Prodinamik Engine**\n"
        msg += f"   Aktif run: {data.get('active_runs', 0)}\n"
        msg += f"   Sağlık: %{data.get('health_score', 0)*100:.0f}\n"
        msg += f"   Profiller: {', '.join(data.get('profiles', []))}\n"
    return msg


def _handle_slash_resume(raw_args: str, ctx: Any) -> str:
    """/p-resume <slug> <answer>"""
    parts = raw_args.strip().split(maxsplit=1)
    if len(parts) < 2:
        return ("ℹ️ **Kullanım:** `/p-resume <slug> <cevap>`\n"
                "   Örnek: `/p-resume hitl-test-1 yes`\n"
                "   Örnek: `/p-resume hitl-test-1 Blog`")
    slug, answer_text = parts[0], parts[1]

    # Normalize answer to dict
    answers = {"answer": answer_text}

    result = _handle_tool({"action": "resume", "slug": slug, "answers": answers}, ctx)
    data = json.loads(result)
    if "error" in data:
        return f"❌ Hata: {data['error']}"
    
    if data.get("status") == "transitioned":
        return (f"✅ **{slug}** devam ediyor!\n"
                f"   {data.get('from_state', '?')} → **{data.get('to_state', '?')}**")
    if data.get("status") == "awaiting_input":
        msg = f"⏸️ **{slug}** — yeni bir pause state: **{data.get('current_state', '?')}**\n"
        for q in data.get("questions", []):
            msg += f"\n❓ {q['question']}"
        return msg
    if data.get("status") == "answers_recorded":
        return f"📝 **{slug}** — cevabın kaydedildi. Sıradaki adımı sen belirle: `/p-next {slug}`"
    if data.get("chain_loop_guard"):
        return f"⚠️ **{slug}** — çok fazla HITL adımı, otomatik devam ediliyor."
    return f"✅ **{slug}** güncellendi"


# ═══════════════════════════════════════════════════════════════════
# Hook: Event → Telegram Push
# ═══════════════════════════════════════════════════════════════════

def _hook_post_tool(**kw):
    """Post-tool hook — engine event'lerini Telegram'a push'la + HITL timeout bildirimi."""
    ctx = kw.get("_ctx")
    tool_name = kw.get("tool_name", "")
    args = kw.get("args", {})
    result = kw.get("result", "")

    if tool_name != "prodinamik":
        return

    action = args.get("action", "")
    slug = args.get("slug", "")

    # HITL timeout: engine timeout watcher'dan gelen bildirim
    hook_type = kw.get("hook_type", "")
    if hook_type == "on_hitl_timeout":
        try:
            state = kw.get("state", "")
            elapsed = kw.get("elapsed", 0)
            policy = kw.get("policy", "proceed")
            reminder = kw.get("reminder", "")
            
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            
            msg = (
                f"⏰ **HITL Timeout**\n"
                f"   `{slug}` → **{state}**\n"
                f"   Bekleme: {hours}s {minutes}d\n"
                f"   Politika: `{policy}`\n"
            )
            if reminder:
                msg += f"   {reminder}\n"
            
            if policy == "hold":
                msg += f"\n   ⏸️ Hâlâ cevap bekliyor..."
            elif policy == "proceed":
                msg += f"\n   ➡️ Otomatik devam edildi"
            elif policy == "abort":
                msg += f"\n   🛑 İptal edildi"
            
            try:
                from run_agent import AIAgent
                agent = AIAgent()
                agent.send_message("telegram", msg)
            except Exception:
                pass
        except Exception:
            pass
        return

    if action not in ("transition", "approve", "reject", "run", "resume"):
        return

    try:
        data = json.loads(result) if isinstance(result, str) else result
        state = data.get("state", data.get("current_state", ""))
        
        # HITL: awaiting_input durumunda özel bildirim
        if data.get("awaiting_input") or data.get("_hitl"):
            questions = data.get("questions", [])
            q_text = "\n".join(
                f"❓ {q['question']}" 
                + (f" [`{'`,`'.join(q.get('choices',[]))}`]" if q.get('choices') else "")
                for q in questions
            )
            msg = (
                f"⏸️ **{slug}** → **{state}**\n"
                f"   Kullanıcı girdisi bekleniyor:\n"
                f"{q_text}\n\n"
                f"   💡 /p-resume {slug} <cevap>"
            )
        else:
            emoji = {
                "run": "🆕", "approve": "✅", "reject": "❌",
                "transition": "🔔", "resume": "▶️",
            }
            msg = f"{emoji.get(action, '🔔')} `{slug}` → **{state}**"

        try:
            from run_agent import AIAgent
            agent = AIAgent()
            agent.send_message("telegram", msg)
        except Exception:
            pass
    except Exception:
        pass
