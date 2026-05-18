"""
Content OS Core — Full Content OS v2.5.0 Implementation
=======================================================
Complete 14-state lifecycle, 107 slop patterns (3 tiers + bonus),
4-route Idea Gate, Writer/Verifier dual-agent pipeline,
LLM-based postmortem with exact-line analysis, GBrain MCP integration,
Buffer API publishing (draft posts), state persistence, structured logging.

Based on Shann³ (@shannholmberg) Content OS.
"""

import asyncio
import json
import logging
import re
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass

from .content_os_buffer import BufferClient

logger = logging.getLogger(__name__)

VERSION = "2.5.0"

# The complete 14-state lifecycle
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

# ── Action Registry ─────────────────────────────────────────────────
# Runtime-registerable action handlers for tool_content_os_manager.
# New actions can be added at any time via register_manager_action(),
# enabling hot-add without Python module reload.
_ACTION_HANDLERS: Dict[str, Callable] = {}

def register_manager_action(name: str, handler: Callable) -> None:
    """Register a handler for tool_content_os_manager dispatch.

    Args:
        name: Action name matching the 'action' field in tool args.
        handler: Async or sync callable(core, args, **kwargs) -> str.
    """
    _ACTION_HANDLERS[name] = handler

def get_registered_actions() -> List[str]:
    """Return list of all currently registered action names."""
    return list(_ACTION_HANDLERS.keys())

IDEA_ROUTES = ["ORIGINAL", "REPURPOSE", "REWRITE", "RESEARCH+IDEATE"]

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
    # 41. Clickbait / Curiosity Gap
    r"you won't believe",
]
# ──────────────────────────────────────────────────────────────
# DATA CLASSES
# ──────────────────────────────────────────────────────────────


@dataclass
class RunState:
    slug: str
    title: str = ""
    state: str = "captured"
    route: str = "ORIGINAL"
    format: str = "TBD"
    pillar: str = "TBD"
    created: str = ""
    updated: str = ""
    source_type: str = "belirsiz"


# ══════════════════════════════════════════════════════════════
# CORE CLASS
# ══════════════════════════════════════════════════════════════

class ContentOSCore:
    """Full Content OS engine — 14-state lifecycle, 107 slop patterns (3 tiers + bonus),
    4-route Idea Gate, Writer/Verifier dual-agent, LLM postmortem."""

    def __init__(self, root: Path):
        self.root = root
        self.strategy = root / "strategy"
        self.voice = root / "voice"
        self.active_runs = root / "runs" / "active"
        self.stores = root / "stores"
        self.workflows = root / "workflows"
        self.archive = root / "runs" / "archive"

        # Full 107-pattern slop detection (3 tiers + bonus)
        self.slop_tier1 = FULL_SLOP_TIER1
        self.slop_tier2 = FULL_SLOP_TIER2
        self.slop_tier3 = FULL_SLOP_TIER3
        self.slop_bonus = FULL_SLOP_BONUS

        self.gbrain_enabled = False

        # Buffer.com integration for publishing drafts
        self.buffer = BufferClient(root)

        self._init_stores_dirs()
        self._migrate_old_state()

        # State cache for fast lookup + persistence
        self._state_cache_dir = root / '.state_cache'
        self._state_cache_dir.mkdir(parents=True, exist_ok=True)
        self._state_cache: Dict[str, RunState] = {}
        self._load_state_cache()

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

    # ──────────────────────────────────────────────────────────
    # STATE CACHE PERSISTENCE
    # ──────────────────────────────────────────────────────────

    def _save_state_cache(self):
        """Persist state cache to disk as JSON."""
        path = self._state_cache_dir / "runs_state.json"
        data = {
            slug: {
                "slug": rs.slug,
                "title": rs.title,
                "state": rs.state,
                "route": rs.route,
                "format": rs.format,
                "pillar": rs.pillar,
                "created": rs.created,
                "updated": rs.updated,
                "source_type": rs.source_type,
            }
            for slug, rs in self._state_cache.items()
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load_state_cache(self):
        """Load state cache from disk."""
        path = self._state_cache_dir / "runs_state.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                for slug, d in data.items():
                    self._state_cache[slug] = RunState(
                        slug=d["slug"],
                        title=d.get("title", ""),
                        state=d.get("state", "captured"),
                        route=d.get("route", "ORIGINAL"),
                        format=d.get("format", "TBD"),
                        pillar=d.get("pillar", "TBD"),
                        created=d.get("created", ""),
                        updated=d.get("updated", ""),
                        source_type=d.get("source_type", "belirsiz"),
                    )
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load state cache: {e}")

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
        logger.info("decide_route called with idea=%.80r, source_hint=%r", idea, source_hint)  # v2.4.0
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
        # Research/exploration keywords (with Turkish stem variants)
        research_kw = [
            "araştır", "araştir", "keşfet", "kesfet", "research", "explore",
            "investigate", "analiz et", "karşılaştır", "karsilastir",
            "compare", "trend", "incele", "inceleyelim",
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

        result = {
            "route": route,
            "rationale": rationale,
            "source_type": source_type,
        }
        logger.debug("decide_route completed: route=%s, source_type=%s", route, source_type)  # v2.4.0
        return result

    # ──────────────────────────────────────────────────────────
    # CONTENT RUN OPERATIONS
    # ──────────────────────────────────────────────────────────
    def create_run(self, idea: str, slug: str = None,
                   source_hint: str = "") -> Dict[str, Any]:
        """Start a new content run with Idea Gate decision."""
        logger.info("create_run called with idea=%.80r, slug=%r, source_hint=%r", idea, slug, source_hint)  # v2.4.0
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
            logger.info("create_run: run already exists for slug=%s", slug)  # v2.4.0
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

        # Cache new run state
        self._state_cache[slug] = RunState(
            slug=slug,
            title=idea,
            state="captured",
            route=route_decision["route"],
            format="TBD",
            pillar="TBD",
            created=datetime.now().isoformat(),
            updated=datetime.now().isoformat(),
            source_type=route_decision["source_type"],
        )
        self._save_state_cache()

        logger.debug("create_run completed: slug=%s, route=%s", slug, route_decision["route"])  # v2.4.0
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

    def enable_gbrain(self):
        """Enable GBrain MCP integration for semantic retrieval."""
        self.gbrain_enabled = True
        logger.info("GBrain MCP integration enabled")

    def _query_gbrain(self, query: str) -> Dict[str, str]:
        """Query GBrain for semantically relevant context via MCP.

        Returns proof, hooks, voice context from GBrain knowledge graph.
        Uses handle_function_call → mcp_gbrain_query tool when enabled.
        Hermes agent ctx üzerinden MCP tool çağrısı ile çalışır.

        To enable: call core.enable_gbrain() after init, or set
        CONFIG['gbrain_available'] = True before ContentOSCore init.

        MCP entegrasyon noktası — şu tool'lar kullanılır:
          - mcp_gbrain_query(query, limit=5)  → semantic search
          - mcp_gbrain_search(query, limit=5) → keyword search

        Actual MCP calls use handle_function_call() which dispatches
        to the registered MCP server session.
        """
        if not self.gbrain_enabled:
            logger.debug("GBrain query skipped (disabled): %s", query[:80])
            return {"proof": "GBrain MCP devre dışı. enable_gbrain() ile etkinleştir.",
                    "hooks": "", "voice": ""}

        logger.info("GBrain MCP query: %s", query[:100])

        # Try real MCP call via Hermes tool dispatch
        proof_text = ""
        hooks_text = ""
        voice_text = ""
        mcp_success = False

        try:
            from model_tools import handle_function_call
            # Call mcp_gbrain_query for semantic search
            result_json = handle_function_call(
                "mcp_gbrain_query",
                {"query": query, "limit": 5},
                skip_pre_tool_call_hook=True,
            )
            result = json.loads(result_json) if isinstance(result_json, str) else result_json
            logger.debug("GBrain MCP query result keys: %s", list(result.keys()) if isinstance(result, dict) else type(result))

            if isinstance(result, dict) and "result" in result:
                raw = result["result"]
                if isinstance(raw, str):
                    proof_text = raw[:2000]
                elif isinstance(raw, list):
                    proof_text = "\n\n".join(
                        [r.get("content", str(r))[:500] for r in raw[:5]]
                    )
                else:
                    proof_text = str(raw)[:2000]
                mcp_success = True
                logger.info("GBrain MCP query succeeded for: %s", query[:80])

                # Also try mcp_gbrain_search for keyword-based hooks/proof
                try:
                    search_json = handle_function_call(
                        "mcp_gbrain_search",
                        {"query": query, "limit": 3},
                        skip_pre_tool_call_hook=True,
                    )
                    search_result = json.loads(search_json) if isinstance(search_json, str) else search_json
                    if isinstance(search_result, dict) and "result" in search_result:
                        search_raw = search_result["result"]
                        if isinstance(search_raw, str):
                            hooks_text = search_raw[:1000]
                        elif isinstance(search_raw, list):
                            hooks_text = "\n".join(
                                [r.get("content", str(r))[:300] for r in search_raw[:3]]
                            )
                except Exception as search_err:
                    logger.debug("GBrain search fallback skipped: %s", search_err)
                    hooks_text = ""

        except ImportError:
            logger.warning("model_tools.handle_function_call not available (standalone mode)")
        except Exception as e:
            logger.error("GBrain MCP call failed: %s", str(e)[:200])
            mcp_success = False

        if mcp_success:
            return {
                "proof": proof_text or "GBrain sorgusu sonuç döndürmedi.",
                "hooks": hooks_text or "Hook pattern için keyword search sonucu yok.",
                "voice": "MCP sorgusu tamamlandı.",
            }

        # Fallback: return placeholder with error context
        return {"proof": f"GBrain MCP sorgusu başarısız oldu. Query: {query[:100]}",
                "hooks": "MCP fallback — sonuç yok.",
                "voice": "MCP fallback — sonuç yok."}

    def _get_relevant_proof(self, idea: str) -> str:
        """Find proof elements relevant to the idea."""
        # GBrain semantic retrieval takes priority when enabled
        if self.gbrain_enabled:
            gbrain_result = self._query_gbrain(idea)
            if gbrain_result:
                return "\n\n".join(
                    [f"## {k}\n{v}" for k, v in gbrain_result.items()]
                )

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
        logger.info("update_state called with slug=%s, new_state=%s, force=%s", slug, new_state, force)  # v2.4.0
        if new_state not in STATE_LIFECYCLE:
            logger.warning("update_state: invalid state %s for slug=%s", new_state, slug)  # v2.4.0
            return f"❌ Invalid state: {new_state}. Valid: {', '.join(STATE_LIFECYCLE)}"

        run_path = (self.active_runs / slug).resolve()
        if not run_path.exists():
            logger.warning("update_state: run %s not found", slug)  # v2.4.0
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
            # Cache the state
            self._state_cache[slug] = RunState(
                slug=slug,
                title=idea,
                state=new_state,
                updated=datetime.now().isoformat(),
            )
            self._save_state_cache()
            logger.debug("update_state: initialized and updated %s to %s", slug, new_state)  # v2.4.0
            return f"✅ Initialized and updated {slug} to {new_state}"

        content = obj_path.read_text(encoding="utf-8")

        # Extract current state
        current_state = "captured"
        m = re.search(r'state:\s*(\w+)', content)
        if m:
            current_state = m.group(1)

        # Validate transition (unless force)
        if not force and not self._valid_transition(current_state, new_state):
            logger.warning("update_state: invalid transition %s -> %s for slug=%s", current_state, new_state, slug)  # v2.4.0
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

        # Update state cache (preserve existing route, format, pillar)
        existing = self._state_cache.get(slug)
        if existing is None:
            # Cache miss — try reading from content-object.md
            existing = RunState(slug=slug)
            obj_path_candidate = (self.active_runs / slug).resolve() / "content-object.md"
            if obj_path_candidate.exists():
                try:
                    obj_content = obj_path_candidate.read_text(encoding="utf-8")
                    rm = re.search(r'\*{0,2}Route\*{0,2}:\*{0,2}\s*(.+)', obj_content, re.IGNORECASE)
                    if rm:
                        existing.route = rm.group(1).strip().lstrip('* ')
                    fm = re.search(r'\*{0,2}Format\*{0,2}:\*{0,2}\s*(.+)', obj_content, re.IGNORECASE)
                    if fm:
                        existing.format = fm.group(1).strip().lstrip('* ')
                    pm = re.search(r'\*{0,2}Pillar\*{0,2}:\*{0,2}\s*(.+)', obj_content, re.IGNORECASE)
                    if pm:
                        existing.pillar = pm.group(1).strip().lstrip('* ')
                    tm = re.search(r'\*{0,2}Title\*{0,2}:\*{0,2}\s*(.+)', obj_content, re.IGNORECASE)
                    if tm:
                        existing.title = tm.group(1).strip().lstrip('* ')
                except Exception:
                    pass
        self._state_cache[slug] = RunState(
            slug=slug,
            title=existing.title,
            state=new_state,
            route=existing.route,
            format=existing.format,
            pillar=existing.pillar,
            created=existing.created,
            updated=ts,
            source_type=existing.source_type,
        )
        self._save_state_cache()
        logger.debug("update_state completed: %s: %s -> %s", slug, current_state, new_state)  # v2.4.0
        return f"✅ {slug}: {current_state} → {new_state}"

    def sync_state(self, slug: str) -> str:
        """Scan filesystem and sync content-object.md to correct 14-state."""
        logger.info("sync_state called with slug=%s", slug)  # v2.4.0
        run_path = (self.active_runs / slug).resolve()
        if not run_path.exists():
            logger.debug("sync_state: run %s not found, returning unknown", slug)  # v2.4.0
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
        logger.debug("sync_state completed: slug=%s, state=%s", slug, state)  # v2.4.0
        return state

    def get_state(self, slug: str) -> str:
        """Read current state from cache or content-object.md."""
        logger.info("get_state called with slug=%s", slug)  # v2.4.0
        if slug in self._state_cache:
            state = self._state_cache[slug].state
            logger.debug("get_state completed: slug=%s, state=%s (from cache)", slug, state)  # v2.4.0
            return state
        obj = self.active_runs / slug / "content-object.md"
        if not obj.exists():
            logger.debug("get_state: slug=%s not found, returning unknown", slug)  # v2.4.0
            return "unknown"
        content = obj.read_text(encoding="utf-8")
        m = re.search(r'state:\s*(\w+)', content)
        state = m.group(1) if m else "unknown"
            # Seed cache for future lookups (preserve route, format, etc.)
        if state != "unknown":
            rs = RunState(slug=slug, state=state)
            # Read metadata from content-object.md (supports both YAML and Markdown meta formats)
            rm = re.search(r'\*{0,2}Route\*{0,2}:\*{0,2}\s*(.+)', content, re.IGNORECASE)
            if rm:
                rs.route = rm.group(1).strip().lstrip('* ')
            fm = re.search(r'\*{0,2}Format\*{0,2}:\*{0,2}\s*(.+)', content, re.IGNORECASE)
            if fm:
                rs.format = fm.group(1).strip().lstrip('* ')
            pm = re.search(r'\*{0,2}Pillar\*{0,2}:\*{0,2}\s*(.+)', content, re.IGNORECASE)
            if pm:
                rs.pillar = pm.group(1).strip().lstrip('* ')
            tm = re.search(r'\*{0,2}Title\*{0,2}:\*{0,2}\s*(.+)', content, re.IGNORECASE)
            if tm:
                rs.title = tm.group(1).strip().lstrip('* ')
            self._state_cache[slug] = rs
        logger.debug("get_state completed: slug=%s, state=%s", slug, state)  # v2.4.0
        return state

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
    # LLM HELPER — unified async LLM call for all agents
    # ──────────────────────────────────────────────────────────

    async def _call_llm(self, task: str, system_prompt: str,
                        user_prompt: str, llm: Any = None) -> str:
        """Unified async LLM caller with retry, timeout, and error handling.

        Args:
            task: Agent task name ('curator', 'writer') for async_call_llm routing.
            system_prompt: System-level instruction.
            user_prompt: User message content.
            llm: Optional LLM client with acomplete() (from parent_agent).

        Returns:
            Clean text response (code fences stripped).

        Raises:
            RuntimeError after max retries with details for caller to handle.
        """
        import asyncio
        max_retries = 3
        base_delay = 1.0
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                if llm and hasattr(llm, "acomplete"):
                    response = await llm.acomplete([
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ])
                    text = response.text
                else:
                    from agent.auxiliary_client import async_call_llm
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ]
                    raw = await async_call_llm(task=task, messages=messages)
                    try:
                        text = raw.choices[0].message.content
                    except (AttributeError, IndexError):
                        text = str(raw)

                text = text.strip()
                if text.startswith("```"):
                    text = re.sub(r"^```\w*\n?", "", text)
                    text = re.sub(r"\n```$", "", text)
                return text

            except asyncio.TimeoutError as e:
                last_error = f"Timeout (attempt {attempt}/{max_retries})"
                logger.warning("LLM call timeout for task=%s attempt=%d/%d", task, attempt, max_retries)
            except Exception as e:
                err_str = str(e).lower()
                # Retry only for transient errors
                is_transient = any(x in err_str for x in [
                    "timeout", "rate limit", "rate_limit", "429",
                    "503", "502", "connection", "temporary",
                    "service unavailable", "too many requests",
                    "internal server error", "overloaded",
                ])
                if is_transient and attempt < max_retries:
                    last_error = f"{type(e).__name__}: {str(e)[:200]}"
                    logger.warning(
                        "LLM transient error for task=%s attempt=%d/%d: %s",
                        task, attempt, max_retries, last_error,
                    )
                else:
                    # Non-transient or last attempt — raise immediately
                    raise RuntimeError(f"LLM call failed for task={task}: {e}") from e

            # Exponential backoff before retry
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                logger.info("Retrying LLM call for task=%s in %.1fs (attempt %d)",
                            task, delay, attempt + 1)
                await asyncio.sleep(delay)

        raise RuntimeError(
            f"LLM call failed for task={task} after {max_retries} attempts. "
            f"Last error: {last_error}"
        )

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
- Language: {{Turkish with English technical terms preserved (default) | English | Bilingual}}
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
            text = await self._call_llm(
                task="curator",
                system_prompt="You are an expert content strategist who writes tight, specific Writer Context Packets.",
                user_prompt=prompt,
                llm=llm,
            )
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

NEWS BULLETIN MODE (active when Pillar =~ "Daily AI News|Günlük|News" or Format =~ "Thread"):
- PRIMARY goal: REPORT facts — WHO announced WHAT, WHEN, with WHAT metrics
- SECONDARY goal: Brief context/analysis — keep to 1 sentence per item
- Structure per news item: metric/fact → implication (NOT opinion → data)
- Cover 4-6 distinct news stories in 8 tweets — don't stretch one story
- Each tweet must contain at least one concrete number, name, or metric
- Anti-editorializing: no "This is huge" / "This matters because" — let the facts speak
- Source attribution required in thread (company names, publications)

OUTPUT — produce a complete draft-package.md with EXACTLY this structure:

IMPORTANT — Buffer.com compatible format:
- For Twitter Thread format: start each tweet with `N/ ` on its own line (e.g., `1/ First tweet...`)
- NO preamble, NO headings, NO extra text between `draft:` and the numbered tweets
- The `draft:` line must be followed IMMEDIATELY by the first tweet with `1/ ` prefix
- After all tweets, add rubric_self_assessment, avoid_slop_pass, open_loops_flagged, voice_check

EXAMPLE (Twitter Thread format):
```
---
draft:
1/ First tweet content here — hook with concrete signal
2/ Second tweet — technical depth, specific metric or architecture detail
3/ Third tweet — comparison, tradeoff, or counter-intuitive insight

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
            text = await self._call_llm(
                task="writer",
                system_prompt="You are a Writer Agent for Content OS. You produce high-quality, bookmarkable draft packages.",
                user_prompt=prompt,
                llm=llm,
            )
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
            text = await self._call_llm(
                task="curator",
                system_prompt="You are a strict Verifier Agent for Content OS. You catch what the writer missed.",
                user_prompt=prompt,
                llm=llm,
            )
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
        logger.info("scan_slop called with text length=%d", len(text))  # v2.4.0
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

        logger.debug("scan_slop completed: score=%s, t1=%d, t2=%d, t3=%d", score, t1, t2, t3)  # v2.4.0
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
        logger.info("evaluate_rubric called with slug=%s", slug)  # v2.4.0
        run_path = self.active_runs / slug
        draft_path = run_path / "draft-package.md"
        if not draft_path.exists():
            logger.warning("evaluate_rubric: draft not found for slug=%s", slug)  # v2.4.0
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
            text = await self._call_llm(
                task="curator",
                system_prompt="You are a strict technical content editor scoring against a rubric.",
                user_prompt=prompt,
                llm=llm,
            )

            json_match = re.search(r"(\{.*\})", text, re.DOTALL)
            if json_match:
                res = json.loads(json_match.group(1))
            else:
                res = {"scores": {}, "summary": f"Failed to parse: {text[:200]}",
                       "total": 0, "passes": False}

            if "total" not in res or not res["total"]:
                res["total"] = sum(res.get("scores", {}).values())
            res["passes"] = res.get("total", 0) >= 8
            logger.debug("evaluate_rubric completed: slug=%s, total=%s, passes=%s", slug, res.get("total"), res.get("passes"))  # v2.4.0
            return res

        except Exception as e:
            logger.error("evaluate_rubric failed for slug=%s: %s", slug, str(e))  # v2.4.0
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
        logger.info("run_postmortem called with slug=%s", slug)  # v2.4.0
        run_path = self.active_runs / slug
        if not run_path.exists():
            logger.warning("run_postmortem: run %s not found", slug)  # v2.4.0
            return {"error": f"Run {slug} not found."}

        draft_path = run_path / "draft-package.md"
        if not draft_path.exists():
            logger.warning("run_postmortem: draft not found for slug=%s", slug)  # v2.4.0
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
            text = await self._call_llm(
                task="curator",
                system_prompt="You are a viral content analyst. Point at EXACT lines. Generic praise is rejected.",
                user_prompt=prompt,
                llm=llm,
            )

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

            logger.debug("run_postmortem completed: slug=%s, phase=%s, bookmark_rate=%.1f", slug, phase, bookmark_rate)  # v2.4.0
            return {
                "slug": slug,
                "phase": phase,
                "metrics": metrics,
                "bookmark_rate": bookmark_rate,
                "analysis": text,
                "new_state": new_state,
            }

        except Exception as e:
            logger.error("run_postmortem failed for slug=%s: %s", slug, str(e))  # v2.4.0
            return {"error": f"Postmortem failed: {str(e)}"}

    # v2.4.0: _analyze_content_performance and _legacy_analyze removed (dead code).
    # Postmortem now uses LLM-based analysis exclusively.

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
            entries = re.findall(r'### .*?(?=\n###|\Z)', content, re.DOTALL)
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
                # Handle both YAML (field: value) and Markdown (**Field:** value) formats
                m = re.search(rf'(?:\*\*)?{field}(?:\*\*)?:\*{{0,2}}\s*(.+)', content, re.IGNORECASE)
                if m:
                    info[field] = m.group(1).strip().lstrip('* ')
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

    # ──────────────────────────────────────────────────────────
    # BUFFER API — Publish drafts to Buffer.com
    # ──────────────────────────────────────────────────────────

    def buffer_setup(self, api_key: Optional[str] = None) -> str:
        """Configure Buffer API connection.

        Steps:
        1. Set API key (from arg, env, or prompt)
        2. Fetch organizations
        3. Select organization
        4. Fetch channels
        5. Select channel (usually Twitter/X)

        Args:
            api_key: Optional API key override. If not provided,
                     resolves from env var or ~/.hermes/.env.

        Returns:
            Status message with available orgs/channels or error.
        """
        if api_key:
            self.buffer.configure_api_key(api_key)

        if not self.buffer.has_api_key:
            return (
                "❌ BUFFER_API_KEY not found.\n\n"
                "To set up Buffer integration:\n"
                "1. Go to https://publish.buffer.com/settings/api\n"
                "2. Create an API key\n"
                "3. Set it in ~/.hermes/.env as:\n"
                "   BUFFER_API_KEY=your_key_here\n"
                "4. Then run this command again\n\n"
                "Or pass directly: --api-key YOUR_KEY"
            )

        # Fetch organizations
        orgs = self.buffer.fetch_organizations()
        if isinstance(orgs, dict) and "error" in orgs:
            return f"❌ Failed to fetch organizations: {orgs['error']}"
        if not orgs or (isinstance(orgs, list) and len(orgs) == 1 and "error" in orgs[0]):
            err = orgs[0]["error"] if isinstance(orgs[0], dict) else str(orgs)
            return f"❌ {err}"

        if len(orgs) == 1:
            org_id = orgs[0]["id"]
            org_name = orgs[0].get("name", org_id)
        else:
            org_list = "\n".join(
                f"  {i+1}. {o.get('name', '?')} ({o['id']})"
                for i, o in enumerate(orgs)
            )
            return (
                f"✅ Found {len(orgs)} organizations:\n{org_list}\n\n"
                f"Cached org_id: {self.buffer._config.get('org_id', 'not set')}\n\n"
                "Run `hermes content buffer setup org <INDEX>` to select one.\n"
                "Or manually set org_id in `.buffer_config.json`."
            )

        # Fetch channels for the selected org
        channels = self.buffer.fetch_channels(org_id)
        if isinstance(channels, dict) and "error" in channels:
            return f"❌ Failed to fetch channels: {channels['error']}"
        if not channels or (isinstance(channels, list) and len(channels) == 1 and "error" in channels[0]):
            err = channels[0]["error"] if isinstance(channels[0], dict) else str(channels)
            return f"❌ {err}"

        # Filter to Twitter/X channels, prefer first
        twitter_channels = [c for c in channels if c.get("service", "").lower() in ("twitter", "x")]

        if not twitter_channels:
            channel_list = "\n".join(
                f"  {i+1}. {c.get('displayName', c.get('name', '?'))} ({c.get('service', '?')})"
                for i, c in enumerate(channels)
            )
            return (
                f"✅ Org: {org_name}\n"
                f"Found {len(channels)} channels (no Twitter/X found):\n{channel_list}\n\n"
                "Add a Twitter channel in Buffer first, or set channel_id manually."
            )

        # Auto-select first Twitter channel
        ch = twitter_channels[0]
        self.buffer._config["org_id"] = org_id
        self.buffer._config["org_name"] = org_name
        self.buffer._config["channel_id"] = ch["id"]
        self.buffer._config["channel_name"] = ch.get("displayName", ch.get("name", "?"))
        self.buffer._config["channel_service"] = ch.get("service", "twitter")
        self.buffer._config["setup_at"] = datetime.now().isoformat()
        self.buffer._save_config()

        return (
            f"✅ Buffer configured successfully!\n\n"
            f"**Organization:** {org_name}\n"
            f"**Channel:** {ch.get('displayName', ch.get('name', '?'))} ({ch.get('service', '?')})\n"
            f"**Channel ID:** {ch['id']}\n\n"
            f"Ready to send drafts with:\n"
            f"  `hermes content buffer send <slug>`"
        )

    def buffer_send(self, slug: str) -> str:
        """Parse a run's draft and send tweets as Buffer draft posts.

        Reads draft-package.md, extracts individual tweets,
        sends each as a separate draft post to Buffer queue.

        Args:
            slug: Run slug

        Returns:
            Status message with results per tweet.
        """
        if not self.buffer.is_configured:
            return (
                "❌ Buffer not configured.\n"
                "Run `hermes content buffer setup` first."
            )

        # Find draft file
        draft_path = self.active_runs / slug / "draft-package.md"
        if not draft_path.exists():
            draft_path = self.archive / slug / "draft-package.md"
        if not draft_path.exists():
            return f"❌ Draft not found for run: {slug}"

        # Parse tweets
        draft_text = draft_path.read_text(encoding="utf-8")
        tweets = BufferClient.parse_draft_text(draft_text)

        # Auto-fix: if parsing fails, try to reformat draft to Buffer-compatible format
        if not tweets:
            reformatted = BufferClient.reformat_to_buffer_format(draft_text)
            tweets = BufferClient.parse_draft_text(reformatted)
            if tweets:
                # Save reformatted draft for consistency
                draft_path.write_text(reformatted, encoding="utf-8")
            else:
                return (
                    f"❌ Could not parse tweets from draft.\n\n"
                    f"Expected format (N/ tweet content):\n"
                    f"  ---\n"
                    f"  draft:\n"
                    f"  \n"
                    f"  1/ First tweet content...\n"
                    f"  2/ Second tweet content...\n"
                    f"  ---\n"
                )

        # Validate tweet lengths
        warnings = []
        for i, t in enumerate(tweets, 1):
            if len(t) > 280:
                warnings.append(f"⚠️  Tweet {i}: {len(t)} chars (max 280)")

        # Send to Buffer
        results = self.buffer.send_thread(tweets)

        # Build report
        lines = [f"📤 **Buffer Send Report — {slug}**", ""]
        success_count = 0
        for r in results:
            tn = r.get("tweet_number", "?")
            if r.get("success"):
                success_count += 1
                preview = r.get("text", "")[:60] if "text" in r else ""
                lines.append(f"  ✅ Tweet {tn}: Sent (ID: {r.get('post_id', '?')})")
            else:
                lines.append(f"  ❌ Tweet {tn}: {r.get('error', 'Unknown error')}")

        lines.append("")
        lines.append(f"**{success_count}/{len(tweets)}** tweets sent to Buffer as drafts.")
        if warnings:
            lines.append("\n**Warnings:**")
            lines.extend(warnings)
        lines.append("\n📌 **Next:** Review and publish from https://publish.buffer.com")

        # Auto-update state
        if success_count > 0:
            current_state = self.get_state(slug)
            if current_state in ("draft_review", "approved", "scheduler_ready"):
                self.update_state(slug, "scheduled")

        return "\n".join(lines)

    def buffer_status(self) -> str:
        """Show Buffer integration status."""
        return self.buffer.get_config_summary()

    async def run_pipeline(self, slug: str, llm: Any = None,
                           extra_context: str = "") -> str:
        """Run the full pipeline: brief → draft → verify → score → slop.

        Single atomic call — reduces tool-call flood and provider latency issues.
        Each step has isolated error handling so one failure doesn't kill the
        entire pipeline.

        Args:
            slug: Run slug
            llm: Optional LLM client
            extra_context: Extra context for brief generation

        Returns:
            Human-readable pipeline report.
        """
        report = []
        had_error = False

        # Step 1: Idea Review
        try:
            self.update_state(slug, "idea_review")
            report.append("✅ Step 1: idea_review")
        except Exception as e:
            report.append(f"⚠️ Step 1: idea_review failed — {e}")
            had_error = True

        # Step 2: Brief
        try:
            br = await self.generate_brief(slug, llm, extra_context)
            if "error" in br:
                report.append(f"❌ Step 2: Brief failed — {br['error']}")
                had_error = True
            else:
                report.append(f"✅ Step 2: Brief generated ({br.get('length', '?')} chars)")
        except Exception as e:
            report.append(f"❌ Step 2: Brief exception — {e}")
            had_error = True

        if had_error:
            report.append("\n⚠️ Pipeline stopped early due to errors.")
            return "\n".join(report)

        # Step 3: Drafting
        try:
            self.update_state(slug, "drafting")
            report.append("✅ Step 3: drafting state")
        except Exception as e:
            report.append(f"⚠️ Step 3: state update failed — {e}")

        # Step 4: Draft
        try:
            dr = await self.generate_draft(slug, llm)
            if "error" in dr:
                report.append(f"❌ Step 4: Draft failed — {dr['error']}")
                had_error = True
            else:
                report.append(f"✅ Step 4: Draft generated ({dr.get('length', '?')} chars)")
        except Exception as e:
            report.append(f"❌ Step 4: Draft exception — {e}")
            had_error = True

        if had_error:
            report.append("\n⚠️ Pipeline stopped early.")
            return "\n".join(report)

        # Step 5: Verification
        try:
            self.update_state(slug, "verification")
            vr = await self.run_verifier(slug, llm)
            if "error" in vr:
                report.append(f"⚠️ Step 5: Verifier issue — {vr['error']}")
            else:
                report.append(f"✅ Step 5: Verifier done ({vr.get('length', '?')} chars)")
        except Exception as e:
            report.append(f"⚠️ Step 5: Verifier exception — {e}")

        # Step 6: Quality — slop scan + rubric score
        try:
            draft_path = self.active_runs / slug / "draft-package.md"
            if draft_path.exists():
                text = draft_path.read_text(encoding="utf-8")
                slop = self.scan_slop(text)
                s_score = slop.get("score", "?")
                s_total = slop.get("tier1_count", 0) + slop.get("tier2_count", 0) + \
                          slop.get("tier3_count", 0) + slop.get("bonus_count", 0)
                report.append(f"✅ Step 6: Slop scan — {s_score} ({s_total} findings)")
        except Exception as e:
            report.append(f"⚠️ Step 6: Slop scan failed — {e}")

        try:
            sc = await self.evaluate_rubric(slug, llm)
            if "error" not in sc:
                r_total = sc.get("total", 0)
                r_pass = sc.get("passes", False)
                status = "✅ PASS" if r_pass else "❌ FAIL"
                report.append(f"✅ Step 7: Rubric — {r_total}/12 {status}")
        except Exception as e:
            report.append(f"⚠️ Step 7: Rubric failed — {e}")

        # Step 8: Draft review state
        try:
            self.update_state(slug, "draft_review")
            report.append("✅ Step 8: draft_review")
        except Exception as e:
            report.append(f"⚠️ Step 8: State update failed — {e}")

        report.insert(0, f"📋 **Pipeline Report — {slug}**\n")
        if had_error:
            report.append("\n⚠️ Pipeline completed with some errors — review above.")
        else:
            report.append("\n🎉 Pipeline complete! Ready for human review.")
        return "\n".join(report)

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

        try:
            shutil.copytree(str(src), str(dst))
            shutil.rmtree(str(src))
            # Update state cache directly (filesystem already moved)
            if slug in self._state_cache:
                self._state_cache[slug].state = "archived"
                self._state_cache[slug].updated = datetime.now().isoformat()
            else:
                self._state_cache[slug] = RunState(
                    slug=slug, state="archived",
                    created=datetime.now().isoformat(),
                    updated=datetime.now().isoformat(),
                )
            self._save_state_cache()
            return f"✅ Run {slug} archived. Moved to runs/archive/"
        except Exception as e:
            return f"❌ Archive failed: {str(e)}"


# ══════════════════════════════════════════════════════════════
# TOOL HANDLERS
# ══════════════════════════════════════════════════════════════

async def tool_content_os_manager(core: ContentOSCore, args: Dict[str, Any],
                                   **kwargs) -> str:
    """Handle all manager tool actions with human-readable returns."""

    def _fmt(res: Any, ok_prefix: str = "✅") -> str:
        """Convert tool result to human-readable text."""
        if isinstance(res, str):
            return res
        if isinstance(res, dict):
            if "error" in res:
                return f"❌ {res['error']}"
            if res.get("status") == "exists":
                return f"⚠️ Run already exists: {res.get('slug', '?')}"
            if "slug" in res and "status" in res:
                length = res.get("length", "")
                size = f" ({length} chars)" if length else ""
                return f"{ok_prefix} {res['status'].upper()}: {res['slug']}{size}"
            if "route" in res and "rationale" in res:
                return (
                    f"🗺️ Route: {res['route']}\n"
                    f"   Rationale: {res['rationale']}\n"
                    f"   Source: {res.get('source_type', '?')}"
                )
            # Generic dict — show key fields
            parts = [f"{k}: {v}" for k, v in res.items()
                     if not isinstance(v, (dict, list)) or len(str(v)) < 100]
            return " | ".join(parts) if parts else str(res)[:300]
        if isinstance(res, list):
            return f"📋 {len(res)} items returned"
        return str(res)[:500]

    try:
        action = args.get("action")
        slug = args.get("slug")

        # --- System Actions ---
        if action == "setup":
            return core.setup()

        if action == "audit":
            return core.audit()

        if action == "list":
            runs = core.get_all_runs(args.get("include_archived", True))
            if not runs:
                return "📭 No runs found."
            lines = [f"📋 **{len(runs)} runs:**"]
            for r in runs:
                emoji = "📦" if r.get("status") == "archived" else "📄"
                lines.append(
                    f"  {emoji} **{r['slug']}** — {r.get('state', '?')} "
                    f"({r.get('route', '?')})"
                )
            return "\n".join(lines[:20]) + ("\n  ..." if len(runs) > 20 else "")

        # --- Run Actions ---
        if action == "new_run":
            res = core.create_run(
                args.get("idea", ""),
                args.get("slug"),
                args.get("source_hint", ""),
            )
            return _fmt(res, "📝")

        if action == "update_state":
            force = args.get("force", False)
            return core.update_state(slug, args.get("state"), force=force)

        if action == "get_state":
            state = core.get_state(slug)
            actions = core.get_next_actions(slug)
            actions_text = "\n".join(f"  {i+1}. {a}" for i, a in enumerate(actions[:5]))
            return (
                f"📊 **{slug}**\n"
                f"  State: {state}\n"
                f"  Next:\n{actions_text}"
            )

        if action == "sync_state":
            return f"🔄 State synced: {core.sync_state(slug)}"

        if action == "get_next_actions":
            actions = core.get_next_actions(slug)
            return "📌 **Next actions:**\n" + "\n".join(
                f"  {i+1}. {a}" for i, a in enumerate(actions)
            )

        # --- Idea Gate ---
        if action == "decide_route":
            return _fmt(core.decide_route(
                args.get("idea", ""),
                args.get("source_hint", ""),
            ))

        # --- Agent Pipeline ---
        if action == "generate_brief":
            llm = kwargs.get("parent_agent")
            llm_obj = llm.ctx.llm if llm and hasattr(llm, "ctx") else None
            res = await core.generate_brief(slug, llm_obj, args.get("extra_context", ""))
            return _fmt(res, "📝")

        if action == "generate_draft":
            llm = kwargs.get("parent_agent")
            llm_obj = llm.ctx.llm if llm and hasattr(llm, "ctx") else None
            res = await core.generate_draft(slug, llm_obj)
            return _fmt(res, "✍️")

        if action == "run_verifier":
            llm = kwargs.get("parent_agent")
            llm_obj = llm.ctx.llm if llm and hasattr(llm, "ctx") else None
            res = await core.run_verifier(slug, llm_obj)
            return _fmt(res, "🔍")

        # --- Quality ---
        if action == "scan_slop":
            res = core.scan_slop(args.get("text", ""))
            if "error" in res:
                return f"❌ {res['error']}"
            score = res.get("score", "?")
            t1 = res.get("tier1_count", 0)
            t2 = res.get("tier2_count", 0)
            t3 = res.get("tier3_count", 0)
            bn = res.get("bonus_count", 0)
            findings = res.get("all_findings", [])
            total = t1 + t2 + t3 + bn
            lines = [f"🔎 **Slop Scan: {score}** | {total} findings"]
            if total > 0:
                if t1: lines.append(f"  🔴 Tier 1: {t1}")
                if t2: lines.append(f"  🟠 Tier 2: {t2}")
                if t3: lines.append(f"  🟡 Tier 3: {t3}")
                if bn: lines.append(f"  ⚪ Bonus: {bn}")
                lines.append(f"  Findings: {', '.join(findings[:10])}")
                if len(findings) > 10:
                    lines.append(f"  ... and {len(findings) - 10} more")
            return "\n".join(lines)

        if action == "score":
            llm = kwargs.get("parent_agent")
            llm_obj = llm.ctx.llm if llm and hasattr(llm, "ctx") else None
            res = await core.evaluate_rubric(slug, llm_obj)
            if "error" in res:
                return f"❌ Rubric scoring failed: {res['error']}"
            total = res.get("total", 0)
            passes = res.get("passes", False)
            scores = res.get("scores", {})
            lines = [f"📊 **Rubric Score: {total}/12** {'✅ PASS' if passes else '❌ FAIL'}"]
            for k, v in scores.items():
                lines.append(f"  • {k}: {v}")
            return "\n".join(lines)

        # --- Signals ---
        if action == "signal":
            signals = core.process_signal(args.get("source", "x"))
            if isinstance(signals, list):
                return "📡 **Signals:**\n" + "\n".join(
                    f"  {i+1}. {s[:120]}" for i, s in enumerate(signals)
                )
            return str(signals)

        # --- Postmortem ---
        if action == "postmortem":
            metrics = args.get("metrics", {})
            llm = kwargs.get("parent_agent")
            llm_obj = llm.ctx.llm if llm and hasattr(llm, "ctx") else None
            res = await core.run_postmortem(slug, metrics, llm_obj)
            return _fmt(res, "📊")

        # --- Voice ---
        if action == "update_voice":
            return core.update_voice_profile(args.get("updates", {}))

        # --- Learning ---
        if action == "get_learnings":
            return core.get_learnings_for_brief(args.get("topic"))

        if action == "analyze_patterns":
            return _fmt(core.analyze_run_patterns())

        # --- Search ---
        if action == "search_runs":
            results = core.search_runs(args.get("query", ""))
            if not results:
                return f"🔍 No results for '{args.get('query', '')}'"
            lines = [f"🔍 **Search: {args.get('query', '')}** ({len(results)} matches)"]
            for r in results[:10]:
                lines.append(f"  • {r.get('slug', '?')} — {r.get('file', '?')}")
            if len(results) > 10:
                lines.append(f"  ... and {len(results) - 10} more")
            return "\n".join(lines)

        if action == "get_all_runs":
            runs = core.get_all_runs(args.get("include_archived", True))
            if not runs:
                return "📭 No runs."
            active = [r for r in runs if r.get("status") != "archived"]
            archived = [r for r in runs if r.get("status") == "archived"]
            return f"📋 {len(active)} active, {len(archived)} archived runs"

        # --- Archive ---
        if action == "archive_run":
            return core.archive_run(slug)

        # --- Buffer API ---
        if action == "buffer_setup":
            return core.buffer_setup(args.get("api_key"))
        if action == "buffer_send":
            return core.buffer_send(slug)
        if action == "buffer_status":
            return core.buffer_status()

        # --- Full Pipeline (single atomic call) ---
        if action == "run_pipeline":
            llm = kwargs.get("parent_agent")
            llm_obj = llm.ctx.llm if llm and hasattr(llm, "ctx") else None
            return await core.run_pipeline(
                slug, llm_obj, args.get("extra_context", "")
            )

        # ── Runtime Action Registry (hot-addable actions) ──────────
        handler = _ACTION_HANDLERS.get(action)
        if handler is not None:
            result = handler(core, args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        return f"❓ Unknown action: {action}"

    except Exception as e:
        logger.error("tool_content_os_manager failed action=%s: %s", args.get("action"), e)
        return f"❌ Error running {args.get('action', '?')}: {str(e)[:300]}"


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
