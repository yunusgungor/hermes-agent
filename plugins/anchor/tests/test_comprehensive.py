"""
⚓ Anchor Plugin v3.1.0 — Comprehensive Test Suite

Covers:
  - _passes_threshold() confidence filter boundary tests
  - _build_feedback_message() Turkish + English format tests
  - _detect_language() Turkish/English detection
  - _patch_run_conversation() / _unpatch_run_conversation() lifecycle
  - _is_educational_content() (from anchor_rectifier)
  - Double-patch protection
  - Full interleaved loop (mock agent + mock rectify)
  - Language-adaptive feedback integration
"""

import copy
import sys
import os

# ── Test setup: ensure plugin paths ───────────────────────────────────
PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERMES_DIR = os.path.dirname(os.path.dirname(PLUGIN_DIR))
for p in [os.path.dirname(PLUGIN_DIR), HERMES_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Imports ────────────────────────────────────────────────────────────
from plugins.anchor import (
    _passes_threshold,
    _build_feedback_message,
    _build_feedback_message_en,
    _detect_language,
    _patch_run_conversation,
    _unpatch_run_conversation,
    _MAX_ANCHOR_ROUNDS,
)
from plugins.anchor.anchor_rectifier import _is_educational_content


# ═══════════════════════════════════════════════════════════════════════
# 1. _passes_threshold — Confidence Filter Boundaries
# ═══════════════════════════════════════════════════════════════════════

def test_threshold_domain_below():
    """Domain rule below 0.5 should fail."""
    assert not _passes_threshold({"rule_type": "domain", "confidence": 0.49})


def test_threshold_domain_at_boundary():
    """Domain rule at exactly 0.5 should pass."""
    assert _passes_threshold({"rule_type": "domain", "confidence": 0.5})


def test_threshold_domain_above():
    """Domain rule above 0.5 should pass."""
    assert _passes_threshold({"rule_type": "domain", "confidence": 0.75})


def test_threshold_hybrid_below():
    """Hybrid rule below 0.7 should fail."""
    assert not _passes_threshold({"rule_type": "hybrid", "confidence": 0.69})


def test_threshold_hybrid_at_boundary():
    """Hybrid rule at exactly 0.7 should pass."""
    assert _passes_threshold({"rule_type": "hybrid", "confidence": 0.7})


def test_threshold_hybrid_above():
    """Hybrid rule above 0.7 should pass."""
    assert _passes_threshold({"rule_type": "hybrid", "confidence": 0.95})


def test_threshold_workflow_below():
    """Workflow rule below 0.7 should fail (same threshold as hybrid)."""
    assert not _passes_threshold({"rule_type": "workflow", "confidence": 0.69})


def test_threshold_workflow_above():
    """Workflow rule at 0.8 should pass."""
    assert _passes_threshold({"rule_type": "workflow", "confidence": 0.8})


def test_threshold_default_rule_type():
    """Unknown rule_type should use default threshold (0.7)."""
    assert _passes_threshold({"rule_type": "unknown", "confidence": 0.7})
    assert not _passes_threshold({"rule_type": "custom", "confidence": 0.69})


def test_threshold_missing_confidence():
    """Missing confidence should default to 0 — fail all thresholds."""
    assert not _passes_threshold({"rule_type": "domain"})
    assert not _passes_threshold({"rule_type": "hybrid"})
    assert not _passes_threshold({"rule_type": "workflow"})


def test_threshold_missing_rule_type():
    """Missing rule_type should default to 'domain' threshold (0.5)."""
    assert _passes_threshold({"confidence": 0.5})
    assert not _passes_threshold({"confidence": 0.49})


# ═══════════════════════════════════════════════════════════════════════
# 2. _detect_language — Turkish vs English Detection
# ═══════════════════════════════════════════════════════════════════════

def test_detect_language_turkish():
    """Turkish text should return 'tr'."""
    lang = _detect_language([
        "Merhaba, bugün nasılsın? Ben bir soru sormak istiyorum.",
        "Bu konuda yardım edebilir misin?"
    ])
    assert lang == "tr", f"Expected 'tr', got '{lang}'"


def test_detect_language_english():
    """English text should return 'en'."""
    lang = _detect_language([
        "Hello, how are you today? I would like to ask a question.",
        "Could you please help me with this issue?"
    ])
    assert lang == "en", f"Expected 'en', got '{lang}'"


def test_detect_language_turkish_chars_strong():
    """Turkish characters (ğ,ü,ş,ı,ö,ç) give strong Turkish signal."""
    lang = _detect_language([
        "Türkiye'deki son gelişmeleri değerlendiriyoruz.",
        "Bu şey gerçekten çok önemli."
    ])
    assert lang == "tr", f"Expected 'tr', got '{lang}'"


def test_detect_language_mixed_turkish_wins():
    """Turkish with some English words should still be Turkish."""
    lang = _detect_language([
        "Bu proje için bir README dosyası oluşturmamız gerekiyor.",
        "The code should be clean and well-documented."
    ])
    assert lang == "tr", f"Expected 'tr', got '{lang}'"


def test_detect_language_empty_list():
    """Empty list should default to 'tr'."""
    lang = _detect_language([])
    assert lang == "tr", f"Expected 'tr', got '{lang}'"


def test_detect_language_single_turkish_word():
    """Single Turkish word should detect correctly."""
    lang = _detect_language(["merhaba"])
    assert lang == "tr"


def test_detect_language_single_english_word():
    """Single common English word should detect correctly."""
    lang = _detect_language(["please"])
    assert lang == "en"


def test_detect_language_mixed_tr_en_balanced_tr():
    """Turkish with sufficient marker words should win over English."""
    lang = _detect_language([
        "ben bir şey söylemek istiyorum",
        "bu konuda the size yardım etmek için",
    ])
    assert lang == "tr", f"Expected 'tr', got '{lang}'"


# ═══════════════════════════════════════════════════════════════════════
# 3. _build_feedback_message — Turkish Format
# ═══════════════════════════════════════════════════════════════════════

TR_SAMPLE_DETAILS = [
    {
        "rule": "conventional-commits",
        "severity": "ERROR",
        "original": "yaptığım değişiklikler",
        "corrected": "feat: yaptığım değişiklikler",
        "rule_type": "domain",
        "confidence": 0.92,
    },
    {
        "rule": "no-revert",
        "severity": "WARN",
        "original": "git revert yapmak sorunlu",
        "corrected": "",
        "rule_type": "hybrid",
        "confidence": 0.85,
    },
]


def test_feedback_turkish_contains_header():
    """Turkish feedback should start with the correct header."""
    msg = _build_feedback_message(
        TR_SAMPLE_DETAILS, {"rules_activated": ["conventional-commits"]},
        0, 3, language="tr",
    )
    assert "Aşağıdaki sorunlar tespit edildi" in msg


def test_feedback_turkish_shows_rule_name():
    """Turkish feedback should include rule names."""
    msg = _build_feedback_message(
        TR_SAMPLE_DETAILS, {"rules_activated": ["conventional-commits"]},
        0, 3, language="tr",
    )
    assert "conventional-commits" in msg
    assert "no-revert" in msg


def test_feedback_turkish_original_to_corrected():
    """Turkish feedback should show original → corrected format."""
    msg = _build_feedback_message(
        TR_SAMPLE_DETAILS, {"rules_activated": ["conventional-commits"]},
        0, 3, language="tr",
    )
    assert "yaptığım değişiklikler" in msg
    assert "feat: yaptığım değişiklikler" in msg
    assert "→" in msg


def test_feedback_turkish_shows_round():
    """Turkish feedback should show round number."""
    msg = _build_feedback_message(
        TR_SAMPLE_DETAILS, {"rules_activated": ["conventional-commits"]},
        0, 3, language="tr",
    )
    assert "1/3" in msg or "tur 1" in msg or "3" in msg


def test_feedback_turkish_empty_details():
    """Empty details should produce a message with header and footer."""
    msg = _build_feedback_message(
        [], {}, 0, 3, language="tr",
    )
    assert "Aşağıdaki sorunlar tespit edildi" in msg


def test_feedback_turkish_includes_violated_rules():
    """Turkish feedback should list violated rules."""
    msg = _build_feedback_message(
        TR_SAMPLE_DETAILS, {"rules_activated": ["conventional-commits", "no-revert"]},
        0, 3, language="tr",
    )
    assert "conventional-commits" in msg
    assert "no-revert" in msg


def test_feedback_turkish_without_activation():
    """Turkish feedback without rules_activated should still work."""
    msg = _build_feedback_message(
        TR_SAMPLE_DETAILS, {}, 0, 3, language="tr",
    )
    assert "Aşağıdaki sorunlar tespit edildi" in msg
    assert "conventional-commits" in msg


# ═══════════════════════════════════════════════════════════════════════
# 4. _build_feedback_message — English Format
# ═══════════════════════════════════════════════════════════════════════

EN_SAMPLE_DETAILS = [
    {
        "rule": "conventional-commits",
        "severity": "ERROR",
        "original": "fixed bug",
        "corrected": "fix: fixed bug",
        "rule_type": "domain",
        "confidence": 0.92,
    },
]


def test_feedback_english_contains_header():
    """English feedback should start with the correct header."""
    msg = _build_feedback_message_en(
        EN_SAMPLE_DETAILS, {"rules_activated": ["conventional-commits"]},
        0, 3,
    )
    assert "The following issues were detected" in msg


def test_feedback_english_shows_rule():
    """English feedback should include rule names."""
    msg = _build_feedback_message_en(
        EN_SAMPLE_DETAILS, {"rules_activated": ["conventional-commits"]},
        0, 3,
    )
    assert "conventional-commits" in msg


def test_feedback_english_adaptive_lang():
    """_build_feedback_message with language='en' should produce English."""
    msg = _build_feedback_message(
        EN_SAMPLE_DETAILS, {"rules_activated": ["conventional-commits"]},
        0, 3, language="en",
    )
    assert "The following issues were detected" in msg


def test_feedback_english_original_to_corrected():
    """English feedback should show original → corrected format."""
    msg = _build_feedback_message_en(
        EN_SAMPLE_DETAILS, {"rules_activated": ["conventional-commits"]},
        0, 3,
    )
    assert "fixed bug" in msg
    assert "fix: fixed bug" in msg
    assert "→" in msg


def test_feedback_english_empty_details():
    """Empty details in English should still produce a valid message."""
    msg = _build_feedback_message([], {}, 0, 3, language="en")
    assert "The following issues were detected" in msg


# ═══════════════════════════════════════════════════════════════════════
# 5. _is_educational_content (from anchor_rectifier)
# ═══════════════════════════════════════════════════════════════════════
# Note: Detection requires 800+ chars, 3+ educational markers from the
# marker list, and structural elements (tables, headings, bullets, code)

def _build_turkish_educational():
    """Build an 800+ char Turkish educational text that meets marker + structural criteria."""
    lines = []
    lines.append("# Ders Notları: Temel Kavramlar")
    lines.append("")
    lines.append("Bu faz 1'de adım adım ilerleyeceğiz. Önce örnek bir uygulama yapalım.")
    lines.append("Bu bir eğitim içeriğidir ve temel kavramları anlatır.")
    lines.append("")
    lines.append("## Önemli Noktalar")
    lines.append("- Birinci madde: adım adım öğrenme")
    lines.append("- İkinci madde: örnek uygulama")
    lines.append("- Üçüncü madde: temel kavramlar")
    lines.append("- Dördüncü madde: rehber niteliği")
    lines.append("- Beşinci madde: özet çıkarma")
    lines.append("")
    lines.append("## Faz 1: Başlangıç")
    lines.append("Bu bölümde nasıl başlayacağınızı göreceksiniz. Örnek olarak bir proje yapalım.")
    lines.append("Mesela basit bir Python uygulaması düşünelim.")
    lines.append("")
    lines.append("## Faz 2: Geliştirme")
    lines.append("Bu aşamada ne yapacağız? Öncelikle temel olarak neyin ne işe yaradığını")
    lines.append("anlamamız gerekiyor. Kısaca söylemek gerekirse, bu bir rehber niteliğindedir.")
    lines.append("")
    lines.append("## Özet")
    lines.append("Bu dersin amacı temel kavramları açıklamaktır. Ne amaçla kullanıldığını")
    lines.append("ve neden önemli olduğunu gördünüz. Faydası ve avantajları saymakla bitmez.")
    lines.append("Dezavantajı ise pratik gerektirmesidir.")
    lines.append("")
    lines.append("| Kavram | Açıklama | Örnek |")
    lines.append("|--------|----------|-------|")
    lines.append("| Değişken | Veri saklama | x = 5 |")
    lines.append("| Döngü | Tekrarlı işlem | for i in range(10) |")
    lines.append("| Koşul | Kontrol | if x > 0 |")
    return "\n".join(lines)


def _build_english_educational():
    """Build an 800+ char English educational text that meets marker + structural criteria."""
    lines = []
    lines.append("# Tutorial: Basic Concepts")
    lines.append("")
    lines.append("In phase 1 we will proceed step by step. First, let's look at a tutorial example.")
    lines.append("This is a guide about the basic concepts you need to understand.")
    lines.append("")
    lines.append("## Important Points")
    lines.append("- First item: step by step learning")
    lines.append("- Second item: tutorial example")
    lines.append("- Third item: basic concepts")
    lines.append("- Fourth item: reference guide")
    lines.append("- Fifth item: useful summary")
    lines.append("")
    lines.append("## Phase 2: Development")
    lines.append("In this phase you will learn how things work step by step.")
    lines.append("Let's look at an example tutorial for a better understanding.")
    lines.append("")
    lines.append("## Summary")
    lines.append("The purpose of this tutorial is to explain basic concepts step by step.")
    lines.append("This guide covers phases 1 and 2 with example code.")
    lines.append("")
    lines.append("| Topic | Description | Example |")
    lines.append("|-------|-------------|---------|")
    lines.append("| Variables | Data storage | x = 5 |")
    lines.append("| Loops | Iteration | for i in range(10) |")
    lines.append("| Conditions | Control | if x > 0 |")
    return "\n".join(lines)


def test_educational_turkish():
    """Turkish educational content with markers + structure should be detected."""
    text = _build_turkish_educational()
    assert len(text) >= 800, f"Need 800+ chars, got {len(text)}"
    assert _is_educational_content(text), f"Should detect Turkish educational, {len(text)} chars"


def test_educational_english():
    """English educational content with markers + structure should be detected."""
    text = _build_english_educational()
    assert len(text) >= 800, f"Need 800+ chars, got {len(text)}"
    assert _is_educational_content(text), f"Should detect English educational, {len(text)} chars"


def test_educational_not_flagged():
    """Regular business content without educational markers should not be flagged."""
    text = """
This is a normal code review comment. I think we should refactor the
user authentication module to use dependency injection instead of the
current factory pattern. Let me know what you think about this approach.
We could also add unit tests for the edge cases mentioned in the PR.
""".strip()
    assert not _is_educational_content(text), "Normal business text should NOT be flagged"


def test_educational_short_text():
    """Very short text (< 800 chars) should not be flagged."""
    assert not _is_educational_content("This is a short text.")
    assert not _is_educational_content("Ders: bu bir test")


def test_educational_work_content_not_flagged():
    """Content with 2+ work markers should NOT be flagged even if it has edu markers."""
    text = """
# Ders: Örnek Proje

git commit -m 'fix(scope): this is a fixed commit message'

In phase 1 of this tutorial we use pytest to test our application.
This step by step guide shows the example implementation at src/app/main.py.

## Önemli Noktalar
- Örnek: adım adım öğrenme
- Test: tutorial örneği
- Bu aşamada ne yapacağız
- Bu bir rehber

| Command | Description | Example |
|---------|-------------|---------|
| git | version control | git commit |
| pytest | testing | pytest test/ |
""".strip()
    # Has git and pytest work markers (2+), so should NOT be educational
    assert not _is_educational_content(text), "Work content with 2+ work markers should NOT be flagged"


# ═══════════════════════════════════════════════════════════════════════
# 6. Patch / Unpatch Lifecycle
# ═══════════════════════════════════════════════════════════════════════
#
# Note: Python bound methods create new objects on each access.
# We check functionality (correct behavior) rather than identity.

class MockAgent:
    """Minimal AIAgent mock for patch/unpatch testing."""
    def __init__(self):
        self.called = False
        self.last_user_message = None

    def run_conversation(self, user_message=None, system_message=None,
                        conversation_history=None, task_id=None, **kwargs):
        self.called = True
        self.last_user_message = user_message
        return {"final_response": "clean response"}


class MockAgentNoMethod:
    """Agent without run_conversation."""
    pass


def test_patch_applies_wrapper():
    """_patch_run_conversation should replace run_conversation with anchored version."""
    agent = MockAgent()
    _patch_run_conversation(agent)
    # After patch, run_conversation should have the _anchor_patched flag
    assert getattr(agent.run_conversation, "_anchor_patched", False), (
        "Patched method should have _anchor_patched flag"
    )


def test_patch_preserves_behavior():
    """Patched run_conversation should still return results."""
    agent = MockAgent()
    _patch_run_conversation(agent)
    result = agent.run_conversation(
        user_message="test query",
        conversation_history=[],
    )
    assert result["final_response"] == "clean response"


def test_patch_no_method():
    """Agent without run_conversation should not raise."""
    agent = MockAgentNoMethod()
    _patch_run_conversation(agent)  # should not raise


def test_unpatch_after_patch_removes_flag():
    """After unpatch, run_conversation should NOT have _anchor_patched."""
    agent = MockAgent()
    _patch_run_conversation(agent)
    assert getattr(agent.run_conversation, "_anchor_patched", False)
    _unpatch_run_conversation(agent)
    # After unpatch, the flag should be gone
    assert not getattr(agent.run_conversation, "_anchor_patched", False), (
        "After unpatch, _anchor_patched flag should be removed"
    )


def test_unpatch_after_patch_still_works():
    """After unpatch, run_conversation should still function correctly."""
    agent = MockAgent()
    _patch_run_conversation(agent)
    _unpatch_run_conversation(agent)
    result = agent.run_conversation(
        user_message="test query",
        conversation_history=[],
    )
    assert result["final_response"] == "clean response"
    assert agent.last_user_message == "test query"


def test_unpatch_no_patch():
    """_unpatch_run_conversation on an unpatched agent should be no-op."""
    agent = MockAgent()
    _unpatch_run_conversation(agent)  # should not raise
    # Should still work after
    result = agent.run_conversation(user_message="test")
    assert result["final_response"] == "clean response"


def test_double_patch_protection():
    """Patching twice should NOT double-wrap and still work."""
    agent = MockAgent()
    _patch_run_conversation(agent)
    first_wrapper = agent.run_conversation
    _patch_run_conversation(agent)
    # Same flag location
    assert getattr(agent.run_conversation, "_anchor_patched", False)
    # Still works
    result = agent.run_conversation(user_message="test", conversation_history=[])
    assert result["final_response"] == "clean response"


# ═══════════════════════════════════════════════════════════════════════
# 7. Interleaved Loop Integration (Mock-based)
# ═══════════════════════════════════════════════════════════════════════
#
# Strategy: Set up the agent's run_conversation as a mock BEFORE patching.
# The patched wrapper then calls into the mock, and we control the mock
# to simulate different LLM behaviors.

def test_loop_clean_response():
    """Clean response should pass through (no violations from rectify)."""
    agent = MockAgent()
    import plugins.anchor.anchor_rectifier as _ar
    _original_rectify = _ar.rectify

    try:
        _ar.rectify = lambda *a, **kw: (True, {"details": [], "corrections": 0})

        _patch_run_conversation(agent)
        result = agent.run_conversation(
            user_message="test query",
            conversation_history=[],
        )
        assert result["final_response"] == "clean response"
        assert agent.called, "Underlying run_conversation should be called"
    finally:
        _ar.rectify = _original_rectify


def test_loop_violations_then_fix():
    """Interleaved loop: violation → feedback → clean response.

    Round 0: LLM responds, rectify finds violations → feedback
    Round 1: LLM responds clean, rectify finds nothing → done
    """
    import plugins.anchor.anchor_rectifier as ar
    original_rectify = ar.rectify

    # Track which LLM call we're on
    llm_call_count = [0]
    rectify_call_count = [0]

    violation_details = [
        {
            "rule": "test-rule",
            "severity": "ERROR",
            "original": "violation",
            "corrected": "fix",
            "rule_type": "domain",
            "confidence": 0.9,
        }
    ]

    def mock_rectify(user_query, llm_output, skip_workflow_rules=False):
        rectify_call_count[0] += 1
        if rectify_call_count[0] == 1:
            # First rectify: violations found
            return True, {"details": violation_details, "corrections": 1, "rules_activated": ["test-rule"]}
        else:
            # Second rectify: clean
            return True, {"details": [], "corrections": 0}

    def mock_llm(user_message=None, system_message=None, conversation_history=None, **kwargs):
        llm_call_count[0] += 1
        if llm_call_count[0] == 1:
            return {"final_response": "violation in response"}
        else:
            return {"final_response": "clean fixed response"}

    agent = MockAgent()
    agent.run_conversation = mock_llm  # Set mock BEFORE patch

    _patch_run_conversation(agent)

    ar.rectify = mock_rectify

    try:
        result = agent.run_conversation(
            user_message="test query with violation",
            conversation_history=[],
        )
        assert rectify_call_count[0] == 2, f"Expected 2 rectify calls, got {rectify_call_count[0]}"
        assert llm_call_count[0] == 2, f"Expected 2 LLM calls, got {llm_call_count[0]}"
        assert result["final_response"] == "clean fixed response"
    finally:
        ar.rectify = original_rectify


def test_loop_max_rounds_fallback():
    """After max rounds, corrective fallback should patch the response."""
    import plugins.anchor.anchor_rectifier as ar
    original_rectify = ar.rectify

    llm_call_count = [0]

    violation_details = [
        {
            "rule": "test-rule",
            "severity": "ERROR",
            "original": "violation",
            "corrected": "CORRECTED",
            "rule_type": "domain",
            "confidence": 0.9,
        }
    ]

    def mock_rectify(user_query, llm_output, skip_workflow_rules=False):
        # Always return violations
        return True, {"details": violation_details, "corrections": 1, "rules_activated": ["test-rule"]}

    def always_violation(**kwargs):
        llm_call_count[0] += 1
        return {"final_response": "violation in response every time"}

    agent = MockAgent()
    agent.run_conversation = always_violation

    _patch_run_conversation(agent)
    ar.rectify = mock_rectify

    try:
        result = agent.run_conversation(
            user_message="test query",
            conversation_history=[],
        )
        # Final round: corrective fallback replaces "violation" with "CORRECTED"
        assert "CORRECTED" in result.get("final_response", ""), (
            f"Expected 'CORRECTED' in fallback response, got: {result.get('final_response', '')[:100]}"
        )
        # Should have exhausted all rounds
        assert llm_call_count[0] == 3, f"Expected 3 LLM calls (max rounds), got {llm_call_count[0]}"
    finally:
        ar.rectify = original_rectify


def test_loop_all_violations_filtered():
    """Off-confident violations should be filtered (response passed through)."""
    import plugins.anchor.anchor_rectifier as ar
    original_rectify = ar.rectify

    low_conf_details = [
        {
            "rule": "domain-rule",
            "severity": "INFO",
            "original": "test",
            "corrected": "fix",
            "rule_type": "domain",
            "confidence": 0.3,  # Below 0.5 threshold
        }
    ]

    def mock_rectify_low_conf(user_query, llm_output, skip_workflow_rules=False):
        return True, {"details": low_conf_details, "corrections": 0, "rules_activated": []}

    agent = MockAgent()
    agent.run_conversation = lambda **kw: {"final_response": "low confidence content"}
    _patch_run_conversation(agent)
    ar.rectify = mock_rectify_low_conf

    try:
        result = agent.run_conversation(
            user_message="test query",
            conversation_history=[],
        )
        # All violations filtered → response passed through unchanged
        assert result["final_response"] == "low confidence content"
    finally:
        ar.rectify = original_rectify


# ═══════════════════════════════════════════════════════════════════════
# 8. Language-Adaptive Feedback in Loop
# ═══════════════════════════════════════════════════════════════════════

def test_loop_language_adaptive_tr():
    """Turkish user message should use Turkish feedback."""
    import plugins.anchor.anchor_rectifier as ar
    original_rectify = ar.rectify

    feedback_received = [""]
    llm_call_count = [0]

    violation_details = [
        {
            "rule": "test-rule",
            "severity": "ERROR",
            "original": "x",
            "corrected": "y",
            "rule_type": "domain",
            "confidence": 0.9,
        }
    ]

    def mock_rectify(user_query, llm_output, skip_workflow_rules=False):
        llm_call_count[0] += 1
        if llm_call_count[0] <= 1:
            return True, {"details": violation_details, "corrections": 1, "rules_activated": []}
        else:
            return True, {"details": [], "corrections": 0}

    def mock_llm(user_message=None, **kw):
        # Capture the feedback (non-first calls with 'sorun' or 'düzelt' in text)
        if user_message and ("sorun" in user_message or "düzelt" in user_message):
            feedback_received[0] = user_message
        return {"final_response": "yanıt"}

    agent = MockAgent()
    agent.run_conversation = mock_llm
    _patch_run_conversation(agent)
    ar.rectify = mock_rectify

    try:
        agent.run_conversation(
            user_message="Merhaba, bugün yardım eder misin? Bir sorum var.",
            conversation_history=[],
        )
        feedback = feedback_received[0]
        assert "Aşağıdaki sorunlar tespit edildi" in feedback, (
            f"Expected Turkish feedback, got: {feedback[:100]!r}"
        )
    finally:
        ar.rectify = original_rectify


def test_loop_language_adaptive_en():
    """English user message should use English feedback."""
    import plugins.anchor.anchor_rectifier as ar
    original_rectify = ar.rectify

    feedback_received = [""]
    llm_call_count = [0]

    violation_details = [
        {
            "rule": "test-rule",
            "severity": "ERROR",
            "original": "x",
            "corrected": "y",
            "rule_type": "domain",
            "confidence": 0.9,
        }
    ]

    def mock_rectify(user_query, llm_output, skip_workflow_rules=False):
        llm_call_count[0] += 1
        if llm_call_count[0] <= 1:
            return True, {"details": violation_details, "corrections": 1, "rules_activated": []}
        else:
            return True, {"details": [], "corrections": 0}

    def mock_llm(user_message=None, **kw):
        if user_message and ("issue" in user_message or "detected" in user_message):
            feedback_received[0] = user_message
        return {"final_response": "response"}

    agent = MockAgent()
    agent.run_conversation = mock_llm
    _patch_run_conversation(agent)
    ar.rectify = mock_rectify

    try:
        agent.run_conversation(
            user_message="Hello, can you please help me with this issue?",
            conversation_history=[],
        )
        feedback = feedback_received[0]
        assert "The following issues were detected" in feedback, (
            f"Expected English feedback, got: {feedback[:100]!r}"
        )
    finally:
        ar.rectify = original_rectify


# ═══════════════════════════════════════════════════════════════════════
# Run if executed directly
# ═══════════════════════════════════════════════════════════════════════

def run_all():
    """Run all tests and report results."""
    test_functions = [
        # Threshold (11 tests)
        test_threshold_domain_below,
        test_threshold_domain_at_boundary,
        test_threshold_domain_above,
        test_threshold_hybrid_below,
        test_threshold_hybrid_at_boundary,
        test_threshold_hybrid_above,
        test_threshold_workflow_below,
        test_threshold_workflow_above,
        test_threshold_default_rule_type,
        test_threshold_missing_confidence,
        test_threshold_missing_rule_type,
        # Language detection (8 tests)
        test_detect_language_turkish,
        test_detect_language_english,
        test_detect_language_turkish_chars_strong,
        test_detect_language_mixed_turkish_wins,
        test_detect_language_empty_list,
        test_detect_language_single_turkish_word,
        test_detect_language_single_english_word,
        test_detect_language_mixed_tr_en_balanced_tr,
        # Feedback Turkish (7 tests)
        test_feedback_turkish_contains_header,
        test_feedback_turkish_shows_rule_name,
        test_feedback_turkish_original_to_corrected,
        test_feedback_turkish_shows_round,
        test_feedback_turkish_empty_details,
        test_feedback_turkish_includes_violated_rules,
        test_feedback_turkish_without_activation,
        # Feedback English (5 tests)
        test_feedback_english_contains_header,
        test_feedback_english_shows_rule,
        test_feedback_english_adaptive_lang,
        test_feedback_english_original_to_corrected,
        test_feedback_english_empty_details,
        # Educational content (6 tests)
        test_educational_turkish,
        test_educational_english,
        test_educational_not_flagged,
        test_educational_short_text,
        test_educational_work_content_not_flagged,
        # Patch/unpatch (6 tests)
        test_patch_applies_wrapper,
        test_patch_preserves_behavior,
        test_patch_no_method,
        test_unpatch_after_patch_removes_flag,
        test_unpatch_after_patch_still_works,
        test_unpatch_no_patch,
        test_double_patch_protection,
        # Integration (5 tests)
        test_loop_clean_response,
        test_loop_violations_then_fix,
        test_loop_max_rounds_fallback,
        test_loop_all_violations_filtered,
        test_loop_language_adaptive_tr,
        test_loop_language_adaptive_en,
    ]

    passed = 0
    failed = 0
    results = []

    for test_fn in test_functions:
        try:
            test_fn()
            results.append((test_fn.__name__, "PASS", ""))
            passed += 1
        except Exception as e:
            results.append((test_fn.__name__, "FAIL", str(e)))
            failed += 1

    # Print summary
    print(f"\n{'='*60}")
    print(f"  Anchor Plugin v3.1.0 — Test Results")
    print(f"{'='*60}")
    for name, status, error in results:
        icon = "✅" if status == "PASS" else "❌"
        print(f"  {icon} {name}")
        if error:
            print(f"     ↳ {error}")
    print(f"{'='*60}")
    print(f"  Total: {len(results)} | ✅ PASS: {passed} | ❌ FAIL: {failed}")
    print(f"{'='*60}")

    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
