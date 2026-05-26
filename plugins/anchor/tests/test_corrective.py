"""
⚓ Anchor Corrective Mode — Test Suite

Tests for the apply_corrections() function that replaces LLM output
text in-place based on Anchor's correction report.

TDD: These tests are written BEFORE the implementation (RED).
"""

import sys
import os

# Ensure plugin is importable
PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PLUGIN_DIR not in sys.path:
    sys.path.insert(0, os.path.dirname(PLUGIN_DIR))  # for plugins.anchor
if os.path.dirname(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, os.path.dirname(PLUGIN_DIR))

from plugins.anchor.anchor_rectifier import apply_corrections


# ═══════════════════════════════════════════════════════════════════
# 1. Basic Replacement
# ═══════════════════════════════════════════════════════════════════

def test_simple_text_replacement():
    """Domain correction replaces a phrase in the LLM output."""
    llm_output = "git commit -m 'yaptığım değişiklikler' yeterlidir"
    report = {
        "corrections": 1,
        "details": [{
            "original": "yaptığım değişiklikler",
            "corrected": "feat: yaptığım değişiklikler",
            "rule": "conventional-commits",
            "rule_type": "domain",
            "confidence": 0.92,
            "severity": "ERROR",
        }],
    }
    result, count = apply_corrections(llm_output, report)
    assert count == 1, f"Expected 1 replacement, got {count}"
    assert "feat: yaptığım değişiklikler" in result
    # Corrected text contains original as substring, so check the full text
    assert result == "git commit -m 'feat: yaptığım değişiklikler' yeterlidir"


def test_single_occurrence_only():
    """Only the FIRST occurrence is replaced when text appears multiple times."""
    llm_output = "hatalı metin burada ve hatalı metin orada da var"
    report = {
        "corrections": 1,
        "details": [{
            "original": "hatalı metin",
            "corrected": "doğru metin",
            "rule": "test-rule",
            "rule_type": "domain",
            "confidence": 0.85,
        }],
    }
    result, count = apply_corrections(llm_output, report)
    assert count == 1
    assert result == "doğru metin burada ve hatalı metin orada da var"


# ═══════════════════════════════════════════════════════════════════
# 2. Confidence Threshold Filtering
# ═══════════════════════════════════════════════════════════════════

def test_low_confidence_skipped():
    """Corrections below confidence threshold are NOT applied."""
    llm_output = "bir miktar hatalı ifade"
    report = {
        "corrections": 1,
        "details": [{
            "original": "hatalı ifade",
            "corrected": "doğru ifade",
            "rule": "test-rule",
            "rule_type": "domain",
            "confidence": 0.3,  # Below 0.5 domain threshold
        }],
    }
    result, count = apply_corrections(llm_output, report)
    assert count == 0, f"Expected 0 replacements, got {count}"
    assert result == llm_output  # Unchanged


def test_domain_threshold_boundary():
    """Domain threshold is 0.5 — exactly at threshold should pass."""
    llm_output = "sınırda bir ifade"
    report = {
        "corrections": 1,
        "details": [{
            "original": "sınırda bir ifade",
            "corrected": "düzeltilmiş ifade",
            "rule": "test-rule",
            "rule_type": "domain",
            "confidence": 0.5,  # Exactly at domain threshold
        }],
    }
    result, count = apply_corrections(llm_output, report)
    assert count == 1


def test_hybrid_threshold_higher():
    """Hybrid rules need 0.7 confidence to apply corrective."""
    llm_output = "hibrit kural tetiklendi"
    report = {
        "corrections": 1,
        "details": [{
            "original": "hibrit kural",
            "corrected": "düzeltilmiş kural",
            "rule": "hybrid-rule",
            "rule_type": "hybrid",
            "confidence": 0.6,  # Below 0.7 hybrid threshold
        }],
    }
    result, count = apply_corrections(llm_output, report)
    assert count == 0
    
    # Now with high enough confidence
    report["details"][0]["confidence"] = 0.75
    result, count = apply_corrections(llm_output, report)
    assert count == 1


def test_workflow_threshold():
    """Workflow rules need 0.8 confidence for corrective."""
    llm_output = "workflow adımı yanlış"
    report = {
        "corrections": 1,
        "details": [{
            "original": "workflow adımı",
            "corrected": "doğru adım",
            "rule": "wf-rule",
            "rule_type": "workflow",
            "confidence": 0.75,  # Below 0.8 workflow threshold
        }],
    }
    result, count = apply_corrections(llm_output, report)
    assert count == 0
    
    # Now with high enough confidence
    report["details"][0]["confidence"] = 0.85
    result, count = apply_corrections(llm_output, report)
    assert count == 1


# ═══════════════════════════════════════════════════════════════════
# 3. Multiple Corrections
# ═══════════════════════════════════════════════════════════════════

def test_multiple_corrections():
    """Multiple independent corrections all applied."""
    llm_output = "ilk hata ve ikinci hata burada"
    report = {
        "corrections": 2,
        "details": [
            {
                "original": "ilk hata",
                "corrected": "ilk düzeltme",
                "rule": "rule-1",
                "rule_type": "domain",
                "confidence": 0.9,
            },
            {
                "original": "ikinci hata",
                "corrected": "ikinci düzeltme",
                "rule": "rule-2",
                "rule_type": "domain",
                "confidence": 0.85,
            },
        ],
    }
    result, count = apply_corrections(llm_output, report)
    assert count == 2
    assert "ilk düzeltme" in result
    assert "ikinci düzeltme" in result
    assert "ilk hata" not in result
    assert "ikinci hata" not in result


def test_partial_filtering():
    """Only corrections above threshold are applied, others skipped."""
    llm_output = "yüksek güven ve düşük güven"
    report = {
        "corrections": 2,
        "details": [
            {
                "original": "yüksek güven",
                "corrected": "YG",
                "rule": "rule-1",
                "rule_type": "domain",
                "confidence": 0.95,
            },
            {
                "original": "düşük güven",
                "corrected": "DG",
                "rule": "rule-2",
                "rule_type": "domain",
                "confidence": 0.3,  # Below threshold
            },
        ],
    }
    result, count = apply_corrections(llm_output, report)
    assert count == 1
    assert "YG" in result
    assert "düşük güven" in result  # Unchanged


# ═══════════════════════════════════════════════════════════════════
# 4. Edge Cases
# ═══════════════════════════════════════════════════════════════════

def test_empty_report():
    """No report returns original text unchanged."""
    result, count = apply_corrections("hello world", None)
    assert count == 0
    assert result == "hello world"


def test_empty_details():
    """Empty details list means no corrections."""
    report = {"corrections": 0, "details": []}
    result, count = apply_corrections("hello world", report)
    assert count == 0
    assert result == "hello world"


def test_original_not_found():
    """If original text is not in the output, skip gracefully."""
    llm_output = "tamamen farklı metin"
    report = {
        "corrections": 1,
        "details": [{
            "original": "bu metin yok",
            "corrected": "düzeltme",
            "rule": "rule",
            "rule_type": "domain",
            "confidence": 0.9,
        }],
    }
    result, count = apply_corrections(llm_output, report)
    assert count == 0
    assert result == llm_output


def test_identical_original_corrected():
    """No replacement if original == corrected."""
    llm_output = "bir metin"
    report = {
        "corrections": 1,
        "details": [{
            "original": "bir metin",
            "corrected": "bir metin",  # Same!
            "rule": "rule",
            "rule_type": "domain",
            "confidence": 0.9,
        }],
    }
    result, count = apply_corrections(llm_output, report)
    assert count == 0
    assert result == llm_output


def test_empty_original_or_corrected():
    """Empty strings in original/corrected should not cause errors."""
    llm_output = "test metni"
    report = {
        "corrections": 1,
        "details": [{
            "original": "",
            "corrected": "düzeltme",
            "rule": "rule",
            "rule_type": "domain",
            "confidence": 0.9,
        }],
    }
    result, count = apply_corrections(llm_output, report)
    assert count == 0


def test_long_text_preservation():
    """Full original/corrected text (not truncated) is used for replacement."""
    long_orig = "bu çok uzun bir cümle ki anchor engine bunu tespit etti ve düzeltilmesi gerekiyor" * 3
    long_corr = "bu düzeltilmiş uzun cümle ki artık doğru" * 3
    llm_output = f"başlangıç {long_orig} bitiş"
    report = {
        "corrections": 1,
        "details": [{
            "original": long_orig,
            "corrected": long_corr,
            "rule": "rule",
            "rule_type": "domain",
            "confidence": 0.95,
        }],
    }
    result, count = apply_corrections(llm_output, report)
    assert count == 1
    assert long_orig not in result
    assert long_corr in result


# ═══════════════════════════════════════════════════════════════════
# 5. Custom Confidence Thresholds
# ═══════════════════════════════════════════════════════════════════

def test_custom_thresholds():
    """Custom confidence thresholds can be passed."""
    llm_output = "özel eşik testi"
    report = {
        "corrections": 1,
        "details": [{
            "original": "özel eşik",
            "corrected": "custom threshold",
            "rule": "rule",
            "rule_type": "domain",
            "confidence": 0.7,  # Below default 0.5? No, above. Let's use 0.95
        }],
    }
    # Use very strict custom threshold
    custom = {"domain": 0.99, "hybrid": 0.99, "workflow": 0.99}
    result, count = apply_corrections(llm_output, report, confidence_threshold=custom)
    assert count == 0  # 0.7 < 0.99
    
    # Now with lenient threshold
    lenient = {"domain": 0.1, "hybrid": 0.1, "workflow": 0.1}
    result, count = apply_corrections(llm_output, report, confidence_threshold=lenient)
    assert count == 1


# ═══════════════════════════════════════════════════════════════════
# 6. Integration: Full Wrapper Behavior
# ═══════════════════════════════════════════════════════════════════

def test_corrective_mode_no_annotation_appended():
    """In corrective mode, the annotation should NOT be appended to output.
    
    The wrapper should replace text inline; the user sees corrected output
    without any ⚓ marker visible.
    """
    llm_output = "git add ve git commit yapın yeterli"
    report = {
        "corrections": 1,
        "details": [{
            "original": "git commit yapın yeterli",
            "corrected": "git commit -m 'mesaj' yapın",
            "rule": "conventional-commits",
            "rule_type": "domain",
            "confidence": 0.9,
        }],
    }
    result, count = apply_corrections(llm_output, report)
    assert count == 1
    # Warning: assert not in "yeterli" — the replacement removed it
    assert "git commit -m 'mesaj' yapın" in result
    # No annotation markers in corrective output
    assert "⚓" not in result


# ═══════════════════════════════════════════════════════════════════
# Run all
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Collect all test functions
    tests = [
        (test_simple_text_replacement, "test_simple_text_replacement"),
        (test_single_occurrence_only, "test_single_occurrence_only"),
        (test_low_confidence_skipped, "test_low_confidence_skipped"),
        (test_domain_threshold_boundary, "test_domain_threshold_boundary"),
        (test_hybrid_threshold_higher, "test_hybrid_threshold_higher"),
        (test_workflow_threshold, "test_workflow_threshold"),
        (test_multiple_corrections, "test_multiple_corrections"),
        (test_partial_filtering, "test_partial_filtering"),
        (test_empty_report, "test_empty_report"),
        (test_empty_details, "test_empty_details"),
        (test_original_not_found, "test_original_not_found"),
        (test_identical_original_corrected, "test_identical_original_corrected"),
        (test_empty_original_or_corrected, "test_empty_original_or_corrected"),
        (test_long_text_preservation, "test_long_text_preservation"),
        (test_custom_thresholds, "test_custom_thresholds"),
        (test_corrective_mode_no_annotation_appended, "test_corrective_mode_no_annotation_appended"),
    ]
    
    passed = 0
    failed = 0
    
    print("╔══════════════════════════════════════════════╗")
    print("║  ⚓ Anchor Corrective Mode — Test Suite     ║")
    print("╚══════════════════════════════════════════════╝")
    print()
    
    for test_fn, test_name in tests:
        try:
            test_fn()
            print(f"  ✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {test_name}: {e}")
            failed += 1
    
    print()
    print(f"  {'─' * 40}")
    print(f"  📊 Results: {passed} passed, {failed} failed, {len(tests)} total")
    print()
    
    if failed > 0:
        print("  ⚠️  Implementation needed — these tests should fail (RED phase)")
        sys.exit(1)
    else:
        print("  ✅ All tests pass — implementation is complete (GREEN)")
