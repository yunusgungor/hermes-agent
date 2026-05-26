"""
⚓ Anchor Rectifier Plugin — Hermes Agent için deterministik LLM doğrulama.

Her LLM yanıtı otomatik olarak Anchor Engine'den geçer.
v2.0.0: v5.0 Active Steering entegrasyonu:
  - posthoc mod (varsayılan): eski davranış, report + visibility footer
  - corrective mod: direkt düzeltme uygula
  - steering mod: GaaA structured feedback + escalation ladder + exhaustion
  - interactive mod (LLM re-gen): SteeringLoop.run() ile tam döngü
"""
from __future__ import annotations

import logging
from typing import Any, Optional

VERSION = "2.0.0"
logger = logging.getLogger(__name__)

# ── Plug Mode Mapping ─────────────────────────────────────────────────────
# Config'daki mode değerleri için işleme mantığı
# posthoc:     Klasik rectification (varsayılan), corrections report + footer
# corrective:  Direkt metin düzeltmesi uygula
# steering:    GaaA structured feedback + escalation ladder
# interactive: Tam steering loop (LLM re-gen) [future]


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
    from plugins.anchor.anchor_rectifier import (
        init_engine, is_active, get_rules_path,
    )

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


# ── Footer Builders ──────────────────────────────────────────────────────
# Seçenek 2: Sadece müdahale olduğunda detay göster.
# Hiçbir şey düzeltilmediyse TAMAMEN SESSİZ.


def _build_anchor_footer(
    report: dict,
    filtered_details: list[dict],
    rules_count: int,
) -> str:
    """
    Anchor düzeltme raporunu kullanıcıya gösteren footer.

    Format:
    ━━━ Anchor ▸ 23 kural denetlendi ⚡ 2 düzeltme:
    • naming-convention: `getData` → `fetchData`
    • tdd-cycle: Test yazılmadan implementasyon önerildi → uyarı eklendi

    Hiç düzeltme yoksa boş string döndürür.
    """
    n = len(filtered_details)
    if n == 0:
        return ""

    # Kural isimlerini kısalt
    rules_str = ", ".join(report.get("rules_activated", [])[:3])

    lines = [
        "",
        f"━━━ Anchor ▸ {rules_count} kural denetlendi ⚡ {n} düzeltme:",
    ]

    for d in filtered_details[:5]:
        rule = d.get("rule", "?")
        orig = d.get("original", "").strip()[:80]
        corr = d.get("corrected", "").strip()[:80]

        if orig and corr and orig != corr:
            lines.append(f"• `{rule}`: ~~{orig}~~ → **{corr}**")
        else:
            # Sadece uyarı (replace edilemeyen)
            lines.append(f"• `{rule}`: {orig[:100]} → ⚠️ düzeltme önerisi")

    if n > 5:
        lines.append(f"… ve {n - 5} düzeltme daha")

    if rules_str:
        lines.append(f"📋 {rules_str}")

    return "\n".join(lines)


def _build_steering_footer(
    feedback_dict: dict,
    report: Optional[dict] = None,
    rules_count: int = 0,
) -> str:
    """
    Steering modu için structured feedback footer'ı.

    Format:
    ━━━ Anchor v5.0 STEERING ▸ 23 kural · 3 violation [ERROR]
    🟠 Kural [tdd-cycle]: Adım 2 atlanmış — RED test yazılmadı
        → Önce RED test yaz, sonra implement et (%92 güven)
    📋 tdd-cycle, clean-arch | İçerik: factual | Merdiven: REGENERATE

    Hiç violation yoksa boş string döndürür.
    """
    if not feedback_dict or not feedback_dict.get("items"):
        return ""

    items = feedback_dict.get("items", [])
    total = feedback_dict.get("total_violations", 0)
    max_sev = feedback_dict.get("max_severity", "INFO")
    content_type = feedback_dict.get("content_type", "factual")

    # Escalation level (report'tan veya feedback_dict'ten)
    escalation_level = feedback_dict.get("escalation_level", None)

    severity_icon = {
        "CRITICAL": "🔴",
        "ERROR": "🟠",
        "WARNING": "🟡",
        "INFO": "🔵",
    }.get(max_sev, "⚪")

    lines = [
        "",
        f"━━━ Anchor v5.0 STEERING ▸ {rules_count} kural · "
        f"{total} violation {severity_icon}[{max_sev}]",
    ]

    for item in items[:5]:
        sev_icon = {
            "CRITICAL": "🔴",
            "ERROR": "🟠",
            "WARNING": "🟡",
            "INFO": "🔵",
        }.get(item.get("severity", "INFO"), "⚪")

        rule = item.get("rule", "?")
        violation = item.get("violation", "").strip()[:100]
        correction = item.get("correction", "").strip()[:80]
        confidence = item.get("confidence", 0)

        lines.append(
            f"{sev_icon} Kural [{rule}]: {violation}"
        )
        if correction:
            confidence_str = f" (%{confidence * 100:.0f} güven)" if confidence > 0 else ""
            lines.append(f"    → {correction}{confidence_str}")

    if total > 5:
        lines.append(f"… ve {total - 5} violation daha")

    # Status line
    status_parts = []
    if rules_str := (
        ", ".join(report.get("rules_activated", [])[:3])
        if report and report.get("rules_activated")
        else ""
    ):
        status_parts.append(f"📋 {rules_str}")
    status_parts.append(f"İçerik: {content_type}")
    if escalation_level:
        status_parts.append(f"Merdiven: {escalation_level}")

    if status_parts:
        lines.append(" | ".join(status_parts))

    return "\n".join(lines)


def _build_interactive_footer(
    history_summary: str,
    escalation_level: str,
    is_exhausted: bool,
    total_rounds: int,
    correction_count: int,
    rules_count: int,
) -> str:
    """
    Interactive mod için steering loop sonuç footer'ı.

    Format:
    ━━ Anchor v5.0 INTERACTIVE ▸ 23 kural · 3 tur · 5→1 violation
    Merdiven: CORRECT ⛔ Tükendi: Stagnasyon...
    """
    lines = [
        "",
        f"━━━ Anchor v5.0 INTERACTIVE ▸ {rules_count} kural · "
        f"{total_rounds} tur",
    ]

    lines.append(f"Merdiven: {escalation_level}")
    if is_exhausted:
        lines.append("⛔ Tükendi — corrective fallback uygulandı")

    # History summary kısaltması
    if history_summary:
        # İlk satırı al (özet)
        first_line = history_summary.split("\n")[0] if history_summary else ""
        if first_line:
            lines.append(f"📊 {first_line}")

    return "\n".join(lines)


# ── Mode-specific post-processors ─────────────────────────────────────────


def _process_posthoc_mode(
    final_response: str,
    report: Optional[dict],
    report_details: list[dict],
    rules_count: int,
    result: dict,
) -> None:
    """Posthoc mod: eski davranış — corrections report + footer."""
    footer = _build_anchor_footer(report, report_details, rules_count)
    if footer:
        result["final_response"] = (result.get("final_response") or final_response) + footer


def _process_corrective_mode(
    final_response: str,
    report: Optional[dict],
    report_details: list[dict],
    rules_count: int,
    result: dict,
    mode: str,
) -> None:
    """Corrective mod: direkt düzeltme + footer."""
    from plugins.anchor.anchor_rectifier import apply_corrections

    # Corrective replacement
    corrected_text, actual_changes = apply_corrections(
        final_response, report,
    )
    if actual_changes > 0:
        logger.info(
            "⚓ Corrective: %d replacement(s) applied (rules=%s)",
            actual_changes, report.get("rules_activated", [])[:3] if report else [],
        )
        result["final_response"] = corrected_text

    # Her durumda footer ekle
    footer = _build_anchor_footer(report, report_details, rules_count)
    if footer:
        result["final_response"] = (result.get("final_response") or final_response) + footer


def _process_steering_mode(
    final_response: str,
    user_message: str,
    skip_workflow_rules: bool,
    report: Optional[dict],
    rules_count: int,
    result: dict,
) -> None:
    """Steering mod: GaaA structured feedback + escalation ladder."""
    from plugins.anchor.anchor_rectifier import generate_steering_feedback

    # Structured feedback üret
    feedback_dict = generate_steering_feedback(
        user_query=user_message,
        llm_output=final_response,
        skip_workflow_rules=skip_workflow_rules,
    )

    if feedback_dict:
        logger.info(
            "⚓ Steering: %d structured feedback items (%d rules, severity=%s)",
            feedback_dict.get("total_violations", 0),
            feedback_dict.get("rule_count", 0),
            feedback_dict.get("max_severity", "NONE"),
        )

        # Steering footer'ı
        footer = _build_steering_footer(
            feedback_dict, report, rules_count,
        )
        if footer:
            result["final_response"] = (result.get("final_response") or final_response) + footer
    else:
        # Violation yok — sessiz geç (eski davranış)
        pass


def _process_interactive_mode(
    final_response: str,
    user_message: str,
    skip_workflow_rules: bool,
    agent: Any,
    rules_count: int,
    result: dict,
) -> None:
    """Interactive mod: tam steering loop + LLM re-generation.

    Bu mod, SteeringLoop.run()'u HermesLLMGenerator ile çalıştırarak:
    1. Post-hoc corrective round (Round 0)
    2. Structured feedback + escalation kararı
    3. LLM re-generation (eğer violation devam ediyor ve tükenme yoksa)
    4. Round 1+ analizi
    5. Tükenme veya yakınsama → döngü sonu

    Sonuç: corrected output + interactive footer
    """
    from plugins.anchor.anchor_rectifier import (
        HermesLLMGenerator,
        steering_posthoc,
        create_steering_loop,
    )

    # Önce post-hoc steering dene (corrective + feedback)
    steering_result = steering_posthoc(
        user_query=user_message,
        llm_output=final_response,
        skip_workflow_rules=skip_workflow_rules,
    )

    corrected_output = steering_result["corrected"]
    has_violations = (
        steering_result["feedback"] is not None
        and steering_result["feedback"].get("total_violations", 0) > 0
    )
    is_exhausted = steering_result["is_exhausted"]

    # Interactive loop: eğer violation varsa ve tükenme yoksa LLM re-gen dene
    if has_violations and not is_exhausted:
        try:
            generator = HermesLLMGenerator(agent)
            loop = create_steering_loop(generator=generator)

            # SteeringLoop.run() — multi-round LLM re-generation
            history = loop.run(
                user_query=user_message,
                llm_output=corrected_output,
            )

            if history and history.rounds:
                last_round = history.rounds[-1]
                corrected_output = last_round.corrected or corrected_output

                logger.info(
                    "⚓ Interactive steering completed: %d rounds, "
                    "last round corrections=%d",
                    history.total_rounds,
                    last_round.correction_count,
                )

            # SteeringLoop.run() çıktısını kullan
            steering_result["corrected"] = corrected_output
            steering_result["total_rounds"] = (
                history.total_rounds if history else 1
            )
            steering_result["is_exhausted"] = (
                history.rounds[-1].exhaustion.is_exhausted
                if history and history.rounds and history.rounds[-1].exhaustion
                else False
            )

            # Escalation level'ı güncelle
            if last_round and last_round.escalation:
                steering_result["escalation_level"] = last_round.escalation.level.name
                steering_result["history_summary"] = history.summary()

            # Re-gen output'u kullan
            if corrected_output != final_response:
                result["final_response"] = corrected_output

        except Exception as e:
            logger.warning(
                "⚓ Interactive LLM re-generation failed: %s — "
                "using post-hoc result", e,
            )

    # Interactive footer
    footer = _build_interactive_footer(
        history_summary=steering_result["history_summary"],
        escalation_level=steering_result["escalation_level"],
        is_exhausted=steering_result["is_exhausted"],
        total_rounds=steering_result["total_rounds"],
        correction_count=steering_result["correction_count"],
        rules_count=rules_count,
    )
    if footer:
        result["final_response"] = (result.get("final_response") or final_response) + footer


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


# ── Main Patch ────────────────────────────────────────────────────────────


def _patch_run_conversation(agent: Any, mode: str = "annotated") -> None:
    """
    AIAgent.run_conversation() metodunu Anchor post-processing ile saran wrapper.

    v2.0.0: Steering mod desteği — mode değerleri:
      - annotated:   Eski davranış (varsayılan), visibility footer
      - corrective:  Direkt metin düzeltmesi + footer
      - steering:    GaaA structured feedback + escalation ladder
      - interactive: Tam steering loop (LLM re-gen) + posthoc fallback

    CLI (interactive + -q): agent.run_conversation()
    Gateway (Telegram, Discord): agent.run_conversation()
    API Server: agent.run_conversation()
    chat() metodu: sadece run_conversation()'ı çağıran wrapper
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

        from plugins.anchor.anchor_rectifier import (
            rectify,
            _is_educational_content,
            _anchor_engine,
        )

        # 🔍 Yanıtı sınıflandır — eğitim içeriğinde workflow rule'larını pasifleştir
        is_educational = _is_educational_content(final_response)
        if is_educational:
            logger.debug(
                "⚓ Educational content detected — workflow rules disabled for this response"
            )

        skip_workflow_rules = is_educational

        # ── 0. Engine'den kural sayısını al ─────────────────────────────
        rules_count = 0
        engine = _anchor_engine
        if engine and hasattr(engine, "store") and hasattr(engine.store, "_rule_meta"):
            rules_count = len(engine.store._rule_meta)

        # ── 1. Rectification (her modda ortak) ──────────────────────────
        _, report = rectify(
            user_query=user_message,
            llm_output=final_response,
            skip_workflow_rules=skip_workflow_rules,
        )

        # ── 2. Confidence Filtresi ──────────────────────────────────────
        report_details = report.get("details", []) if report else []
        filtered_details = [d for d in report_details if _passes_threshold(d)]
        filtered_out = len(report_details) - len(filtered_details)

        if filtered_out > 0:
            logger.debug(
                "⚓ Filtered %d/%d corrections below threshold (domain=0.5, hybrid=0.7)",
                filtered_out, len(report_details),
            )

        # ── 3. Mod seçimi ───────────────────────────────────────────────
        mode_lower = mode.lower()

        if mode_lower == "corrective":
            _process_corrective_mode(
                final_response, report, filtered_details,
                rules_count, result, mode,
            )
        elif mode_lower == "steering":
            _process_steering_mode(
                final_response, user_message, skip_workflow_rules,
                report, rules_count, result,
            )
        elif mode_lower == "interactive":
            _process_interactive_mode(
                final_response, user_message, skip_workflow_rules,
                agent, rules_count, result,
            )
        else:  # annotated (default) veya diğer
            _process_posthoc_mode(
                final_response, report, filtered_details,
                rules_count, result,
            )

        return result

    agent.run_conversation = anchored_run_conversation
    # chat() metodu zaten run_conversation()'ı çağırdığı için otomatik kapsanır
    logger.debug(
        "⚓ AIAgent.run_conversation() patched with Anchor v%s (mode=%s)",
        VERSION, mode,
    )
