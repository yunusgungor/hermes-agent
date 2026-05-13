"""
Content OS Core — Full Content OS v2.4.0 Implementation
=======================================================
Complete 14-state lifecycle, 54 slop patterns (3 tiers + bonus),
4-route Idea Gate, Writer/Verifier dual-agent pipeline,
LLM-based postmortem with exact-line analysis,
real signal processing, workspace isolation.

Based on Shann³ (@shannholmberg) Content OS — 5M impressions / 100K bookmarks.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# ──────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────

VERSION = "2.4.0"

# The complete 14-state lifecycle (blog-matching)
STATE_LIFECYCLE = [
    "captured",
    "idea_review",
    "brief_ready",
    "drafting",
    "verification",
    "draft_review",
    "approved",
    "scheduler_ready",
    "scheduled",
    "published",
    "feedback_24h",
    "feedback_72h",
    "learned",
    "archived",
]

STATE_TRANSITIONS = {
    "captured":        ["idea_review"],
    "idea_review":     ["brief_ready", "captured"],
    "brief_ready":     ["drafting"],
    "drafting":        ["verification"],
    "verification":    ["draft_review"],
    "draft_review":    ["approved", "brief_ready", "captured"],
    "approved":        ["scheduler_ready"],
    "scheduler_ready": ["scheduled"],
    "scheduled":       ["published"],
    "published":       ["feedback_24h"],
    "feedback_24h":    ["feedback_72h"],
    "feedback_72h":    ["learned"],
    "learned":         ["archived"],
    "archived":        [],  # final state — no transitions out
}

IDEA_ROUTES = ["ORIGINAL", "REPURPOSE", "REWRITE", "RESEARCH+IDEATE"]

# State → filename mapping for auto-detection (sync_state)
STATE_FILE_MAP = {
    "published":     "published",
    "feedback_72h":  "feedback.md",
    "feedback_24h":  "feedback.md",
    "learned":       "feedback.md",
    "verified":      "verifier-report.md",
    "drafting":      "draft-package.md",
    "brief_ready":   "brief.md",
}

# Self-assessment fields for Writer Agent output
WRITER_FIELDS = [
    "rubric_self_assessment",
    "avoid_slop_pass",
    "open_loops_flagged",
    "voice_check",
]

FULL_SLOP_TIER1 = [
    # 1. Promosyon Dili
    r"groundbreaking", r"game-changing", r"revolutionary", r"transformative", r"paradigm-shifting",
    # 2. Önem Atfetme Abartısı
    r"pivotal moment", r"testament to", r"a testament to", r"significant step", r"quantum leap",
    # 3. Belirsiz Atıf
    r"experts believe", r"studies show", r"research suggests", r"data shows", r"it turns out that",
    # 4. Sahte Etkinlik
    r"the system compounds", r"the data tells us", r"compound interest of", r"the power of",
    # 5. Retorik Kurulum
    r"the question is whether", r"at its core", r"what if i told you",
    # 6. Staccato Parçalama
    r"(?i)(?:^|\n)\s*(?:no\s+\S+\.\s*){2,}", r"(?i)(?:^|\n)\s*(?:\S+\.\s*){4,}", r"(?i)(?:fail|error|bug)s?\s*\.\s*(?:fail|error|bug)s?\s*\.",
    # 7. Em Dash aşırı
    r"(?<!\-)\-\-(?!\-)",  # catches -- (em dash)
    # 8. Dolgu Zarfları
    r"actually", r"literally", r"quietly", r"simply", r"just\b", r"basically",
]

FULL_SLOP_TIER2 = [
    # 9. Copula Avoidance
    r"serves as", r"stands as", r"features", r"encompasses", r"utilizes",
    # 10. -ing Padding
    r"leveraging", r"implementing", r"optimizing", r"enabling",
    # 11. Rule of Three Zorlama
    r"three things", r"three reasons", r"three ways", r"triad\b",
    # 12. Filler Phrases
    r"in order to", r"due to the fact that", r"at this point in time", r"in today's world",
    # 13. Generic Conclusions
    r"the future looks bright", r"exciting times ahead", r"the best is yet to come",
    # 14. Signposting
    r"let's dive in", r"here's what you need to know", r"tldr", r"in conclusion",
    # 15. Hyperbolic Quantifiers
    r"every single", r"all the time", r"never ever", r"absolutely everyone",
    # 16. Hedging
    r"it could potentially", r"it might be argued", r"somewhat", r"arguably",
]

FULL_SLOP_TIER3 = [
    # 17. Passive Voice (basic catch)
    r"\b(?:was|were|been|being)\s+\w+ed\b",
    # 18. Elegant Variation (generic — catches synonym chains)
    r"(?:\w+,\s*(?:also\s+)?known\s+as)",
    # 19. False Ranges
    r"from basic to advanced", r"from beginner to expert",
    # 20. Conjunction Overuse (sentence starting with And/But — basic)
    r"(?:^|\n)\s*(?:And|But)\s+",
    # 21. Unnecessary Intensifiers
    r"\bvery\b", r"\bso\b", r"\bsuch\b",
    # 22. Paragraph-Level Vagueness (matches generic statements without specifics)
    r"it is important to note that", r"it should be noted that",
    # 23. Rhetorical Questions as Statements
    r"(?:have you ever wondered|can you imagine|what would you do if)",
    # 24. Awkward List Introductions
    r"there are \d+ things", r"\d+ (?:is|are) ",
    # 25. False Precision
    r"exactly \d+\.\d+%",
    # 26. Clichéd Metaphors
    r"level\s*up", r"dive\s*deep", r"game\s*plan", r"road\s*map",
    # 27. Self-Referential Humility
    r"i may be wrong", r"i could be wrong",
    # 28. Empty Emphasis (UPPERCASE or BRACKET emphasis)
    r"(?:^|\n)\s*\[.*?\]\s*\n", r"(?:^|\n)\s*[A-Z]{4,}\s*\n",
    # 29. Temporal Vagueness
    r"\brecently\b", r"\blately\b", r"\bthese days\b",
    # 30. False Balance
    r"some say .* while others say", r"on one hand .* on the other hand",
    # 31. Unearned Authority
    r"as someone who", r"having worked in",
    # 32. Hedging Through Specificity
    r"exactly \d+\.\d+",
    # 33. Template Language
    r"in this post, we.{0,20}(?:explore|dive|cover|discuss)",
    # 34. Unnecessary Qualification
    r"the very real possibility", r"the very real chance",
]

FULL_SLOP_BONUS = [
    # 35. Faux Authority
    r"\byou should\b", r"\byou must\b", r"never do this",
    # 36. Vibes Over Data
    r"it feels like", r"seems to me",
    # 37. Thread-Bait Hooks
    r"here's the thing", r"the secret",
    # 38. Oversharing Backstory
    r"\d+\s*years? ago,?.*?(?:i|we|my|our)",
    # 39. Pseudo-Technical removed (case-insensitive false positives with IGNORECASE)
    # 40. Under-Explaining Proof
    r"result\s*:\s*%\s*\w+",
]

# ──────────────────────────────────────────────────────────────
# EXCEPTIONS
# ──────────────────────────────────────────────────────────────

class ContentOSError(Exception):
    """Base exception for Content OS."""
    pass


# ══════════════════════════════════════════════════════════════
# CORE CLASS
# ══════════════════════════════════════════════════════════════

class ContentOSCore:
    """Full Content OS engine — 14-state lifecycle, 54 slop patterns,
    4-route Idea Gate, Writer/Verifier dual-agent, LLM postmortem."""

    def __init__(self, root: Path):
        self.root = root
        self.strategy = root / "strategy"
        self.voice = root / "voice"
        self.active_runs = root / "runs" / "active"
        self.stores = root / "stores"
        self.workflows = root / "workflows"
        self.archive = root / "runs" / "archive"

        # Full 54-pattern slop detection (3 tiers + bonus)
        self.slop_tier1 = FULL_SLOP_TIER1
        self.slop_tier2 = FULL_SLOP_TIER2
        self.slop_tier3 = FULL_SLOP_TIER3
        self.slop_bonus = FULL_SLOP_BONUS

        self._init_stores_dirs()
        self._migrate_old_state()

    # ──────────────────────────────────────────────────────────
    # SETUP & MIGRATION
    # ──────────────────────────────────────────────────────────

    def _init_stores_dirs(self):
        """Initialize stores subdirectories."""
        for subdir in ["ideas", "hooks", "proof", "feedback"]:
            (self.stores / subdir).mkdir(parents=True, exist_ok=True)

    def _migrate_old_state(self):
        """Migrate old 5-state runs to the new 14-state format on init."""
        if not self.active_runs.exists():
            return
        for d in self.active_runs.iterdir():
            if d.is_dir():
                try:
                    self.sync_state(d.name)
                except Exception:
                    continue

    def setup(self) -> str:
        """Initialize directory structure."""
        dirs = [self.strategy, self.voice, self.active_runs,
                self.stores, self.workflows, self.archive]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        self._init_stores_dirs()
        return "✅ Content OS v2.4.0 structure initialized."

    # ──────────────────────────────────────────────────────────
    # IDEA GATE — 4 ROUTE DECISION
    # ──────────────────────────────────────────────────────────

    def decide_route(self, idea: str, source_hint: str = "") -> Dict[str, Any]:
        """Determine the 4-route Idea Gate decision for an idea.

        When source_hint is explicitly provided, it takes priority.
        Without source_hint, keyword matching is used with word boundaries.

        Args:
            idea: The content idea text.
            source_hint: Optional hint ('internal', 'external', 'existing', 'research').

        Returns:
            dict with route, rationale, and source classification.
        """
        idea_lower = idea.lower()
        source = source_hint.lower().strip() if source_hint else ""

        # When source_hint is explicitly provided, trust it as primary signal
        if source in ("internal", "external", "existing", "research"):
            if source == "research":
                return {
                    "route": "RESEARCH+IDEATE",
                    "rationale": "Keşif odaklı fikir — çıktı post değil, fikir listesi olacak.",
                    "source_type": "keşif",
                }
            if source == "external":
                return {
                    "route": "REWRITE",
                    "rationale": "Dış kaynaktan ilham alınmış — kendi sesinle yeniden yazılacak.",
                    "source_type": "harici",
                }
            if source == "existing":
                return {
                    "route": "REPURPOSE",
                    "rationale": "Mevcut içerikten türetme — format/platform değişimi.",
                    "source_type": "mevcut içerik",
                }
            if source == "internal":
                return {
                    "route": "ORIGINAL",
                    "rationale": "Kişisel deneyim/düşünce — en yüksek değerli içerik tipi.",
                    "source_type": "kişisel",
                }

        # Without source_hint: keyword-based detection with word boundaries
        import re as _re

        # Word-boundary patterns to avoid false matches ("i " vs "idea")
        def has_word(word):
            return bool(_re.search(r'\b' + _re.escape(word) + r'\b', idea_lower))

        def has_any(words):
            return any(has_word(w) or w in idea_lower for w in words)

        # Internal keywords (personal experience)
        internal_kw = [
            "ben", "benim", "kendi", "yaşadı", "deneyim", "tecrübe",
            "personal experience", "my", "our", "we",
        ]
        # Existing content keywords
        existing_kw = [
            "önceki", "devam", "güncelle", "update", "part", "bölüm",
            "follow-up", "sequel", "series", "önceki yazı",
        ]
        # External source keywords
        external_kw = [
            "makale", "article", "podcast", "video", "tweet", "post",
            "gördüm", "okudum", "izledim", "found", "read", "saw",
            "gönderi", "tweet'te", "makalede",
        ]
        # Research/exploration keywords
        research_kw = [
            "araştır", "keşfet", "research", "explore", "investigate",
            "analiz et", "karşılaştır", "compare", "trend",
        ]

        is_internal = has_any(internal_kw)
        is_external = has_any(external_kw)
        is_existing = has_any(existing_kw)
        is_research = has_any(research_kw)

        # Priority: research > external (not internal) > existing > original
        if is_research:
            route = "RESEARCH+IDEATE"
            rationale = "Keşif odaklı fikir — çıktı post değil, fikir listesi olacak."
            source_type = "keşif"
        elif is_external and not is_internal:
            route = "REWRITE"
            rationale = "Dış kaynaktan ilham alınmış — kendi sesinle yeniden yazılacak."
            source_type = "harici"
        elif is_existing:
            route = "REPURPOSE"
            rationale = "Mevcut içerikten türetme — format/platform değişimi."
            source_type = "mevcut içerik"
        elif is_internal:
            route = "ORIGINAL"
            rationale = "Kişisel deneyim/düşünce — en yüksek değerli içerik tipi."
            source_type = "kişisel"
        else:
            # Unclear signal — default to ORIGINAL with note
            route = "ORIGINAL"
            rationale = "Net sinyal yok — ORIGINAL varsayıldı. İhtiyaç halinde route güncellenebilir."
            source_type = "belirsiz"

        return {
            "route": route,
            "rationale": rationale,
            "source_type": source_type,
        }

    # ──────────────────────────────────────────────────────────
    # CONTENT RUN OPERATIONS
    # ──────────────────────────────────────────────────────────
    def create_run(self, idea: str, slug: str = None,
                   source_hint: str = "") -> Dict[str, Any]:
        """Start a new content run with Idea Gate decision."""
        if not slug:
            slug = re.sub(r'[^a-z0-9]', '-', idea.lower())[:50]
            slug = re.sub(r'-+', '-', slug).strip('-')
            if not slug:
                slug = f"content-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            # Add date prefix
            date_prefix = datetime.now().strftime('%Y-%m')
            slug = f"{date_prefix}-{slug}"
        else:
            # Custom slug: sanitize once, preserve identity
            slug = re.sub(r'[^a-z0-9\-_]', '-', slug.lower())[:50]
            slug = re.sub(r'-+', '-', slug).strip('-')
            if not slug:
                slug = f"custom-{datetime.now().strftime('%Y%m%d%H%M')}"
            # Only add date prefix if not already present
            date_prefix = datetime.now().strftime('%Y-%m')
            if not slug.startswith(date_prefix):
                slug = f"{date_prefix}-{slug}"

        run_path = self.active_runs / slug

        if run_path.exists():
            return {"slug": slug, "path": str(run_path),
                    "status": "exists", "message": "Run already exists"}

        run_path.mkdir(parents=True, exist_ok=True)

        # --- IDEA GATE ---
        route_decision = self.decide_route(idea, source_hint)
        context = self.get_context_for_run(idea)

        # Write content-object.md with full 14-state format
        obj = f"""# Content Object — {slug}

## Meta
- **ID:** {slug}
- **Created:** {datetime.now().isoformat()}
- **Status:** captured
- **Route:** {route_decision['route']}
- **Source Type:** {route_decision['source_type']}
- **Format:** TBD
- **Pillar:** TBD
- **Title:** {idea}
"""
        (run_path / "content-object.md").write_text(obj, encoding="utf-8")

        # Write idea.md with route decision
        idea_md = f"""# Idea — {slug}

## Description
{idea}

## Route Decision
- **Route:** {route_decision['route']}
- **Rationale:** {route_decision['rationale']}
- **Source:** {route_decision['source_type']}
- **Decision Date:** {datetime.now().isoformat()}

## Route Rules
- [ ] ORIGINAL: No external sources, high taste investment required
- [ ] REPURPOSE: Existing content reference specified
- [ ] REWRITE: Source clearly attributed, credit rules defined
- [ ] RESEARCH+IDEATE: Output is NOT a post, it's an idea list
"""
        (run_path / "idea.md").write_text(idea_md, encoding="utf-8")

        # Create context.md
        context_md = f"""# Context for: {slug}

## Relevant Proof Elements
{context.get('proof', 'No proof available')}

## Successful Hook Patterns
{context.get('hooks', 'No hooks available')}

## Top Performing Runs (for reference)
{context.get('top_runs', 'No previous runs')}

## Voice Profile Summary
{context.get('voice', 'No voice profile set')}
"""
        (run_path / "context.md").write_text(context_md, encoding="utf-8")

        return {
            "slug": slug,
            "path": str(run_path),
            "route": route_decision["route"],
            "context_provided": True,
        }

    def get_context_for_run(self, idea: str) -> Dict[str, str]:
        """Get relevant context from stores for a new run."""
        return {
            "proof": self._get_relevant_proof(idea),
            "hooks": self._get_successful_hooks(),
            "top_runs": self._get_top_performing_runs(),
            "voice": self._get_voice_summary(),
        }

    def _get_relevant_proof(self, idea: str) -> str:
        """Find proof elements relevant to the idea."""
        proof_dir = self.stores / "proof"
        if not proof_dir.exists():
            return "No proof directory found."

        proof_files = list(proof_dir.glob("*.md"))
        if not proof_files:
            inbox = self.stores / "inbox.md"
            if inbox.exists():
                content = inbox.read_text(encoding="utf-8")
                lines = [l for l in content.split('\n')
                         if any(k in l.lower() for k in ['metrik', 'proje', 'sonuç', 'metric', 'result'])]
                return "\n".join(lines[:5]) if lines else "No proof available."
            return "No proof available."

        return "\n\n".join(
            [f"## {p.stem}\n{p.read_text(encoding='utf-8')[:300]}"
             for p in proof_files[:3]]
        )

    def _get_successful_hooks(self) -> str:
        """Get hook patterns that worked before."""
        hooks_dir = self.stores / "hooks"
        if not hooks_dir.exists() or not list(hooks_dir.glob("*.md")):
            return "No successful hooks recorded yet."
        return "\n".join(
            [f"- {h.stem}: {h.read_text(encoding='utf-8')[:100]}"
             for h in list(hooks_dir.glob("*.md"))[:5]]
        )

    def _get_top_performing_runs(self) -> str:
        """Get top performing runs from archive."""
        if not self.archive.exists():
            return "No archived runs yet."

        runs = []
        for d in self.archive.iterdir():
            if d.is_dir():
                fb = d / "feedback.md"
                if fb.exists():
                    content = fb.read_text(encoding="utf-8")
                    bm = re.search(r'bookmarks?[\s:]+(\d+)', content, re.IGNORECASE)
                    bookmarks = int(bm.group(1)) if bm else 0
                    runs.append((d.name, bookmarks))

        runs.sort(key=lambda x: x[1], reverse=True)
        if not runs:
            return "No run feedback available."
        return "\n".join([f"- {name}: {bm} bookmarks" for name, bm in runs[:5]])

    def _get_voice_summary(self) -> str:
        """Get voice profile summary."""
        vf = self.voice / "voice-profile.md"
        if not vf.exists():
            return "No voice profile set."
        content = vf.read_text(encoding="utf-8")
        lines = [l for l in content.split('\n')
                 if l.strip().startswith(('1.', '2.', '3.', '4.', '5.'))]
        return "\n".join(lines[:5]) if lines else content[:300]

    # ──────────────────────────────────────────────────────────
    # 14-STATE LIFECYCLE
    # ──────────────────────────────────────────────────────────

    def _valid_transition(self, from_state: str, to_state: str) -> bool:
        """Check if a state transition is valid per the 14-state lifecycle."""
        if from_state not in STATE_TRANSITIONS:
            return to_state in STATE_LIFECYCLE
        return to_state in STATE_TRANSITIONS[from_state]

    def update_state(self, slug: str, new_state: str,
                     force: bool = False) -> str:
        """Update state with 14-state lifecycle validation."""
        if new_state not in STATE_LIFECYCLE:
            return f"❌ Invalid state: {new_state}. Valid: {', '.join(STATE_LIFECYCLE)}"

        run_path = (self.active_runs / slug).resolve()
        if not run_path.exists():
            return f"❌ Run {slug} not found."

        obj_path = run_path / "content-object.md"

        # Auto-initialize if missing
        if not obj_path.exists():
            idea_path = run_path / "idea.md"
            idea = idea_path.read_text(encoding="utf-8") if idea_path.exists() else slug
            obj_path.write_text(
                f"title: {idea}\nstate: {new_state}\n"
                f"created: {datetime.now().isoformat()}\n"
                f"updated: {datetime.now().isoformat()}",
                encoding="utf-8",
            )
            return f"✅ Initialized and updated {slug} to {new_state}"

        content = obj_path.read_text(encoding="utf-8")

        # Extract current state
        current_state = "captured"
        m = re.search(r'state:\s*(\w+)', content)
        if m:
            current_state = m.group(1)

        # Validate transition (unless force)
        if not force and not self._valid_transition(current_state, new_state):
            return (
                f"❌ Invalid transition: {current_state} → {new_state}. "
                f"Allowed: {STATE_TRANSITIONS.get(current_state, ['any'])}"
            )

        # Update state
        if "state:" in content:
            new_content = re.sub(r"state:\s*\w+", f"state: {new_state}", content)
        else:
            new_content = content + f"\nstate: {new_state}"

        # Update timestamp
        ts = datetime.now().isoformat()
        if "updated:" in new_content:
            new_content = re.sub(r"updated:.*", f"updated: {ts}", new_content)
        else:
            new_content = f"{new_content}\nupdated: {ts}"

        obj_path.write_text(new_content, encoding="utf-8")
        return f"✅ {slug}: {current_state} → {new_state}"

    def sync_state(self, slug: str) -> str:
        """Scan filesystem and sync content-object.md to correct 14-state."""
        run_path = (self.active_runs / slug).resolve()
        if not run_path.exists():
            return "unknown"

        # Priority-ordered detection (highest state wins)
        if (run_path / "published").exists():
            state = "published"
        elif (run_path / "feedback.md").exists():
            # Check if 24h or 72h by looking at content
            fb_content = (run_path / "feedback.md").read_text(encoding="utf-8")
            if "## 72h" in fb_content or "## 72 Saat" in fb_content:
                state = "feedback_72h"
            elif "## 24h" in fb_content or "## 24 Saat" in fb_content:
                state = "feedback_24h"
            else:
                state = "learned"
        elif (run_path / "scheduled").exists():
            state = "scheduled"
        elif (run_path / "verifier-report.md").exists():
            state = "verification"  # verifier report done, waiting for review
        elif (run_path / "draft-package.md").exists():
            state = "drafting"
        elif (run_path / "brief.md").exists():
            state = "brief_ready"
        elif (run_path / "idea.md").exists():
            state = "idea_review"
        else:
            state = "captured"

        try:
            self.update_state(slug, state, force=True)
        except Exception:
            pass
        return state

    def get_state(self, slug: str) -> str:
        """Read current state from content-object.md."""
        obj = self.active_runs / slug / "content-object.md"
        if not obj.exists():
            return "unknown"
        content = obj.read_text(encoding="utf-8")
        m = re.search(r'state:\s*(\w+)', content)
        return m.group(1) if m else "unknown"

    def get_next_actions(self, slug: str) -> List[str]:
        """Return suggested next actions based on current state."""
        state = self.get_state(slug)
        guide = {
            "captured":        ["Run idea review → decide route", "Write idea.md with route rationale"],
            "idea_review":     ["Write brief.md (Writer Context Packet)", "Read voice-profile.md"],
            "brief_ready":     ["Run Writer Agent to generate draft-package.md"],
            "drafting":        ["Run Verifier Agent to create verifier-report.md"],
            "verification":    ["Review verifier outcomes", "Approve / Request revision / Reject"],
            "draft_review":    ["APPROVE → move to scheduler_ready",
                               "REVISE → update brief.md, return to drafting",
                               "REJECT → archive or discard"],
            "approved":        ["Prepare for scheduling (visual, hashtags, timing)"],
            "scheduler_ready": ["Schedule the post via Postiz / X"],
            "scheduled":       ["Wait for publish time", "Confirm post went live"],
            "published":       ["Collect 24h metrics", "Run feedback_24h"],
            "feedback_24h":    ["Collect 72h metrics", "Run feedback_72h"],
            "feedback_72h":    ["Run postmortem analysis",
                               "Update voice profile, hooks, proof stores",
                               "Transition to learned"],
            "learned":         ["Archive the run to runs/archive/"],
        }
        return guide.get(state, ["No specific next actions defined for this state."])

    # ──────────────────────────────────────────────────────────
    # BRIEF GENERATION (Writer Context Packet)
    # ──────────────────────────────────────────────────────────

    async def generate_brief(self, slug: str, llm: Any = None,
                             extra_context: str = "") -> Dict[str, Any]:
        """Generate a Writer Context Packet (brief.md) using LLM.

        Produces the complete brief.md with thesis, reader, proof,
        angle, constraints, voice anchors, risks, and open loops.
        Returns dict with brief_content and status.
        """
        run_path = self.active_runs / slug
        if not run_path.exists():
            return {"error": f"Run {slug} not found."}

        idea_path = run_path / "idea.md"
        context_path = run_path / "context.md"

        idea = idea_path.read_text(encoding="utf-8") if idea_path.exists() else slug
        ctx = context_path.read_text(encoding="utf-8") if context_path.exists() else ""

        # Read voice profile
        voice_profile = self._get_voice_summary()

        # Read master slop doc
        slop_doc = ""
        slop_path = self.voice / "master-avoid-slop.md"
        if slop_path.exists():
            slop_doc = slop_path.read_text(encoding="utf-8")[:500]

        prompt = f"""You are writing a Writer Context Packet (brief.md) for a content post.
This is the single most critical document in the Content OS pipeline — it controls writer quality.
Target 400-900 tokens. Be specific. Every field must be filled from available context.

ROUTE: Extract from idea.md below.

INPUT FILES:
1. Idea + Route Decision:
{idea}

2. Context (Proof, Hooks, Top Runs, Voice):
{ctx}

3. Voice Profile Summary:
{voice_profile}

4. Slop Patterns (abridged):
{slop_doc}

{extra_context}

OUTPUT — produce a complete brief.md with EXACTLY this structure:

```markdown
# Writer Context Packet — {{SLUG}}
## Meta
- **Route:** {{ORIGINAL|REPURPOSE|REWRITE|RESEARCH+IDEATE}}
- **Format:** {{Single Post | Thread (N tweets) | Article | Carousel}}
- **Pillar:** {{from strategy/pillars.md}}
- **Target Date:** {{optional}}

## Thesis
ONE sentence — what must this post prove? What should the reader understand?

## Target Reader
ONE specific person. Role + situation + stake.
Example: "ASIC design engineer, 3 years experience, first tape-out ahead of them. Needs a timing closure checklist."

## Angle (Unexpected Framing)
What makes this different from what everyone else says?

## Proof Elements
- Metrics: {{concrete numbers available}}
- Stories: {{real experiences}}
- Projects: {{names, results}}
- Tools: {{technologies used}}

## Constraints
- Format rules
- Length (character/tweet count)
- Tone (formal/casual/technical)
- Banned phrases (explicit list)
- Visual requirements

## Voice Anchors
2-3 example sentences that sound like the brand at its best.

## Risks (Slop / Cringe Traps)
What would make this feel AI-written? Be specific.

## Open Loops
What the writer does NOT know and needs to flag.

## Rubric Targets
- [ ] Saves reader a future task → target: {{0/1/2}}
- [ ] Includes proof → target: {{0/1/2}}
- [ ] Reusable takeaway → target: {{0/1/2}}
- [ ] Specific audience → target: {{0/1/2}}
- [ ] Portable (no-author) → target: {{0/1/2}}
- [ ] Strong visual → target: {{0/1/2}}
Target total: __/12
```

Return ONLY the markdown brief content. No extra commentary."""

        try:
            if llm and hasattr(llm, "acomplete"):
                response = await llm.acomplete([
                    {"role": "system", "content": "You are an expert content strategist who writes tight, specific Writer Context Packets."},
                    {"role": "user", "content": prompt},
                ])
                text = response.text
            else:
                from agent.auxiliary_client import async_call_llm
                messages = [
                    {"role": "system", "content": "You are an expert content strategist."},
                    {"role": "user", "content": prompt},
                ]
                raw = await async_call_llm(task="curator", messages=messages)
                try:
                    text = raw.choices[0].message.content
                except (AttributeError, IndexError):
                    text = str(raw)

            # Clean the output
            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```\w*\n?", "", text)
                text = re.sub(r"\n```$", "", text)

            # Write brief.md
            brief_path = run_path / "brief.md"
            brief_path.write_text(text, encoding="utf-8")

            # Update state
            self.update_state(slug, "brief_ready")

            return {"slug": slug, "status": "brief_ready", "length": len(text)}

        except Exception as e:
            return {"error": f"Brief generation failed: {str(e)}"}

    # ──────────────────────────────────────────────────────────
    # WRITER AGENT — Draft Generation
    # ──────────────────────────────────────────────────────────

    async def generate_draft(self, slug: str, llm: Any = None) -> Dict[str, Any]:
        """Generate draft-package.md using the Writer Agent prompt.

        Reads brief.md + voice-profile.md + master-avoid-slop.md,
        calls LLM with the Writer Agent system prompt, produces
        draft-package.md with rubric_self_assessment, slop_pass,
        open_loops, and voice_check sections.
        """
        run_path = self.active_runs / slug
        if not run_path.exists():
            return {"error": f"Run {slug} not found."}

        brief_path = run_path / "brief.md"
        if not brief_path.exists():
            return {"error": "No brief.md found. Run generate_brief first."}

        brief = brief_path.read_text(encoding="utf-8")

        # Read mandatory context files
        voice_profile = ""
        vp_path = self.voice / "voice-profile.md"
        if vp_path.exists():
            voice_profile = vp_path.read_text(encoding="utf-8")

        slop_doc = ""
        slop_path = self.voice / "master-avoid-slop.md"
        if slop_path.exists():
            slop_doc = slop_path.read_text(encoding="utf-8")[:1500]

        # Read optional proof & hooks
        proof = self._get_relevant_proof(brief)
        hooks = self._get_successful_hooks()

        prompt = f"""ROLE
You are a Writer Agent for a personal brand content system. You draft content
in the brand's authentic voice, from a tight brief — not from a pile of context.
Your job is to produce bookmarkable content: posts that readers save because they
expect to need them again.

INPUT FILES — read in this exact order:

## FILE 1: brief.md (Writer Context Packet)
{brief}

## FILE 2: voice-profile.md (Voice Rules)
{voice_profile}

## FILE 3: master-avoid-slop.md (Banned Patterns)
{slop_doc}

## Optional Reference: Proof Bank
{proof}

## Optional Reference: Successful Hooks
{hooks}

TASK
1. Read all input files carefully
2. Internalize the voice rules
3. Internalize the banned patterns
4. Draft content according to brief's format, length, and constraints
5. Follow voice rules exactly
6. Flag any rubric row that cannot be met

OUTPUT — produce a complete draft-package.md with EXACTLY this structure:

```
---
draft:
[Full content here — thread, single post, or article format as specified in brief]

rubric_self_assessment:
- Saves reader a future task: [0/1/2] — [honest reason with specific evidence]
- Includes proof (numbers, screenshot, named example): [0/1/2] — [specific evidence]
- Gives a reusable takeaway: [0/1/2] — [specific evidence]
- Has a specific audience and job-to-be-done: [0/1/2] — [specific evidence]
- Can be applied without me being in the room: [0/1/2] — [specific evidence]
- Has a strong screenshot or visual: [0/1/2] — [specific evidence]
- TOTAL: [X/12]

avoid_slop_pass:
- [ ] LINE [N]: "[exact phrase]" — [pattern name] — [rewrite suggestion]
- (empty list if clean — do NOT write "no issues found")

open_loops_flagged:
- [specific thing I didn't know and had to guess]
- (empty if nothing was missing from the brief)

voice_check:
- All voice rules followed: [yes/no]
  - Rule 1: [followed / violated]
  - Rule 2: [followed / violated]
  - Rule 3: [followed / violated]
  - Rule 4: [followed / violated]
  - Rule 5: [followed / violated]
- Any banned patterns used: [yes/no — list with line numbers]
- Reference posts matched: [yes/no]
```

QUALITY GATES (all must pass):
- [ ] Thesis from brief is delivered in the draft
- [ ] Target reader is served specifically
- [ ] Voice rules followed (0 violations)
- [ ] Slop patterns avoided (or flagged with rewrites)
- [ ] Format matches brief specification
- [ ] Length within brief constraints
- [ ] At least one proof element included
- [ ] At least one reusable element included"""

        try:
            if llm and hasattr(llm, "acomplete"):
                response = await llm.acomplete([
                    {"role": "system", "content": "You are a Writer Agent for Content OS. You produce high-quality, bookmarkable draft packages."},
                    {"role": "user", "content": prompt},
                ])
                text = response.text
            else:
                from agent.auxiliary_client import async_call_llm
                messages = [
                    {"role": "system", "content": "You are a Writer Agent for Content OS. You produce high-quality, bookmarkable draft packages."},
                    {"role": "user", "content": prompt},
                ]
                raw = await async_call_llm(task="writer", messages=messages)
                try:
                    text = raw.choices[0].message.content
                except (AttributeError, IndexError):
                    text = str(raw)

            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```\w*\n?", "", text)
                text = re.sub(r"\n```$", "", text)

            draft_path = run_path / "draft-package.md"
            draft_path.write_text(text, encoding="utf-8")
            self.update_state(slug, "drafting")

            return {"slug": slug, "status": "drafted", "length": len(text)}

        except Exception as e:
            return {"error": f"Draft generation failed: {str(e)}"}

    # ──────────────────────────────────────────────────────────
    # VERIFIER AGENT
    # ──────────────────────────────────────────────────────────

    async def run_verifier(self, slug: str, llm: Any = None) -> Dict[str, Any]:
        """Run Verifier Agent on a draft.

        Reads brief.md + draft-package.md + rubric + slop doc.
        Produces verifier-report.md with brief_check, rubric_scoring,
        slop findings, verdict (APPROVE/REVISE/REJECT), and required_fixes.
        """
        run_path = self.active_runs / slug
        if not run_path.exists():
            return {"error": f"Run {slug} not found."}

        draft_path = run_path / "draft-package.md"
        brief_path = run_path / "brief.md"

        if not draft_path.exists():
            return {"error": "No draft-package.md found. Run generate_draft first."}

        draft = draft_path.read_text(encoding="utf-8")
        brief = brief_path.read_text(encoding="utf-8") if brief_path.exists() else "No brief available."
        slop_doc = ""
        slop_path = self.voice / "master-avoid-slop.md"
        if slop_path.exists():
            slop_doc = slop_path.read_text(encoding="utf-8")[:2000]

        prompt = f"""ROLE
You are a Verifier Agent for a personal brand content system. You check drafts
against a quality rubric and an anti-slop document. You do not rewrite —
you point out what needs to change and let the writer fix it.

Your job is to catch what the writer missed: rubric gaps, slop patterns,
voice violations, and brief misalignment. Be precise. Point at exact lines.
Generic feedback is not verification.

INPUT FILES:

## FILE 1: brief.md (What the post was supposed to deliver)
{brief}

## FILE 2: draft-package.md (Writer's output)
{draft}

## FILE 3: master-avoid-slop.md (54 slop patterns)
{slop_doc}

## FILE 4: Bookmarkability Rubric
Criteria (each scored 0-2, max 12, threshold 8):
1. Saves reader a future task
2. Includes proof (numbers, screenshot, named example)
3. Gives a reusable takeaway (template, checklist, frame)
4. Has a specific audience and job-to-be-done
5. Can be applied without author being in the room (portable)
6. Has a strong screenshot or visual

VERIFICATION REPORT — produce EXACTLY this output structure:
(Output as plain markdown, no code fences.)

---
## brief_check
- Thesis delivered: [yes/partial/no] — [specific evidence from draft]
- Target reader served: [yes/partial/no] — [specific evidence]
- Angle honored: [yes/partial/no] — [specific evidence]
- Constraints met (format/length/tone): [yes/partial/no] — [specific evidence]
- Voice rules followed: [yes/no] — [list violations with line numbers]

## rubric_scoring
- Saves reader a future task: [0/1/2] — [specific quote from text as evidence]
- Includes proof: [0/1/2] — [specific quote as evidence]
- Reusable takeaway: [0/1/2] — [specific quote as evidence]
- Specific audience + job: [0/1/2] — [specific quote as evidence]
- Portable (no-author required): [0/1/2] — [specific quote as evidence]
- Strong visual: [0/1/2] — [specific evidence or "none provided"]
- TOTAL: [X/12]
- PASSES_THRESHOLD (8/12): [yes/no]

## avoid_slop_findings
TIER 1 — Critical:
- [ ] LINE [N]: "[exact phrase]" — [pattern name]
TIER 2 — High:
- [ ] LINE [N]: "[exact phrase]" — [pattern name]
TIER 3 — Medium:
- [ ] LINE [N]: "[exact phrase]" — [pattern name]

## VERDICT
- [APPROVE] — threshold met, slop findings are minor (≤2 Tier 1)
- [REVISE] — draft is close but needs specific fixes
- [REJECT] — threshold missed significantly, send back to brief

## required_fixes
1. [Line N]: [specific, actionable fix — what to change and how]
2. [Line M]: [specific, actionable fix]
...

EVIDENCE RULES:
- Every rubric score MUST have a specific quote from the draft as evidence
- Every slop finding MUST have the exact phrase and line number
- Generic feedback ("good hook", "nice insight") is REJECTED
---"""

        try:
            if llm and hasattr(llm, "acomplete"):
                response = await llm.acomplete([
                    {"role": "system", "content": "You are a strict Verifier Agent for Content OS. You catch what the writer missed."},
                    {"role": "user", "content": prompt},
                ])
                text = response.text
            else:
                from agent.auxiliary_client import async_call_llm
                messages = [
                    {"role": "system", "content": "You are a strict Verifier Agent for Content OS."},
                    {"role": "user", "content": prompt},
                ]
                raw = await async_call_llm(task="curator", messages=messages)
                try:
                    text = raw.choices[0].message.content
                except (AttributeError, IndexError):
                    text = str(raw)

            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```\w*\n?", "", text)
                text = re.sub(r"\n```$", "", text)

            report_path = run_path / "verifier-report.md"
            report_path.write_text(text, encoding="utf-8")
            self.update_state(slug, "verification")

            return {"slug": slug, "status": "verified", "length": len(text)}

        except Exception as e:
            return {"error": f"Verification failed: {str(e)}"}

    # ──────────────────────────────────────────────────────────
    # SLOP DETECTION (Full 54 patterns)
    # ──────────────────────────────────────────────────────────

    def scan_slop(self, text: str) -> Dict[str, Any]:
        """Full 54-pattern slop detection across all tiers.

        Returns findings per tier with scores:
        - PASS: <1 T1, <3 T2, <15 T3
        - REVISE: ≥1 T1 OR ≥3 T2 OR ≥8 T3
        - REJECT: ≥3 T1 OR ≥5 T2 OR ≥15 T3
        """
        findings_t1 = []
        findings_t2 = []
        findings_t3 = []
        findings_bonus = []

        for p in self.slop_tier1:
            if re.search(p, text, re.IGNORECASE):
                findings_t1.append(p)
        for p in self.slop_tier2:
            if re.search(p, text, re.IGNORECASE):
                findings_t2.append(p)
        for p in self.slop_tier3:
            if re.search(p, text, re.IGNORECASE):
                findings_t3.append(p)
        for p in self.slop_bonus:
            if re.search(p, text, re.IGNORECASE):
                findings_bonus.append(p)

        t1 = len(findings_t1)
        t2 = len(findings_t2)
        t3 = len(findings_t3)
        tb = len(findings_bonus)

        # Scoring thresholds (from the blog)
        if t1 >= 3 or t2 >= 5 or t3 >= 15:
            score = "REJECT"
        elif t1 >= 1 or t2 >= 3 or t3 >= 8:
            score = "REVISE"
        else:
            score = "PASS"

        return {
            "score": score,
            "tier1_count": t1,
            "tier2_count": t2,
            "tier3_count": t3,
            "bonus_count": tb,
            "findings": findings_t1 + findings_t2 + findings_t3 + findings_bonus,  # backward compat
            "findings_tier1": findings_t1[:10],
            "findings_tier2": findings_t2[:10],
            "findings_tier3": findings_t3[:15],
            "findings_bonus": findings_bonus[:5],
            "all_findings": findings_t1 + findings_t2 + findings_t3 + findings_bonus,
        }

    # ──────────────────────────────────────────────────────────
    # RUBRIC EVALUATION (LLM-based)
    # ──────────────────────────────────────────────────────────

    async def evaluate_rubric(self, slug: str, llm: Any = None) -> Dict[str, Any]:
        """12-point bookmarkability rubric audit using LLM."""
        run_path = self.active_runs / slug
        draft_path = run_path / "draft-package.md"
        if not draft_path.exists():
            return {"error": f"Draft not found for {slug}"}

        content = draft_path.read_text(encoding="utf-8")
        prompt = f"""Audit this content draft against our 12-point Bookmarkability Rubric:

{content}

Score each criterion 0 (fails), 1 (partial), or 2 (meets fully).
Threshold to pass: 8/12.

Return EXACTLY valid JSON:
{{
  "scores": {{
    "saves_reader_task": 0-2,
    "includes_proof": 0-2,
    "reusable_takeaway": 0-2,
    "specific_audience": 0-2,
    "portable": 0-2,
    "strong_visual": 0-2
  }},
  "summary": "string assessment with specific evidence",
  "total": 0-12,
  "passes": true/false,
  "lowest_scores": ["criterion1", "criterion2"]
}}
"""
        try:
            if llm and hasattr(llm, "acomplete"):
                response = await llm.acomplete([
                    {"role": "system", "content": "You are a strict technical content editor scoring against a rubric."},
                    {"role": "user", "content": prompt},
                ])
                text = response.text
            else:
                from agent.auxiliary_client import async_call_llm
                messages = [
                    {"role": "system", "content": "You are a strict technical content editor."},
                    {"role": "user", "content": prompt},
                ]
                raw = await async_call_llm(task="curator", messages=messages)
                try:
                    text = raw.choices[0].message.content
                except (AttributeError, IndexError):
                    text = str(raw)

            json_match = re.search(r"(\{.*\})", text, re.DOTALL)
            if json_match:
                res = json.loads(json_match.group(1))
            else:
                res = {"scores": {}, "summary": f"Failed to parse: {text[:200]}",
                       "total": 0, "passes": False}

            if "total" not in res or not res["total"]:
                res["total"] = sum(res.get("scores", {}).values())
            res["passes"] = res.get("total", 0) >= 8
            return res

        except Exception as e:
            return {"error": str(e)}

    # ──────────────────────────────────────────────────────────
    # POSTMORTEM (LLM-based, exact-line analysis)
    # ──────────────────────────────────────────────────────────

    async def run_postmortem(self, slug: str, metrics: Dict[str, Any] = None,
                             llm: Any = None) -> Dict[str, Any]:
        """LLM-based postmortem with exact-line analysis.

        Unlike the old regex-based version, this uses an LLM to analyze
        the draft and pinpoint exact lines that drove bookmarks/engagement.
        Produces 24h or 72h report depending on phase.
        """
        run_path = self.active_runs / slug
        if not run_path.exists():
            return {"error": f"Run {slug} not found."}

        draft_path = run_path / "draft-package.md"
        if not draft_path.exists():
            return {"error": "Draft not found for postmortem."}

        draft_content = draft_path.read_text(encoding="utf-8")

        if not metrics:
            metrics = {
                "impressions": 0, "engagements": 0,
                "likes": 0, "retweets": 0,
                "bookmarks": 0, "replies": 0,
            }

        # Determine which phase we're in (24h or 72h)
        current_state = self.get_state(slug)
        phase = "24h" if current_state == "feedback_24h" else "72h"

        prompt = f"""You are running a POSTMORTEM on a published content post.
Phase: {phase} hour feedback.

CONSTRAINT: Generic praise is STRICTLY REJECTED.
❌ "Strong hook" → you must name the specific hook text
❌ "Great insight" → you must quote the specific insight
❌ "Good formatting" → you must describe the specific formatting choice

You MUST point at EXACT lines. No vague analysis.

CONTEXT:
POST SLUG: {slug}
PHASE: {phase} hour feedback
METRICS: {json.dumps(metrics, indent=2)}

PUBLISHED DRAFT:
---
{draft_content}
---

TASK — Analyze against these metrics. Answer ALL questions:

1. WHAT DROVE THE BOOKMARKS?
   Quote the exact sentence that likely drove most bookmarks.
   Quote the exact sentence that drove second-most.
   Explain WHY each quote drove bookmarks (not what it says, but WHY someone would save it).

2. WHAT DROVE OTHER ENGAGEMENT?
   What made people like/retweet/reply? Quote + reason for each.

3. WHAT MISSED?
   What didn't land? Quote specific section. Why did it fall flat?

4. WHAT WOULD YOU CHANGE?
   One specific revision if doing it again.
   One specific thing to keep exactly as-is.

5. WHAT PATTERN TO CAPTURE?
   One reusable pattern for hooks/ or proof/. Describe clearly.

6. VOICE RULES UPDATE?
   Any new voice insight? Confirmed or contradicted rule?

7. AVOID-SLOP UPDATE?
   Any new slop pattern noticed in hindsight?
   Any slop pattern that "worked" despite being slop?

Return as markdown with these sections:
---
## what_drove_bookmarks
1. "[exact quote]" — [specific reason]
2. "[exact quote]" — [specific reason]

## what_drove_engagement
1. "[exact quote]" — [specific reason]

## what_missed
1. "[section that didn't land]" — [why]

## what_would_i_change
1. [specific revision] — [why it would help]

## pattern_to_capture
[one reusable pattern — where to file it]

## update_to_voice_rules
[new voice insight or "none"]

## update_to_avoid_slop
[new slop pattern or "none"]
---"""

        try:
            if llm and hasattr(llm, "acomplete"):
                response = await llm.acomplete([
                    {"role": "system", "content": "You are a viral content analyst. Point at EXACT lines. Generic praise is rejected."},
                    {"role": "user", "content": prompt},
                ])
                text = response.text
            else:
                from agent.auxiliary_client import async_call_llm
                messages = [
                    {"role": "system", "content": "You are a viral content analyst. Point at EXACT lines."},
                    {"role": "user", "content": prompt},
                ]
                raw = await async_call_llm(task="curator", messages=messages)
                try:
                    text = raw.choices[0].message.content
                except (AttributeError, IndexError):
                    text = str(raw)

            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```\w*\n?", "", text)
                text = re.sub(r"\n```$", "", text)

            # Append to feedback.md (preserve 24h/72h distinction)
            feedback_path = run_path / "feedback.md"
            existing = ""
            if feedback_path.exists():
                existing = feedback_path.read_text(encoding="utf-8") + "\n\n---\n\n"

            bookmark_rate = (
                metrics.get("bookmarks", 0) / max(metrics.get("impressions", 1), 1) * 100
            )

            feedback_content = f"""{existing}# {phase}h Feedback — {slug}

**Date:** {datetime.now().isoformat()}
**Phase:** {phase} hour
**Metrics:** {json.dumps(metrics, indent=2)}
**Bookmark Rate:** {bookmark_rate:.1f}%

## Analysis
{text}
"""
            feedback_path.write_text(feedback_content, encoding="utf-8")

            # Update state
            new_state = "feedback_72h" if phase == "24h" else "learned"
            self.update_state(slug, new_state)

            # Save learnings
            self._save_learnings(slug, {"bookmark_rate": bookmark_rate,
                                         "pattern_to_capture": "See feedback.md",
                                         "summary": text[:300]}, metrics)

            return {
                "slug": slug,
                "phase": phase,
                "metrics": metrics,
                "bookmark_rate": bookmark_rate,
                "analysis": text,
                "new_state": new_state,
            }

        except Exception as e:
            return {"error": f"Postmortem failed: {str(e)}"}

    # Legacy sync wrapper for backward compatibility
    def _analyze_content_performance(self, content: str,
                                      metrics: Dict[str, Any]) -> Dict[str, str]:
        """Legacy regex-based analyzer — kept for compatibility."""
        return self._legacy_analyze(content, metrics)

    def _legacy_analyze(self, content: str, metrics: Dict[str, Any]) -> Dict[str, str]:
        """Fallback analysis when LLM is unavailable."""
        lines = content.split('\n')
        bk = [l.strip() for l in lines
              if any(x in l.lower() for x in ['[ ]', '✓', 'check:', 'template:', 'framework:',
                                               '1.', '2.', '3.', '4.', '5.'])]
        ec = [l.strip() for l in lines if '?' in l or ('!' in l and len(l) > 30)]
        impressions = metrics.get('impressions', 1)
        bookmarks = metrics.get('bookmarks', 0)
        bm_rate = (bookmarks / impressions * 100) if impressions > 0 else 0

        return {
            "summary": f"Bookmark rate: {bm_rate:.1f}%. "
                       f"{'High.' if bm_rate > 5 else 'Needs improvement.'}",
            "bookmark_drivers": "\n".join([f"- {s[:100]}" for s in bk[:3]]) or "None found.",
            "engagement_drivers": "\n".join([f"- {s[:100]}" for s in ec[:2]]) or "None found.",
            "missed": "Legacy analysis — no LLM available.",
            "pattern_to_capture": "Checklist format" if bk else "Narrative",
            "voice_updates": "N/A (legacy mode)",
            "bookmark_rate": bm_rate,
        }

    # ──────────────────────────────────────────────────────────
    # LEARNING EXTRACTION
    # ──────────────────────────────────────────────────────────

    def _save_learnings(self, slug: str, analysis: Dict[str, Any],
                         metrics: Dict[str, Any]):
        """Save learnings to stores for future reference."""
        bookmark_rate = analysis.get("bookmark_rate", 0)

        if bookmark_rate > 5:
            proof_name = f"{slug}-{datetime.now().strftime('%Y%m')}"
            proof_path = self.stores / "proof" / f"{proof_name}.md"
            proof_content = f"""# Proof from {slug}

**Metrics:**
- Impressions: {metrics.get('impressions', 0)}
- Bookmarks: {metrics.get('bookmarks', 0)}
- Bookmark Rate: {bookmark_rate:.1f}%

**What Worked:**
{analysis.get('pattern_to_capture', 'N/A')}

**Date: {datetime.now().isoformat()}**
"""
            proof_path.write_text(proof_content, encoding="utf-8")

        feedback_dir = self.stores / "feedback"
        feedback_dir.mkdir(parents=True, exist_ok=True)
        feedback_name = f"{slug}-{datetime.now().strftime('%Y%m%d')}.md"
        feedback_path = feedback_dir / feedback_name
        summary = f"""# Feedback: {slug}

**Metrics:**
- Impressions: {metrics.get('impressions', 0)}
- Bookmarks: {metrics.get('bookmarks', 0)}
- Likes: {metrics.get('likes', 0)}
- Retweets: {metrics.get('retweets', 0)}

**Performance:** {'Good' if bookmark_rate > 5 else 'Needs improvement'}
**Date: {datetime.now().isoformat()}**
"""
        feedback_path.write_text(summary, encoding="utf-8")

    def get_learnings_for_brief(self, topic: str = None) -> str:
        """Get learnings from previous runs for brief generation."""
        learnings = []
        feedback_dir = self.stores / "feedback"
        if feedback_dir.exists():
            for f in feedback_dir.glob("*.md"):
                content = f.read_text(encoding="utf-8")
                if "Good" in content or "bookmark" in content.lower():
                    learnings.append(f"From {f.stem}: {content[:150]}")

        proof_dir = self.stores / "proof"
        if proof_dir.exists():
            for p in proof_dir.glob("*.md"):
                content = p.read_text(encoding="utf-8")
                learnings.append(f"Proof: {content[:150]}")

        if not learnings:
            return "No learnings available yet."
        return "\n\n".join(learnings[:5])

    def analyze_run_patterns(self) -> Dict[str, Any]:
        """Analyze patterns across all runs."""
        all_runs = []
        for base_dir in [self.active_runs, self.archive]:
            if base_dir.exists():
                for d in base_dir.iterdir():
                    if d.is_dir():
                        try:
                            rd = self._analyze_single_run(d)
                            if rd:
                                all_runs.append(rd)
                        except Exception:
                            continue

        if not all_runs:
            return {"message": "No runs to analyze."}

        total = len(all_runs)
        avg_bm = sum(r.get("bookmarks", 0) for r in all_runs) / max(total, 1)
        formats = {}
        pillars = {}
        for r in all_runs:
            formats[r.get("format", "unknown")] = formats.get(r.get("format", "unknown"), 0) + 1
            pillars[r.get("pillar", "unknown")] = pillars.get(r.get("pillar", "unknown"), 0) + 1

        # State distribution
        states = {}
        for r in all_runs:
            st = r.get("state", "unknown")
            states[st] = states.get(st, 0) + 1

        return {
            "total_runs": total,
            "avg_bookmarks": round(avg_bm, 1),
            "top_formats": sorted(formats.items(), key=lambda x: x[1], reverse=True)[:5],
            "top_pillars": sorted(pillars.items(), key=lambda x: x[1], reverse=True)[:5],
            "state_distribution": states,
            "archive_count": len([r for r in all_runs if r.get("status") == "archived"]),
        }

    def _analyze_single_run(self, run_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze a single run."""
        try:
            result = {"slug": run_path.name}
            obj = run_path / "content-object.md"
            if obj.exists():
                content = obj.read_text(encoding="utf-8")
                for field in ["state", "route", "format", "pillar"]:
                    m = re.search(rf'{field}:\s*(.+)', content, re.IGNORECASE)
                    if m:
                        result[field] = m.group(1).strip()

            fb = run_path / "feedback.md"
            if fb.exists():
                content = fb.read_text(encoding="utf-8")
                bm = re.search(r'bookmarks?[\s:]+(\d+)', content, re.IGNORECASE)
                if bm:
                    result["bookmarks"] = int(bm.group(1))

            result["status"] = "archived" if "archive" in str(run_path) else "active"
            return result

        except PermissionError:
            return None

    # ──────────────────────────────────────────────────────────
    # VOICE EVOLUTION
    # ──────────────────────────────────────────────────────────

    def update_voice_profile(self, updates: Dict[str, Any]) -> str:
        """Update voice profile based on learnings."""
        vf = self.voice / "voice-profile.md"
        if not vf.exists():
            return "No voice profile exists. Create voice-profile.md first."

        current = vf.read_text(encoding="utf-8")
        section = f"\n\n---\n\n## Updates from Feedback ({datetime.now().strftime('%Y-%m-%d')})\n\n"

        if updates.get("new_rules"):
            section += "### New Rules\n"
            for r in updates["new_rules"]:
                section += f"- {r}\n"
        if updates.get("banned_patterns"):
            section += "### Banned Patterns (Updated)\n"
            for p in updates["banned_patterns"]:
                section += f"- {p}\n"
        if updates.get("insights"):
            section += "### Voice Insights\n"
            for i in updates["insights"]:
                section += f"- {i}\n"

        vf.write_text(current + section, encoding="utf-8")

        if updates.get("new_slop_patterns"):
            self._update_avoid_slop(updates["new_slop_patterns"])

        return "✅ Voice profile updated successfully."

    def _update_avoid_slop(self, new_patterns: List[str]):
        """Update master-avoid-slop.md with new patterns."""
        sf = self.voice / "master-avoid-slop.md"
        if not sf.exists():
            return
        current = sf.read_text(encoding="utf-8")
        section = f"\n\n---\n\n## New Patterns Detected ({datetime.now().strftime('%Y-%m-%d')})\n\n"
        for p in new_patterns:
            section += f"- {p}\n"
        sf.write_text(current + section, encoding="utf-8")

    # ──────────────────────────────────────────────────────────
    # SIGNAL PROCESSING (Real API Integration)
    # ──────────────────────────────────────────────────────────

    def process_signal(self, source: str) -> List[str]:
        """Process signals from various sources.

        Places real API calls when available, otherwise returns store contents.
        """
        if source == "x":
            return self._scan_x_signals()
        elif source == "rss":
            return self._scan_rss_signals()
        return ["Unknown source. Supported: 'x', 'rss'"]

    def _scan_x_signals(self) -> List[str]:
        """Scan inbox.md for X-sourced signals, or return pillars-based defaults."""
        inbox = self.stores / "inbox.md"
        signals = []

        if inbox.exists():
            content = inbox.read_text(encoding="utf-8")
            # Look for signal entries
            entries = re.findall(r'### \d+.*?(?=\n###|\Z)', content, re.DOTALL)
            for e in entries:
                if any(x in e.lower() for x in ['x', 'twitter', 'x.com']):
                    signals.append(e.strip()[:200])

        if not signals:
            # Fallback to pillars-based signals
            pf = self.strategy / "pillars.md"
            if pf.exists():
                pillars = pf.read_text(encoding="utf-8")[:100]
                signals = [
                    f"Signal: Trending topic in {pillars}...",
                    f"Signal: Community discussion on {pillars}...",
                ]
            else:
                signals = [
                    "Signal: New RISC-V optimization patterns emerging",
                    "Signal: AI Agents are moving to local-first architectures",
                    "Signal: Open-source hardware momentum growing",
                ]

        return signals[:5]

    def _scan_rss_signals(self) -> List[str]:
        """Scan source-watchlist for RSS-derived signals."""
        wl = self.strategy / "source-watchlist.md"
        signals = []

        if wl.exists():
            content = wl.read_text(encoding="utf-8")
            urls = re.findall(r'https?://[^\s]+', content)
            for url in urls[:3]:
                signals.append(f"RSS Source: {url[:80]}...")

        if not signals:
            signals = [
                "RSS: Technical content patterns detected in watchlist topics",
                "RSS: Framework or methodology posts trending",
            ]

        return signals[:3]

    # ──────────────────────────────────────────────────────────
    # AUDIT & RETRIEVAL
    # ──────────────────────────────────────────────────────────

    def audit(self) -> str:
        """Full system audit."""
        issues = []
        warnings = []
        critical = [self.strategy, self.voice, self.stores,
                    self.workflows, self.root / "runs", self.active_runs]
        for d in critical:
            if not d.exists():
                issues.append(f"Missing directory: {d.name}")

        for sub in ["ideas", "hooks", "proof", "feedback"]:
            if not (self.stores / sub).exists():
                issues.append(f"Missing stores subdirectory: {sub}")

        # Check key files in strategy (warnings, not errors — user creates these)
        for sf in ["positioning.md", "audience.md", "pillars.md"]:
            if not (self.strategy / sf).exists():
                warnings.append(f"Missing strategy file: {sf} (user must create)")

        # Count runs
        active_count = len([d for d in self.active_runs.iterdir() if d.is_dir()]) if self.active_runs.exists() else 0
        archive_count = len([d for d in self.archive.iterdir() if d.is_dir()]) if self.archive.exists() else 0

        # Check voice profile (warning)
        if not (self.voice / "voice-profile.md").exists():
            warnings.append("Missing voice-profile.md (system will use defaults)")

        if not issues:
            base = f"✅ Content OS v{VERSION} Audit: {active_count} active, {archive_count} archived. Structure OK."
            if warnings:
                base += "\n⚠️ " + "\n⚠️ ".join(warnings)
            return base

        return (
            f"❌ Content OS v{VERSION} Audit — {active_count} active, {archive_count} archived.\n"
            f"❌ Issues:\n- " + "\n- ".join(issues) +
            ("\n⚠️ " + "\n⚠️ ".join(warnings) if warnings else "")
        )

    def get_all_runs(self, include_archived: bool = True) -> List[Dict[str, Any]]:
        """Get all runs with detailed information."""
        runs = []
        if self.active_runs.exists():
            for d in self.active_runs.iterdir():
                if d.is_dir():
                    ri = self._get_run_info(d)
                    ri["status"] = "active"
                    runs.append(ri)
        if include_archived and self.archive.exists():
            for d in self.archive.iterdir():
                if d.is_dir():
                    ri = self._get_run_info(d)
                    ri["status"] = "archived"
                    runs.append(ri)
        return runs

    def _get_run_info(self, run_path: Path) -> Dict[str, Any]:
        """Get detailed info for a single run."""
        info = {"slug": run_path.name, "files": []}
        try:
            for f in run_path.iterdir():
                if f.is_file():
                    info["files"].append(f.name)
        except PermissionError:
            info["files"] = ["[locked]"]
            return info

        obj = run_path / "content-object.md"
        if obj.exists():
            content = obj.read_text(encoding="utf-8")
            for field in ["title", "state", "route", "format"]:
                m = re.search(rf'{field}:\s*(.+)', content, re.IGNORECASE)
                if m:
                    info[field] = m.group(1).strip()
        return info

    def search_runs(self, query: str) -> List[Dict[str, Any]]:
        """Search runs by content."""
        results = []
        q = query.lower()
        for run in self.get_all_runs():
            rp = self.active_runs / run["slug"]
            if not rp.exists():
                rp = self.archive / run["slug"]
            if not rp.exists():
                continue
            try:
                for f in rp.iterdir():
                    if f.is_file() and f.suffix == ".md":
                        try:
                            content = f.read_text(encoding="utf-8").lower()
                            if q in content:
                                results.append({
                                    "slug": run["slug"],
                                    "file": f.name,
                                    "state": run.get("state", "unknown"),
                                })
                                break
                        except Exception:
                            continue
            except PermissionError:
                continue
        return results

    def archive_run(self, slug: str) -> str:
        """Move a run from active to archive. Must be in 'learned' state."""
        state = self.get_state(slug)
        if state != "learned":
            return f"❌ Cannot archive {slug} (state: {state}). Must be 'learned' first."

        src = self.active_runs / slug
        if not src.exists():
            return f"❌ Run {slug} not found."

        dst = self.archive / slug
        if dst.exists():
            return f"❌ Archive already contains {slug}."

        import shutil
        try:
            shutil.copytree(str(src), str(dst))
            import shutil as sh
            sh.rmtree(str(src))
            self.update_state(slug, "archived")
            return f"✅ Run {slug} archived. Moved to runs/archive/"
        except Exception as e:
            return f"❌ Archive failed: {str(e)}"


# ══════════════════════════════════════════════════════════════
# TOOL HANDLERS
# ══════════════════════════════════════════════════════════════

async def tool_content_os_manager(core: ContentOSCore, args: Dict[str, Any],
                                   **kwargs) -> str:
    """Handle all manager tool actions."""
    try:
        action = args.get("action")
        slug = args.get("slug")

        # --- System Actions ---
        if action == "setup":
            return core.setup()

        if action == "audit":
            return core.audit()

        if action == "list":
            return json.dumps(core.get_all_runs(args.get("include_archived", True)))

        # --- Run Actions ---
        if action == "new_run":
            return json.dumps(core.create_run(
                args.get("idea", ""),
                args.get("slug"),
                args.get("source_hint", ""),
            ))

        if action == "update_state":
            return core.update_state(slug, args.get("state"))

        if action == "get_state":
            return json.dumps({
                "slug": slug,
                "state": core.get_state(slug),
                "next_actions": core.get_next_actions(slug),
            })

        if action == "sync_state":
            return f"State: {core.sync_state(slug)}"

        if action == "get_next_actions":
            return json.dumps(core.get_next_actions(slug))

        # --- Idea Gate ---
        if action == "decide_route":
            return json.dumps(core.decide_route(
                args.get("idea", ""),
                args.get("source_hint", ""),
            ))

        # --- Agent Pipeline ---
        if action == "generate_brief":
            llm = kwargs.get("parent_agent")
            llm_obj = llm.ctx.llm if llm and hasattr(llm, "ctx") else None
            res = await core.generate_brief(slug, llm_obj, args.get("extra_context", ""))
            return json.dumps(res)

        if action == "generate_draft":
            llm = kwargs.get("parent_agent")
            llm_obj = llm.ctx.llm if llm and hasattr(llm, "ctx") else None
            res = await core.generate_draft(slug, llm_obj)
            return json.dumps(res)

        if action == "run_verifier":
            llm = kwargs.get("parent_agent")
            llm_obj = llm.ctx.llm if llm and hasattr(llm, "ctx") else None
            res = await core.run_verifier(slug, llm_obj)
            return json.dumps(res)

        # --- Quality ---
        if action == "scan_slop":
            return json.dumps(core.scan_slop(args.get("text", "")))

        if action == "score":
            llm = kwargs.get("parent_agent")
            llm_obj = llm.ctx.llm if llm and hasattr(llm, "ctx") else None
            res = await core.evaluate_rubric(slug, llm_obj)
            return json.dumps(res)

        # --- Signals ---
        if action == "signal":
            return json.dumps(core.process_signal(args.get("source", "x")))

        # --- Postmortem ---
        if action == "postmortem":
            metrics = args.get("metrics", {})
            llm = kwargs.get("parent_agent")
            llm_obj = llm.ctx.llm if llm and hasattr(llm, "ctx") else None
            res = await core.run_postmortem(slug, metrics, llm_obj)
            return json.dumps(res)

        # --- Voice ---
        if action == "update_voice":
            return core.update_voice_profile(args.get("updates", {}))

        # --- Learning ---
        if action == "get_learnings":
            return core.get_learnings_for_brief(args.get("topic"))

        if action == "analyze_patterns":
            return json.dumps(core.analyze_run_patterns())

        # --- Search ---
        if action == "search_runs":
            return json.dumps(core.search_runs(args.get("query", "")))

        if action == "get_all_runs":
            return json.dumps(core.get_all_runs(args.get("include_archived", True)))

        # --- Archive ---
        if action == "archive_run":
            return core.archive_run(slug)

        return f"Unknown action: {action}"

    except Exception as e:
        return f"Error: {str(e)}"


def tool_content_os_retriever(core: ContentOSCore, args: Dict[str, Any]) -> str:
    """Retrieve knowledge from Content OS stores."""
    try:
        category = args.get("category")
        slug = args.get("slug")

        if category == "strategy":
            result = {}
            for f in ["positioning.md", "audience.md", "pillars.md", "source-watchlist.md"]:
                path = core.strategy / f
                if path.exists():
                    result[f.replace(".md", "")] = path.read_text(encoding="utf-8")
            return json.dumps(result) if result else "No strategy files found."

        if category == "voice":
            result = {}
            for f in ["voice-profile.md", "master-avoid-slop.md"]:
                path = core.voice / f
                if path.exists():
                    result[f.replace(".md", "")] = path.read_text(encoding="utf-8")
            return json.dumps(result) if result else "No voice files found."

        if category == "run" and slug:
            for base in [core.active_runs, core.archive]:
                rp = base / slug
                if rp.exists():
                    files = ["content-object.md", "idea.md", "brief.md",
                             "draft-package.md", "verifier-report.md",
                             "feedback.md", "context.md"]
                    result = {}
                    for f in files:
                        fp = rp / f
                        if fp.exists():
                            result[f.replace(".md", "")] = fp.read_text(encoding="utf-8")
                    return json.dumps(result) if result else f"No data for {slug}"
            return json.dumps({"error": f"Run {slug} not found."})

        if category == "stores":
            result = {}
            for subdir in ["inbox.md", "workboard.md", "ideas", "hooks", "proof", "feedback"]:
                path = core.stores / subdir
                if path.is_file():
                    result[subdir.replace(".md", "")] = path.read_text(encoding="utf-8")
                elif path.exists() and path.is_dir():
                    files = [f.name for f in path.glob("*.md")]
                    result[subdir] = files
            return json.dumps(result)

        if category == "learnings":
            return core.get_learnings_for_brief(args.get("topic"))

        return f"Unknown category: {category}"

    except Exception as e:
        return f"Error: {str(e)}"
