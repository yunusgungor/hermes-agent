"""
Anchor Rectifier — Hermes Agent için Anchor Engine entegrasyonu.

Bu modül, LLM çıktılarını Anchor Engine ile deterministik olarak
doğrular ve düzeltir. Her turda OTOMATİK çalışır — LLM kararı değil.

v1.3.0: Type-aware educational filtering — domain rules always active, hybrid rules factual-only.
"""

import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Module-level singleton (initialize once, use for all sessions)
_anchor_engine = None
_anchor_enabled = False
_anchor_rules_path = None

# ── Educational Content Detection ─────────────────────────────────────────

# Eğitim içeriği belirteçleri — LLM yanıtı bu marker'lardan yeterince
# içeriyorsa "eğitim/mentoring" olarak sınıflandırılır, workflow rule'ları pasif geçer.
_EDUCATIONAL_MARKERS: list[str] = [
    # Phase/Step markers (structured explanations)
    "faz", "phase", "adım", "step", "aşama",
    # Teaching/explanation markers
    "örnek", "örneğin", "örnek olarak", "mesela",
    "yani", "şöyle", "şu şekilde", "nedir",
    "nasıl", "ne işe yarar", "ne demek",
    "amacı", "anlamı", "tanımı",
    "temel olarak", "genel olarak", "kısaca",
    "başlıca", "önemli", "dikkat",
    "gördüğün gibi", "gösterir", "açıklar",
    # Educational section headers
    "ne amaçla", "neden önemli", "faydası",
    "avantaj", "dezavantaj", "özet",
    "rehber", "kılavuz", "guide", "tutorial",
]

# Gerçek iş çıktısı belirteçleri — bunlar varsa büyük ihtimal eğitim içeriği DEĞİL
_WORK_MARKERS: list[str] = [
    # Commit/fix identifiers
    r'[a-f0-9]{7,40}',          # commit hash
    r'(?:fix|feat|refactor|chore|docs|test)\(',  # conventional commit
    r'#[0-9]+',                  # issue/PR number
    r'(?:PR|pr|Mr|mr)[-#]\d+',   # PR/MR number
    r'commit\s+[a-f0-9]{7,}',    # explicit commit reference
    # File paths
    r'(?:/[\w.-]+)+/\w+\.\w+',   # file path
    r'(?:src|lib|app|test|docs)/',
    # CLI commands
    r'(?:pip|npm|yarn|pnpm|brew|apt|docker)\s+(?:install|run|build|deploy)',
    r'pytest\s+',
    r'git\s+(?:commit|push|merge|rebase|checkout|branch)',
    # Versions/output
    r'v?\d+\.\d+\.\d+(?:-\w+)?', # semver
    r'(?:PASS|FAIL|ERROR|OK)\s', # test results
]

# Alt sınır — eğitim içeriği sayılması için minimum yanıt uzunluğu
_EDUCATIONAL_MIN_LENGTH = 800
# Eğitim marker eşiği — bu kadar farklı marker türü varsa eğitim say
_EDUCATIONAL_MARKER_THRESHOLD = 3


def _is_educational_content(text: str) -> bool:
    """
    LLM yanıtının eğitim/mentoring içeriği mi yoksa gerçek iş çıktısı mı
    olduğunu tespit eder.

    Strateji:
      1. Kısa yanıtlar (< 800 chars) → eğitim içeriği sayılmaz (gerçek iş olabilir)
      2. Gerçek iş marker'ları (commit hash, PR#, file path) varsa → eğitim DEĞİL
      3. Eğitim marker'ları eşik değerin üstündeyse → eğitim içeriği

    Returns:
        True: yanıt eğitim/mentoring içeriği (workflow rule'ları pasif)
        False: yanıt gerçek iş çıktısı (tüm rule'lar aktif)
    """
    if not text or len(text) < _EDUCATIONAL_MIN_LENGTH:
        return False

    text_lower = text.lower()

    # 1. Gerçek iş marker'larını kontrol et — varsa eğitim sayma
    work_marker_count = 0
    for pattern in _WORK_MARKERS:
        try:
            if re.search(pattern, text):
                work_marker_count += 1
        except re.error:
            continue
    if work_marker_count >= 2:
        return False  # Birden fazla gerçek iş marker'ı → gerçek iş çıktısı

    # 2. Eğitim marker'larını say
    edu_marker_count = 0
    found_markers: set[str] = set()
    for marker in _EDUCATIONAL_MARKERS:
        if marker in text_lower:
            if marker not in found_markers:
                found_markers.add(marker)
                edu_marker_count += 1

    # 3. Yapısal analiz: tablo/liste/heading yoğunluğu
    #    Eğitim içerikleri genelde yapılandırılmış formatta olur
    has_tables = text.count("|") > 6  # Markdown tablo
    has_headings = len(re.findall(r'^#{1,4}\s', text, re.MULTILINE)) >= 3  # 3+ heading
    has_bullets = len(re.findall(r'^\s*[-*]\s', text, re.MULTILINE)) >= 5  # 5+ bullet
    has_code_blocks = len(re.findall(r'```', text)) >= 2  # code block çifti

    structural_score = sum([has_tables, has_headings, has_bullets, has_code_blocks])

    # 4. Karar
    if edu_marker_count >= _EDUCATIONAL_MARKER_THRESHOLD and structural_score >= 1:
        logger.debug(
            "⚓ Educational content detected: markers=%d, structure=%d/4",
            edu_marker_count, structural_score,
        )
        return True

    # Yüksek yapısal skor + en az 1 eğitim marker'ı da yeterli
    if structural_score >= 3 and edu_marker_count >= 1:
        logger.debug(
            "⚓ Educational content detected (structural): structure=%d/4, markers=%d",
            structural_score, edu_marker_count,
        )
        return True

    return False


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
    try:
        import anchor
        anchor_dir = Path(anchor.__file__).parent.parent  # src/anchor/..
        bundled = Path(__file__).parent / "rules"
        if bundled.exists():
            return str(bundled)
    except ImportError:
        pass

    # 5. User must configure
    logger.warning("⚓ No Anchor rules found. Set ANCHOR_RULES_PATH or create ~/.hermes/anchor-rules/")
    return str(project_rules)


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


def rectify(user_query: str, llm_output: str,
            skip_workflow_rules: bool = False) -> tuple[str, Optional[dict]]:
    """
    LLM çıktısını Anchor ile doğrula ve düzelt.

    Hermes stratejisi:
    - LLM'in orijinal cevabını HER ZAMAN koru (asla değiştirme)
    - Düzeltme varsa rapor olarak döndür, report modu ekler
    - skip_workflow_rules=True ise workflow rule'ları pasif geçer (eğitim içeriği)

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
                orig = c.original_text[:100]
                corr = c.corrected_text[:100]
                sev = c.conflict.severity.name if hasattr(c.conflict, 'severity') else "INFO"
                confidence = getattr(c.conflict, 'confidence', 0.5)
                rule_type = getattr(c.conflict, 'rule_type', 'domain')
                report["details"].append({
                    "original": orig,
                    "corrected": corr,
                    "severity": sev,
                    "confidence": round(confidence, 2),
                    "rule": c.conflict.rule_id if hasattr(c.conflict, 'rule_id') else "?",
                    "rule_type": rule_type,
                })

            logger.info(
                "⚓ Detected: %d corrections in LLM output (rules=%s, educational=%s) — original preserved",
                n, result.rules_activated[:3], skip_workflow_rules,
            )

            return llm_output, report
        else:
            return llm_output, None

    except Exception as e:
        logger.warning("⚓ Anchor rectification failed (non-fatal): %s", e)
        return llm_output, None


def is_active() -> bool:
    """Anchor aktif mi?"""
    return _anchor_enabled and _anchor_engine is not None
