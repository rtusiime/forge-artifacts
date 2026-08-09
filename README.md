# Forge Prep · Artifacts

A tiny static-site host for the shareable HTML docs the Forge Prep team passes
around — playbooks, one-pagers, references. Instead of emailing an `.html`
file, drop it here and share the link.

**Live site:** https://rtusiime.github.io/forge-artifacts/ _(once GitHub Pages is enabled — see below)_

## How it's organized

Each artifact gets its own folder → its own clean URL:

```
forge-artifacts/
├── index.html          ← generated library home (do not hand-edit)
├── artifacts.json      ← the catalog / source of truth        ← EDIT THIS
├── build.py            ← regenerates index.html (+ hubs)
├── sync.py             ← pulls latest source HTML in, then builds
├── sources.local.json  ← local-only map: repo page → original on disk (git-ignored)
├── .nojekyll           ← makes Pages serve files verbatim
└── decouple-math/
    └── index.html      ← the shareable page  →  …/forge-artifacts/decouple-math/
```

- **Single-page artifact** (the common case): the page lives at
  `<slug>/index.html`. Example: `decouple-math/` shares one team-facing page.
- **Multi-version artifact** (team-facing vs. leadership-facing, etc.): keep each
  version at `<slug>/<version>/index.html`; `build.py` then generates a small
  **hub** at `<slug>/index.html` that leads with the primary version and lists
  the rest.

`index.html` and any per-topic hubs are **generated**. Your actual content pages
are never rewritten by the build.

## The sync model (important)

Most pages here are **copies** of "source of truth" HTML that you keep editing in
the `DLA/Meetings/audios/…` working folders. `sources.local.json` maps each repo
page to its original on disk, and `sync.py` re-pulls the latest before you push:

```bash
python3 sync.py     # copy any changed originals in, skip unchanged, rebuild index
```

`sources.local.json` is **git-ignored** — it holds absolute local paths, so it
stays on your machine and never lands in the (possibly public) repo.

## Add a new artifact

1. **Point at the source.** Add a line to `sources.local.json` mapping the repo
   page to the original file:
   ```json
   { "dest": "audit-playbook/index.html", "src": "/Users/…/Forge_Audit_Playbook.html" }
   ```
   (Or, if there's no living original, just save the file straight to
   `<slug>/index.html` and skip this step.)
2. **List it in `artifacts.json`** — add an entry with `slug`, `title`,
   `summary`, `tags`, `updated`. For a multi-version artifact, add a `variants`
   array (mark the main one `"primary": true`).
3. **Sync + preview:**
   ```bash
   python3 sync.py     # or: python3 build.py  if there's no source to pull
   ```
4. **Publish:**
   ```bash
   git add -A && git commit -m "Add audit-playbook" && git push
   ```
   GitHub Pages redeploys within a minute.

## Keeping shared pages current

When you update an original in the audios folder, just:

```bash
python3 sync.py && git add -A && git commit -m "Refresh decouple-math" && git push
```

## Deployment

Served by **GitHub Pages** from `main`, repository root. `.nojekyll` disables
Jekyll so folders and underscored filenames serve as-is. Pages that use Google
Fonts load them over the CDN — no build step required.

First-time setup: repo **Settings → Pages → Source: Deploy from a branch →
`main` / `/ (root)`**.

## Notes

- This repo holds the **shareable HTML only**. Source images and markdown drafts
  stay in `DLA/…` to keep the repo small.
