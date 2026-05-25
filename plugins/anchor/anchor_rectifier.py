"""
Anchor Rectifier — Hermes Agent için Anchor Engine entegrasyonu.

Bu modül, LLM çıktılarını Anchor Engine ile deterministik olarak
doğrular ve düzeltir. Her turda OTOMATİK çalışır — LLM kararı değil.
"""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Module-level singleton (initialize once, use for all sessions)
_anchor_engine = None
_anchor_enabled = False
_anchor_rules_path = None


def get_rules_path() -> str:
    """Anchor rules dizinini bul — hybrid: project > global > builtin."""
    # 1. Environment override
    env_path = os.environ.get("ANCHOR_RULES_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    # 2. Project local (cwd)
    project_rules = Path.cwd() / ".hermes" / "anchor-rules"
    if project_rules.exists():
        return str(project_rules)

    # 3. Hermes home
    hermes_home = os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
    global_rules = Path(hermes_home) / "anchor-rules"
    if global_rules.exists():
        return str(global_rules)

    # 4. Bundled rules (from pip installed anchor-engine)
    # Fallback: check if anchor is installed and has bundled rules
    try:
        import anchor
        anchor_dir = Path(anchor.__file__).parent.parent  # src/anchor/..
        # Rules might be alongside the package
        bundled = Path(__file__).parent / "rules"
        if bundled.exists():
            return str(bundled)
    except ImportError:
        pass

    # 5. User must configure
    logger.warning("⚓ No Anchor rules found. Set ANCHOR_RULES_PATH or create ~/.hermes/anchor-rules/")
    return str(project_rules)  # return path anyway, user needs to create it


def init_engine(rules_path: Optional[str] = None, use_embedding: bool = False):
    """AnchorEngine'i başlat (singleton)."""
    global _anchor_engine, _anchor_enabled, _anchor_rules_path

    if _anchor_engine is not None:
        return _anchor_engine

    _anchor_rules_path = rules_path or get_rules_path()

    try:
        from anchor.engine import AnchorEngine
        _anchor_engine = AnchorEngine(
            rules_path=_anchor_rules_path,
            use_embedding=use_embedding,
        )
        _anchor_engine.build()
        _anchor_enabled = True
        logger.info(
            "⚓ Anchor Engine initialized: rules=%s, rules_count=%d",
            _anchor_rules_path,
            len(_anchor_engine.store._rule_meta),
        )
    except ImportError:
        logger.warning("⚓ anchor-engine not installed. Run: pip install anchor-engine")
        _anchor_enabled = False
    except Exception as e:
        logger.warning("⚓ Anchor Engine init failed: %s", e)
        _anchor_enabled = False

    return _anchor_engine


def rectify(user_query: str, llm_output: str) -> tuple[str, Optional[dict]]:
    """
    LLM çıktısını Anchor ile doğrula ve düzelt.

    Hermes stratejisi:
    - LLM'in orijinal cevabını HER ZAMAN koru (asla değiştirme)
    - Düzeltme varsa rapor olarak döndür, report modu ekler
    - Anchor'ın corrected metnini kullanma — sadece tespit için kullan

    Returns:
        (orijinal_llm_yaniti, report_dict or None)
    """
    if not _anchor_enabled or _anchor_engine is None:
        return llm_output, None

    try:
        result = _anchor_engine.process(
            user_query=user_query,
            llm_output=llm_output,
        )

        if result.modified:
            n = len(result.corrections)
            report = {
                "corrections": n,
                "rules_activated": result.rules_activated,
                "topics_found": [t.name for t in result.topics_found],
                "step_violations": len(result.step_violations) if result.step_violations else 0,
                "details": [],
            }

            for c in result.corrections:
                orig = c.original_text[:100]
                corr = c.corrected_text[:100]
                sev = c.conflict.severity.name if hasattr(c.conflict, 'severity') else "INFO"
                report["details"].append({
                    "original": orig,
                    "corrected": corr,
                    "severity": sev,
                    "rule": c.conflict.rule_id if hasattr(c.conflict, 'rule_id') else "?",
                })

            logger.info(
                "⚓ Detected: %d corrections in LLM output (rules=%s) — original preserved",
                n, result.rules_activated[:3],
            )

            # LLM'in orijinal cevabını döndür, düzeltmeler rapor olarak gelir
            return llm_output, report
        else:
            return llm_output, None

    except Exception as e:
        logger.warning("⚓ Anchor rectification failed (non-fatal): %s", e)
        return llm_output, None


def is_active() -> bool:
    """Anchor aktif mi?"""
    return _anchor_enabled and _anchor_engine is not None
