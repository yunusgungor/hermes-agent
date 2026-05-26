"""
⚓ Anchor Rectifier Plugin — Hermes Agent için deterministik LLM doğrulama.

Her LLM yanıtı otomatik olarak Anchor Engine'den geçer.
v1.4.0: Corrective mode — LLM çıktısını append değil doğrudan düzeltir.
v1.3.0: Type-aware rule filtering (domain/hybrid/workflow) + adaptive confidence.
LLM'in kararına bırakılmaz — her zaman aktif.
"""

import logging
from typing import Any

VERSION = "1.4.0"
logger = logging.getLogger(__name__)


def register(ctx: Any) -> None:
    """Plugin kaydı."""
    logger.info("⚓ Anchor Rectifier plugin v%s loading...", VERSION)

    # 🔥 Engine'i plugin yükleme anında başlat (her session'da rebuild önler)
    # Singleton olduğu için tüm session'lar paylaşır — ilk yanıt kaçmaz
    try:
        from plugins.anchor.anchor_rectifier import init_engine, get_rules_path
        _preload_engine(rules_path=get_rules_path())
    except Exception:
        logger.debug("⚓ Engine preload deferred to session start")

    # Register on_session_start hook
    ctx.register_hook("on_session_start", _on_session_start)

    logger.info("⚓ Anchor Rectifier plugin v%s loaded", VERSION)


def _preload_engine(rules_path: str = None) -> None:
    """Plugin yükleme anında engine'i pre-init et (singleton)."""
    from plugins.anchor.anchor_rectifier import init_engine, is_active
    engine = init_engine(rules_path=rules_path)
    if is_active():
        logger.info("⚓ Engine preloaded at plugin registration time")
    else:
        logger.debug("⚓ Engine preload not available yet")


def _read_anchor_config_from_file() -> dict:
    """Config dosyasını doğrudan oku — agent.config'a güvenme (AIAgent'te yok)."""
    try:
        from hermes_cli.config import load_config, get_config_path
        cfg = load_config()
        if cfg and isinstance(cfg, dict):
            anchor_cfg = cfg.get("anchor", {})
            if isinstance(anchor_cfg, dict):
                return anchor_cfg
    except Exception as exc:
        logger.debug("⚓ Config file read failed (%s), trying YAML direct", exc)

    # Fallback: YAML'i doğrudan parse et
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
    except Exception as exc:
        logger.debug("⚓ YAML direct read also failed: %s", exc)

    return {}


def _on_session_start(**kwargs: Any) -> None:
    """Session başlangıcında Anchor'ı başlat ve agent.run_conversation()'ı yamala."""
    agent = kwargs.get("agent")
    if not agent:
        logger.debug("⚓ No agent in on_session_start — skipping")
        return

    # Anchor config'ini DOĞRUDAN config dosyasından oku (AIAgent.config yok!)
    anchor_config = _read_anchor_config_from_file()

    if not anchor_config.get("enabled", True):
        logger.info("⚓ Anchor disabled in config")
        return

    # Import'ları en başta yap — scope hatasını önler
    from plugins.anchor.anchor_rectifier import init_engine, is_active, get_rules_path

    rules_path = anchor_config.get("rules_path", get_rules_path())
    use_embedding = anchor_config.get("use_embedding", False)
    mode = anchor_config.get("mode", "annotated")

    logger.debug(
        "⚓ Config loaded: mode=%s, rules_path=%s, use_embedding=%s",
        mode, rules_path, use_embedding,
    )

    # 🔥 KRİTİK: Önce PATCH uygula — engine hazır olmasa bile wrapper sarılır
    # rectify() engine None ise pass-through yapar, hazır olunca otomatik devreye girer
    _patch_run_conversation(agent, mode=mode)

    # Sonra engine'i başlat (singleton — register'da preload edildiyse anında döner)
    engine = init_engine(rules_path=rules_path, use_embedding=use_embedding)

    if not is_active():
        logger.warning("⚓ Engine not ready — responses pass through until engine initializes")
    else:
        logger.info(
            "⚓ Anchor active — every response will be rectified (mode=%s)",
            mode,
        )


def _patch_run_conversation(agent: Any, mode: str = "silent") -> None:
    """
    AIAgent.run_conversation() metodunu Anchor post-processing ile saran wrapper.

    chat()'i değil run_conversation()'ı yamalamak kritik çünkü:
    - CLI (interactive + -q):      agent.run_conversation()
    - Gateway (Telegram, Discord): agent.run_conversation()
    - API Server:                  agent.run_conversation()
    - chat() metodu:               sadece run_conversation()'ı çağıran wrapper

    v1.2.0: Educational content detection + confidence threshold.
    """
    original_run_conversation = agent.run_conversation

    def anchored_run_conversation(
        user_message: str,
        system_message: str = None,
        conversation_history: list = None,
        task_id: str = None,
        **kwargs: Any,
    ) -> dict:
        """Anchor post-processing ile run_conversation."""
        result = original_run_conversation(
            user_message=user_message,
            system_message=system_message,
            conversation_history=conversation_history,
            task_id=task_id,
            **kwargs,
        )

        # final_response yoksa veya None ise Anchor çalıştırma
        final_response = result.get("final_response")
        if not final_response:
            return result

        from plugins.anchor.anchor_rectifier import rectify, _is_educational_content, apply_corrections

        # 🔍 Yanıtı sınıflandır — eğitim içeriğinde workflow rule'larını pasifleştir
        is_educational = _is_educational_content(final_response)
        if is_educational:
            logger.debug(
                "⚓ Educational content detected — workflow rules disabled for this response"
            )

        corrected, report = rectify(
            user_query=user_message,
            llm_output=final_response,
            skip_workflow_rules=is_educational,
        )

        # Annotated mode: confidence eşiği filtresi
        # Domain corrections: lower threshold (0.5) — factual bilgi kritik
        # Hybrid corrections: medium threshold (0.7) — eğitim içeriğinde FP önleme
        CONFIDENCE_THRESHOLD = 0.7

        if report:
            n_corrections = report.get("corrections", 0)
            details = report.get("details", [])
            mode_now = mode

            # ── Corrective Mode ──────────────────────────────────────────
            # LLM çıktısını doğrudan düzelt, annotation ekleme
            if mode_now == "corrective":
                corrected_text, actual_changes = apply_corrections(
                    final_response, report,
                )
                if actual_changes > 0:
                    logger.info(
                        "⚓ Corrective: %d replacement(s) applied (rules=%s)",
                        actual_changes, report.get("rules_activated", [])[:3],
                    )
                    result["final_response"] = corrected_text
                else:
                    # Hiçbir düzeltme eşiği geçemediyse annotated'a düş
                    logger.debug(
                        "⚓ Corrective: 0 replacements above threshold — falling back to annotated"
                    )
                    # Yine de annotated mode'a düş
                    corrected_text = final_response
                    mode_now = "annotated"
                if actual_changes > 0:
                    return result

            # Confidence filtresi — rule_type'a göre adaptive threshold
            # Domain: 0.5 (factual bilgi kritik, düşük confidence'da da göster)
            # Hybrid: 0.7 (eğitim içeriğinde FP önleme)
            # Workflow: zaten engine'de filtrelendi, buraya gelmez
            
            def _passes_threshold(d: dict) -> bool:
                rt = d.get("rule_type", "domain")
                conf = d.get("confidence", 0)
                if rt == "domain":
                    return conf >= 0.5
                elif rt == "hybrid":
                    return conf >= 0.7
                return conf >= 0.7  # fallback
            
            filtered_details = [
                d for d in details
                if _passes_threshold(d)
            ]
            filtered_count = len(filtered_details)
            filtered_out = n_corrections - filtered_count

            if filtered_out > 0:
                logger.debug(
                    "⚓ Filtered %d/%d corrections below threshold (domain=0.5, hybrid=0.7)",
                    filtered_out, n_corrections,
                )

            if mode_now == "report":
                if filtered_count > 0:
                    corrected += f"\n\n---\n⚓ **Anchor Düzeltmesi:** {filtered_count} hata"
                    if filtered_out > 0:
                        corrected += f" ({filtered_out} düşük güven atlandı)"
                    rules = ", ".join(report.get("rules_activated", [])[:3])
                    if rules:
                        corrected += f"\n📋 Kurallar: {rules}"
                    for d in filtered_details[:5]:
                        sev_icon = {
                            "CRITICAL": "🔴",
                            "ERROR": "❌",
                            "WARNING": "⚠️",
                            "INFO": "ℹ️",
                        }.get(d.get("severity", ""), "•")
                        orig = d.get("original", "")[:60]
                        corr = d.get("corrected", "")[:60]
                        corrected += f"\n{sev_icon} ~~{orig}~~ → {corr}"
                    if len(filtered_details) > 5:
                        corrected += f"\n... ve {len(filtered_details) - 5} düzeltme daha"
                elif filtered_out > 0:
                    corrected += f"\n\n---\n⚓ {filtered_out} düşük güvenli uyarı atlandı"
            elif mode_now == "annotated":
                if filtered_count > 0:
                    corrected += f"\n\n⚓ {filtered_count} düzeltme uygulandı"
                    if filtered_out > 0:
                        corrected += f" ({filtered_out} düşük güven atlandı)"
                elif filtered_out > 0 and is_educational:
                    # Eğitim içeriği + tümü filtrelendi → sessiz geç
                    pass

            # Update final_response in the result dict
            result["final_response"] = corrected

        return result

    agent.run_conversation = anchored_run_conversation
    # chat() metodu zaten run_conversation()'ı çağırdığı için otomatik kapsanır
    logger.debug(
        "⚓ AIAgent.run_conversation() patched with Anchor rectification v1.2.0 (mode=%s)",
        mode,
    )
