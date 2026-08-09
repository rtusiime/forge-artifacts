#!/usr/bin/env python3
"""
Forge Prep · Artifacts — pull the latest source HTML into the repo, then rebuild.

The shareable pages here are COPIES of "source of truth" HTML files that live
elsewhere on disk (the DLA/Meetings/audios working folders) and get updated
often. This script re-copies the latest version of each mapped source into its
repo location, injects a noindex tag (the site is public but search-hidden),
skips anything already up to date, then regenerates the navigation via build.py.

The source map lives in sources.local.json (git-ignored, machine-specific), so
local file paths never get committed.

    python3 sync.py     # pull latest sources, then rebuild the library index
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAP = ROOT / "sources.local.json"

NOINDEX = '<meta name="robots" content="noindex, nofollow">'


def inject_noindex(html: str) -> str:
    """Add a noindex meta right after <head>. Idempotent — safe to run repeatedly."""
    if NOINDEX in html:
        return html
    m = re.search(r"<head[^>]*>", html, re.IGNORECASE)
    if m:
        i = m.end()
        return html[:i] + "\n" + NOINDEX + html[i:]
    return NOINDEX + "\n" + html  # no <head> — prepend as a fallback


def main() -> int:
    if not MAP.is_file():
        print(f"ERROR: {MAP.name} not found — it maps repo pages to source HTML on disk.",
              file=sys.stderr)
        return 1

    cfg = json.loads(MAP.read_text(encoding="utf-8"))
    mappings = cfg.get("mappings", [])
    changed = unchanged = 0
    missing = []

    for m in mappings:
        src = Path(m["src"]).expanduser()
        dest = ROOT / m["dest"]
        if not src.is_file():
            missing.append(m["src"])
            print(f"  MISSING SRC  {m['dest']}  <-  {m['src']}")
            continue

        # Final desired content = latest source + noindex tag.
        final = inject_noindex(src.read_text(encoding="utf-8"))
        current = dest.read_text(encoding="utf-8") if dest.is_file() else None

        if current == final:
            unchanged += 1
            print(f"  ok           {m['dest']}")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(final, encoding="utf-8")
            changed += 1
            print(f"  UPDATED      {m['dest']}")

    print(f"\n{changed} updated, {unchanged} unchanged, {len(missing)} missing source(s).")
    if missing:
        print("Fix the paths in sources.local.json for the missing sources above.\n")

    # Regenerate the library index / hubs from the freshly-synced files.
    try:
        import build
        build.main()
    except Exception as exc:  # pragma: no cover - defensive
        print(f"(could not auto-run build.py: {exc}) — run 'python3 build.py' yourself.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
