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
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Lazy engine singleton
_engine = None
_engine_loop = None
_engine_thread = None


def _get_engine():
    """Lazy-init Prodinamik Engine instance with background async loop.
    
    Engine'i bir background thread'de asyncio loop ile başlatır, böylece:
      - Timeout Watcher v2 (PAUSE timeout kontrolleri) canlı çalışır
      - Warm Agent Coordinator (periyodik task'lar) canlı çalışır
      - sync tool çağrıları (create_run, _do_transition, etc.) thread-safe çalışır
    """
    global _engine, _engine_loop, _engine_thread
    if _engine is None:
        try:
            import sys
            import asyncio
            import threading
            plugin_root = Path(__file__).parent
            if str(plugin_root) not in sys.path:
                sys.path.insert(0, str(plugin_root))

            from engine.config import ProdinamikConfig
            from engine.runtime import AsyncEngine

            cfg = ProdinamikConfig.load()
            # Point data_dir to plugin's .hermes/
            cfg.data_dir = str(plugin_root / ".hermes")
            _engine = AsyncEngine(cfg)
            
            # HITL timeout callback: Telegram bildirimi
            def _hitl_timeout_notify(**kw):
                """HITL timeout bildirimini Telegram'a push'la"""
                try:
                    slug = kw.get("slug", "")
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
            
            _engine.on_hitl_timeout(_hitl_timeout_notify)
            
            # ── Warm Agent task'larını HEmen kaydet (sync) ──
            # Background thread'de start() çağrılmadan önce bile
            # warm agent task'ları kullanılabilir olsun
            _engine._agent_coordinator.setup_default_tasks(_engine)
            
            # ── Background async loop ───────────────────────────
            # Engine'in timeout watcher + warm agent background task'ları
            # için asyncio loop'u background thread'de başlat
            _engine_loop = asyncio.new_event_loop()
            
            async def _start_engine():
                """Start engine and keep loop alive for background tasks"""
                await _engine.start()
                # Engine.start() creates background tasks (timeout-watcher,
                # health-checker) that keep the loop busy. We don't need
                # an infinite loop here — the background tasks keep the
                # event loop from being idle.
            
            def _run_loop():
                """Background thread: run event loop with engine's background tasks"""
                asyncio.set_event_loop(_engine_loop)
                try:
                    _engine_loop.run_until_complete(_start_engine())
                    logger.info("Prodinamik Engine background loop started")
                    _engine_loop.run_forever()
                except asyncio.CancelledError:
                    logger.info("Prodinamik Engine background loop cancelled")
                except Exception as e:
                    logger.error(f"Prodinamik Engine background loop failed: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            _engine_thread = threading.Thread(target=_run_loop, daemon=True, name="prodinamik-engine")
            _engine_thread.start()
            
            # Wait briefly for engine to initialize
            import time
            time.sleep(0.5)
            
            logger.info(f"Prodinamik Engine initialized with background async loop "
                        f"(data_dir={cfg.data_dir}), thread_alive={_engine_thread.is_alive()}")
        except Exception as e:
            logger.error(f"Engine init failed: {e}")
            # Clean up on failure
            if _engine_loop:
                _engine_loop.close()
            _engine = None
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
        sm = profile.state_machine if profile else None
        if sm:
            next_states = sm.get_next_states(run.meta.state)
            for s in next_states:
                can, reason = sm.can_transition(
                    run.meta.state, s
                )
                available.append(s if can else f"{s} ({reason})")

        # HITL kontrolü — pause state'te mi?
        awaiting_input = False
        questions = []
        if sm and sm.is_pause_state(run.meta.state):
            from engine.state_machine import RuntimeState
            rt = RuntimeState(current_state=run.meta.state)
            hitl_qs = sm.get_hitl_questions(run.meta.state, rt)
            if hitl_qs:
                awaiting_input = True
                questions = [
                    {
                        "question": q["question"],
                        "type": q["type"],
                        "choices": q.get("choices", []),
                    }
                    for q in hitl_qs
                ]

        return {
            "slug": run.meta.slug,
            "state": run.meta.state,
            "profile": run.meta.profile,
            "title": run.meta.title,
            "status": run.meta.status,
            "elapsed": elapsed,
            "awaiting_input": awaiting_input,
            "questions": questions,
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
    """Approve a pending task — profile-aware, condition override ile."""
    slug = args.get("slug", "")
    user_id = args.get("user_id", "hermes")
    if not slug:
        return {"error": "slug is required"}
    engine = _get_engine()

    # Run ve profil bilgilerini al
    run = engine.get_run(slug)
    if not run:
        return {"error": f"Run '{slug}' not found"}

    profile = engine._get_profile(run.meta.profile)
    if not profile or not profile.state_machine:
        return {"error": "Profile or state machine not available"}

    sm = profile.state_machine
    current_state = run.meta.state

    # Mevcut state'ten human_approved condition'ı olan transition'ı bul
    transitions = sm._transition_map.get(current_state, [])
    target_state = None
    for t in transitions:
        if t.condition and "human_approved" in t.condition:
            target_state = t.to_state
            break

    if not target_state:
        # human_approved condition'ı yoksa fallback: "release" (software profile)
        target_state = "release"

    try:
        # runtime_overrides ile human_approved=True geç → condition engine bypass
        run = engine._do_transition(slug, target_state,
                                    runtime_overrides={"human_approved": True})
        if hasattr(engine, 'approval_gate') and engine.approval_gate:
            import asyncio
            try:
                asyncio.run(engine.approval_gate.approve_task(slug, user_id))
            except Exception:
                pass
        return {
            "slug": slug,
            "state": run.meta.state,
            "from_state": current_state,
            "transition": target_state,
            "approved": True,
        }
    except ValueError as e:
        if hasattr(engine, 'approval_gate') and engine.approval_gate:
            import asyncio
            try:
                asyncio.run(engine.approval_gate.approve_task(slug, user_id))
                return {"slug": slug, "approved": True, "note": "approval_gate only", "error": str(e)}
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
    """Execute a state transition with HITL support.
    
    Normal transition yapar. Yeni state bir PAUSE/ask_user state'i ise
    awaiting_input=True + questions döndürür.
    
    Agent bu response'u görünce OTOMATİK clarify kullanmalıdır.
    
    NEW: runtime_overrides parametresi ile condition engine override edilebilir.
    Örn: runtime_overrides={"changes_requested": True} ile rejection loop tetiklenir.
    
    NEW: HITL rejection mantığı — resume sırasında kullanıcı "no"/"hayır"/"red"
    cevabı verirse otomatik olarak changes_requested=True ile rejection rotasına
    yönlendirilir.
    """
    slug = args.get("slug", "")
    target_state = args.get("target_state", "")
    if not slug or not target_state:
        return {"error": "slug and target_state are required"}
    
    # runtime_overrides: condition engine'i bypass etmek için
    # Kullanıcı tarafından gönderilebilir (ör: {"changes_requested": True})
    runtime_overrides = args.get("runtime_overrides", None)
    if runtime_overrides is not None and not isinstance(runtime_overrides, dict):
        try:
            import json
            runtime_overrides = json.loads(runtime_overrides)
        except (json.JSONDecodeError, TypeError):
            runtime_overrides = None
    
    engine = _get_engine()
    try:
        # Force profile reload if requested (for runtime profile changes)
        if args.get("force", False):
            run = engine.get_run(slug)
            if run and run.meta.profile in engine._profile_cache:
                del engine._profile_cache[run.meta.profile]

        # Capture old state before transition
        old_run = engine.get_run(slug)
        old_state = old_run.meta.state if old_run else "unknown"
        
        # Use transition_with_hitl for HITL-aware transitions
        hitl_check = args.get("hitl", True)  # Default: check HITL
        
        if hitl_check:
            result = engine.transition_with_hitl(slug, target_state)
            if not result.get("success"):
                # If transition_with_hitl fails, try _do_transition with overrides
                kwargs = {}
                if runtime_overrides:
                    kwargs["runtime_overrides"] = runtime_overrides
                run = engine._do_transition(slug, target_state, **kwargs)
                base = {"slug": slug, "state": run.meta.state, "from_state": old_state, "transition": target_state}
                if runtime_overrides:
                    base["runtime_overrides"] = runtime_overrides
                # Check if new state is a PAUSE state
                profile = engine._get_profile(run.meta.profile)
                sm = profile.state_machine if profile else None
                if sm and sm.is_pause_state(run.meta.state):
                    from engine.state_machine import RuntimeState
                    rt = RuntimeState(current_state=run.meta.state)
                    questions = sm.get_hitl_questions(run.meta.state, rt)
                    if questions:
                        base["awaiting_input"] = True
                        base["questions"] = [
                            {"question": q["question"], "type": q["type"],
                             "choices": q.get("choices", [])}
                            for q in questions
                        ]
                        base["_hitl"] = True
                        base["_instruction"] = "Kullanıcıya clarify ile sor, cevabı resume(action='resume', slug=..., answers={'answer': ...}) ile ilet"
                return base
            
            if result.get("awaiting_input"):
                return {
                    "slug": slug,
                    "state": result["current_state"],
                    "from_state": old_state,
                    "transition": target_state,
                    "awaiting_input": True,
                    "questions": result.get("questions", []),
                    "timeout": result.get("timeout", 300),
                    "_hitl": True,
                    "_instruction": "Kullanıcıya clarify ile sor, cevabı resume(action='resume', slug=..., answers={'answer': ...}) ile ilet",
                }
            
            # Normal transition - no HITL
            return {"slug": slug, "state": result["current_state"], "from_state": old_state, "transition": target_state}
        else:
            # Legacy mode: no HITL checking
            kwargs = {}
            if runtime_overrides:
                kwargs["runtime_overrides"] = runtime_overrides
            run = engine._do_transition(slug, target_state, **kwargs)
            result = {"slug": slug, "state": run.meta.state, "from_state": old_state, "transition": target_state}
            if runtime_overrides:
                result["runtime_overrides"] = runtime_overrides
            return result
            
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def handle_resume(args: Dict[str, Any]) -> Dict[str, Any]:
    """Resume a paused run with user answers (HITL).

    HITL: Kullanıcı cevaplarını engine'e iletir.
    Engine resume_transitions mapping'ine bakar ve uygun state'e geçer.

    NEW (HITL Rejection Logic):
    Kullanıcı cevabı "no", "hayır", "red" (veya türevleri) ise,
    otomatik olarak runtime_overrides={"changes_requested": True} ile
    engine'e iletilir. Böylece draft_review → drafting gibi rejection
    rotaları çalışır.

    Required:
      - slug: Run slug
      - answers: dict of user answers (e.g. {"answer": "yes"})
    """
    slug = args.get("slug", "")
    answers = args.get("answers", {})
    if not slug:
        return {"error": "slug is required"}
    if not answers:
        return {"error": "answers is required"}

    engine = _get_engine()
    try:
        # ── HITL Rejection Logic ──
        # Detect rejection answers and auto-set changes_requested
        answer_value = ""
        if isinstance(answers, dict):
            answer_value = str(list(answers.values())[0]).lower().strip() if answers else ""
        elif isinstance(answers, str):
            answer_value = answers.lower().strip()
        
        REJECTION_PATTERNS = ("no", "hayır", "hayir", "red", "yok", "iptal",
                              "düzelt", "duzelt", "revise", "changes",
                              "olmaz", "degistir", "değiştir")
        
        is_rejection = any(p in answer_value for p in REJECTION_PATTERNS)
        
        if is_rejection:
            # Try: engine.resume_run already has changes_requested override built in
            # If it transitions successfully, return the result directly
            result = engine.resume_run(slug, answers)
            
            # Case 1: resume_run successfully transitioned (it has built-in overrides)
            if result.get("status") == "transitioned":
                result["rejection_auto_resolved"] = True
                result["message"] = (
                    f"Red cevabı algılandı, "
                    f"{result.get('from_state', '?')} → {result.get('to_state', '?')} "
                    f"(changes_requested auto-resolved)"
                )
                return result
            
            # Case 2: resume_run recorded answer but couldn't transition → manual override
            if result.get("status") == "answers_recorded":
                run = engine.get_run(slug)
                if run:
                    profile = engine._get_profile(run.meta.profile)
                    sm = profile.state_machine if profile else None
                    if sm:
                        current_state = run.meta.state
                        for t in sm._transition_map.get(current_state, []):
                            if t.condition and "changes_requested" in t.condition:
                                next_state = t.to_state
                                run = engine._do_transition(
                                    slug, next_state,
                                    runtime_overrides={"changes_requested": True}
                                )
                                return {
                                    "status": "transitioned",
                                    "run_slug": slug,
                                    "from_state": current_state,
                                    "to_state": next_state,
                                    "rejection_auto_resolved": True,
                                    "message": f"Red cevabı algılandı, {current_state} → {next_state} (changes_requested=True)",
                                }
        
        result = engine.resume_run(slug, answers)
        return result
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
    """Hot-reload action handlers + profile cache."""
    try:
        import importlib
        import sys

        # Reload content_os_core (legacy)
        mod = sys.modules.get("content_os_core")
        if mod:
            importlib.reload(mod)

        # Reload profile modules + clear engine cache
        engine = _get_engine()
        if engine:
            # Clear profile cache so next _get_profile re-loads
            engine._profile_cache.clear()
            # Remove cached profile modules so they re-import fresh
            for mod_name in list(sys.modules.keys()):
                if mod_name.startswith("profiles.") or mod_name == "profiles":
                    sys.modules.pop(mod_name, None)
            # Re-discover profiles with fresh imports
            from engine.runtime import _discover_profiles
            _discover_profiles()

        return {"message": "Actions + profiles reloaded."}
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
            import sys
            import importlib
            plugins_dir = str(Path(__file__).parent.parent)
            if plugins_dir not in sys.path:
                sys.path.insert(0, plugins_dir)

            # Try archive first (clean migration path)
            try:
                mod = importlib.import_module("plugins.archive.content_os.content_os_core")
                ContentOSCore = mod.ContentOSCore
            except (ImportError, AttributeError):
                # Fallback: live plugin dir (pre-cleanup compat)
                try:
                    mod = importlib.import_module("content_os.content_os_core")
                    ContentOSCore = mod.ContentOSCore
                except (ImportError, AttributeError):
                    return {"error": "ContentOSCore not available (migrated to Prodinamik Engine). Use 'prodinamik' tool directly or check plugins/archive/content-os/"}

            plugin_root = Path(__file__).parent.parent / "content-os"
            if not plugin_root.exists() or not (plugin_root / "strategy").exists():
                plugin_root = Path(__file__).parent.parent / "archive" / "content-os"
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
        import sys
        import importlib
        import importlib.util
        from pathlib import Path as _Path
        plugins_dir = str(Path(__file__).parent.parent)
        if plugins_dir not in sys.path:
            sys.path.insert(0, plugins_dir)

        # Try archive first (clean migration path), fallback to live dir
        HaberKuratorCore = None
        for candidate in [
            Path(__file__).parent.parent / "archive" / "haber-kurator" / "haber_kurator_core.py",
            Path(__file__).parent.parent / "haber-kurator" / "haber_kurator_core.py",
        ]:
            if candidate.exists():
                try:
                    spec = importlib.util.spec_from_file_location("haber_kurator_core", str(candidate))
                    if spec:
                        mod = importlib.util.module_from_spec(spec)
                        mod.__package__ = ""
                        sys.modules["haber_kurator_core"] = mod
                        spec.loader.exec_module(mod)
                        HaberKuratorCore = getattr(mod, "HaberKuratorCore", None)
                        if HaberKuratorCore:
                            break
                except Exception:
                    continue

        if not HaberKuratorCore:
            logger.warning("HaberKuratorCore not available (migrated to Prodinamik Engine)")
            return

        plugin_root = plugin_root = Path(__file__).parent.parent / "haber-kurator"
        if not plugin_root.exists() or not (plugin_root / "strategy").exists():
            plugin_root = Path(__file__).parent.parent / "archive" / "haber-kurator"

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

    # ── Special: force-reload engine (hot-reload config changes) ──
    if action == "_reload_engine":
        try:
            import sys as _sys
            import importlib

            mod_name = __name__  # "hermes_bridge"

            # Engine modüllerini temizle
            for m in list(_sys.modules.keys()):
                if m.startswith("engine.") and m != "engine":
                    _sys.modules.pop(m, None)
                if m.startswith("profiles.") or m == "profiles":
                    _sys.modules.pop(m, None)
            for key in ["engine.config", "engine.engine", "engine.runtime"]:
                _sys.modules.pop(key, None)

            # Kendi modülümüzü sys.modules'ten çıkarıp yeniden import et
            _sys.modules.pop(mod_name, None)
            _hb = importlib.import_module(mod_name)

            # Yeni modülün engine'ini başlat
            eng = _hb._get_engine()
            return {
                "message": "Engine + bridge reloaded",
                "profiles": list(eng.health_snapshot.get("profiles", [])),
                "active_runs": eng.health_snapshot.get("active_runs", 0),
                "health_score": eng.health_snapshot.get("health_score", 0),
            }
        except Exception as e:
            import traceback
            return {"error": f"Engine reload failed: {e}", "traceback": traceback.format_exc()}

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
        "resume": handle_resume,
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

    # ── AI feature: drift detection ──
    if action == "ai_detect":
        return _handle_ai_detect(args)

    # ── AI feature: degradation forecast ──
    if action == "ai_predict":
        return _handle_ai_predict(args)

    # ── AI feature: run recommendation ──
    if action == "ai_recommend":
        return _handle_ai_recommend(args)

    # ── AI feature: AI status overview ──
    if action == "ai_status":
        return _handle_ai_status(args)

    # ── C2: Skill emergence (AI Grid) ──
    if action == "generate_skills":
        return _handle_generate_skills(args)
    if action == "drift_emergence":
        return _handle_drift_emergence(args)
    
    # ── C3: Warm Agent ──
    if action == "agent_status":
        return _handle_agent_status(args)
    if action == "agent_queue":
        return _handle_agent_queue(args)

    # ── Audit: query audit log ──
    if action == "audit_query":
        return _handle_audit_query(args)

    # ── Metrics: engine metrics export ──
    if action == "metrics":
        return _handle_metrics(args)

    # ── Alert: send alert to configured channels ──
    if action == "alert_send":
        return _handle_alert_send(args)

    # ── Auth: API key management ──
    if action == "auth_create":
        return _handle_auth_create(args)
    if action == "auth_list":
        return _handle_auth_list(args)
    if action == "auth_revoke":
        return _handle_auth_revoke(args)

    # ── Raft: cluster status ──
    if action == "raft_status":
        return _handle_raft_status(args)

    # ── Plugin: engine plugin management ──
    if action == "plugin_list":
        return _handle_plugin_list(args)
    if action == "plugin_info":
        return _handle_plugin_info(args)

    # ── Debug: run timeline/debug view ──
    if action == "debug":
        return _handle_debug(args)

    # ── Config: engine configuration ──
    if action == "config":
        return _handle_config(args)

    return {"error": f"Unknown action: {action}"}


# ═══════════════════════════════════════════════════════════════════
# AI FEATURE HANDLERS
# ═══════════════════════════════════════════════════════════════════


def _get_ai_detector(engine):
    """Lazy-init AIDriftDetector from engine."""
    try:
        from engine.aidetect import AIDriftDetector, DriftType, DriftSeverity
        if not hasattr(engine, '_ai_detector') or engine._ai_detector is None:
            engine._ai_detector = AIDriftDetector()
            # Seed with engine's run data for analysis
            for run in engine.list_runs():
                engine._ai_detector.record_drift(
                    drift_id=f"seed-{run.slug}",
                    drift_type=DriftType.STATE_TRANSITION,
                    severity=DriftSeverity.LOW,
                    run_id=run.slug,
                    state=run.state,
                    description=f"Run {run.slug} in state {run.state}",
                )
        return engine._ai_detector
    except Exception as e:
        logger.debug(f"AIDriftDetector not available: {e}")
        return None


def _get_forecaster(engine):
    """Lazy-init AIDegradationForecaster from engine."""
    try:
        from engine.predict import AIDegradationForecaster
        if not hasattr(engine, '_forecaster') or engine._forecaster is None:
            engine._forecaster = AIDegradationForecaster()
        return engine._forecaster
    except Exception as e:
        logger.debug(f"AIDegradationForecaster not available: {e}")
        return None


def _get_recommender(engine):
    """Lazy-init AIRecommender from engine."""
    try:
        from engine.recommend import AIRecommender
        if not hasattr(engine, '_recommender') or engine._recommender is None:
            engine._recommender = AIRecommender()
        return engine._recommender
    except Exception as e:
        logger.debug(f"AIRecommender not available: {e}")
        return None


def _handle_ai_detect(args: Dict[str, Any]) -> Dict[str, Any]:
    """Detect drift patterns and emergence candidates."""
    engine = _get_engine()
    detector = _get_ai_detector(engine)
    if not detector:
        return {"error": "AI drift detector not available", "health_score": 100, "total_events": 0}

    json_output = args.get("format", "") == "json"
    report = detector.generate_report()

    # Remove LLM analysis for compact output unless requested
    if not args.get("verbose", False):
        report.pop("ai_analysis", None)

    report["status"] = "ok"
    return report


def _handle_ai_predict(args: Dict[str, Any]) -> Dict[str, Any]:
    """Predict degradation across engine metrics."""
    engine = _get_engine()
    forecaster = _get_forecaster(engine)
    if not forecaster:
        return {"error": "Degradation forecaster not available"}

    horizon = args.get("horizon", 60)
    metric = args.get("metric", "")

    if metric:
        result = forecaster.predict(metric, horizon)
        if not result:
            return {"error": f"Metric '{metric}' not tracked"}
        return {"predictions": {metric: result.to_dict()}, "metric": metric}
    else:
        predictions = forecaster.predict_all(horizon)
        report = forecaster.generate_report(horizon)
        report["status"] = "ok"
        return report


def _handle_ai_recommend(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get AI-driven run recommendations."""
    engine = _get_engine()
    recommender = _get_recommender(engine)
    if not recommender:
        return {"error": "AI recommender not available"}

    from_state = args.get("from_state", "")
    profile = args.get("profile", "")
    slug = args.get("slug", "")

    if slug:
        # Get recommendation for a specific run
        run = engine.get_run(slug)
        if not run:
            return {"error": f"Run '{slug}' not found"}
        rec = recommender.get_recommendation(slug, run.meta.state, run.meta.profile)
        if not rec:
            return {"slug": slug, "recommendation": None, "note": "Insufficient data for recommendation"}
        return {
            "slug": slug,
            "current_state": rec.current_state,
            "best_next_state": rec.best_next_state,
            "confidence": round(rec.confidence, 3),
            "estimated_duration": rec.estimated_duration,
            "warnings": rec.warnings,
            "reasoning": rec.reasoning,
        }
    elif from_state:
        # Get transition stats for a state
        stats = recommender.get_transition_stats(from_state, profile)
        return {
            "from_state": from_state,
            "profile": profile or "all",
            "transitions": {k: v.to_dict() for k, v in stats.items()},
        }
    else:
        # Overview report
        report = recommender.generate_report()
        report["status"] = "ok"
        return report


def _handle_ai_status(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get all AI module metrics at a glance."""
    engine = _get_engine()

    detector = _get_ai_detector(engine)
    forecaster = _get_forecaster(engine)
    recommender = _get_recommender(engine)

    return {
        "drift_detector": {
            "available": detector is not None,
            "metrics": detector.metrics if detector else {},
        },
        "degradation_forecaster": {
            "available": forecaster is not None,
            "metrics": forecaster.metrics if forecaster else {},
        },
        "run_recommender": {
            "available": recommender is not None,
            "metrics": recommender.metrics if recommender else {},
        },
        "engine": {
            "profiles": list(engine._profile_cache.keys()),
            "active_runs": engine.health_snapshot.get("active_runs", 0),
            "health_score": engine.health_snapshot.get("health_score", 0),
        },
        "status": "ok",
    }


# ═══════════════════════════════════════════════════════════════════
# C2: SKILL EMERGENCE — AI Grid Action Handlers
# ═══════════════════════════════════════════════════════════════════


def _handle_generate_skills(args: Dict[str, Any]) -> Dict[str, Any]:
    """Trigger emergence detection + skill generation (C2).
    
    Scans recorded drift events, finds emergence candidates (3+ same type),
    generates SKILL.md files, and saves them to disk.
    """
    engine = _get_engine()
    try:
        results = engine.check_emergence()
        return {
            "skills_generated": len(results),
            "skills": results,
            "status": "ok",
        }
    except Exception as e:
        logger.error(f"generate_skills failed: {e}")
        return {"error": str(e)}


def _handle_drift_emergence(args: Dict[str, Any]) -> Dict[str, Any]:
    """Show drift data + emergence candidates.
    
    Shows all recorded drift events and emergence candidates
    without generating skills.
    """
    engine = _get_engine()
    try:
        # Get drift events
        drift_events = engine._drift_detector.collector._events
        events_by_type = engine._drift_detector.collector.count_by_type()
        
        # Find emergence candidates
        candidates = engine._drift_detector.find_emergence_candidates(min_occurrences=3)
        
        # Anomaly scan
        anomalies = engine._drift_detector.scan_anomalies()
        
        return {
            "total_drift_events": len(drift_events),
            "events_by_type": events_by_type,
            "emergence_candidates": [c.to_dict() for c in candidates],
            "anomalous_runs": anomalies.get("anomalous_runs", []),
            "anomalous_types": anomalies.get("anomalous_types", []),
            "status": "ok",
        }
    except Exception as e:
        logger.error(f"drift_emergence failed: {e}")
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════
# C3: WARM AGENT — Background Coordinator Handlers
# ═══════════════════════════════════════════════════════════════════


def _handle_agent_status(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get Warm Agent Coordinator status and metrics."""
    engine = _get_engine()
    try:
        return engine.agent_status()
    except Exception as e:
        logger.error(f"agent_status failed: {e}")
        return {"error": str(e)}


def _handle_agent_queue(args: Dict[str, Any]) -> Dict[str, Any]:
    """List all background agent tasks."""
    engine = _get_engine()
    try:
        return engine.agent_queue()
    except Exception as e:
        logger.error(f"agent_queue failed: {e}")
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════
# AUDIT LOG HANDLER
# ═══════════════════════════════════════════════════════════════════


def _handle_audit_query(args: Dict[str, Any]) -> Dict[str, Any]:
    """Query engine audit log."""
    engine = _get_engine()
    try:
        from engine.audit import AuditLog
        audit_path = Path(engine.config.data_dir) / "audit"
        audit_path.mkdir(parents=True, exist_ok=True)
        audit = AuditLog(str(audit_path))
    except Exception as e:
        return {"error": f"Audit log init failed: {e}"}

    since = args.get("since", "")
    until = args.get("until", "")
    event_type = args.get("type", "")
    limit = args.get("limit", 50)

    try:
        kwargs = {"since": since, "until": until, "limit": limit}
        if event_type:
            kwargs["event_type"] = event_type
        entries = list(audit.query(**kwargs))
        return {
            "count": len(entries),
            "entries": [e.to_dict() for e in entries],
            "stats": audit.stats(),
        }
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════
# METRICS EXPORT HANDLER
# ═══════════════════════════════════════════════════════════════════


def _handle_metrics(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get engine metrics in structured or Prometheus format."""
    engine = _get_engine()

    prometheus = args.get("format", "") == "prometheus"
    health = engine.health_snapshot

    metrics_data = {
        "engine": {
            "health_score": health.get("health_score", 0),
            "active_runs": health.get("active_runs", 0),
            "total_cost": health.get("total_cost", 0),
            "profile_count": len(health.get("profiles", list(engine._profile_cache.keys()))),
        },
        "run_counts": {
            slug: run.state for slug, run in engine._run_cache.items()
        } if hasattr(engine, '_run_cache') else {},
        "degradation": health.get("degradation_level", "full"),
    }

    if prometheus:
        lines = [
            f'# HELP prodinamik_health_score Engine health score (0-1)',
            f'# TYPE prodinamik_health_score gauge',
            f'prodinamik_health_score {metrics_data["engine"]["health_score"]}',
            f'# HELP prodinamik_active_runs Number of active runs',
            f'# TYPE prodinamik_active_runs gauge',
            f'prodinamik_active_runs {metrics_data["engine"]["active_runs"]}',
            f'# HELP prodinamik_total_cost Total engine cost in USD',
            f'# TYPE prodinamik_total_cost gauge',
            f'prodinamik_total_cost {metrics_data["engine"]["total_cost"]}',
        ]
        metrics_data["prometheus"] = "\n".join(lines)

    metrics_data["status"] = "ok"
    return metrics_data


# ═══════════════════════════════════════════════════════════════════
# ALERT HANDLER
# ═══════════════════════════════════════════════════════════════════


def _handle_alert_send(args: Dict[str, Any]) -> Dict[str, Any]:
    """Send an alert to configured channels."""
    level = args.get("level", "info")
    title = args.get("title", "")
    message = args.get("message", "")
    metric_name = args.get("metric", "")
    metric_value = args.get("value", 0)

    if not title:
        return {"error": "title is required"}

    if level not in ("info", "warning", "critical"):
        return {"error": f"Invalid level: {level}. Use: info, warning, critical"}

    try:
        from engine.alert import AlertManager, alert_config_from_env
        mgr = alert_config_from_env()

        metrics = {}
        if metric_name:
            metrics[metric_name] = metric_value

        alert = mgr.send_alert(level, title, message, metrics)
        return {
            "alert_id": alert.id,
            "level": alert.level,
            "title": alert.title,
            "channels": mgr.enabled_channels,
            "configured": mgr.is_configured,
            "status": "sent" if mgr.is_configured else "config_only",
            "note": "No channels configured" if not mgr.is_configured else "",
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}


# ═══════════════════════════════════════════════════════════════════
# AUTH HANDLERS (Phase 2)
# ═══════════════════════════════════════════════════════════════════


def _get_auth_manager(engine) -> object:
    """Lazy-init AuthManager from engine config path."""
    try:
        from engine.auth import AuthManager
        auth_path = Path(engine.config.data_dir) / "auth"
        auth_path.mkdir(parents=True, exist_ok=True)
        return AuthManager(str(auth_path))
    except Exception as e:
        logger.debug(f"AuthManager init failed: {e}")
        return None


def _handle_auth_create(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new API key."""
    engine = _get_engine()
    mgr = _get_auth_manager(engine)
    if not mgr:
        return {"error": "AuthManager not available"}

    name = args.get("name", "")
    role = args.get("role", "user")
    expires_in_days = args.get("expires_in_days", None)

    if not name:
        return {"error": "name is required"}

    if role not in ("admin", "user", "readonly"):
        return {"error": "Invalid role. Use: admin, user, readonly"}

    try:
        key_id, raw_key = mgr.create_key(name, role, expires_in_days)
        return {
            "key_id": key_id,
            "raw_key": raw_key,
            "name": name,
            "role": role,
            "note": "Save the raw_key — it is shown only once!",
            "status": "ok",
        }
    except Exception as e:
        return {"error": str(e)}


def _handle_auth_list(args: Dict[str, Any]) -> Dict[str, Any]:
    """List all API keys (without secrets)."""
    engine = _get_engine()
    mgr = _get_auth_manager(engine)
    if not mgr:
        return {"error": "AuthManager not available"}

    try:
        keys = mgr.list_keys()
        return {
            "keys": keys,
            "count": len(keys),
            "status": "ok",
        }
    except Exception as e:
        return {"error": str(e)}


def _handle_auth_revoke(args: Dict[str, Any]) -> Dict[str, Any]:
    """Revoke an API key."""
    engine = _get_engine()
    mgr = _get_auth_manager(engine)
    if not mgr:
        return {"error": "AuthManager not available"}

    key_id = args.get("key_id", "")
    if not key_id:
        return {"error": "key_id is required"}

    try:
        result = mgr.revoke_key(key_id)
        return {
            "key_id": key_id,
            "revoked": result,
            "status": "ok" if result else "not_found",
        }
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════
# RAFT HANDLER (Phase 2)
# ═══════════════════════════════════════════════════════════════════


def _handle_raft_status(args: Dict[str, Any]) -> Dict[str, Any]:
    """Show Raft cluster status."""
    engine = _get_engine()
    try:
        from engine.raft_consensus import HybridConsensusNode
        from engine.raft_cluster import RaftCluster
    except ImportError:
        return {"error": "Raft modules not available"}

    # Check if engine has a Raft node configured
    raft_node = getattr(engine, 'raft_node', None)
    if raft_node is None:
        return {
            "configured": False,
            "message": "No Raft node configured. Engine running in standalone mode.",
            "status": "standalone",
        }

    try:
        cluster = RaftCluster(raft_node)
        report = cluster.health_report()
        return {
            "configured": True,
            "cluster_size": report.get("cluster_size", 1),
            "local_role": report.get("local_role", "unknown"),
            "leader": report.get("leader", "standalone"),
            "healthy_nodes": report.get("healthy_nodes", 0),
            "status": "ok",
            "raw_report": report,
        }
    except Exception as e:
        return {"error": str(e), "configured": True}


# ═══════════════════════════════════════════════════════════════════
# PLUGIN HANDLERS (Phase 2)
# ═══════════════════════════════════════════════════════════════════


def _get_plugin_registry(engine) -> object:
    """Lazy-init PluginRegistry from engine."""
    try:
        from engine.plugin_registry import PluginRegistry
        return PluginRegistry(engine)
    except Exception as e:
        logger.debug(f"PluginRegistry init failed: {e}")
        return None


def _handle_plugin_list(args: Dict[str, Any]) -> Dict[str, Any]:
    """List all registered engine plugins."""
    engine = _get_engine()
    reg = _get_plugin_registry(engine)
    if not reg:
        return {"error": "PluginRegistry not available"}

    try:
        plugins = reg.list_plugins()
        enabled = reg.get_enabled()
        return {
            "plugins": [
                {
                    "id": p.id,
                    "name": p.manifest.name if hasattr(p, 'manifest') else p.id,
                    "version": p.manifest.version if hasattr(p, 'manifest') else "?",
                    "type": p.plugin_type.value if hasattr(p, 'plugin_type') else "?",
                    "enabled": p.id in enabled,
                }
                for p in plugins
            ],
            "total": len(plugins),
            "enabled_count": len(enabled),
            "status": "ok",
        }
    except Exception as e:
        return {"error": str(e)}


def _handle_plugin_info(args: Dict[str, Any]) -> Dict[str, Any]:
    """Show details of a specific plugin."""
    engine = _get_engine()
    reg = _get_plugin_registry(engine)
    if not reg:
        return {"error": "PluginRegistry not available"}

    plugin_id = args.get("plugin_id", "")
    if not plugin_id:
        return {"error": "plugin_id is required"}

    try:
        plugin = reg.get(plugin_id)
        if not plugin:
            return {"error": f"Plugin '{plugin_id}' not found"}

        info = {"id": plugin.id, "type": "unknown", "enabled": False}
        if hasattr(plugin, 'manifest'):
            m = plugin.manifest
            info.update({
                "name": m.name, "version": m.version,
                "description": m.description, "author": m.author,
            })
        if hasattr(plugin, 'plugin_type'):
            info["type"] = plugin.plugin_type.value
        if hasattr(plugin, 'state'):
            info["state"] = plugin.state.value if hasattr(plugin.state, 'value') else str(plugin.state)
        if hasattr(plugin, 'tools'):
            info["tools"] = [t.name for t in plugin.tools] if plugin.tools else []
        info["enabled"] = plugin.id in reg.get_enabled()
        info["status"] = "ok"
        return info
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════
# DEBUG + CONFIG HANDLERS (Phase 3)
# ═══════════════════════════════════════════════════════════════════


def _get_debug_cli(engine: Any) -> object:
    """Create DebugCLI from engine components."""
    try:
        from engine.debug_cli import DebugCLI
        return DebugCLI(
            run_manager=getattr(engine, 'run_manager', None),
            event_store=getattr(engine, 'event_store', None),
            cost_tracker=getattr(engine, 'cost_tracker', None),
            degradation_manager=getattr(engine, 'degradation_manager', None),
            budget_enforcer=getattr(engine, 'budget', None),
        )
    except Exception as e:
        logger.debug(f"DebugCLI init failed: {e}")
        return None


def _handle_debug(args: Dict[str, Any]) -> Dict[str, Any]:
    """Run debug commands on a specific run."""
    slug = args.get("slug", "")
    command = args.get("command", "summary")

    engine = _get_engine()
    run = engine.get_run(slug) if slug else None
    if slug and not run:
        return {"error": f"Run '{slug}' not found"}

    # Without slug, show engine-level health
    if not slug:
        health = engine.health_snapshot
        return {
            "slug": None,
            "command": "health",
            "output": {
                "health_score": health.get("health_score", 0),
                "active_runs": health.get("active_runs", 0),
                "total_cost": health.get("total_cost", 0),
                "profiles": health.get("profiles", []),
                "degradation": health.get("degradation_level", "full"),
            },
            "status": "ok",
        }

    cli = _get_debug_cli(engine)
    if not cli:
        return {"error": "DebugCLI not available"}

    try:
        # Run debug command via DebugCLI
        text_output = cli.handle(command, slug)
        return {
            "slug": slug,
            "command": command,
            "output": text_output,
            "status": "ok",
        }
    except Exception as e:
        return {"error": str(e)}


def _handle_config(args: Dict[str, Any]) -> Dict[str, Any]:
    """Show engine configuration."""
    engine = _get_engine()
    try:
        cfg = engine.config
        if hasattr(cfg, 'to_dict'):
            config_dict = cfg.to_dict()
        else:
            import dataclasses
            config_dict = dataclasses.asdict(cfg)

        config_dict["status"] = "ok"
        return config_dict
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════
# Aliases for backward compatibility (old import paths)
# ═══════════════════════════════════════════════════════════════════

handle_new_run = handle_run
handle_setup = _handle_content_setup
handle_scan_slop_action = _handle_scan_slop
