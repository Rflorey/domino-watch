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

# build the site
python scripts/build.py

# preview locally
python -m http.server --directory docs 8000
```

See [PROJECT_SCOPE.md](PROJECT_SCOPE.md) for architecture, data model, and workflow.
See [prompts/daily-brief.md](prompts/daily-brief.md) for the briefing spec.
