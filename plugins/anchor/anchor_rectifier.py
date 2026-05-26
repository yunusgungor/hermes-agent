"""
Anchor Rectifier — Hermes Agent için Anchor Engine entegrasyonu.

Bu modül, LLM çıktılarını Anchor Engine ile deterministik olarak
doğrular ve düzeltir. Her turda OTOMATİK çalışır — LLM kararı değil.

v2.0.0: v5.0 Active Steering entegrasyonu:
  - generate_steering_feedback() → GaaA-inspired StructuredFeedback
  - steering_rectify()          → Enhanced report + feedback
  - steering_posthoc()          → Post-hoc steering loop (corrective + history)
  - HermesLLMGenerator          → Interactive mode için LLM generator protocol
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
                    "full_original": c.original_text,
                    "full_corrected": c.corrected_text,
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


def apply_corrections(llm_output: str, report: Optional[dict],
                      confidence_threshold: Optional[dict] = None) -> tuple[str, int]:
    """
    LLM çıktısındaki hataları, Anchor raporundaki düzeltmelerle değiştirir.

    Corrective mode için kullanılır — orijinal metin içindeki hatalı kısımları
    düzeltilmiş versiyonlarıyla değiştirir. Her düzeltme için sadece İLK geçen
    değiştirilir (str.replace(..., 1)).

    Bu graduated escalation'ın "CORRECT" seviyesidir — direkt müdahale.

    Args:
        llm_output: LLM'in orijinal çıktısı (string)
        report: Anchor rectify()'den gelen report dict (veya None)
        confidence_threshold: Rule type'a göre eşik değerleri.
            Varsayılan: domain=0.5, hybrid=0.7, workflow=0.8

    Returns:
        (düzeltilmiş_metin, yapılan_değişiklik_sayısı)
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

        # Confidence eşiğini geçemeyenleri atla
        if confidence < threshold:
            continue

        # Tam metin (full_*) veya kısaltılmış (original/corrected) kullan
        orig = d.get("full_original", d.get("original", ""))
        corr = d.get("full_corrected", d.get("corrected", ""))

        # Güvenlik kontrolleri
        if not orig or not corr or orig == corr:
            continue

        # Metin içinde ara ve ilk geçeni değiştir
        if orig in corrected:
            corrected = corrected.replace(orig, corr, 1)
            actual_changes += 1

    return corrected, actual_changes


# ══════════════════════════════════════════════════════════════════════════
# v5.0 Active Steering — Structured Feedback & Steering Loop Integration
# ══════════════════════════════════════════════════════════════════════════

def generate_steering_feedback(
    user_query: str,
    llm_output: str,
    skip_workflow_rules: bool = False,
) -> Optional[dict]:
    """
    LLM çıktısından yapılandırılmış geribildirim üret (GaaA formatı).

    StructuredFeedback objesini makine tarafından işlenebilir dict'e
    dönüştürür. Hermes plugin'in "steering" modu için.

    Returns:
        {
            "feedback_text":       "İnsan tarafından okunabilir metin",
            "items":               [feedback_item_dict, ...],
            "rule_count":          int,
            "total_violations":    int,
            "max_severity":        str,
            "content_type":        str,
            "has_workflow_violations": bool,
            "has_factual_conflicts":   bool,
        } veya None (violation yoksa / engine hazır değilse)
    """
    if not _anchor_enabled or _anchor_engine is None:
        return None

    try:
        feedback = _anchor_engine.generate_feedback(
            user_query=user_query,
            llm_output=llm_output,
            skip_workflow_rules=skip_workflow_rules,
        )
    except Exception as e:
        logger.warning("⚓ Feedback generation failed (non-fatal): %s", e)
        return None

    if not feedback.feedback_items:
        return None

    # Dict'e çevir
    items = []
    for item in feedback.feedback_items:
        items.append({
            "rule": item.rule,
            "rule_type": item.rule_type,
            "violation": item.violation,
            "severity": item.severity,
            "correction": item.correction,
            "original": item.original,
            "confidence": item.confidence,
            "step_violation": item.step_violation,
        })

    return {
        "feedback_text": feedback.feedback_text,
        "items": items,
        "rule_count": feedback.rule_count,
        "total_violations": feedback.total_violations,
        "max_severity": feedback.max_severity.name if feedback.max_severity else "NONE",
        "content_type": feedback.content_type.value if feedback.content_type else "factual",
        "has_workflow_violations": feedback.has_workflow_violations,
        "has_factual_conflicts": feedback.has_factual_conflicts,
    }


def steering_rectify(
    user_query: str,
    llm_output: str,
    skip_workflow_rules: bool = False,
) -> tuple[str, Optional[dict], Optional[dict]]:
    """
    Enhanced rectification — hem klasik report hem de GaaA feedback döndürür.

    "steering" modu için unified API:
      - corrections_report: Eski tarz anchor_rectifier report dict (rectify() gibi)
      - feedback_dict:      Yeni StructuredFeedback dict (generate_steering_feedback() gibi)

    Returns:
        (orijinal_llm_yaniti, corrections_report, feedback_dict)
    """
    if not _anchor_enabled or _anchor_engine is None:
        return llm_output, None, None

    # Önce klasik rectification (corrections report)
    corrections_report = None
    feedback_dict = None

    try:
        result = _anchor_engine.process(
            user_query=user_query,
            llm_output=llm_output,
            skip_workflow_rules=skip_workflow_rules,
        )

        if result.modified:
            n = len(result.corrections)
            corrections_report = {
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
                corrections_report["details"].append({
                    "original": c.original_text[:100],
                    "corrected": c.corrected_text[:100],
                    "full_original": c.original_text,
                    "full_corrected": c.corrected_text,
                    "severity": sev,
                    "confidence": round(confidence, 2),
                    "rule": c.conflict.rule_id if hasattr(c.conflict, 'rule_id') else "?",
                    "rule_type": rule_type,
                })
    except Exception as e:
        logger.warning("⚓ Steering rectify process failed (non-fatal): %s", e)

    # Ardından structured feedback
    try:
        feedback = _anchor_engine.generate_feedback(
            user_query=user_query,
            llm_output=llm_output,
            skip_workflow_rules=skip_workflow_rules,
        )

        if feedback and feedback.feedback_items:
            items = []
            for item in feedback.feedback_items:
                items.append({
                    "rule": item.rule,
                    "rule_type": item.rule_type,
                    "violation": item.violation,
                    "severity": item.severity,
                    "correction": item.correction,
                    "original": item.original,
                    "confidence": item.confidence,
                    "step_violation": item.step_violation,
                })

            feedback_dict = {
                "feedback_text": feedback.feedback_text,
                "items": items,
                "rule_count": feedback.rule_count,
                "total_violations": feedback.total_violations,
                "max_severity": feedback.max_severity.name if feedback.max_severity else "NONE",
                "content_type": feedback.content_type.value if feedback.content_type else "factual",
                "has_workflow_violations": feedback.has_workflow_violations,
                "has_factual_conflicts": feedback.has_factual_conflicts,
            }
    except Exception as e:
        logger.warning("⚓ Steering feedback gen failed (non-fatal): %s", e)

    return llm_output, corrections_report, feedback_dict


def steering_posthoc(
    user_query: str,
    llm_output: str,
    skip_workflow_rules: bool = False,
) -> dict:
    """
    Post-hoc steering loop — tek tur, LLM re-gen olmadan.

    SteeringLoop.run_posthoc()'u sarar. Corrective mode +
    structured feedback + escalation + exhaustion döndürür.

    Returns:
        {
            "corrected":              str (düzeltilmiş output veya original)
            "feedback":               dict veya None (StructuredFeedback)
            "history_summary":        str
            "escalation_level":       str (NOOP, ADVISE, ..., ESCALATE)
            "is_exhausted":           bool
            "total_rounds":           int
            "correction_count":       int
        }
    """
    if not _anchor_enabled or _anchor_engine is None:
        return {
            "corrected": llm_output,
            "feedback": None,
            "history_summary": "Engine not active",
            "escalation_level": "NOOP",
            "is_exhausted": False,
            "total_rounds": 0,
            "correction_count": 0,
        }

    try:
        from anchor.steering.loop import SteeringLoop

        loop = SteeringLoop(engine=_anchor_engine)
        corrected, feedback, history = loop.run_posthoc(
            user_query=user_query,
            llm_output=llm_output,
            skip_workflow_rules=skip_workflow_rules,
        )

        # Son turdan escalation/exhaustion bilgisi
        last_round = history.rounds[-1] if history.rounds else None
        escalation_level = "NOOP"
        is_exhausted = False
        correction_count = 0

        if last_round:
            if last_round.escalation:
                escalation_level = last_round.escalation.level.name
            if last_round.exhaustion:
                is_exhausted = last_round.exhaustion.is_exhausted
            correction_count = last_round.correction_count

        # Feedback'i dict'e çevir
        feedback_dict = None
        if feedback and feedback.feedback_items:
            items = []
            for item in feedback.feedback_items:
                items.append({
                    "rule": item.rule,
                    "rule_type": item.rule_type,
                    "violation": item.violation,
                    "severity": item.severity,
                    "correction": item.correction,
                    "original": item.original,
                    "confidence": item.confidence,
                    "step_violation": item.step_violation,
                })

            feedback_dict = {
                "feedback_text": feedback.feedback_text,
                "items": items,
                "rule_count": feedback.rule_count,
                "total_violations": feedback.total_violations,
                "max_severity": feedback.max_severity.name if feedback.max_severity else "NONE",
                "content_type": feedback.content_type.value if feedback.content_type else "factual",
                "has_workflow_violations": feedback.has_workflow_violations,
                "has_factual_conflicts": feedback.has_factual_conflicts,
            }

        return {
            "corrected": corrected,
            "feedback": feedback_dict,
            "history_summary": history.summary(),
            "escalation_level": escalation_level,
            "is_exhausted": is_exhausted,
            "total_rounds": history.total_rounds,
            "correction_count": correction_count,
        }

    except Exception as e:
        logger.warning("⚓ Steering posthoc failed (non-fatal): %s", e)
        return {
            "corrected": llm_output,
            "feedback": None,
            "history_summary": f"Error: {e}",
            "escalation_level": "NOOP",
            "is_exhausted": False,
            "total_rounds": 0,
            "correction_count": 0,
        }


# ══════════════════════════════════════════════════════════════════════════
# Interactive Steering — Hermes LLM Generator Protocol
# ══════════════════════════════════════════════════════════════════════════

class HermesLLMGenerator:
    """
    Hermes Agent için LLMGeneratorProtocol implementasyonu.

    SteeringLoop.run()'un LLM re-generation ihtiyacı için.
    Hermes agent'ın LLM client'ını kullanarak yeniden üretim yapar.

    Kullanım:
        generator = HermesLLMGenerator(agent)
        loop = SteeringLoop(engine=_anchor_engine, generator=generator)
        history = loop.run(user_query, llm_output)
    """

    def __init__(self, agent: Any):
        """
        Args:
            agent: Hermes AIAgent instance (session'daki agent)
        """
        self._agent = agent
        self._llm_client = self._resolve_llm_client()

    def _resolve_llm_client(self) -> Optional[Any]:
        """Hermes agent'ın LLM client'ını bul."""
        # AIAgent.llm_client (yeni mimari)
        if hasattr(self._agent, 'llm_client') and self._agent.llm_client:
            return self._agent.llm_client
        # AIAgent.client (eski mimari)
        if hasattr(self._agent, 'client') and self._agent.client:
            return self._agent.client
        # AIAgent.model_client
        if hasattr(self._agent, 'model_client') and self._agent.model_client:
            return self._agent.model_client
        return None

    def generate(self, prompt: str, context: str = "") -> str:
        """
        Hermes LLM client ile yeniden üretim yap.

        Args:
            prompt:  Orijinal kullanıcı sorgusu
            context: Anchor feedback + re-generation talimatı

        Returns:
            LLM'in yeniden ürettiği yanıt
        """
        if not self._llm_client:
            logger.warning(
                "⚓ No LLM client available for steering re-generation. "
                "Falling back to original output."
            )
            return context if context else prompt

        # Re-generation prompt'u oluştur
        full_prompt = self._build_regen_prompt(prompt, context)

        try:
            # Hermes LLM client'ı çağır
            if hasattr(self._llm_client, 'chat_completion'):
                response = self._llm_client.chat_completion(
                    messages=[{"role": "user", "content": full_prompt}],
                )
            elif hasattr(self._llm_client, 'generate'):
                response = self._llm_client.generate(prompt=full_prompt)
            else:
                # Generic call method
                response = self._llm_client(full_prompt)

            text = self._extract_text(response)
            if text:
                logger.info("⚓ Steering re-generation successful (%d chars)", len(text))
                return text
        except Exception as e:
            logger.warning("⚓ Steering re-generation failed: %s — using original output", e)

        # Fallback: context içinde LLM yanıtı yoksa original output'u döndür
        return context if context else prompt

    def _build_regen_prompt(self, original_query: str, feedback_context: str) -> str:
        """Yeniden üretim prompt'unu oluştur."""
        return (
            f"## Kullanıcı Sorusu\n{original_query}\n\n"
            f"{feedback_context}\n\n"
            "Yukarıdaki düzeltme önerilerini dikkate alarak "
            "yanıtınızı yeniden yazın. "
            "Önerilerdeki tüm düzeltmeleri uygulayın, "
            "ancak yanıtınızın doğal akışını koruyun. "
            "Anchor notlarını yanıta eklemeyin."
        )

    def _extract_text(self, response: Any) -> Optional[str]:
        """LLM yanıtından metin çıkar — çeşitli response formatlarını dene."""
        if isinstance(response, str):
            return response
        if isinstance(response, dict):
            # OpenAI format
            if 'choices' in response:
                choice = response['choices'][0]
                if isinstance(choice, dict):
                    msg = choice.get('message', {})
                    if isinstance(msg, dict):
                        return msg.get('content', '')
                    return getattr(msg, 'content', '') if hasattr(msg, 'content') else ''
                return getattr(choice, 'message', {}).get('content', '') if hasattr(choice, 'message') else ''
            # Direct content
            return response.get('content', response.get('text', ''))
        # Object
        if hasattr(response, 'choices'):
            choice = response.choices[0]
            if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                return choice.message.content
            return getattr(choice, 'text', '')
        return str(response) if response else None


def create_steering_loop(generator: Optional[Any] = None) -> Any:
    """
    SteeringLoop instance'ı oluştur.

    Args:
        generator: HermesLLMGenerator veya None (post-hoc)
            None → sadece run_posthoc() kullanılabilir

    Returns:
        SteeringLoop instance
    """
    if not _anchor_engine:
        raise RuntimeError("Anchor Engine not initialized. Call init_engine() first.")

    from anchor.steering.loop import SteeringLoop
    return SteeringLoop(engine=_anchor_engine, generator=generator)


def is_active() -> bool:
    """Anchor aktif mi?"""
    return _anchor_enabled and _anchor_engine is not None
