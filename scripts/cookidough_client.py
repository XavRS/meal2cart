#!/usr/bin/env python3
"""Cliente Python para cookidough-mcp vía JSON-RPC sobre stdio.

Uso:
    from cookidough_client import CookidoughClient
    client = CookidoughClient()
    
    # Búsqueda
    recipes = client.search("gazpacho", limit=3)
    
    # Detalles de receta
    detail = client.get_recipe("r132404")
    
    # Añadir al calendario "Mi semana"
    client.add_to_calendar(["r221200"], "2026-07-15")
    
    # Ver calendario
    week = client.get_calendar_week("2026-07-15")
    
    client.close()
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from typing import Any


class CookidoughClient:
    """Wrapper around cookidough-mcp subprocess with MCP JSON-RPC protocol."""

    def __init__(self, mcp_bin: str = "/root/.local/bin/cookidough-mcp"):
        env = {
            "COOKIDOUGH_EMAIL": os.environ.get("COOKIDOUGH_EMAIL", ""),
            "COOKIDOUGH_PASSWORD": os.environ.get("COOKIDOUGH_PASSWORD", ""),
            "COOKIDOUGH_COOKIES_FILE": os.environ.get(
                "COOKIDOUGH_COOKIES_FILE",
                os.path.expanduser("~/.hermes/data/cookidough_cookies.json"),
            ),
            "COOKIDOUGH_COUNTRY": os.environ.get("COOKIDOUGH_COUNTRY", "es"),
            "COOKIDOUGH_LANGUAGE": os.environ.get("COOKIDOUGH_LANGUAGE", "es"),
            "PATH": os.environ.get("PATH", ""),
        }

        cookies_dir = os.path.dirname(env["COOKIDOUGH_COOKIES_FILE"])
        os.makedirs(cookies_dir, exist_ok=True)

        self._proc = subprocess.Popen(
            [mcp_bin],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            bufsize=1,
        )

        # MCP init sequence
        self._send(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "meal-to-cart", "version": "1.0"},
            },
        )
        # Consume init response
        line = self._proc.stdout.readline()
        resp = json.loads(line)
        if resp.get("id") != 2 or "result" not in resp:
            raise RuntimeError(f"MCP init failed: {resp}")

        # Send initialized notification (no id, no response expected)
        self._proc.stdin.write(
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
            + "\n"
        )
        self._proc.stdin.flush()

        # Trigger lazy login
        self._call_tool("get_user_profile")

    def _send(self, method: str, params: dict[str, Any]) -> None:
        payload = json.dumps(
            {"jsonrpc": "2.0", "id": 2, "method": method, "params": params}
        )
        self._proc.stdin.write(payload + "\n")
        self._proc.stdin.flush()

    def _call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Call a tool and return parsed content items."""
        if arguments is None:
            arguments = {}

        req_id = int(time.time() * 10000) % 100000
        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
        )
        self._proc.stdin.write(payload + "\n")
        self._proc.stdin.flush()

        # Read until we get the response with matching id
        while True:
            line = self._proc.stdout.readline()
            if not line:
                raise RuntimeError("MCP process closed stdout")
            resp = json.loads(line)
            if resp.get("id") == req_id:
                if "error" in resp:
                    raise RuntimeError(f"Tool error: {resp['error']}")
                # Parse content
                items: list[dict[str, Any]] = []
                for c in resp["result"].get("content", []):
                    if c.get("type") == "text":
                        try:
                            items.append(json.loads(c["text"]))
                        except json.JSONDecodeError:
                            items.append({"raw": c["text"]})
                return items

    # ── Convenience methods ──────────────────────────────────────────

    def search(
        self,
        query: str,
        limit: int = 10,
        max_total_minutes: int | None = None,
    ) -> list[dict[str, Any]]:
        """Search Cookidoo recipes."""
        args: dict[str, Any] = {"query": query, "limit": limit}
        if max_total_minutes is not None:
            args["max_total_minutes"] = max_total_minutes
        return self._call_tool("search_recipes", args)

    def get_recipe(self, recipe_id: str) -> dict[str, Any] | None:
        """Get full recipe details (no steps — see references/cookidough-mcp-usage.md)."""
        items = self._call_tool("get_recipe_details", {"recipe_id": recipe_id})
        return items[0] if items else None

    def get_profile(self) -> dict[str, Any] | None:
        """Get user profile (also triggers lazy login)."""
        items = self._call_tool("get_user_profile")
        return items[0] if items else None

    def add_to_calendar(self, recipe_ids: list[str], day: str) -> dict[str, Any] | None:
        """Add recipes to calendar 'Mi semana' for a specific day.
        
        Args:
            recipe_ids: List of recipe IDs (e.g., ["r221200", "r505494"])
            day: Date in YYYY-MM-DD format (e.g., "2026-07-15")
            
        Returns:
            Result dict or None if failed
            
        Example:
            client.add_to_calendar(["r221200"], "2026-07-15")
        """
        items = self._call_tool("add_recipes_to_calendar", {
            "day": day,
            "recipe_ids": recipe_ids
        })
        return items[0] if items else None

    def get_calendar_week(self, day: str) -> dict[str, Any] | None:
        """Get the calendar week containing the given day.
        
        Args:
            day: Date in YYYY-MM-DD format
            
        Returns:
            Calendar week data with recipes per day
        """
        items = self._call_tool("get_calendar_week", {"day": day})
        return items[0] if items else None

    def remove_from_calendar(self, recipe_id: str, day: str) -> dict[str, Any] | None:
        """Remove a recipe from calendar for a specific day.
        
        Args:
            recipe_id: Recipe ID to remove
            day: Date in YYYY-MM-DD format
        """
        items = self._call_tool("remove_recipe_from_calendar", {
            "day": day,
            "recipe_id": recipe_id
        })
        return items[0] if items else None

    def close(self) -> None:
        """Close the MCP subprocess."""
        try:
            self._proc.stdin.close()
            self._proc.wait(timeout=5)
        except Exception:
            self._proc.kill()


# ── CLI ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 cookidough_client.py <search|get|add-calendar|get-calendar> <args...>")
        sys.exit(1)

    client = CookidoughClient()

    try:
        cmd = sys.argv[1]
        if cmd == "search":
            query = sys.argv[2] if len(sys.argv) > 2 else "gazpacho"
            recipes = client.search(query, limit=5)
            for r in recipes:
                mins = (r.get("total_time_seconds") or 0) // 60
                print(f"  {r['id']}: {r['name']} | {mins}min | ★{r.get('rating', '?')}")
        elif cmd == "get":
            rid = sys.argv[2] if len(sys.argv) > 2 else "r132404"
            detail = client.get_recipe(rid)
            if detail:
                print(json.dumps(detail, indent=2, ensure_ascii=False))
        elif cmd == "add-calendar":
            if len(sys.argv) < 4:
                print("Uso: python3 cookidough_client.py add-calendar <day> <recipe_id> [recipe_id2...]")
                print("Ejemplo: python3 cookidough_client.py add-calendar 2026-07-15 r221200")
                sys.exit(1)
            day = sys.argv[2]
            recipe_ids = sys.argv[3:]
            result = client.add_to_calendar(recipe_ids, day)
            print(f"✓ Añadidas {len(recipe_ids)} receta(s) al {day}")
            if result:
                print(json.dumps(result, indent=2, ensure_ascii=False))
        elif cmd == "get-calendar":
            day = sys.argv[2] if len(sys.argv) > 2 else None
            if not day:
                from datetime import date
                day = date.today().isoformat()
            week = client.get_calendar_week(day)
            if week:
                print(json.dumps(week, indent=2, ensure_ascii=False))
        else:
            print(f"Comando desconocido: {cmd}")
    finally:
        client.close()
