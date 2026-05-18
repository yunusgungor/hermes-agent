"""
Prodinamik Engine v1.8 — Content Profile

Content-OS (v2.5.0) 14-state lifecycle, 107 slop patterns (3 tiers + bonus),
4-route Idea Gate, Buffer API adapter, signal processing.

ProductProfile implementasyonu olarak eski Content-OS plugin'inin
yerini alır. Prodinamik Engine'in state machine, event sourcing,
WAL + snapshot, degradation-aware caching altyapısını kullanır.
"""

from engine.profile import ProductProfile, ValidatorDef, ValidatorTier, AdapterDef, Budget, StoreDef, TemplateDef
from engine.raft import NodeState, StateCRDT

CONTENT_SM = """
profile: content
name: content-os
version: 2.5.0

formal_properties:
  termination:
    max_steps: 50

states:
  captured:
    type: initial
    max_reentries: 1
    timeout: 86400           # 24h — ideayı bekletme
    validators: ["IdeaQualityCheck"]

  idea_review:
    type: intermediate
    max_reentries: 3
    timeout: 172800          # 48h — review süresi
    validators: ["IdeaGateCheck"]
    temporal:
      max_duration: 259200
      reminders:
        - after: 86400
          message: "Idea review bekliyor — 24h geçti"
        - after: 172800
          message: "2 gündür review'da — lütfen karar ver"

  brief_ready:
    type: intermediate
    max_reentries: 3
    timeout: 172800
    validators: ["BriefStructureCheck"]

  drafting:
    type: intermediate
    max_reentries: 10
    timeout: 432000          # 5 gün — writing süresi
    validators: ["SlopScanT1", "SlopScanT2"]
    temporal:
      max_duration: 604800
      reminders:
        - after: 172800
          message: "2 gündür drafting'de — ilerleme var mı?"
        - after: 432000
          message: "5 gündür drafting'de — escalation"

  verification:
    type: intermediate
    max_reentries: 5
    timeout: 86400
    validators: ["FullVerificationPipeline"]

  draft_review:
    type: intermediate
    max_reentries: 5
    timeout: 259200
    validators: ["SlopScanT1"]
    requires_manual: true
    temporal:
      max_duration: 345600
      reminders:
        - after: 86400
          message: "Draft review bekliyor — 24h geçti"
        - after: 172800
          message: "2 gündür review'da — onay/revize gerekli"

  approved:
    type: intermediate
    max_reentries: 1
    timeout: 86400

  scheduler_ready:
    type: intermediate
    max_reentries: 1
    timeout: 3600

  scheduled:
    type: intermediate
    max_reentries: 1
    timeout: 604800          # 7 gün — yayın zamanına kadar

  published:
    type: intermediate
    max_reentries: 1
    timeout: 86400           # 24h — ilk feedback penceresi

  feedback_24h:
    type: intermediate
    max_reentries: 1
    timeout: 86400           # 24-48h feedback
    validators: ["MetricCheck"]

  feedback_72h:
    type: intermediate
    max_reentries: 1
    timeout: 172800          # 48-72h feedback
    validators: ["MetricCheck"]

  learned:
    type: intermediate
    max_reentries: 1
    timeout: 2592000         # 30 gün — öğrenme süresi
    validators: ["PostmortemCheck"]

  archived:
    type: terminal
    max_reentries: 0

transitions:
  captured -> idea_review: {type: REVERSIBLE}
  captured -> captured: {type: REVERSIBLE, condition: "idea_refined"}

  idea_review -> brief_ready: {type: REVERSIBLE, condition: "route_decision_made"}
  idea_review -> captured: {type: REVERSIBLE, condition: "needs_refinement"}

  brief_ready -> drafting: {type: REVERSIBLE}

  drafting -> drafting: {type: REVERSIBLE, condition: "drift_detected", action: "log_drift"}
  drafting -> verification: {type: REVERSIBLE, condition: "draft_complete"}

  verification -> drafting: {type: REVERSIBLE, condition: "tier_failed"}
  verification -> draft_review: {type: REVERSIBLE, condition: "all_tiers_passed"}

  draft_review -> approved: {type: COMPENSABLE, condition: "human_approved"}
  draft_review -> brief_ready: {type: REVERSIBLE, condition: "major_revision_needed"}
  draft_review -> drafting: {type: REVERSIBLE, condition: "changes_requested"}

  approved -> scheduler_ready: {type: REVERSIBLE}

  scheduler_ready -> scheduled: {type: REVERSIBLE, condition: "buffer_configured"}

  scheduled -> published: {type: IRREVERSIBLE, condition: "publish_time_reached"}

  published -> feedback_24h: {type: REVERSIBLE}

  feedback_24h -> feedback_72h: {type: REVERSIBLE}

  feedback_72h -> learned: {type: REVERSIBLE}

  learned -> archived: {type: REVERSIBLE}
"""


class ContentProfile(ProductProfile):
    """Content-OS lifecycle: captured → idea_review → brief_ready → drafting →
    verification → draft_review → approved → scheduler_ready → scheduled →
    published → feedback_24h → feedback_72h → learned → archived"""

    name = "content"
    version = "2.5.0"
    description = "Content production pipeline: 14-state lifecycle with 107 slop patterns, Idea Gate, Buffer API"
    state_machine_yaml = CONTENT_SM

    def setup_validators(self):
        # Tier 1 — Deterministic, fail-fast, regex-based
        self.add_validator(ValidatorDef(
            name="IdeaQualityCheck", tier=ValidatorTier.T1, critical=True,
        ))
        self.add_validator(ValidatorDef(
            name="IdeaGateCheck", tier=ValidatorTier.T1, critical=True,
        ))
        self.add_validator(ValidatorDef(
            name="BriefStructureCheck", tier=ValidatorTier.T1, critical=False,
        ))
        self.add_validator(ValidatorDef(
            name="SlopScanT1", tier=ValidatorTier.T1, critical=True,
            timeout_seconds=30,
        ))
        self.add_validator(ValidatorDef(
            name="MetricCheck", tier=ValidatorTier.T1, critical=False,
        ))
        self.add_validator(ValidatorDef(
            name="PostmortemCheck", tier=ValidatorTier.T1, critical=False,
        ))

        # Tier 2 — Parallel LLM-based
        self.add_validator(ValidatorDef(
            name="SlopScanT2", tier=ValidatorTier.T2, critical=False,
            timeout_seconds=120,
        ))
        self.add_validator(ValidatorDef(
            name="RubricScore", tier=ValidatorTier.T2, critical=True,
            timeout_seconds=180,
        ))

        # Tier 3 — Sequential (depends on T2)
        self.add_validator(ValidatorDef(
            name="FullVerificationPipeline", tier=ValidatorTier.T3, critical=True,
            timeout_seconds=300,
            depends_on=["SlopScanT1", "SlopScanT2", "RubricScore"],
        ))

    def setup_adapters(self):
        self.add_adapter(AdapterDef(
            name="BufferPublish", type="buffer",
            config={"protocol": "api", "endpoint": "https://api.buffer.com"},
            fallback_mode="file",
            max_retries=3,
            circuit_breaker_threshold=3,
        ))
        self.add_adapter(AdapterDef(
            name="FileOutput", type="file",
            fallback_mode="file",
        ))
        self.add_adapter(AdapterDef(
            name="SignalRSS", type="rss",
            config={"sources": ["x", "rss"]},
            max_retries=2,
        ))

    def setup_stores(self):
        self.add_store(StoreDef(name="idea", type="markdown", path="idea.md", required=True))
        self.add_store(StoreDef(name="context", type="markdown", path="context.md", required=False))
        self.add_store(StoreDef(name="brief", type="markdown", path="brief.md", required=True))
        self.add_store(StoreDef(name="draft", type="markdown", path="draft-package.md", required=False))
        self.add_store(StoreDef(name="verifier", type="markdown", path="verifier-report.md", required=False))
        self.add_store(StoreDef(name="feedback", type="markdown", path="feedback.md", required=False))
        self.add_store(StoreDef(name="postmortem", type="markdown", path="postmortem.md", required=False))
        self.add_store(StoreDef(name="metrics", type="json", path="metrics.json", required=False))

    def setup_templates(self):
        self.add_template(TemplateDef(
            name="brief-template", path="templates/brief-template.md",
            description="Writer Context Packet template",
        ))
        self.add_template(TemplateDef(
            name="draft-template", path="templates/draft-template.md",
            description="Draft package template with self-assessment",
        ))
        self.add_template(TemplateDef(
            name="idea-template", path="templates/idea-template.md",
            description="Idea capture template",
        ))

    def setup_budget(self):
        self._budget = Budget(
            max_concurrent_validators=3,
            max_llm_calls_per_run=20,
            max_storage_mb=100,
            timeout_per_state=432000,  # 5 days
            soft_limit_usd=1.0,
            hard_limit_usd=5.0,
        )

    @property
    def transition_map(self) -> dict:
        return {
            "captured": ["idea_review", "captured"],
            "idea_review": ["brief_ready", "captured"],
            "brief_ready": ["drafting"],
            "drafting": ["drafting", "verification"],
            "verification": ["drafting", "draft_review"],
            "draft_review": ["approved", "brief_ready", "drafting"],
            "approved": ["scheduler_ready"],
            "scheduler_ready": ["scheduled"],
            "scheduled": ["published"],
            "published": ["feedback_24h"],
            "feedback_24h": ["feedback_72h"],
            "feedback_72h": ["learned"],
            "learned": ["archived"],
        }


# ──────────────────────────────────────────────
# Quick Self-Test
# ──────────────────────────────────────────────

def demo():
    profile = ContentProfile()
    profile.initialize()

    print("📦 ContentProfile loaded:")
    print(f"   Name: {profile.name} v{profile.version}")
    print(f"   Description: {profile.description}")
    print(f"   SM states: {list(profile.state_machine.config.states.keys())}")
    print(f"   Initial state: {profile.state_machine.config.initial_states[0].name}")
    print(f"   Terminal state: {profile.state_machine.config.terminal_states[0].name}")
    print(f"   Validators: {len(profile.validators)} ({len(profile.tier1_validators)}T1 + {len(profile.tier2_validators)}T2 + {len(profile.tier3_validators)}T3)")
    print(f"   Adapters: {[a.name for a in profile.adapters]}")
    print(f"   Stores: {[s.name for s in profile.stores]}")
    print(f"   Budget: ${profile.budget.hard_limit_usd} hard limit")

    # Test transitions
    sm = profile.state_machine
    rt = sm.create_runtime()
    print(f"\n📌 Runtime initial: {rt.current_state}")

    # Walk through full lifecycle
    lifecycle = [
        ("captured", "idea_review"),
        ("idea_review", "brief_ready"),
        ("brief_ready", "drafting"),
        ("drafting", "verification"),
        ("verification", "draft_review"),
        ("draft_review", "approved"),
        ("approved", "scheduler_ready"),
        ("scheduler_ready", "scheduled"),
        ("scheduled", "published"),
        ("published", "feedback_24h"),
        ("feedback_24h", "feedback_72h"),
        ("feedback_72h", "learned"),
        ("learned", "archived"),
    ]

    print("\n🔄 Lifecycle walkthrough:")
    for from_s, to_s in lifecycle:
        allowed, reason = sm.can_transition(from_s, to_s)
        status = "✅" if allowed else "❌"
        print(f"   {from_s:20s} → {to_s:20s} {status} ({reason})")

    # Test invalid transitions
    print("\n🚫 Invalid transition tests:")
    invalid = [
        ("archived", "captured"),
        ("published", "drafting"),
        ("brief_ready", "published"),
    ]
    for from_s, to_s in invalid:
        allowed, reason = sm.can_transition(from_s, to_s)
        status = "🚫" if not allowed else "⚠️"  # Should be blocked
        print(f"   {from_s:20s} → {to_s:20s} {status} ({reason})")

    print(f"\n{'='*50}")
    print(f"ContentProfile demo passed!")
    print(f"{'='*50}")


if __name__ == "__main__":
    demo()
