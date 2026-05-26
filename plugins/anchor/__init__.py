"""
⚓ Anchor Guardrail Plugin — Hermes Agent için deterministik LLM doğrulama.

v3.1.0: In-Turn Interleaved Guardrail + Tüm iyileştirmeler.

  Round 0: LLM generates → Anchor checks → violations? → feedback appended
  Round 1: LLM self-corrects → Anchor checks → clean? → done
  Round 2: Final chance → corrective fallback

Her tur AYNI konuşma içinde — context, tool sonuçları, sistem mesajı korunur.
Anchor tamamen invisible — kullanıcı sadece temiz çıktıyı görür.

v3.1.0 İyileştirmeleri:
  - Config'deki `mode` alanı deprecated — deprecation warning loglanır
  - `get_hermes_home()` kullanıldı (profile-aware config okuma)
  - Loop içi import'lar module level'a çıkarıldı (perf + stil)
  - Feedback dili conversation diline göre adapte (Türkçe/İngilizce)
  - Plugin disable/unload: `_unpatch_run_conversation()` public API
  - Çift patch koruması: `_anchor_patched` attribute check
"""

from __future__ import annotations

import copy
import logging
from typing import Any, Optional

VERSION = "3.1.0"
logger = logging.getLogger(__name__)

# ── Module-level import (hoisted from loop — perf + stil) ──────────────
# Module-level import for mock-friendly access in tests.
# Tests can do `ar.rectify = mock_fn` and the loop picks it up.
import plugins.anchor.anchor_rectifier as _anchor_rectifier

# ── Profile-aware config path (fallback: env → ~/.hermes) ──────────────
try:
    from hermes_constants import get_hermes_home as _get_hermes_home
except (ModuleNotFoundError, ImportError):
    import os
    from pathlib import Path

    def _get_hermes_home() -> Path:  # type: ignore[misc]
        val = os.environ.get("HERMES_HOME", "").strip()
        return Path(val) if val else Path.home() / ".hermes"


_MAX_ANCHOR_ROUNDS = 3
_original_run_conversation = None
"""Patch geri alma için store — _unpatch_run_conversation() kullanır."""


# ── Language Detection ─────────────────────────────────────────────────

_TR_CHARS: set[str] = {"ğ", "ü", "ş", "ı", "ö", "ç"}
_TR_WORDS: set[str] = {
    "bir", "ile", "için", "bu", "veya",
    "eder", "yap", "olan", "ancak",
    "ve", "veya", "değil", "çünkü", "ise",
    "nasıl", "neden", "hangi", "kendi",
    "ama", "fakat", "lakin", "eğer",
    "şey", "şeyler", "bunu", "buna",
    "biz", "siz", "onlar", "bizim",
    "ben", "sen", "o", "bana", "sana",
}
_EN_WORDS: set[str] = {
    "the", "this", "that", "with", "would",
    "should", "could", "please", "thank",
    "however", "therefore", "although",
    "actually", "basically", "essentially",
    "because", "between", "through",
    "their", "there", "these", "those",
    "have", "has", "had", "does", "doesn",
    "what", "when", "where", "which", "who",
}


def _detect_language(texts: list[str]) -> str:
    """Conversation dilini tespit et: 'tr' veya 'en'.

    Strateji: Türkçe karakterler (güçlü sinyal) + sık kelime karşılaştırması.
    Beraberlik durumunda varsayılan 'tr'.
    """
    if not texts:
        return "tr"

    tr_score = 0
    en_score = 0

    for text in texts:
        lower = text.lower()

        # Türkçe karakterler varsa güçlü sinyal
        if any(c in _TR_CHARS for c in lower):
            tr_score += 3

        # Token bazlı kelime eşleştirme
        tokens = set(lower.split())
        tr_score += len(tokens & _TR_WORDS)
        en_score += len(tokens & _EN_WORDS)

    return "tr" if tr_score >= en_score else "en"


# ── Config ────────────────────────────────────────────────────────────


def _read_anchor_config_from_file() -> dict:
    """Anchor config'ini oku — profile-aware (`get_hermes_home()`)."""
    # Önce Hermes'in kendi config loader'ı (tercih edilen yol)
    try:
        from hermes_cli.config import load_config
        cfg = load_config()
        if cfg and isinstance(cfg, dict):
            anchor_cfg = cfg.get("anchor", {})
            if isinstance(anchor_cfg, dict):
                return anchor_cfg
    except Exception as exc:
        logger.debug("⚓ Config read via load_config failed (%s)", exc)

    # Fallback: doğrudan YAML oku (profile-aware path ile)
    try:
        import yaml
        config_path = _get_hermes_home() / "config.yaml"
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


# ── Plugin Lifecycle ──────────────────────────────────────────────────


def register(ctx: Any) -> None:
    """Plugin kaydı — Hermes Agent tarafından çağrılır."""
    logger.info("⚓ Anchor Guardrail plugin v%s loading...", VERSION)

    try:
        _preload_engine()
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


def _on_session_start(**kwargs: Any) -> None:
    """Session başlangıcı: config oku, patch uygula, engine başlat."""
    agent = kwargs.get("agent")
    if not agent:
        logger.debug("⚓ No agent in on_session_start — skipping")
        return

    anchor_config = _read_anchor_config_from_file()

    if not anchor_config.get("enabled", True):
        logger.info("⚓ Anchor disabled in config")
        return

    # ── Deprecation warning: `mode` ölü config key ────────────────────
    if "mode" in anchor_config:
        logger.warning(
            "⚓ Config key 'anchor.mode' is DEPRECATED in v3.0.0+. "
            "All modes were removed — only interleaved guardrail mode is used. "
            "Remove 'mode' from config.yaml to suppress this warning."
        )

    from plugins.anchor.anchor_rectifier import (
        init_engine, is_active, get_rules_path,
    )

    rules_path = anchor_config.get("rules_path", get_rules_path())
    use_embedding = anchor_config.get("use_embedding", False)

    logger.debug(
        "⚓ Config: rules_path=%s, use_embedding=%s",
        rules_path, use_embedding,
    )

    # Önce patch uygula — engine hazır olmasa bile wrapper sarılır
    _patch_run_conversation(agent)

    # Engine singleton başlat
    engine = init_engine(rules_path=rules_path, use_embedding=use_embedding)

    if not is_active():
        logger.warning(
            "⚓ Engine not ready — responses pass through until engine initializes"
        )
    else:
        logger.info(
            "⚓ Anchor active — interleaved guardrail enabled (max_rounds=%d)",
            _MAX_ANCHOR_ROUNDS,
        )


# ── Confidence Filter ─────────────────────────────────────────────────


def _passes_threshold(d: dict) -> bool:
    """Confidence eşiği kontrolü — rule_type bazlı."""
    rt = d.get("rule_type", "domain")
    conf = d.get("confidence", 0)
    if rt == "domain":
        return conf >= 0.5
    elif rt == "hybrid":
        return conf >= 0.7
    return conf >= 0.7


# ── Language-Adaptive Feedback Builder ─────────────────────────────────


def _build_feedback_message(
    filtered_details: list[dict],
    report: dict,
    round_num: int,
    max_rounds: int,
    *,
    language: str = "tr",
) -> str:
    """LLM feedback mesajı — conversation diline göre adaptif.

    Args:
        language: 'tr' (Türkçe) veya 'en' (İngilizce)
    """
    if language == "en":
        return _build_feedback_message_en(
            filtered_details, report, round_num, max_rounds,
        )

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


def _build_feedback_message_en(
    filtered_details: list[dict],
    report: dict,
    round_num: int,
    max_rounds: int,
) -> str:
    """English version of Anchor feedback message."""
    parts = [
        "The following issues were detected. Please correct your response:",
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
            line += f": `{orig}` — needs correction"
        parts.append(line)

    if report.get("rules_activated"):
        parts.extend([
            "",
            f"Violated rules: {', '.join(report['rules_activated'][:5])}",
        ])

    parts.extend([
        "",
        "Update your previous response based on these corrections. "
        "Do not include Anchor notes in your answer — just fix the content "
        "while keeping the natural flow and meaning of your response.",
        f"(Anchor — round {round_num + 1}/{max_rounds})",
    ])

    return "\n".join(parts)


# ── Main Patch ────────────────────────────────────────────────────────


def _patch_run_conversation(agent: Any) -> None:
    """AIAgent.run_conversation()'ı interleaved guardrail ile sar.

    v3.0.0+: In-Turn Interleaved Guardrail.
      Round 0: LLM generates → Anchor checks → clean? → done
      Round 1-2: LLM self-corrects with feedback → Anchor checks
      Fallback: Corrective replacement

    Anchor INVISIBLE — kullanıcı sadece temiz çıktıyı görür.
    """
    global _original_run_conversation

    original = getattr(agent, "run_conversation", None)
    if original is None:
        logger.warning("⚓ agent.run_conversation not found — cannot patch")
        return

    # Çift patch koruması
    if getattr(original, "_anchor_patched", False):
        logger.debug("⚓ Already patched — skipping")
        return

    _original_run_conversation = original

    def anchored_run_conversation(
        user_message: str,
        system_message: str = None,
        conversation_history: list = None,
        task_id: str = None,
        **kwargs: Any,
    ) -> dict:
        """Interleaved guardrail ile run_conversation."""

        original_user_message = user_message
        current_history = copy.deepcopy(conversation_history) if conversation_history else None

        # Conversation dilini tespit et (adaptif feedback için)
        texts_for_lang = [original_user_message]
        if current_history:
            for msg in current_history:
                content = msg.get("content", "")
                if isinstance(content, str) and content:
                    texts_for_lang.append(content)
                    if len(texts_for_lang) > 5:
                        break
        lang = _detect_language(texts_for_lang)

        for round_num in range(_MAX_ANCHOR_ROUNDS):
            result = original(
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
            is_educational = _anchor_rectifier._is_educational_content(final_response)
            if is_educational:
                logger.debug("⚓ Educational content — workflow rules disabled")

            _, report = _anchor_rectifier.rectify(
                user_query=original_user_message,
                llm_output=final_response,
                skip_workflow_rules=is_educational,
            )

            # Clean — no violations
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

            # Last round → corrective fallback
            if round_num >= _MAX_ANCHOR_ROUNDS - 1:
                corrected, actual = _anchor_rectifier.apply_corrections(final_response, report)
                if actual > 0:
                    logger.info(
                        "⚓ Fallback: %d corrective replacement(s) applied",
                        actual,
                    )
                    result["final_response"] = corrected
                return result

            # ── Build language-adaptive feedback ─────────────────────
            feedback_text = _build_feedback_message(
                filtered, report, round_num, _MAX_ANCHOR_ROUNDS,
                language=lang,
            )

            # Assistant response → history, feedback → next user_message
            if current_history is None:
                current_history = []
            current_history.append({"role": "assistant", "content": final_response})

            user_message = feedback_text
            logger.debug(
                "⚓ Round %d: %s feedback as user_message (%d chars) — continuing",
                round_num, lang.upper(), len(feedback_text),
            )

        return result

    anchored_run_conversation._anchor_patched = True  # type: ignore[attr-defined]
    agent.run_conversation = anchored_run_conversation
    logger.debug(
        "⚓ AIAgent.run_conversation() patched with Anchor v%s (interleaved guardrail)",
        VERSION,
    )


def _unpatch_run_conversation(agent: Any = None) -> None:
    """Original run_conversation'ı geri yükle.

    Plugin disable edildiğinde çağrılır. Mevcut Hermes plugin sistemi
    mid-session disable tetiklemez — bu fonksiyon manuel çağrı içindir.
    Tam disable için yeni session gerekir (/reset).

    Args:
        agent: AIAgent instance. None ise global store'dan dene.
    """
    global _original_run_conversation

    target = agent if agent is not None else None
    if target is None and _original_run_conversation is not None:
        # Global store var, agent'si bulamadık — cleanup
        _original_run_conversation = None
        logger.info("⚓ Anchor patch references cleared")
        return

    if target is None:
        logger.debug("⚓ No agent and no stored reference — nothing to unpatch")
        return

    current = getattr(target, "run_conversation", None)
    if current is not None and getattr(current, "_anchor_patched", False):
        target.run_conversation = _original_run_conversation
        logger.info("⚓ run_conversation() restored to original")
        _original_run_conversation = None
    else:
        logger.debug("⚓ run_conversation() was not patched — nothing to do")
