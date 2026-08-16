"""Bifrost MCP HTTP client — web search provider.

Speaks the MCP Streamable HTTP protocol to the Bifrost gateway's /mcp
endpoint. The gateway proxies NeuralDeep Search (web, telegram, crawl).

Protocol flow (per MCP 2024-11-05 spec):
  1. POST /mcp  — initialize (get protocol version, capabilities)
  2. POST /mcp  — notifications/initialized (202 Accepted, no body)
  3. POST /mcp  — tools/call (execute search/crawl)

Each request carries the virtual key via ``Authorization: Bearer sk-bf-*``.
No session ID is needed — Bifrost is stateless between requests.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List

import requests

from agent.web_search_provider import WebSearchProvider

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "http://127.0.0.1:8082"

# MCP protocol version we speak
_MCP_PROTOCOL = "2024-11-05"


class BifrostMCPClient:
    """Minimal MCP Streamable HTTP client for Bifrost gateway."""

    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        self._base = base_url.rstrip("/")
        self._url = f"{self._base}/mcp"
        self._key = api_key
        self._timeout = timeout
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        self._initialized = False

    def _post(self, payload: dict) -> dict:
        resp = requests.post(
            self._url, json=payload, headers=self._headers, timeout=self._timeout
        )
        if resp.status_code == 202:
            # Notification accepted — no body
            return {}
        resp.raise_for_status()
        return resp.json()

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        # Step 1: initialize
        init = self._post({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": _MCP_PROTOCOL,
                "capabilities": {},
                "clientInfo": {"name": "hermes-bifrost-web", "version": "1.0"},
            },
        })
        logger.debug("MCP initialize: %s", init.get("result", {}).get("serverInfo"))
        # Step 2: notifications/initialized
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        self._initialized = True

    def call_tool(self, name: str, arguments: dict, request_id: int = 100) -> dict:
        """Call an MCP tool by name. Returns the raw JSON-RPC response."""
        self._ensure_initialized()
        return self._post({
            "jsonrpc": "2.0", "id": request_id, "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        })


def _extract_text_from_mcp_result(result: dict) -> str:
    """Extract text content from MCP tools/call result.

    MCP returns content as a list of content blocks:
    {"result": {"content": [{"type": "text", "text": "..."}]}}
    """
    content_list = result.get("result", {}).get("content", [])
    texts = []
    for item in content_list:
        if isinstance(item, dict) and item.get("type") == "text":
            texts.append(item.get("text", ""))
        elif isinstance(item, str):
            texts.append(item)
    return "\n".join(texts)


class BifrostWebSearchProvider(WebSearchProvider):
    """Web search + extract via Bifrost gateway MCP."""

    @property
    def name(self) -> str:
        return "bifrost"

    @property
    def display_name(self) -> str:
        return "Bifrost Gateway (MCP)"

    def is_available(self) -> bool:
        return bool(os.environ.get("BIFROST_API_KEY"))

    def _get_client(self) -> BifrostMCPClient | None:
        key = os.environ.get("BIFROST_API_KEY", "")
        if not key:
            return None
        base = os.environ.get("BIFROST_BASE_URL", _DEFAULT_BASE_URL)
        # Strip /v1 suffix if present — /mcp is at the gateway root
        if base.endswith("/v1"):
            base = base[:-3]
        return BifrostMCPClient(base, key)

    def search(self, query: str, num_results: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Search the web via Bifrost MCP (web_search + tg_search tools).

        Returns a list of dicts with keys: title, url, description.
        """
        client = self._get_client()
        if not client:
            logger.warning("BIFROST_API_KEY not set — Bifrost search unavailable")
            return []

        results: List[Dict[str, Any]] = []
        lang = kwargs.get("lang", "ru")

        # Web search
        try:
            resp = client.call_tool("web_search", {
                "query": query, "limit": num_results, "lang": lang,
            })
            if resp.get("error"):
                logger.error("MCP web_search error: %s", resp["error"])
            else:
                text = _extract_text_from_mcp_result(resp)
                results.extend(_parse_search_results(text))
        except Exception as e:
            logger.error("Bifrost web_search failed: %s", e)

        # Telegram search (bonus — merges TG channels into results)
        try:
            resp2 = client.call_tool("tg_search", {
                "query": query, "limit": min(num_results, 5),
            })
            if not resp2.get("error"):
                text2 = _extract_text_from_mcp_result(resp2)
                results.extend(_parse_search_results(text2))
        except Exception as e:
            logger.debug("Bifrost tg_search failed (non-critical): %s", e)

        # Deduplicate by URL
        seen = set()
        unique = []
        for r in results:
            url = r.get("url", "")
            if url and url not in seen:
                seen.add(url)
                unique.append(r)

        return unique[:num_results]

    def extract(self, urls: List[str], char_limit: int = 15000, **kwargs) -> Dict[str, Dict[str, Any]]:
        """Extract/crawl content from URLs via Bifrost MCP (crawl tool).

        Returns {url: {"title": ..., "content": ..., "error": ...}}.
        """
        client = self._get_client()
        if not client:
            return {u: {"error": "BIFROST_API_KEY not set"} for u in urls}

        out: Dict[str, Dict[str, Any]] = {}
        for url in urls:
            try:
                resp = client.call_tool("crawl", {
                    "url": url, "limit": char_limit,
                })
                if resp.get("error"):
                    out[url] = {"error": str(resp["error"].get("message", "unknown"))}
                else:
                    text = _extract_text_from_mcp_result(resp)
                    out[url] = {
                        "title": _extract_title(text, url),
                        "content": text[:char_limit],
                    }
            except Exception as e:
                out[url] = {"error": str(e)}

        return out


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_search_results(text: str) -> List[Dict[str, Any]]:
    """Parse search results from MCP text output.

    NeuralDeep search returns JSON or formatted text. We try JSON first,
    then fall back to line-based parsing.
    """
    results = []

    # Try parsing as JSON first
    try:
        data = json.loads(text)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", item.get("link", "")),
                        "description": item.get("description", item.get("snippet", item.get("content", ""))),
                    })
        elif isinstance(data, dict) and "results" in data:
            for item in data["results"]:
                if isinstance(item, dict):
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", item.get("link", "")),
                        "description": item.get("description", item.get("snippet", item.get("content", ""))),
                    })
        if results:
            return results
    except (json.JSONDecodeError, TypeError):
        pass

    # Fallback: parse line-by-line for "Title: ... URL: ..." format
    current = {}
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Match patterns like "1. Title — url" or "Title: ... | URL: ..."
        url_match = re.search(r'https?://\S+', line)
        if url_match and current.get("url") is None:
            current["url"] = url_match.group(0).rstrip(")")
            # Everything before the URL is the title
            title_part = line[:url_match.start()].strip(" -—|.")
            if title_part:
                current["title"] = title_part.lstrip("0123456789. ")
        elif line.startswith(("Title:", "title:")):
            current["title"] = line.split(":", 1)[1].strip()
        elif line.startswith(("URL:", "url:", "Link:", "link:")):
            current["url"] = line.split(":", 1)[1].strip()
        elif line.startswith(("Snippet:", "Description:", "snippet:", "description:")):
            current["description"] = line.split(":", 1)[1].strip()
        elif current.get("url") and not current.get("description"):
            # Accumulate as description
            current.setdefault("description", "")
            current["description"] += " " + line if current["description"] else line

        if current.get("url") and current.get("title"):
            results.append(current)
            current = {}

    return results


def _extract_title(text: str, fallback_url: str) -> str:
    """Try to extract a title from crawled content."""
    # Look for first markdown heading or <title> tag
    for line in text.split("\n")[:20]:
        line = line.strip()
        if line.startswith("# "):
            return line.lstrip("# ").strip()
        if line.startswith("Title:"):
            return line.split(":", 1)[1].strip()
    # Fallback: first non-empty line
    for line in text.split("\n"):
        line = line.strip()
        if line and len(line) > 5:
            return line[:100]
    return fallback_url
