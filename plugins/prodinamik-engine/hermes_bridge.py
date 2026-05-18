"""Prodinamik Engine — Hermes Tool Bridge

Hermes tool çağrılarını Prodinamik Engine API'sine bağlar.
Artık content profile action'larını da destekler.

Actions:
  Core:        run, list, status, approve, reject, next, transition, dashboard, budget
  Content:     setup, audit, decide_route, scan_slop, score, signal,
               search_runs, archive_run, buffer_setup, buffer_send, buffer_status,
               update_voice, analyze_patterns, get_learnings, reload_actions
"""

from typing import Any, Dict, Optional, List
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Lazy engine singleton
_engine = None


def _get_engine():
    """Lazy-init Prodinamik Engine instance."""
    global _engine
    if _engine is None:
        try:
            from engine.config import ProdinamikConfig
            from engine.runtime import AsyncEngine
            cfg = ProdinamikConfig.load()
            _engine = AsyncEngine(cfg)
            logger.info("Prodinamik Engine initialized")
        except Exception as e:
            logger.error(f"Engine init failed: {e}")
            raise
    return _engine


def _get_content_core():
    """Lazy-init ContentOSCore from the old plugin (backward compat during migration)."""
    try:
        import sys
        plugin_root = Path(__file__).parent.parent / "content-os"
        if plugin_root.exists():
            sys.path.insert(0, str(plugin_root.parent))
            from plugins.content_os.content_os_core import ContentOSCore  # type: ignore
            core = ContentOSCore(plugin_root)
            return core
    except Exception as e:
        logger.debug(f"ContentOSCore not available: {e}")
    return None


# ═══════════════════════════════════════════════════════════════════
# CORE ENGINE ACTIONS (existing, enhanced)
# ═══════════════════════════════════════════════════════════════════

def handle_run(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new workflow run."""
    profile = args.get("profile", "software")
    title = args.get("title", "")
    slug = args.get("slug")

    if not title:
        return {"error": "title is required"}

    engine = _get_engine()
    try:
        run = engine.create_run(profile, title, slug)
        return {
            "slug": run.meta.slug,
            "state": run.meta.state,
            "profile": run.meta.profile,
            "title": run.meta.title,
        }
    except ValueError as e:
        return {"error": str(e)}


def handle_list(args: Dict[str, Any]) -> Dict[str, Any]:
    """List all active runs."""
    engine = _get_engine()
    filter_profile = args.get("profile", "")
    try:
        runs = engine.list_runs(include_archived=args.get("include_archived", False))
        if filter_profile:
            runs = [r for r in runs if r.profile == filter_profile]
        return {
            "runs": [
                {
                    "slug": r.slug,
                    "profile": r.profile,
                    "state": r.state,
                    "title": r.title,
                    "status": r.status,
                }
                for r in runs
            ],
            "count": len(runs),
        }
    except Exception as e:
        return {"error": str(e)}


def handle_status(args: Dict[str, Any]) -> Dict[str, Any]:
    """Show run or engine status."""
    slug = args.get("slug", "")
    engine = _get_engine()

    if slug:
        run = engine.get_run(slug)
        if not run:
            return {"error": f"Run '{slug}' not found"}
        try:
            elapsed = engine.run_manager.get_state_elapsed(slug)
        except Exception:
            elapsed = 0

        available = []
        profile = engine._get_profile(run.meta.profile)
        if profile and profile.state_machine:
            next_states = profile.state_machine.get_next_states(run.meta.state)
            for s in next_states:
                can, reason = profile.state_machine.can_transition(
                    run.meta.state, s
                )
                available.append(s if can else f"{s} ({reason})")

        return {
            "slug": run.meta.slug,
            "state": run.meta.state,
            "profile": run.meta.profile,
            "title": run.meta.title,
            "status": run.meta.status,
            "elapsed": elapsed,
            "available_states": [s for s in available if not s.startswith("(")],
        }
    else:
        health = engine.health_snapshot
        return {
            "active_runs": health.get("active_runs", 0),
            "health_score": health.get("health_score", 0),
            "total_cost": health.get("total_cost", 0),
            "profiles": health.get("profiles", list(engine._profile_cache.keys())),
            "pending_approvals": 0,
        }


def handle_approve(args: Dict[str, Any]) -> Dict[str, Any]:
    """Approve a pending task."""
    slug = args.get("slug", "")
    user_id = args.get("user_id", "hermes")
    if not slug:
        return {"error": "slug is required"}
    engine = _get_engine()
    try:
        run = engine._do_transition(slug, "release")
        if hasattr(engine, 'approval_gate') and engine.approval_gate:
            import asyncio
            try:
                asyncio.run(engine.approval_gate.approve_task(slug, user_id))
            except Exception:
                pass
        return {"slug": slug, "state": run.meta.state, "approved": True}
    except ValueError as e:
        if hasattr(engine, 'approval_gate') and engine.approval_gate:
            import asyncio
            try:
                asyncio.run(engine.approval_gate.approve_task(slug, user_id))
                return {"slug": slug, "approved": True, "note": "approval_gate only"}
            except Exception:
                pass
        return {"error": str(e)}


def handle_reject(args: Dict[str, Any]) -> Dict[str, Any]:
    """Reject a pending task."""
    slug = args.get("slug", "")
    user_id = args.get("user_id", "hermes")
    if not slug:
        return {"error": "slug is required"}
    engine = _get_engine()
    if hasattr(engine, 'approval_gate') and engine.approval_gate:
        import asyncio
        try:
            asyncio.run(engine.approval_gate.reject_task(slug, user_id))
            return {"slug": slug, "rejected": True}
        except Exception as e:
            return {"error": str(e)}
    return {"error": "approval_gate not available"}


def handle_next(args: Dict[str, Any]) -> Dict[str, Any]:
    """Show next recommended step for a run."""
    slug = args.get("slug", "")
    if not slug:
        return {"error": "slug is required"}
    engine = _get_engine()
    run = engine.get_run(slug)
    if not run:
        return {"error": f"Run '{slug}' not found"}
    profile = engine._get_profile(run.meta.profile)
    if not profile or not profile.state_machine:
        return {"error": "Profile or state machine not available"}
    sm = profile.state_machine
    next_states = sm.get_next_states(run.meta.state)
    available = []
    for s in next_states:
        can, reason = sm.can_transition(run.meta.state, s)
        available.append({
            "state": s, "allowed": can,
            "condition": reason if not can else "",
        })
    first_allowed = next((a for a in available if a["allowed"]), None)
    return {
        "slug": slug,
        "current_state": run.meta.state,
        "next_state": first_allowed["state"] if first_allowed else None,
        "condition": first_allowed.get("condition", "") if first_allowed else "",
        "available_states": [a["state"] for a in available if a["allowed"]],
    }


def handle_transition(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a state transition."""
    slug = args.get("slug", "")
    target_state = args.get("target_state", "")
    if not slug or not target_state:
        return {"error": "slug and target_state are required"}
    engine = _get_engine()
    try:
        run = engine._do_transition(slug, target_state)
        return {"slug": slug, "state": run.meta.state, "from_state": run.meta.state, "transition": target_state}
    except ValueError as e:
        return {"error": str(e)}


def handle_dashboard(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get engine dashboard data."""
    engine = _get_engine()
    health = engine.health_snapshot
    runs = engine.list_runs(include_archived=False)
    return {
        "health_score": health.get("health_score", 0),
        "active_runs": health.get("active_runs", 0),
        "total_cost": health.get("total_cost", 0),
        "profiles": health.get("profiles", list(engine._profile_cache.keys())),
        "runs": [
            {"slug": r.slug, "profile": r.profile,
             "state": r.state, "title": r.title, "status": r.status}
            for r in runs
        ],
    }


def handle_budget(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get budget status."""
    engine = _get_engine()
    return {
        "total_cost": engine.cost_tracker.total_usd if hasattr(engine, 'cost_tracker') else 0,
        "limits": engine.budget.limits if hasattr(engine, 'budget') else {},
    }


# ═══════════════════════════════════════════════════════════════════
# CONTENT-SPECIFIC ACTIONS (bridge to old ContentOSCore)
# ═══════════════════════════════════════════════════════════════════

def _handle_content_setup(core, args):
    """Initialize content directory structure."""
    result = core.setup()
    return {"message": result}


def _handle_content_audit(core, args):
    """Audit content runs."""
    result = core.audit()
    return {"message": result}


def _handle_decide_route(core, args):
    """Idea Gate routing decision."""
    idea = args.get("idea", "")
    source = args.get("source_hint", "")
    if not idea:
        return {"error": "idea is required"}
    result = core.decide_route(idea, source)
    return {
        "route": result["route"],
        "rationale": result["rationale"],
        "source_type": result["source_type"],
    }


def _handle_scan_slop(core, args):
    """Scan text for slop patterns."""
    text = args.get("text", "")
    if not text:
        return {"error": "text is required"}
    result = core.scan_slop(text)
    return {
        "score": result["score"],
        "tier1_count": result["tier1_count"],
        "tier2_count": result["tier2_count"],
        "tier3_count": result["tier3_count"],
        "bonus_count": result["bonus_count"],
        "findings": result["all_findings"][:10],
        "pass": result.get("score", "REJECT") in ("PASS", "ACCEPT"),
    }


def _handle_score(core, args):
    """Rubric scoring for a run."""
    slug = args.get("slug", "")
    if not slug:
        return {"error": "slug is required"}
    # Score reads the draft and returns rubric
    draft_path = core.active_runs / slug / "draft-package.md"
    if not draft_path.exists():
        return {"error": f"Draft not found for {slug}"}
    return {"message": f"Rubric scoring requested for {slug}. Run /inspect {slug} for details."}


def _handle_signal(core, args):
    """Process signals from X or RSS."""
    source = args.get("source", "x")
    try:
        signals = core.process_signal(source)
        return {"signals": signals, "count": len(signals)}
    except Exception as e:
        return {"error": str(e), "signals": []}


def _handle_archive_run(core, args):
    """Archive a run."""
    slug = args.get("slug", "")
    if not slug:
        return {"error": "slug is required"}
    result = core.archive_run(slug)
    if isinstance(result, str):
        return {"message": result}
    return result


def _handle_buffer_setup(core, args):
    """Configure Buffer API."""
    api_key = args.get("api_key", "")
    if not api_key:
        return {"error": "api_key is required"}
    result = core.buffer_setup(api_key)
    return {"message": result}


def _handle_buffer_send(core, args):
    """Send to Buffer API."""
    slug = args.get("slug", "")
    if not slug:
        return {"error": "slug is required"}
    result = core.buffer_send(slug)
    return {"message": result}


def _handle_buffer_status(core, args):
    """Get Buffer API status."""
    result = core.buffer_status()
    return {"message": result}


def _handle_update_voice(core, args):
    """Update voice profile."""
    updates = args.get("updates", {})
    if not updates:
        return {"error": "updates object is required"}
    if hasattr(core, 'update_voice_profile'):
        result = core.update_voice_profile(updates)
    else:
        result = "Voice update not supported in this version"
    return {"message": result}


def _handle_analyze_patterns(core, args):
    """Analyze run patterns."""
    result = core.analyze_run_patterns()
    return result


def _handle_get_learnings(core, args):
    """Get cross-run learnings."""
    topic = args.get("topic", "")
    result = core.get_learnings_for_brief(topic)
    return {"learnings": result}


def _handle_search_runs(core, args):
    """Search through runs."""
    query = args.get("query", "")
    include_archived = args.get("include_archived", True)
    all_runs = core.get_all_runs(include_archived)
    result = [r for r in all_runs if query.lower() in r.get("slug", "").lower() or query.lower() in r.get("title", "").lower()]
    return {"runs": result, "count": len(result)}


def _handle_reload_actions(core, args):
    """Hot-reload action handlers."""
    try:
        import importlib
        import sys
        mod = sys.modules.get("content_os_core")
        if mod:
            importlib.reload(mod)
        return {"message": "Actions reloaded."}
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════
# Content action registry (defined AFTER all handlers)
# ═══════════════════════════════════════════════════════════════════

_RAW_CONTENT_ACTIONS = {
    "setup": _handle_content_setup,
    "audit": _handle_content_audit,
    "decide_route": _handle_decide_route,
    "scan_slop": _handle_scan_slop,
    "score": _handle_score,
    "signal": _handle_signal,
    "archive_run": _handle_archive_run,
    "buffer_setup": _handle_buffer_setup,
    "buffer_send": _handle_buffer_send,
    "buffer_status": _handle_buffer_status,
    "update_voice": _handle_update_voice,
    "analyze_patterns": _handle_analyze_patterns,
    "get_learnings": _handle_get_learnings,
    "search_runs": _handle_search_runs,
    "reload_actions": _handle_reload_actions,
}


def _with_core(func):
    """Decorator: get ContentOSCore and pass to handler, or return error."""
    def wrapper(args):
        try:
            plugin_root = Path(__file__).parent.parent / "content-os"
            if not plugin_root.exists():
                return {"error": f"content-os plugin not found at {plugin_root}"}
            import sys
            import importlib

            # Add plugins parent to sys.path so content_os package is importable
            plugins_dir = str(plugin_root.parent)
            if plugins_dir not in sys.path:
                sys.path.insert(0, plugins_dir)

            # Import via symlink: content_os -> content-os
            # This keeps __package__ correct so relative imports (from .buffer) work
            mod = importlib.import_module("content_os.content_os_core")
            ContentOSCore = mod.ContentOSCore

            core = ContentOSCore(plugin_root)
            return func(core, args)
        except Exception as e:
            import traceback
            logger.error(f"Content action failed: {e}\n{traceback.format_exc()}")
            return {"error": str(e)}
    return wrapper


def _get_content_actions() -> Dict[str, callable]:
    """Build content action handlers map (all wrapped with _with_core)."""
    return {name: _with_core(fn) for name, fn in _RAW_CONTENT_ACTIONS.items()}


# ═══════════════════════════════════════════════════════════════════
# HABER-KURATOR ACTIONS (bridge to old HaberKuratorCore)
# ═══════════════════════════════════════════════════════════════════

_RAW_HABER_ACTIONS: Dict[str, callable] = {}


def register_haber_actions():
    """Dynamically register haber actions from HaberKuratorCore."""
    global _RAW_HABER_ACTIONS
    if _RAW_HABER_ACTIONS:
        return

    try:
        plugin_root = Path(__file__).parent.parent / "haber-kurator"
        if not plugin_root.exists():
            logger.warning(f"Haber-kurator plugin not found at {plugin_root}")
            return

        import sys
        import importlib.util
        plugins_dir = str(plugin_root.parent)
        if plugins_dir not in sys.path:
            sys.path.insert(0, plugins_dir)

        # Import via symlink: haber_os -> haber-kurator
        mod = importlib.import_module("haber_os.haber_kurator_core")
        HaberKuratorCore = mod.HaberKuratorCore

        def _wrap_haber(fn):
            def wrapper(args):
                try:
                    core = HaberKuratorCore(plugin_root)
                    return fn(core, args)
                except Exception as e:
                    import traceback
                    logger.error(f"Haber action failed: {e}\n{traceback.format_exc()}")
                    return {"error": str(e)}
            return wrapper

        # Define all haber action handlers
        def _handle_fetch_news(core, args):
            country = args.get("country", "turkey")
            category = args.get("category", "news")
            result = core.fetch_all_news(category, country)
            # Result could be a list or dict
            if isinstance(result, dict):
                return result
            return {"items": result, "count": len(result) if isinstance(result, list) else 0}

        def _handle_verify_news(core, args):
            # Composite: fetch → cluster → verify
            country = args.get("country", "turkey")
            category = args.get("category", "news")
            raw = core.fetch_all_news(category, country)
            items = raw if isinstance(raw, list) else raw.get("items", [])
            clustered = core.cluster_stories(items)
            return {"message": f"Fetched and clustered {len(items)} news items for {country}.", "clusters": clustered}

        def _handle_publish_verified(core, args):
            country = args.get("country", "turkey")
            human_review = args.get("human_review", True)
            raw = core.fetch_all_news("news", country)
            items = raw if isinstance(raw, list) else raw.get("items", [])
            clustered = core.cluster_stories(items)
            if isinstance(clustered, list) and clustered:
                result = core.publish_verified_news(clustered[0], human_review)
                return {"message": f"Published cluster for {country}", "result": result}
            return {"message": f"No news clusters found for {country}"}

        def _handle_cross_verify_story(core, args):
            cluster_data = args.get("cluster_data", {})
            if not cluster_data:
                return {"error": "cluster_data is required"}
            return core.cross_verify_story(cluster_data)

        def _handle_search_news(core, args):
            query = args.get("search_query", "")
            language = args.get("language", "tr")
            country = args.get("country", "")
            max_results = args.get("max_results", 20)
            if not query:
                return {"error": "search_query is required"}
            return core.search_news(query, max_results, language, country)

        def _handle_auto_publish(core, args):
            country = args.get("country", "global")
            category = args.get("category", "news")
            raw = core.fetch_all_news(category, country)
            items = raw if isinstance(raw, list) else raw.get("items", [])
            clustered = core.cluster_stories(items)
            if isinstance(clustered, list) and clustered:
                for cluster in clustered[:3]:
                    core.publish_verified_news(cluster, human_review=False)
                return {"message": f"Auto-published {min(len(clustered), 3)} clusters for {country}"}
            return {"message": f"No news clusters found for {country}"}

        def _handle_hallucination_check(core, args):
            slug = args.get("slug", "")
            if not slug:
                return {"error": "slug is required"}
            return core.hallucination_check(slug)

        def _handle_issue_correction(core, args):
            slug = args.get("slug", "")
            error_desc = args.get("error_description", "")
            correct_info = args.get("correct_information", "")
            retract = args.get("retract", False)
            if not slug:
                return {"error": "slug is required"}
            return core.issue_correction(slug, error_desc, correct_info, retract)

        def _handle_check_correction(core, args):
            slug = args.get("slug", "")
            if not slug:
                return {"error": "slug is required"}
            return core.check_correction_needed(slug)

        def _handle_sources(core, args):
            category = args.get("category", "")
            if category:
                return core.get_sources_by_category(category)
            return core.get_all_sources()

        # Register all
        action_map = {
            "fetch_news": _handle_fetch_news,
            "verify_news": _handle_verify_news,
            "publish_verified": _handle_publish_verified,
            "cross_verify_story": _handle_cross_verify_story,
            "search_news": _handle_search_news,
            "auto_publish": _handle_auto_publish,
            "hallucination_check": _handle_hallucination_check,
            "issue_correction": _handle_issue_correction,
            "check_correction": _handle_check_correction,
            "sources": _handle_sources,
        }
        _RAW_HABER_ACTIONS.update({k: _wrap_haber(v) for k, v in action_map.items()})
        logger.info(f"Registered {len(action_map)} haber actions")

    except Exception as e:
        import traceback
        logger.warning(f"Haber actions registration failed: {e}\n{traceback.format_exc()}")


def _get_haber_actions() -> Dict[str, callable]:
    """Get haber action handlers (lazy-registered)."""
    register_haber_actions()
    return dict(_RAW_HABER_ACTIONS)


def handle_all(args: Dict[str, Any]) -> Dict[str, Any]:
    """Unified handler — dispatches to core or content actions."""
    action = args.get("action", "")

    # ── Legacy Content-OS aliases ──
    ALIAS_MAP = {
        "new_run": "run",
        "get_state": "status",
        "get_all_runs": "list",
        "update_state": "transition",
        "get_next_actions": "next",
    }
    if action in ALIAS_MAP:
        action = ALIAS_MAP[action]
        args["action"] = action

    # Core engine handlers
    core_handlers = {
        "run": handle_run,
        "list": handle_list,
        "status": handle_status,
        "approve": handle_approve,
        "reject": handle_reject,
        "next": handle_next,
        "transition": handle_transition,
        "dashboard": handle_dashboard,
        "budget": handle_budget,
    }

    if action in core_handlers:
        try:
            result = core_handlers[action](args)
            return result
        except Exception as e:
            logger.error(f"Core action '{action}' failed: {e}")
            return {"error": str(e)}

    # Content-specific handlers
    content_handlers = _get_content_actions()
    if action in content_handlers:
        handler = content_handlers[action]
        # Content handlers use the decorator internally
        result = handler(args)
        return result

    # Haber-specific handlers
    haber_handlers = _get_haber_actions()
    if action in haber_handlers:
        handler = haber_handlers[action]
        result = handler(args)
        return result

    return {"error": f"Unknown action: {action}"}


# ═══════════════════════════════════════════════════════════════════
# Aliases for backward compatibility (old import paths)
# ═══════════════════════════════════════════════════════════════════

handle_new_run = handle_run
handle_setup = _handle_content_setup
handle_scan_slop_action = _handle_scan_slop
