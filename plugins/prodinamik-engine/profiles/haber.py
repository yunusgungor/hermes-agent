"""
Prodinamik Engine v1.8 — Haber (News) Profile

Haber-Kurator (v3.1.0) 8-state news lifecycle: captured → fact_checking →
cross_verified → published → correction_needed → corrected/retracted → archived.

4-tier source credibility system, cross-verification (2+ independent sources),
hallucination protection, correction workflow.
"""

from engine.profile import ProductProfile, ValidatorDef, ValidatorTier, AdapterDef, Budget, StoreDef, TemplateDef

HABER_SM = """
profile: haber
name: haber-kurator
version: 3.1.0

formal_properties:
  termination:
    max_steps: 30

states:
  captured:
    type: initial
    max_reentries: 1
    timeout: 3600           # 1h — hızlı haber döngüsü
    validators: ["NewsQualityCheck"]

  fact_checking:
    type: intermediate
    max_reentries: 3
    timeout: 7200           # 2h — cross-verification süresi
    validators: ["CrossVerifyCheck"]
    temporal:
      max_duration: 14400
      reminders:
        - after: 7200
          message: "2 saat geçti — fakt-check hala sürüyor"

  cross_verified:
    type: intermediate
    max_reentries: 3
    timeout: 3600           # 1h — publish kararı
    validators: ["HallucinationCheck", "SourceAttributionCheck"]
    requires_manual: true

  published:
    type: intermediate
    max_reentries: 1
    timeout: 86400          # 24h — feedback penceresi

  correction_needed:
    type: intermediate
    max_reentries: 2
    timeout: 7200           # 2h — düzeltme zamanı
    validators: ["CorrectionCheck"]

  corrected:
    type: intermediate
    max_reentries: 2
    timeout: 3600

  retracted:
    type: intermediate
    max_reentries: 0

  archived:
    type: intermediate
    max_reentries: 0

transitions:
  captured -> fact_checking: {type: REVERSIBLE}

  fact_checking -> cross_verified: {type: REVERSIBLE, condition: "all_sources_agree"}
  fact_checking -> captured: {type: REVERSIBLE, condition: "insufficient_sources"}

  cross_verified -> captured: {type: REVERSIBLE, condition: "rejected"}
  cross_verified -> published: {type: COMPENSABLE, condition: "human_approved"}

  published -> correction_needed: {type: REVERSIBLE, condition: "error_detected"}
  published -> archived: {type: REVERSIBLE, condition: "normal_archive"}

  correction_needed -> corrected: {type: REVERSIBLE, condition: "fix_issued"}
  correction_needed -> retracted: {type: IRREVERSIBLE, condition: "story_retracted"}

  corrected -> published: {type: REVERSIBLE, condition: "correction_published"}

  retracted -> archived: {type: REVERSIBLE}

  archived -> correction_needed: {type: REVERSIBLE, condition: "new_evidence"}
"""


class HaberProfile(ProductProfile):
    """News verification lifecycle: captured → fact_checking → cross_verified →
    published → correction_needed → corrected/retracted → archived"""

    name = "haber"
    version = "3.1.0"
    description = "News verification pipeline: 8-state lifecycle with 122 slop patterns, cross-verification, hallucination guard"
    state_machine_yaml = HABER_SM

    def setup_validators(self):
        # Tier 1 — Deterministic
        self.add_validator(ValidatorDef(
            name="NewsQualityCheck", tier=ValidatorTier.T1, critical=True,
        ))
        self.add_validator(ValidatorDef(
            name="CrossVerifyCheck", tier=ValidatorTier.T1, critical=True,
            timeout_seconds=60,
        ))
        self.add_validator(ValidatorDef(
            name="SourceAttributionCheck", tier=ValidatorTier.T1, critical=True,
        ))
        self.add_validator(ValidatorDef(
            name="CorrectionCheck", tier=ValidatorTier.T1, critical=True,
        ))

        # Tier 2 — Parallel LLM
        self.add_validator(ValidatorDef(
            name="HallucinationCheck", tier=ValidatorTier.T2, critical=True,
            timeout_seconds=180,
        ))
        self.add_validator(ValidatorDef(
            name="SlopScanNews", tier=ValidatorTier.T2, critical=False,
            timeout_seconds=120,
        ))

        # Tier 3 — Sequential
        self.add_validator(ValidatorDef(
            name="FullNewsPipeline", tier=ValidatorTier.T3, critical=True,
            timeout_seconds=300,
            depends_on=["CrossVerifyCheck", "HallucinationCheck", "SourceAttributionCheck"],
        ))

    def setup_adapters(self):
        self.add_adapter(AdapterDef(
            name="MemosPublish", type="api",
            config={"protocol": "api", "endpoint": "https://memos.googig.cloud"},
            fallback_mode="file",
            max_retries=3,
            circuit_breaker_threshold=3,
        ))
        self.add_adapter(AdapterDef(
            name="RSSFetch", type="rss",
            config={"sources": ["Reuters", "AP", "AFP", "BBC", "Bloomberg"]},
            max_retries=2,
        ))
        self.add_adapter(AdapterDef(
            name="FileOutput", type="file",
            fallback_mode="file",
        ))

    def setup_stores(self):
        self.add_store(StoreDef(name="idea", type="markdown", path="idea.md", required=True))
        self.add_store(StoreDef(name="context", type="markdown", path="context.md", required=False))
        self.add_store(StoreDef(name="brief", type="markdown", path="brief.md", required=True))
        self.add_store(StoreDef(name="draft", type="markdown", path="draft-package.md", required=False))
        self.add_store(StoreDef(name="fact_check", type="markdown", path="fact-check-report.md", required=True))
        self.add_store(StoreDef(name="haber_object", type="markdown", path="haber-object.md", required=True))
        self.add_store(StoreDef(name="feedback", type="markdown", path="feedback.md", required=False))

    def setup_templates(self):
        self.add_template(TemplateDef(
            name="idea-template", path="templates/idea-template.md",
            description="News idea capture template",
        ))
        self.add_template(TemplateDef(
            name="fact-check-template", path="templates/fact-check-template.md",
            description="Fact-check report template",
        ))

    def setup_budget(self):
        self._budget = Budget(
            max_concurrent_validators=3,
            max_llm_calls_per_run=15,
            max_storage_mb=50,
            timeout_per_state=7200,
            soft_limit_usd=0.5,
            hard_limit_usd=2.0,
        )

    @property
    def transition_map(self) -> dict:
        return {
            "captured": ["fact_checking"],
            "fact_checking": ["cross_verified", "captured"],
            "cross_verified": ["captured", "published"],
            "published": ["correction_needed", "archived"],
            "correction_needed": ["corrected", "retracted"],
            "corrected": ["published"],
            "retracted": ["archived"],
            "archived": ["correction_needed"],
        }


# ──────────────────────────────────────────────
# Quick Self-Test
# ──────────────────────────────────────────────

def demo():
    profile = HaberProfile()
    profile.initialize()

    print("📦 HaberProfile loaded:")
    print(f"   Name: {profile.name} v{profile.version}")
    print(f"   Description: {profile.description}")
    print(f"   SM states: {list(profile.state_machine.config.states.keys())}")
    print(f"   Initial: {profile.state_machine.config.initial_states[0].name}")
    print(f"   Terminal: {[s.name for s in profile.state_machine.config.terminal_states]}")
    print(f"   Validators: {len(profile.validators)} ({len(profile.tier1_validators)}T1 + {len(profile.tier2_validators)}T2 + {len(profile.tier3_validators)}T3)")
    print(f"   Adapters: {[a.name for a in profile.adapters]}")
    print(f"   Stores: {[s.name for s in profile.stores]}")

    # Test transitions
    sm = profile.state_machine
    print("\n🔄 Lifecycle walkthrough:")
    lifecycle = [
        ("captured", "fact_checking"),
        ("fact_checking", "cross_verified"),
        ("cross_verified", "published"),
        ("published", "correction_needed"),
        ("correction_needed", "corrected"),
        ("corrected", "published"),
        ("published", "archived"),
    ]
    all_ok = True
    for from_s, to_s in lifecycle:
        allowed, reason = sm.can_transition(from_s, to_s)
        ok = "✅" if allowed else "❌"
        if not allowed:
            all_ok = False
        print(f"   {from_s:25s} → {to_s:25s} {ok} ({reason})")

    # Test retraction path
    print("\n🔄 Retraction path:")
    allowed, reason = sm.can_transition("correction_needed", "retracted")
    print(f"   correction_needed → retracted: {'✅' if allowed else '❌'} ({reason})")
    allowed, reason = sm.can_transition("retracted", "archived")
    print(f"   retracted → archived: {'✅' if allowed else '❌'} ({reason})")

    # Test error recovery
    print("\n🔄 Error recovery:")
    allowed, reason = sm.can_transition("archived", "correction_needed")
    print(f"   archived → correction_needed: {'✅' if allowed else '❌'} ({reason})")

    print(f"\n{'='*50}")
    print(f"{'✅ All transitions valid!' if all_ok else '❌ Some transitions failed!'}")
    print(f"{'='*50}")


if __name__ == "__main__":
    demo()
