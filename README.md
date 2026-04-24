# Domino Watch

Daily macro brief tracking yen carry trade unwind risk (Jake Claver "Domino Theory" framework).

Published at `https://<username>.github.io/domino-watch/` (URL TBD).

**Not financial advice.**

## Quick start

```powershell
# one-time
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# one-time: copy .env.example -> .env, fill in ANTHROPIC_API_KEY

# generate today's brief via Claude API + web_search, build, push to a PR branch
python scripts/run_brief.py --commit

# (or build the site from existing JSON without calling the API)
python scripts/build.py

# preview locally
python -m http.server --directory docs 8000
```

`run_brief.py` flags:
- (no flag) — dry run, writes JSON + builds, no git
- `--commit` — push to a `brief/YYYY-MM-DD` branch, prints a PR link
- `--commit --merge` — merge straight to `main` (skip PR review)

See [PROJECT_SCOPE.md](PROJECT_SCOPE.md) for architecture and workflow.
See [prompts/daily-brief.md](prompts/daily-brief.md) for the briefing spec.
