"""
Anchor Rectifier — Hermes Agent için Anchor Engine entegrasyonu.

Bu modül, LLM çıktılarını Anchor Engine ile deterministik olarak
doğrular ve düzeltir. Her turda OTOMATİK çalışır — LLM kararı değil.

v3.0.0: Artık sadece In-Turn Interleaved Guardrail.
  - generate_steering_feedback, steering_posthoc, HermesLLMGenerator kaldırıldı
  - Bu fonksiyonlar __init__.py'deki interleaved loop ile değiştirildi
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Module-level singleton (initialize once, use for all sessions)
_anchor_engine = None
_anchor_enabled = False
_anchor_rules_path = None

# ── Educational Content Detection ─────────────────────────────────────────

_EDUCATIONAL_MARKERS: list[str] = [
    "faz", "phase", "adım", "step", "aşama",
    "örnek", "örneğin", "örnek olarak", "mesela",
    "yani", "şöyle", "şu şekilde", "nedir",
    "nasıl", "ne işe yarar", "ne demek",
    "amacı", "anlamı", "tanımı",
    "temel olarak", "genel olarak", "kısaca",
    "başlıca", "önemli", "dikkat",
    "gördüğün gibi", "gösterir", "açıklar",
    "ne amaçla", "neden önemli", "faydası",
    "avantaj", "dezavantaj", "özet",
    "rehber", "kılavuz", "guide", "tutorial",
]

_WORK_MARKERS: list[str] = [
    r'[a-f0-9]{7,40}',
    r'(?:fix|feat|refactor|chore|docs|test)\(',
    r'#[0-9]+',
    r'(?:PR|pr|Mr|mr)[-#]\d+',
    r'commit\s+[a-f0-9]{7,}',
    r'(?:/[\w.-]+)+/\w+\.\w+',
    r'(?:src|lib|app|test|docs)/',
    r'(?:pip|npm|yarn|pnpm|brew|apt|docker)\s+(?:install|run|build|deploy)',
    r'pytest\s+',
    r'git\s+(?:commit|push|merge|rebase|checkout|branch)',
    r'v?\d+\.\d+\.\d+(?:-\w+)?',
    r'(?:PASS|FAIL|ERROR|OK)\s',
]

_EDUCATIONAL_MIN_LENGTH = 800
_EDUCATIONAL_MARKER_THRESHOLD = 3


def _is_educational_content(text: str) -> bool:
    """LLM yanıtının eğitim/mentoring içeriği mi, gerçek iş çıktısı mı?"""
    if not text or len(text) < _EDUCATIONAL_MIN_LENGTH:
        return False

    text_lower = text.lower()

    # 1. Gerçek iş marker'ları
    work_marker_count = 0
    for pattern in _WORK_MARKERS:
        try:
            if re.search(pattern, text):
                work_marker_count += 1
        except re.error:
            continue
    if work_marker_count >= 2:
        return False

    # 2. Eğitim marker'ları
    edu_marker_count = 0
    found_markers: set[str] = set()
    for marker in _EDUCATIONAL_MARKERS:
        if marker in text_lower:
            if marker not in found_markers:
                found_markers.add(marker)
                edu_marker_count += 1

    # 3. Yapısal analiz
    has_tables = text.count("|") > 6
    has_headings = len(re.findall(r'^#{1,4}\s', text, re.MULTILINE)) >= 3
    has_bullets = len(re.findall(r'^\s*[-*]\s', text, re.MULTILINE)) >= 5
    has_code_blocks = len(re.findall(r'```', text)) >= 2
    structural_score = sum([has_tables, has_headings, has_bullets, has_code_blocks])

    # 4. Karar
    if edu_marker_count >= _EDUCATIONAL_MARKER_THRESHOLD and structural_score >= 1:
        return True
    if structural_score >= 3 and edu_marker_count >= 1:
        return True

    return False


# ── Rules Path ────────────────────────────────────────────────────────────


def get_rules_path() -> str:
    """Anchor rules dizinini bul — hybrid: project > global > builtin."""
    env_path = os.environ.get("ANCHOR_RULES_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    project_rules = Path.cwd() / ".hermes" / "anchor-rules"
    if project_rules.exists():
        return str(project_rules)

    hermes_home = os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
    global_rules = Path(hermes_home) / "anchor-rules"
    if global_rules.exists():
        return str(global_rules)

    try:
        bundled = Path(__file__).parent / "rules"
        if bundled.exists():
            return str(bundled)
    except Exception:
        pass

    logger.warning("⚓ No Anchor rules found. Set ANCHOR_RULES_PATH or create ~/.hermes/anchor-rules/")
    return str(project_rules)


# ── Engine Init ───────────────────────────────────────────────────────────


def init_engine(rules_path: Optional[str] = None, use_embedding: bool = False):
    """AnchorEngine'i başlat (singleton)."""
    global _anchor_engine, _anchor_enabled, _anchor_rules_path

    if _anchor_engine is not None:
        return _anchor_engine

    _anchor_rules_path = os.path.expanduser(rules_path or get_rules_path())

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


# ── Rectify ───────────────────────────────────────────────────────────────


def rectify(user_query: str, llm_output: str,
            skip_workflow_rules: bool = False) -> tuple[str, Optional[dict]]:
    """LLM çıktısını Anchor ile doğrula ve düzeltme raporu üret.

    Returns:
        (orijinal_llm_yaniti, report_dict or None)
    """
    if not _anchor_enabled or _anchor_engine is None:
        return llm_output, None

    try:
        result = _anchor_engine.process(
            user_query=user_query,
            llm_output=llm_output,
            skip_workflow_rules=skip_workflow_rules,
        )

        if result.modified:
            n = len(result.corrections)
            report = {
                "modified": True,
                "corrections": n,
                "rules_activated": result.rules_activated,
                "topics_found": [t.name for t in result.topics_found],
                "step_violations": len(result.step_violations) if result.step_violations else 0,
                "details": [],
            }

            for c in result.corrections:
                sev = c.conflict.severity.name if hasattr(c.conflict, 'severity') else "INFO"
                confidence = getattr(c.conflict, 'confidence', 0.5)
                rule_type = getattr(c.conflict, 'rule_type', 'domain')
                report["details"].append({
                    "original": c.original_text[:100],
                    "corrected": c.corrected_text[:100],
                    "full_original": c.original_text,
                    "full_corrected": c.corrected_text,
                    "severity": sev,
                    "confidence": round(confidence, 2),
                    "rule": c.conflict.rule_id if hasattr(c.conflict, 'rule_id') else "?",
                    "rule_type": rule_type,
                })

            logger.info(
                "⚓ Detected: %d corrections (rules=%s, educational=%s) — feedback will be injected",
                n, result.rules_activated[:3], skip_workflow_rules,
            )

            return llm_output, report
        else:
            return llm_output, None

    except Exception as e:
        logger.warning("⚓ Anchor rectification failed (non-fatal): %s", e)
        return llm_output, None


# ── Apply Corrections (fallback) ──────────────────────────────────────────


def apply_corrections(llm_output: str, report: Optional[dict],
                      confidence_threshold: Optional[dict] = None) -> tuple[str, int]:
    """LLM çıktısındaki hataları Anchor raporundaki düzeltmelerle değiştirir.

    Son çare (fallback) düzeltme — interleaved loop tükendiğinde kullanılır.
    """
    if not report:
        return llm_output, 0

    if confidence_threshold is None:
        confidence_threshold = {
            "domain": 0.5,
            "hybrid": 0.7,
            "workflow": 0.8,
        }

    details = report.get("details", [])
    if not details:
        return llm_output, 0

    actual_changes = 0
    corrected = llm_output

    for d in details:
        rule_type = d.get("rule_type", "domain")
        confidence = d.get("confidence", 0)
        threshold = confidence_threshold.get(rule_type, 0.7)

        if confidence < threshold:
            continue

        orig = d.get("full_original", d.get("original", ""))
        corr = d.get("full_corrected", d.get("corrected", ""))

        if not orig or not corr or orig == corr:
            continue

        if orig in corrected:
            corrected = corrected.replace(orig, corr, 1)
            actual_changes += 1

    return corrected, actual_changes


def is_active() -> bool:
    """Anchor aktif mi?"""
    return _anchor_enabled and _anchor_engine is not None
