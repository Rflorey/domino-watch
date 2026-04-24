# Domino Watch — Project Scope

**Owner:** Russ Florey
**Purpose:** A daily macro brief tracking yen carry trade unwind risk (Jake Claver's "Domino Theory" framework), generated via Claude and published as a static website for personal use and sharing with a small audience.
**Status:** Scaffolding

**Stack decisions (locked):**
- Build: **Python** (Jinja2), venv at `./venv`
- Repo name: `domino-watch` (not tied to GitHub username)
- Hosting: GitHub Pages, served from `main` branch `/docs` folder (Pages requires `/(root)` or `/docs`)

---

## 1. Goals

### Primary
- Produce a daily macro brief grounded in fresh market data and news
- Publish the brief to a static website at a shareable URL
- Maintain an archive of past briefs with grade history

### Secondary
- Editable prompt template so the briefing spec can evolve
- Grade-over-time tracking (sparkline or chart) to see drift
- Mobile-readable output (this gets checked on a phone)

### Non-goals (for v1)
- Real-time / intraday updates
- Multi-user auth or comment systems
- Paid data feeds (web_search is the v1 data source, accept the quality tradeoff)
- Automated scheduled runs (v1 is manually triggered from a Claude session)

---

## 2. Architecture

```
┌─────────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Claude session     │────▶│  Local project   │────▶│  GitHub repo    │
│  (VS Code / Code)   │     │  (generate HTML) │     │  (GitHub Pages) │
└─────────────────────┘     └──────────────────┘     └─────────────────┘
       │                           │                          │
       │                           │                          │
   web_search                  templates/                  public URL
   pulls data                  renders .html               auto-served
```

### Flow
1. User runs a daily-brief command in VS Code (with Claude)
2. Claude pulls market data via `web_search` per the briefing spec
3. Claude writes two files:
   - `site/index.html` — today's brief (overwrites previous)
   - `site/archive/YYYY-MM-DD.html` — dated archive copy
4. Claude updates `site/archive/index.html` (the archive list page)
5. Claude updates `data/grade-history.json` (append today's grades)
6. `git commit` + `git push` to `main`
7. GitHub Pages auto-serves the updated site within ~30s

---

## 3. Repo Structure

```
domino-watch/
├── README.md                     # Human-readable project overview
├── PROJECT_SCOPE.md              # This file
├── requirements.txt              # Python dependencies (Jinja2, jsonschema)
├── venv/                         # Local Python virtual environment (gitignored)
├── .github/
│   └── workflows/
│       └── pages.yml             # (optional) GitHub Pages action if needed
├── prompts/
│   ├── daily-brief.md            # The briefing spec (editable, the "prompt")
│   └── changelog.md              # Track changes to the briefing spec over time
├── templates/
│   ├── brief.html                # Jinja2 template for a single brief
│   ├── archive-index.html        # Template for the archive listing page
│   └── styles.css                # Shared styles (inlined into output at build time)
├── data/
│   ├── grade-history.json        # Rolling history of grades for sparkline
│   ├── brief.schema.json         # JSON schema validating per-day brief data
│   └── briefs/
│       └── YYYY-MM-DD.json       # Structured data for each brief (for rebuilds)
├── scripts/
│   ├── build.py                  # Renders templates + data into site/
│   └── new-brief.md              # Instructions for Claude to run a new brief
└── docs/                         # Build output — this is what GitHub Pages serves
    ├── index.html                # Today's brief
    ├── archive/
    │   ├── index.html            # Archive listing
    │   └── YYYY-MM-DD.html       # Individual archived briefs
    └── assets/
        └── styles.css
```

**Design decision:** Keep the `docs/` directory in the repo (not in `.gitignore`). GitHub Pages serves from `main` branch `/docs` folder. This means every brief is a git commit and fully reproducible.

---

## 4. Data Model

### `data/briefs/2026-04-24.json`
Structured snapshot of each brief so we can rebuild HTML from data if templates change.

```json
{
  "date": "2026-04-24",
  "generated_at": "2026-04-24T06:15:00-07:00",
  "regime_flag": "yellow",
  "regime_justification": "...",
  "grades": {
    "1w": { "grade": "C", "label": "Watchful", "driver": "..." },
    "2w": { "grade": "C", "label": "Watchful", "driver": "..." },
    "3w": { "grade": "D", "label": "Unlikely", "driver": "..." },
    "4w": { "grade": "D", "label": "Unlikely", "driver": "..." }
  },
  "bottom_line": "...",
  "stack": [
    { "marker": "USD/JPY", "level": "...", "change_1d": "...", "note": "..." }
  ],
  "narrative": { "p1": "...", "p2": "...", "p3": "..." },
  "horizon_rationale": { "w1_w2": "...", "w2_w3": "...", "w3_w4": "..." },
  "watch_list": ["...", "..."],
  "sources": [{ "title": "...", "url": "..." }]
}
```

### `data/grade-history.json`
Append-only array for sparkline rendering.

```json
[
  { "date": "2026-04-23", "grade_1w": "D", "regime": "green" },
  { "date": "2026-04-24", "grade_1w": "C", "regime": "yellow" }
]
```

**Grade → numeric mapping for charting:** A=5, B=4, C=3, D=2, F=1 (higher = more risk).

---

## 5. Build System

### Option A — Minimal (v1, locked)
Pure Python script, no build framework.

- `scripts/build.py` reads latest `data/briefs/*.json` + `data/grade-history.json`
- Validates each brief against `data/brief.schema.json` before rendering
- Renders Jinja2 templates from `templates/` to `docs/`
- Run via `python scripts/build.py` (with venv activated)

**Dependencies (`requirements.txt`):**
- `Jinja2` — templating
- `jsonschema` — brief data validation
- No web framework, no bundler

### Option B — Upgrade path
If v1 works and we want client-side interactivity (filterable archive, grade chart with tooltips), migrate to:
- Astro (static site generator, keeps HTML simple, allows islands of interactivity)
- OR Eleventy (simpler, pure static)

Defer this decision until after 2-4 weeks of daily use.

---

## 6. Claude Workflow in VS Code

### Daily "run brief" workflow
User opens the project in VS Code with Claude available. User says:

> "Run today's Domino Watch brief and publish it."

Claude then:
1. Reads `prompts/daily-brief.md` for the current spec
2. Reads `data/grade-history.json` to show yesterday's grades (for "what changed" context)
3. Runs web_search for each mandatory data pull
4. Computes anchors (spread, ¥/bbl, etc.)
5. Determines grades and regime flag
6. Writes `data/briefs/YYYY-MM-DD.json` (structured)
7. Appends to `data/grade-history.json`
8. Runs `python scripts/build.py` to regenerate `site/`
9. Shows user the rendered HTML preview
10. On user confirmation: `git add`, `git commit`, `git push`

### Other workflows
- **"Edit the brief spec"** — opens `prompts/daily-brief.md`, user edits, logs change to `prompts/changelog.md`
- **"Show grade history"** — Claude reads `data/grade-history.json`, renders a quick summary or sparkline
- **"Rebuild all briefs from data"** — if templates change, regenerate all HTML from stored JSON

---

## 7. Briefing Spec (lives at `prompts/daily-brief.md`)

The full current briefing spec (mandatory data pulls, grade scale, regime flag, output format, discipline rules) — already defined, drops in as-is. Key pieces:

- 5-tier grade scale (A highest alert → F all-clear)
- 4 forward horizons (1w, 2w, 3w, 4w)
- Regime flag (🟢 Carry-On / 🟡 Carry-Neutral / 🔴 Carry-Off)
- Mandatory data pulls (USD/JPY, JGB 10Y, US 10Y, WTI, Nikkei, DXY, BOJ headlines, BTC, XRP)
- Computed anchors (US-JP spread, carry-to-vol, ¥/bbl, distance from 60d mean)
- Strict output format (Executive Summary, Stack table, Narrative, Horizon Rationale, Watch List, Sources)

---

## 8. Publishing

### GitHub Pages setup (one-time)
1. Create a public GitHub repo named `domino-watch`
2. Settings → Pages → Source: `main` branch, **`/docs` folder**
3. Wait ~60 seconds for first build
4. Verify URL: `https://<username>.github.io/domino-watch/`

### Custom domain (optional, later)
GitHub Pages supports custom domains free. Requires a CNAME record. Defer to after v1 is working.

---

## 9. v1 Build Checklist

Ordered. Each item should take < 30 minutes if scope holds.

### Phase 1 — Scaffolding
- [ ] Create GitHub repo (public)
- [ ] Clone locally, open in VS Code
- [ ] Add `README.md`, `PROJECT_SCOPE.md` (this file), `.gitignore`
- [ ] Enable GitHub Pages (serve from `main` branch, `/site` folder)
- [ ] Add placeholder `site/index.html` to verify Pages works
- [ ] Confirm site loads at `https://<username>.github.io/domino-watch/`

### Phase 2 — Content structure
- [ ] Drop the briefing spec into `prompts/daily-brief.md`
- [ ] Create `templates/brief.html` with placeholders for all brief fields
- [ ] Create `templates/archive-index.html`
- [ ] Create `templates/styles.css` — mobile-first, dark/light, no external fonts
- [ ] Design the HTML output to be self-contained (inline CSS) per brief

### Phase 3 — Build pipeline
- [ ] `package.json` with `mustache` dependency
- [ ] `scripts/build.js` — reads JSON data, renders templates, writes to `site/`
- [ ] Test: hand-craft one `data/briefs/2026-04-24.json`, run build, inspect output
- [ ] Add grade-history sparkline rendering (inline SVG) to `brief.html` footer
- [ ] Verify mobile rendering at 375px width

### Phase 4 — First live brief
- [ ] In VS Code with Claude, run the first real brief end-to-end
- [ ] Verify JSON saved, history appended, HTML rendered
- [ ] `git push`, wait for Pages, verify live
- [ ] Share the link with a test recipient, get feedback on readability

### Phase 5 — Iteration (next 2 weeks of daily use)
- [ ] Track what's annoying or broken
- [ ] Iterate on the briefing spec as needed (log to `prompts/changelog.md`)
- [ ] Decide: stay on v1 architecture, or migrate to Astro/Eleventy for interactivity

---

## 10. Open Questions

**Resolved:**
- Stack: Python (Jinja2)
- Repo name: `domino-watch`
- Serve from: `/docs` folder on `main`

**Still open (non-blocking for scaffold):**
1. GitHub username (needed before publishing — repo can be created locally first)
2. Custom domain, or `.github.io` subdomain? (defer past v1)
3. Public-findable or effectively unlisted? (default: public, no profile pin)
4. Audience size and sophistication — glossary needed?
5. Branding — alt name or tagline beyond "Domino Watch"?
6. Commit policy — Claude auto-commit to `main`, or stage to a `draft` branch for review?

---

## 11. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| `web_search` returns stale/wrong market data | Briefing spec requires explicit flagging when a datapoint can't be pulled; never fabricate |
| You skip a day → site looks stale | Add a "last updated" timestamp prominently; consider a banner if > 24h old |
| Grade drift feels gameable / inconsistent over time | `prompts/changelog.md` tracks spec changes; grade-history.json provides audit trail |
| Readers misinterpret the brief as financial advice | Persistent footer disclaimer on every published page |
| GitHub token / auth issues when Claude pushes | Using connected GitHub tools means Claude pushes directly — no token on disk |
| Repo grows large with archives | At ~4KB per brief HTML + JSON, 1000 briefs = ~4MB. Not a concern for years. |

---

## 12. Success Criteria (v1, 30 days after launch)

- [ ] Brief published every weekday (allow misses on travel / sick days)
- [ ] At least 1 external reader checking the link regularly
- [ ] `data/grade-history.json` has 20+ entries
- [ ] You haven't rage-quit the project
- [ ] You're still iterating on the briefing spec based on real use, not rebuilding the infrastructure

If all five hit, move to v2 discussions (scheduled runs, real data feeds, email digest, etc.).

---

## Appendix A — Suggested `.gitignore`

```
venv/
__pycache__/
*.pyc
.DS_Store
.env
.env.local
*.log
/tmp/
# NOTE: do NOT gitignore docs/ — it's the published output
```

## Appendix B — Suggested `README.md` (one-liner)

```markdown
# Domino Watch

Daily macro brief tracking yen carry trade unwind risk.
Published at https://<username>.github.io/domino-watch/

Not financial advice.
```

## Appendix C — Starter `requirements.txt`

```
Jinja2>=3.1
jsonschema>=4.0
```

Local preview: `python -m http.server --directory docs 8000`
