"""
Buffer API Client for Content OS v2.5.0
========================================
Send tweet threads to Buffer.com as draft posts.
User reviews on Buffer.com, then publishes to Twitter manually.

Buffer GraphQL API: https://developers.buffer.com/
"""

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)

BUFFER_API_ENDPOINT = "https://api.buffer.com"
BUFFER_CONFIG_FILE = ".buffer_config.json"


class BufferClientError(Exception):
    """Buffer API client error."""
    pass


class BufferClient:
    """GraphQL client for Buffer API.

    Two-step auth:
      1. API key → `BUFFER_API_KEY` env var or `~/.hermes/.env`
      2. Org + Channel → cached in `.buffer_config.json`
    """

    def __init__(self, plugin_root: Path):
        self.plugin_root = Path(plugin_root)
        self.config_path = self.plugin_root / BUFFER_CONFIG_FILE
        self._api_key = self._resolve_api_key()
        self._config = self._load_config()

    # ── API Key Resolution ──────────────────────────────────────

    def _resolve_api_key(self) -> Optional[str]:
        """Resolve Buffer API key: env var > Hermes .env > None."""
        key = os.environ.get("BUFFER_API_KEY")
        if key:
            return key

        # Check ~/.hermes/.env
        try:
            env_path = Path.home() / ".hermes" / ".env"
            if env_path.exists():
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("BUFFER_API_KEY="):
                        return line.split("=", 1)[1].strip().strip("\"'")
        except Exception:
            pass

        return None

    def configure_api_key(self, api_key: str) -> None:
        """Set a new API key for this session."""
        self._api_key = api_key

    @property
    def has_api_key(self) -> bool:
        return bool(self._api_key)

    # ── Config Persistence ──────────────────────────────────────

    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            try:
                return json.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _save_config(self) -> None:
        self.config_path.write_text(
            json.dumps(self._config, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @property
    def is_configured(self) -> bool:
        return bool(self._config.get("channel_id")) and self.has_api_key

    def get_config_summary(self) -> str:
        """Return human-readable config status."""
        lines = ["### Buffer Integration Status", ""]
        lines.append(f"- **API Key:** {'✅ Set' if self.has_api_key else '❌ Not set'}")
        lines.append(f"- **Organization:** {self._config.get('org_name', '—')} ({self._config.get('org_id', '—')})")
        lines.append(f"- **Channel:** {self._config.get('channel_name', '—')} ({self._config.get('channel_service', '—')})")
        lines.append(f"- **Config file:** `{self.config_path}`")
        if self.is_configured:
            lines.append("\n✅ Ready to publish to Buffer.")
        else:
            lines.append("\n⚠️  Run `hermes content buffer setup` to configure.")
        return "\n".join(lines)

    # ── GraphQL Request ─────────────────────────────────────────

    def _graphql(self, query: str) -> Dict[str, Any]:
        """Execute a GraphQL query/mutation against Buffer API."""
        if not self._api_key:
            return {"error": "BUFFER_API_KEY not set. Run `hermes content buffer setup` first."}

        payload = json.dumps({"query": query}).encode("utf-8")
        req = Request(
            BUFFER_API_ENDPOINT,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            method="POST",
        )
        try:
            with urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            logger.error("Buffer API HTTP %s: %s", e.code, body[:300])
            return {"error": f"HTTP {e.code}: {body[:500]}"}
        except URLError as e:
            logger.error("Buffer API connection error: %s", e)
            return {"error": f"Connection error: {str(e)}"}
        except Exception as e:
            logger.error("Buffer API request failed: %s", e)
            return {"error": f"Request failed: {str(e)}"}

    # ── Organizations ───────────────────────────────────────────

    def fetch_organizations(self) -> List[Dict[str, str]]:
        """Fetch all organizations for the authenticated account."""
        query = """
        query GetOrganizations {
            account {
                organizations {
                    id
                    name
                    ownerEmail
                }
            }
        }
        """
        result = self._graphql(query)
        if "error" in result:
            return result

        try:
            orgs = result.get("data", {}).get("account", {}).get("organizations", [])
            return orgs if orgs else [{"error": "No organizations found."}]
        except Exception as e:
            return [{"error": f"Failed to parse organizations: {str(e)}"}]

    # ── Channels ────────────────────────────────────────────────

    def fetch_channels(self, org_id: str) -> List[Dict[str, Any]]:
        """Fetch all channels for a given organization."""
        query = f"""
        query GetChannels {{
            channels(input: {{ organizationId: "{org_id}" }}) {{
                id
                name
                displayName
                service
                avatar
                isQueuePaused
            }}
        }}
        """
        result = self._graphql(query)
        if "error" in result:
            return [{"error": result["error"]}]

        try:
            channels = result.get("data", {}).get("channels", [])
            return channels if channels else [{"error": "No channels found for this organization."}]
        except Exception as e:
            return [{"error": f"Failed to parse channels: {str(e)}"}]

    # ── Create Draft Post ───────────────────────────────────────

    def create_draft_post(self, channel_id: str, text: str) -> Dict[str, Any]:
        """Create a single draft post on Buffer.

        The post is saved as a draft (not published) — user must
        review and publish from Buffer.com.
        """
        # Escape special chars for GraphQL string
        escaped_text = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

        query = f"""
        mutation CreateDraftPost {{
            createPost(input: {{
                text: "{escaped_text}",
                channelId: "{channel_id}",
                schedulingType: automatic,
                mode: addToQueue,
                saveToDraft: true
            }}) {{
                ... on PostActionSuccess {{
                    post {{
                        id
                        text
                    }}
                }}
                ... on MutationError {{
                    message
                }}
            }}
        }}
        """
        result = self._graphql(query)
        if "error" in result:
            return result

        try:
            data = result.get("data", {}).get("createPost", {})
            if "post" in data:
                return {"success": True, "post_id": data["post"]["id"]}
            elif "message" in data:
                return {"error": data["message"]}
            else:
                return {"error": f"Unexpected response: {json.dumps(result)[:200]}"}
        except Exception as e:
            return {"error": f"Failed to parse createPost response: {str(e)}"}

    def send_thread(self, tweets: List[str], channel_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Send a list of tweets as individual draft posts to Buffer.

        Args:
            tweets: List of tweet texts in order
            channel_id: Override cached channel ID

        Returns:
            List of results, one per tweet
        """
        cid = channel_id or self._config.get("channel_id")
        if not cid:
            return [{"error": "No channel configured. Run `hermes content buffer setup` first."}]

        results = []
        for i, tweet_text in enumerate(tweets, 1):
            logger.info("Sending tweet %d/%d to Buffer...", i, len(tweets))
            result = self.create_draft_post(cid, tweet_text)
            result["tweet_number"] = i
            results.append(result)
            # Rate limit: don't hammer the API
            if i < len(tweets):
                time.sleep(0.5)

        return results

    # ── Draft Parser ────────────────────────────────────────────

    @staticmethod
    def parse_draft_text(text: str) -> List[str]:
        """Parse draft-package.md content and extract individual tweets.

        Supports two formats:
        1. News thread format:
           ---
           draft:
           1/ [🔴] Tweet content...
           2/ More content...
           ---
        2. Regular thread format:
           N) content
           or
           **Tweet N:** content

        Args:
            text: Full content of draft-package.md

        Returns:
            List of tweet texts in order, or empty list if parsing fails
        """
        tweets = []

        # Strategy 1: Find the draft section and parse numbered lines (N/ ...)
        draft_section = ""
        lines = text.split("\n")

        in_draft = False
        for i, line in enumerate(lines):
            stripped = line.strip()

            # Start of draft section — look for "draft:" marker or opening "---"
            if stripped.rstrip(":").strip() == "draft" or stripped == "---":
                # Enter draft mode — no strict next-line check, just search ahead
                in_draft = True
                continue

            # Stop at next section header (rubric, slop, voice, or markdown heading)
            if in_draft:
                section_headers = [
                    "rubric_self_assessment", "avoid_slop_pass",
                    "open_loops_flagged", "voice_check",
                    "## ", "### ",
                ]
                if any(stripped.startswith(h) or stripped.rstrip(":").strip() == h
                       for h in section_headers):
                    break
                draft_section += line + "\n"

        if draft_section:
            # Parse numbered tweets — handles both N/ and N/M formats
            # N/ format: 1/ Content here → (1, "Content here")
            # N/M format: 1/8 Content here → (1, "Content here") — skips the total count
            tweet_pattern = re.compile(r"^(\d+)/(?:\d+)?\s*(.+)$", re.MULTILINE)
            for match in tweet_pattern.finditer(draft_section):
                content = match.group(2).strip()
                if content:
                    tweets.append(content)

        # Strategy 1.5: Multi-line N/M format — N/M on its own line, content on next line
        # Example:
        #   1/8
        #   Content here...
        #   2/8
        #   More content...
        if not tweets:
            lines_list = text.split("\n")
            i = 0
            while i < len(lines_list):
                line = lines_list[i].strip()
                # Match a line containing just N/M (e.g., "1/8", "  2/8  ")
                multi_match = re.match(r"^(\d+)/(\d+)$", line)
                if multi_match:
                    # Check if the next non-empty line has content
                    content_lines = []
                    for j in range(i + 1, len(lines_list)):
                        next_line = lines_list[j].strip()
                        if not next_line:
                            continue
                        # Check if next line is also N/M (next counter)
                        if re.match(r"^\d+/\d+$", next_line):
                            i = j - 1
                            break
                        # Stop at section headers
                        if any(next_line.startswith(h) for h in
                               ["rubric_self_assessment", "avoid_slop_pass",
                                "open_loops_flagged", "voice_check", "## ", "### "]):
                            i = len(lines_list)
                            break
                        content_lines.append(lines_list[j].strip())
                        i = j  # advance past this content line
                    joined = " ".join(content_lines).strip()
                    if joined:
                        tweets.append(joined)
                i += 1

        # Strategy 2: Fallback — look for **Tweet N:** pattern (multi-line support)
        # Supports: **Tweet N:** content, **Tweet N] content, **Tweet N (title)** content
        # Stops at next **Tweet or section boundary (rubric_, avoid_, open_loops_, voice_)
        if not tweets:
            tweet_pattern2 = re.compile(
                r"\*\*Tweet\s*(\d+)(?:\s*\([^)]*\))?[:\]]?\*\*\s*(.*?)(?=\*\*Tweet|\Z|rubric_self_assessment|avoid_slop_pass|open_loops_flagged|voice_check)",
                re.DOTALL
            )
            for match in tweet_pattern2.finditer(text):
                content = match.group(2).strip()
                if content:
                    tweets.append(content)

        # Strategy 3: Fallback — look for `N)` pattern (single line)
        if not tweets:
            tweet_pattern3 = re.compile(r"^(\d+)\)\s*(.+)$", re.MULTILINE)
            for match in tweet_pattern3.finditer(text):
                content = match.group(2).strip()
                if content:
                    tweets.append(content)

        # Strategy 4: Last resort — scan ALL lines for "N/" anywhere in the text
        # (handles drafts with preamble between "draft:" and tweet list)
        if not tweets:
            tweet_pattern4 = re.compile(r"^(\d+)/(?:\d+)?\s*(.+)$", re.MULTILINE)
            matches = tweet_pattern4.findall(text)
            if matches:
                for _, content in matches:
                    content = content.strip()
                    if content:
                        tweets.append(content)

        return tweets

    @staticmethod
    def reformat_to_buffer_format(text: str) -> str:
        """Auto-convert any draft text to Buffer-compatible format.

        Handles:
        - 'N/ content' lines anywhere in text (with or without preamble)
        - '**Tweet N:** content' pattern
        - 'N) content' pattern
        - Pure text without numbering (wraps as single tweet)

        Returns reformatted text with proper '---' / 'draft:' / '---' structure.
        """
        import re
        lines = text.split("\n")

        # Strategy A: Already has N/ pattern → handle both N/ and N/M formats
        tweet_pattern = re.compile(r"^(\d+)/(?:\d+)?\s*(.*)$", re.MULTILINE)
        n_slash_matches = tweet_pattern.findall(text)
        if n_slash_matches:
            # Check if we actually got content, or just empty/N-M-only captures
            has_content = any(tweet.strip() for _, tweet in n_slash_matches)
            if not has_content:
                # Multi-line N/M format: 1/8\nContent\n2/8\nMore...
                # Parse by walking lines and collecting content after each N/M marker
                multi_lines = text.split("\n")
                parsed = []
                i = 0
                while i < len(multi_lines):
                    line = multi_lines[i].strip()
                    m = re.match(r"^(\d+)/(\d+)$", line)
                    if m:
                        n = m.group(1)
                        content_parts = []
                        for j in range(i + 1, len(multi_lines)):
                            next_line = multi_lines[j].strip()
                            if not next_line:
                                continue
                            if re.match(r"^\d+/\d+$", next_line):
                                i = j - 1
                                break
                            if any(next_line.startswith(h) for h in
                                   ["rubric_self_assessment", "avoid_slop_pass",
                                    "open_loops_flagged", "voice_check", "## ", "### "]):
                                i = len(multi_lines)
                                break
                            content_parts.append(multi_lines[j].strip())
                            i = j
                        joined = " ".join(content_parts).strip()
                        if joined:
                            parsed.append(f"{n}/ {joined}")
                    i += 1
                if parsed:
                    body = "\n".join(parsed)
                else:
                    body = "\n".join(f"{n}/ {tweet}" for n, tweet in n_slash_matches)
            else:
                body = "\n".join(f"{n}/ {tweet}" for n, tweet in n_slash_matches)
            suffix = ""
            # Preserve sections after tweet list
            in_sections = False
            section_lines = []
            for line in lines:
                stripped = line.strip()
                if any(stripped.startswith(h) for h in
                       ["rubric_self_assessment", "avoid_slop_pass",
                        "open_loops_flagged", "voice_check"]):
                    in_sections = True
                if in_sections:
                    section_lines.append(line)
            if section_lines:
                suffix = "\n" + "\n".join(section_lines)
            return f"---\ndraft:\n{body}\n{suffix}"

        # Strategy B: **Tweet N:** pattern (with optional parenthesized title)
        bold_pattern = re.compile(r"\*\*Tweet\s*(\d+)(?:\s*\([^)]*\))?[:\]]?\*\*\s*(.*?)(?=\*\*Tweet|\Z|rubric_self_assessment|avoid_slop_pass|open_loops_flagged|voice_check)", re.DOTALL)
        bold_matches = bold_pattern.findall(text)
        if bold_matches:
            body = "\n".join(
                f"{n}/ {tweet.strip().split(chr(10))[0]}"
                for n, tweet in bold_matches
            )
            return f"---\ndraft:\n{body}\n---"

        # Strategy C: N) pattern
        paren_pattern = re.compile(r"^(\d+)\)\s*(.+)$", re.MULTILINE)
        paren_matches = paren_pattern.findall(text)
        if paren_matches:
            body = "\n".join(f"{n}/ {tweet}" for n, tweet in paren_matches)
            return f"---\ndraft:\n{body}\n---"

        # Strategy D: No numbering found — wrap entire content as single tweet
        clean = text.strip().strip("-").strip()
        return f"---\ndraft:\n1/ {clean}\n---"

    @staticmethod
    def format_tweet_summary(tweets: List[str]) -> str:
        """Format tweet list as human-readable summary."""
        if not tweets:
            return "❌ No tweets found in draft."

        lines = [f"📝 **{len(tweets)} tweet** found:\n"]
        for i, t in enumerate(tweets, 1):
            preview = t[:80] + ("..." if len(t) > 80 else "")
            char_count = len(t)
            emoji = "✅" if char_count <= 280 else "⚠️"
            lines.append(f"  {emoji} **Tweet {i}** ({char_count} chr): {preview}")
        return "\n".join(lines)


__all__ = ["BufferClient", "BufferClientError"]
