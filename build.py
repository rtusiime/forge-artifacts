#!/usr/bin/env python3
"""
Forge Prep · Artifacts — static site builder.

Reads artifacts.json (the catalog / source of truth) and regenerates:
  - index.html            the library home page (one card per artifact)
  - <slug>/index.html     a topic hub, ONLY for artifacts with >1 variant

It NEVER touches artifact content files (your HTML pages). Single-variant
artifacts live at <slug>/index.html and are linked directly; multi-variant
artifacts keep each version at <slug>/<variant>/index.html and get a
generated hub at <slug>/index.html.

Run it after editing artifacts.json or adding/removing an artifact:

    python3 build.py

No third-party dependencies — standard library only.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "artifacts.json"

# --- Brand tokens (pulled straight from the artifacts themselves) -------------
BRAND_CSS = """
  :root{
    --red:#D93C1D; --tomato:#FB5434; --night:#101010; --ink:#101010;
    --dim:#707070; --mut:#707070; --silver:#AFAFAF; --line:#e6e6e6; --bg:#fff;
    --card:#fff; --chip:#f5f5f5;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
    font:16px/1.6 "Open Sans","Helvetica Neue",Helvetica,Arial,sans-serif}
  a{color:var(--red);text-decoration:none}
  a:hover{text-decoration:underline}
  h1,h2,h3,.wordmark{font-family:Montserrat,"Helvetica Neue",Arial,sans-serif}
  .topbar{border-top:3px solid var(--red);border-bottom:1px solid var(--line);
    padding:12px 20px;font-weight:800;font-size:20px;color:var(--night)}
  .topbar b{color:var(--red)}
  .topbar .motto{float:right;font-weight:400;font-style:italic;font-size:12px;
    color:var(--dim);margin-top:6px;font-family:"Open Sans",Arial}
  .wrap{max-width:940px;margin:0 auto;padding:28px 20px 72px}
  .lede{font-size:17px;color:var(--mut);margin:2px 0 26px;max-width:70ch}
  h1{font-size:32px;line-height:1.15;margin:14px 0 6px;color:var(--night)}
  .crumbs{font-size:13px;color:var(--mut);margin:0 0 6px}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:18px}
  .card{border:1px solid var(--line);border-radius:14px;padding:20px 20px 18px;
    background:var(--card);transition:border-color .15s,box-shadow .15s;display:flex;flex-direction:column}
  .card:hover{border-color:var(--tomato);box-shadow:0 6px 20px rgba(217,60,29,.08)}
  .card h2{font-size:20px;margin:0 0 8px}
  .card h2 a{color:var(--night)}
  .card p{margin:0 0 14px;color:var(--mut);font-size:14.5px;flex:1}
  .chips{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px}
  .chip{font-size:11px;font-weight:600;letter-spacing:.02em;text-transform:uppercase;
    color:var(--dim);background:var(--chip);border-radius:999px;padding:3px 10px}
  .meta{display:flex;justify-content:space-between;align-items:center;font-size:12.5px;color:var(--silver)}
  .go{font-weight:700;color:var(--red)}
  .btn{display:inline-block;background:var(--red);color:#fff;font-weight:700;
    border-radius:10px;padding:12px 20px;font-size:15px}
  .btn:hover{background:var(--tomato);text-decoration:none}
  .btn.secondary{background:#fff;color:var(--red);border:1.5px solid var(--red)}
  .versions{list-style:none;padding:0;margin:22px 0 0;border-top:1px solid var(--line)}
  .versions li{padding:16px 2px;border-bottom:1px solid var(--line);display:flex;
    justify-content:space-between;align-items:flex-start;gap:16px}
  .versions .vlabel{font-weight:700;font-family:Montserrat,Arial;color:var(--night)}
  .versions .vaud{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.03em;
    color:var(--dim);margin-left:8px}
  .versions .vdesc{color:var(--mut);font-size:14px;margin-top:3px}
  .versions .vopen{white-space:nowrap;font-weight:700}
  .footer{margin-top:44px;padding-top:18px;border-top:1px solid var(--line);
    font-size:13px;color:var(--silver)}
  @media (max-width:520px){.topbar .motto{display:none}}
"""

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800&family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
<div class="topbar"><span class="wordmark"><b>Forge</b> Prep</span><span class="motto">artifacts · share a link, not an attachment</span></div>
<div class="wrap">
{body}
<div class="footer">Built from <code>artifacts.json</code> · edit the catalog and run <code>python3 build.py</code> to update.</div>
</div>
</body>
</html>
"""


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def variant_content_ok(art_slug: str, v_slug: str) -> bool:
    return (ROOT / art_slug / v_slug / "index.html").is_file()


def build_home(catalog: dict) -> str:
    site = catalog["site"]
    cards = []
    for art in catalog["artifacts"]:
        slug = art["slug"]
        variants = art.get("variants", [])
        chips = "".join(f'<span class="chip">{esc(t)}</span>' for t in art.get("tags", []))
        n = len(variants)
        version_note = "single page" if n <= 1 else f"{n} versions"
        cards.append(f"""
      <div class="card">
        <h2><a href="{esc(slug)}/">{esc(art['title'])}</a></h2>
        <div class="chips">{chips}</div>
        <p>{esc(art.get('summary',''))}</p>
        <div class="meta"><span>{esc(version_note)} · {esc(art.get('updated',''))}</span><a class="go" href="{esc(slug)}/">Open &rarr;</a></div>
      </div>""")
    body = f"""      <div class="crumbs">Forge Prep</div>
      <h1>{esc(site['title'].split('·')[-1].strip() or 'Artifacts')}</h1>
      <p class="lede">{esc(site['tagline'])}</p>
      <div class="grid">{''.join(cards)}
      </div>"""
    return PAGE.format(title=esc(site["title"]), css=BRAND_CSS, body=body)


def build_hub(catalog: dict, art: dict) -> str:
    site = catalog["site"]
    slug = art["slug"]
    variants = art["variants"]
    # primary = the one flagged primary, else the first
    primary = next((v for v in variants if v.get("primary")), variants[0])

    rows = []
    for v in variants:
        vslug = v["slug"]
        exists = variant_content_ok(slug, vslug)
        open_link = (f'<a class="vopen" href="{esc(vslug)}/">Open &rarr;</a>'
                     if exists else '<span class="vopen" style="color:var(--silver)">missing</span>')
        aud = f'<span class="vaud">{esc(v["audience"])}</span>' if v.get("audience") else ""
        rows.append(f"""
        <li>
          <div>
            <span class="vlabel">{esc(v['label'])}</span>{aud}
            <div class="vdesc">{esc(v.get('description',''))}</div>
          </div>
          {open_link}
        </li>""")

    body = f"""      <div class="crumbs"><a href="../">Forge Prep · Artifacts</a> &nbsp;/&nbsp; {esc(art['title'])}</div>
      <h1>{esc(art['title'])}</h1>
      <p class="lede">{esc(art.get('summary',''))}</p>
      <p><a class="btn" href="{esc(primary['slug'])}/">Open the {esc(primary['label'].lower())} &rarr;</a>
         &nbsp; <a class="btn secondary" href="../">All artifacts</a></p>
      <ul class="versions">{''.join(rows)}
      </ul>"""
    return PAGE.format(title=f"{esc(art['title'])} · Forge Prep Artifacts", css=BRAND_CSS, body=body)


def main() -> int:
    if not CATALOG.is_file():
        print(f"ERROR: {CATALOG} not found", file=sys.stderr)
        return 1
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    (ROOT / "index.html").write_text(build_home(catalog), encoding="utf-8")
    print("wrote index.html")

    missing = []
    for art in catalog["artifacts"]:
        slug = art["slug"]
        variants = art.get("variants", [])
        if len(variants) > 1:
            (ROOT / slug / "index.html").write_text(build_hub(catalog, art), encoding="utf-8")
            print(f"wrote {slug}/index.html (hub, {len(variants)} versions)")
            for v in variants:
                if not variant_content_ok(slug, v["slug"]):
                    missing.append(f"{slug}/{v['slug']}/index.html")
        else:
            if not (ROOT / slug / "index.html").is_file():
                missing.append(f"{slug}/index.html")

    if missing:
        print("\nWARNING — catalog references content files that don't exist yet:")
        for m in missing:
            print(f"  - {m}")
    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
