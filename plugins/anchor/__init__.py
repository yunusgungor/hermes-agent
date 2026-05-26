"""
⚓ Anchor Guardrail Plugin — Hermes Agent için deterministik LLM doğrulama.

v3.0.0: In-Turn Interleaved Guardrail (tek mod).
Anchor, LLM'in üretim anında (same conversation turn) devreye girer:

  Round 0: LLM generates → Anchor checks → violations? → feedback appended
  Round 1: LLM self-corrects → Anchor checks → clean? → done
  Round 2: Final chance → corrective fallback

Her tur AYNI konuşma içinde — context, tool sonuçları, sistem mesajı korunur.
Anchor tamamen invisible — kullanıcı sadece temiz çıktıyı görür.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

VERSION = "3.0.0"
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────

_MAX_ANCHOR_ROUNDS = 3  # Maksimum interleaved düzeltme turu


def register(ctx: Any) -> None:
    """Plugin kaydı."""
    logger.info("⚓ Anchor Guardrail plugin v%s loading...", VERSION)

    try:
        from plugins.anchor.anchor_rectifier import init_engine, get_rules_path
        _preload_engine(rules_path=get_rules_path())
    except Exception:
        logger.debug("⚓ Engine preload deferred to session start")

    ctx.register_hook("on_session_start", _on_session_start)
    logger.info("⚓ Anchor Guardrail plugin v%s loaded", VERSION)


def _preload_engine(rules_path: str = None) -> None:
    """Plugin yükleme anında engine'i pre-init et (singleton)."""
    from plugins.anchor.anchor_rectifier import init_engine, is_active
    engine = init_engine(rules_path=rules_path)
    if is_active():
        logger.info("⚓ Engine preloaded at plugin registration time")
    else:
        logger.debug("⚓ Engine preload not available yet")


def _read_anchor_config_from_file() -> dict:
    """Config dosyasını oku."""
    try:
        from hermes_cli.config import load_config
        cfg = load_config()
        if cfg and isinstance(cfg, dict):
            anchor_cfg = cfg.get("anchor", {})
            if isinstance(anchor_cfg, dict):
                return anchor_cfg
    except Exception as exc:
        logger.debug("⚓ Config read failed (%s)", exc)

    try:
        import os
        import yaml
        from pathlib import Path
        hermes_home = os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
        config_path = Path(hermes_home) / "config.yaml"
        if config_path.exists():
            with open(config_path) as f:
                cfg = yaml.safe_load(f)
            if cfg and isinstance(cfg, dict):
                anchor_cfg = cfg.get("anchor", {})
                if isinstance(anchor_cfg, dict):
                    return anchor_cfg
    except Exception:
        pass

    return {}


def _on_session_start(**kwargs: Any) -> None:
    """Session başlangıcında Anchor'ı başlat ve agent.run_conversation()'ı yamala."""
    agent = kwargs.get("agent")
    if not agent:
        logger.debug("⚓ No agent in on_session_start — skipping")
        return

    anchor_config = _read_anchor_config_from_file()

    if not anchor_config.get("enabled", True):
        logger.info("⚓ Anchor disabled in config")
        return

    from plugins.anchor.anchor_rectifier import (
        init_engine, is_active, get_rules_path,
    )

    rules_path = anchor_config.get("rules_path", get_rules_path())
    use_embedding = anchor_config.get("use_embedding", False)

    logger.debug(
        "⚓ Config: rules_path=%s, use_embedding=%s",
        rules_path, use_embedding,
    )

    # Önce PATCH uygula — engine hazır olmasa bile wrapper sarılır
    _patch_run_conversation(agent)

    # Engine'i başlat (singleton)
    engine = init_engine(rules_path=rules_path, use_embedding=use_embedding)

    if not is_active():
        logger.warning("⚓ Engine not ready — responses pass through until engine initializes")
    else:
        logger.info("⚓ Anchor active — interleaved guardrail enabled (max_rounds=%d)", _MAX_ANCHOR_ROUNDS)


# ── Confidence Filter ─────────────────────────────────────────────────────


def _passes_threshold(d: dict) -> bool:
    """Confidence eşiği kontrolü."""
    rt = d.get("rule_type", "domain")
    conf = d.get("confidence", 0)
    if rt == "domain":
        return conf >= 0.5
    elif rt == "hybrid":
        return conf >= 0.7
    return conf >= 0.7


# ── Feedback Builder ──────────────────────────────────────────────────────


def _build_feedback_message(
    filtered_details: list[dict],
    report: dict,
    round_num: int,
    max_rounds: int,
) -> str:
    """LLM'in kendini düzeltmesi için Anchor feedback mesajı oluştur.

    Bu mesaj conversation_history'e user mesajı olarak eklenir.
    LLM kendi output'unu + bu feedback'i görüp doğal olarak düzeltir.
    """
    parts = [
        "Aşağıdaki sorunlar tespit edildi, lütfen yanıtınızı düzeltin:",
        "",
    ]

    for i, d in enumerate(filtered_details, 1):
        rule = d.get("rule", "?")
        severity = d.get("severity", "INFO")
        orig = d.get("original", "").strip()[:120]
        corr = d.get("corrected", "").strip()[:120]

        line = f"{i}. **{rule}** [{severity}]"
        if orig and corr and orig != corr:
            line += f": `{orig}` → `{corr}`"
        elif orig:
            line += f": `{orig}` — düzeltilmeli"
        parts.append(line)

    if report.get("rules_activated"):
        parts.extend([
            "",
            f"İhlal edilen kurallar: {', '.join(report['rules_activated'][:5])}",
        ])

    parts.extend([
        "",
        "Önceki yanıtınızı bu düzeltmelere göre güncelleyin. "
        "Anchor notlarını yanıta eklemeyin — sadece içeriği düzeltin, "
        "yanıtınızın doğal akışını ve anlamını koruyun.",
        f"(Anchor — tur {round_num + 1}/{max_rounds})",
    ])

    return "\n".join(parts)


# ── Main Patch ────────────────────────────────────────────────────────────


def _patch_run_conversation(agent: Any) -> None:
    """AIAgent.run_conversation()'ı interleaved guardrail ile saran wrapper.

    v3.0.0: In-Turn Interleaved Guardrail.
    Artık 4 mod yok — tek bir akış:
      Round 0: LLM generates → Anchor checks → clean? → done
      Round 1-2: LLM self-corrects with feedback → Anchor checks
      Fallback: Corrective replacement

    Anchor INVISIBLE — kullanıcı sadece temiz çıktıyı görür.
    """
    original_run_conversation = agent.run_conversation

    def anchored_run_conversation(
        user_message: str,
        system_message: str = None,
        conversation_history: list = None,
        task_id: str = None,
        **kwargs: Any,
    ) -> dict:
        """Interleaved guardrail ile run_conversation."""
        import copy

        original_user_message = user_message
        current_history = copy.deepcopy(conversation_history) if conversation_history else None

        for round_num in range(_MAX_ANCHOR_ROUNDS):
            result = original_run_conversation(
                user_message=user_message,
                system_message=system_message,
                conversation_history=current_history,
                task_id=task_id,
                **kwargs,
            )

            final_response = result.get("final_response")
            if not final_response:
                return result

            # ── Anchor check ─────────────────────────────────────────
            from plugins.anchor.anchor_rectifier import (
                rectify,
                _is_educational_content,
                _anchor_engine,
            )

            is_educational = _is_educational_content(final_response)
            if is_educational:
                logger.debug("⚓ Educational content — workflow rules disabled")

            _, report = rectify(
                user_query=original_user_message,
                llm_output=final_response,
                skip_workflow_rules=is_educational,
            )

            # No violations → clean, done
            if not report or not report.get("details"):
                logger.debug("⚓ Round %d: clean — returning response", round_num)
                return result

            # Confidence filter
            report_details = report.get("details", [])
            filtered = [d for d in report_details if _passes_threshold(d)]
            if not filtered:
                logger.debug(
                    "⚓ Round %d: %d violations filtered out (all below threshold) — returning",
                    round_num, len(report_details),
                )
                return result

            logger.info(
                "⚓ Round %d/%d: %d violations (%d rules)",
                round_num + 1, _MAX_ANCHOR_ROUNDS,
                len(filtered), report.get("corrections", 0),
            )

            # Last round → corrective fallback, then done
            if round_num >= _MAX_ANCHOR_ROUNDS - 1:
                from plugins.anchor.anchor_rectifier import apply_corrections
                corrected, actual = apply_corrections(final_response, report)
                if actual > 0:
                    logger.info(
                        "⚓ Fallback: %d corrective replacement(s) applied",
                        actual,
                    )
                    result["final_response"] = corrected
                return result

            # ── Build feedback and append to conversation ────────────
            feedback_text = _build_feedback_message(
                filtered, report, round_num, _MAX_ANCHOR_ROUNDS,
            )

            # Append assistant response + anchor feedback to history
            if current_history is None:
                current_history = []
            current_history.append({"role": "assistant", "content": final_response})
            current_history.append({"role": "user", "content": feedback_text})

            # Next round: user_message becomes empty (feedback is in history)
            user_message = ""
            logger.debug(
                "⚓ Round %d: feedback injected (%d chars) — continuing",
                round_num, len(feedback_text),
            )

        return result

    agent.run_conversation = anchored_run_conversation
    logger.debug("⚓ AIAgent.run_conversation() patched with Anchor v%s (interleaved guardrail)", VERSION)
