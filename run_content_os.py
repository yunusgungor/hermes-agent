#!/usr/bin/env python3
"""
Content OS Run Creation Script
Creates a new run for today's AI news, updates state, generates brief.
"""
import sys
import json
import asyncio
from pathlib import Path

# Add plugins to path
plugins_dir = Path("/usr/local/lib/hermes-agent/plugins")
sys.path.insert(0, str(plugins_dir.parent))

# Import from archive
from plugins.archive.content_os.content_os_core import ContentOSCore

# Setup
plugin_root = plugins_dir / "archive" / "content-os"
core = ContentOSCore(plugin_root)

idea = "Günlük AI Gelişmeleri 19 Mayıs 2026 — Google I/O, Anthropic Stainless Acquisition, Recursive Superintelligence"

async def main():
    # STEP 1: Create new run
    print("=== STEP 1: Create new run ===")
    result = core.create_run(idea, source_hint="external")
    print(f"create_run result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if "error" in result:
        print(f"ERROR in create_run: {result['error']}")
        sys.exit(1)
    
    slug = result.get("slug")
    print(f"Slug: {slug}")
    
    # STEP 2: Update state to idea_review
    print(f"\n=== STEP 2: Update state to idea_review ===")
    sr = core.update_state(slug, "idea_review")
    print(f"update_state result: {sr}")
    
    # STEP 3: Generate brief
    print(f"\n=== STEP 3: Generate brief ===")
    extra_context = json.dumps({
        "date": "2026-05-19",
        "selected_news": [
            {
                "title": "Google I/O 2026: Gemini 4, Omni Video Model, Android XR Glasses",
                "bükülük": "KRİTİK",
                "source": "Google",
                "summary": "Google I/O keynote today unveils Gemini 4, Gemini Omni (unified text/image/video), Android XR glasses with Samsung/Warby Parker, Aluminium OS (ChromeOS replacement), and Gemini Spark persistent agent. Most AI-packed keynote in Google history."
            },
            {
                "title": "Anthropic Acquires Stainless for $300M+ — Cuts Off OpenAI & Google SDK Access",
                "bükülük": "KRİTİK",
                "source": "TechCrunch/Anthropic",
                "summary": "Anthropic acquires SDK/MCP server tooling startup Stainless for $300M+. Used by OpenAI, Google, Cloudflare. Anthropic will shut down hosted Stainless products for competitors. Strategic move to control the agent connectivity layer."
            },
            {
                "title": "Recursive Superintelligence Raises $650M at $4.65B Valuation",
                "bükülük": "YÜKSEK",
                "source": "TechCrunch/VentureBeat",
                "summary": "Richard Socher's stealth AI lab emerges from stealth with $650M from GV, Greycroft, Nvidia, AMD. Building recursively self-improving AI. Team includes Peter Norvig, Tim Rocktäschel, Jeff Clune."
            },
            {
                "title": "SandboxAQ Integrates Physics-Based LQMs into Claude for Drug Discovery",
                "bükülük": "YÜKSEK",
                "source": "TechCrunch",
                "summary": "SandboxAQ brings Large Quantitative Models (physics-grounded AI) to Claude via natural language. Expanded searchable chemical space from 250K to 5.6M molecules. No specialized infrastructure required."
            },
            {
                "title": "Amazon Alexa+ Launches AI Podcast Generation",
                "bükülük": "ORTA",
                "source": "TechCrunch/Amazon",
                "summary": "Alexa+ can now generate podcast episodes on any topic using AI host voices. Partnerships with 200+ news orgs (AP, Reuters, WaPo). NotebookLM-like feature but voice-first."
            }
        ]
    }, ensure_ascii=False)
    
    # generate_brief is async, needs llm arg - try with None
    brief_result = await core.generate_brief(slug, llm=None, extra_context=extra_context)
    print(f"generate_brief result: {json.dumps(brief_result, ensure_ascii=False, indent=2)}")
    
    # STEP 4: Update state to drafting
    print(f"\n=== STEP 4: Update state to drafting ===")
    sr2 = core.update_state(slug, "drafting")
    print(f"update_state result: {sr2}")
    
    # Return the slug
    print(f"\n=== FINAL SLUG: {slug} ===")
    return slug

if __name__ == "__main__":
    slug = asyncio.run(main())
    print(f"\nSLUG={slug}")
