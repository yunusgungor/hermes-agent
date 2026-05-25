"""
⚓ Anchor Rectifier Plugin — Hermes Agent için deterministik LLM doğrulama.

Her LLM yanıtı otomatik olarak Anchor Engine'den geçer.
LLM'in kararına bırakılmaz — her zaman aktif.
"""

import logging
from typing import Any

VERSION = "1.0.0"
logger = logging.getLogger(__name__)


def register(ctx: Any) -> None:
    """Plugin kaydı."""
    logger.info("⚓ Anchor Rectifier plugin v%s loading...", VERSION)

    # Register on_session_start hook — Anchor'ı başlat ve chat()'i yamala
    ctx.register_hook("on_session_start", _on_session_start)

    logger.info("⚓ Anchor Rectifier plugin v%s loaded", VERSION)


def _on_session_start(**kwargs: Any) -> None:
    """Session başlangıcında Anchor'ı başlat ve AIAgent.chat()'i yamala."""
    agent = kwargs.get("agent")
    if not agent:
        logger.debug("⚓ No agent in on_session_start — skipping")
        return

    # Anchor config'ini oku (agent.config veya doğrudan config dict)
    anchor_config = {}
    if hasattr(agent, "config") and isinstance(agent.config, dict):
        anchor_config = agent.config.get("anchor", {})
    elif hasattr(agent, "_config") and isinstance(agent._config, dict):
        anchor_config = agent._config.get("anchor", {})

    if not anchor_config.get("enabled", True):
        logger.info("⚓ Anchor disabled in config")
        return

    rules_path = anchor_config.get("rules_path", get_rules_path())
    use_embedding = anchor_config.get("use_embedding", False)
    mode = anchor_config.get("mode", "silent")

    # Anchor'ı başlat
    from plugins.anchor.anchor_rectifier import init_engine, is_active

    engine = init_engine(rules_path=rules_path, use_embedding=use_embedding)

    if not is_active():
        logger.info("⚓ Anchor not active — responses will pass through unchanged")
        return

    # AIAgent.chat() metodunu Anchor ile yamala
    _patch_chat_method(agent, mode=mode)

    logger.info(
        "⚓ Anchor active — every response will be rectified (mode=%s)",
        mode,
    )


def _patch_chat_method(agent: Any, mode: str = "silent") -> None:
    """AIAgent.chat() metodunu Anchor post-processing ile saran wrapper."""
    original_chat = agent.chat

    def anchored_chat(message: str, stream_callback=None) -> str:
        """Anchor post-processing ile chat."""
        response = original_chat(message, stream_callback=stream_callback)

        from plugins.anchor.anchor_rectifier import rectify

        corrected, report = rectify(
            user_query=message,
            llm_output=response,
        )

        if report:
            n_corrections = report.get("corrections", 0)

            if mode == "report":
                rules = ", ".join(report.get("rules_activated", [])[:3])
                topics = ", ".join(report.get("topics_found", [])[:3])
                corrected += (
                    f"\n\n---\n⚓ **Anchor Düzeltmesi:** {n_corrections} hata düzeltildi"
                )
                if rules:
                    corrected += f"\n📋 Kurallar: {rules}"
                if topics:
                    corrected += f"\n🏷️ Konular: {topics}"
            elif mode == "annotated":
                corrected += f"\n\n⚓ {n_corrections} düzeltme uygulandı"
            # silent mode: seamless

        return corrected

    agent.chat = anchored_chat
    logger.debug("⚓ AIAgent.chat() patched with Anchor rectification (mode=%s)", mode)
