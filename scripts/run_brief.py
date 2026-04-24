"""Generate today's Domino Watch brief via the Anthropic API.

Calls Claude with the briefing spec and the built-in web_search tool,
expects a single JSON object conforming to data/brief.schema.json,
writes the brief, appends to grade history, runs the build, and (with
--commit) opens a pull request.

Usage:
    python scripts/run_brief.py                     # dry run, no git
    python scripts/run_brief.py --commit            # commit + PR
    python scripts/run_brief.py --commit --merge    # commit + push to main

Requires ANTHROPIC_API_KEY in env or .env file.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
BRIEFS_DIR = DATA_DIR / "briefs"
HISTORY_PATH = DATA_DIR / "grade-history.json"
SCHEMA_PATH = DATA_DIR / "brief.schema.json"
SPEC_PATH = ROOT / "prompts" / "daily-brief.md"

DEFAULT_MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 8000
WEB_SEARCH_MAX_USES = 12


SYSTEM_PROMPT = """You are the Domino Watch macro analyst. Follow the
briefing spec EXACTLY. Use the web_search tool to pull live market data
and recent headlines. If a datapoint cannot be retrieved after a
reasonable search, set its level/change to null and note "unavailable"
in the relevant Stack row note — do NOT fabricate.

Your final output MUST be a single JSON object, and ONLY that JSON
object — no prose before or after, no markdown code fence. The JSON
must conform to the schema provided. Use ISO date for `date` and
ISO-8601 with timezone offset for `generated_at`."""


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_user_message(spec: str, schema: dict, history: list[dict],
                       today: dt.date) -> str:
    yesterday_summary = "no prior briefs"
    if history:
        last = history[-1]
        yesterday_summary = (
            f"Last brief on file: {last.get('date')} — "
            f"regime={last.get('regime')}, 1w grade={last.get('grade_1w')}"
        )
    return f"""# Briefing Spec
{spec}

---

# Today
Today's date is {today.isoformat()}. {yesterday_summary}.

# JSON Schema (your output must validate against this)
```json
{json.dumps(schema, indent=2)}
```

# Task
Run the brief for {today.isoformat()}. Use web_search for the mandatory
data pulls and any BOJ/MOF/Ueda/Katayama headlines from the last 24
hours. Compute the anchors. Assign grades for 1w/2w/3w/4w and the
regime flag. Return ONLY the JSON object — no other text."""


def extract_json_from_response(blocks) -> dict:
    """Pull the JSON object out of Claude's response blocks."""
    text_parts = [b.text for b in blocks if getattr(b, "type", None) == "text"]
    text = "\n".join(text_parts).strip()

    # Strip markdown fences if present.
    if text.startswith("```"):
        first_nl = text.find("\n")
        text = text[first_nl + 1:] if first_nl != -1 else text
        if text.endswith("```"):
            text = text[: -3]
        text = text.strip()

    # Locate the outermost JSON object.
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in response:\n{text[:500]}")
    return json.loads(text[start : end + 1])


def call_claude(model: str, spec: str, schema: dict,
                history: list[dict], today: dt.date) -> dict:
    client = Anthropic()
    user_msg = build_user_message(spec, schema, history, today)

    print(f"Calling {model} with web_search...", file=sys.stderr)
    resp = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": WEB_SEARCH_MAX_USES,
        }],
        messages=[{"role": "user", "content": user_msg}],
    )

    usage = resp.usage
    print(
        f"Stop reason: {resp.stop_reason}. "
        f"Tokens: in={usage.input_tokens}, out={usage.output_tokens}",
        file=sys.stderr,
    )
    return extract_json_from_response(resp.content)


def validate(brief: dict, schema: dict) -> None:
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(brief))
    if errors:
        for err in errors:
            print(f"SCHEMA ERROR: {err.message} at {list(err.path)}",
                  file=sys.stderr)
        raise SystemExit(2)


def append_history(brief: dict) -> None:
    history = load_json(HISTORY_PATH) if HISTORY_PATH.exists() else []
    entry = {
        "date": brief["date"],
        "grade_1w": brief["grades"]["1w"]["grade"],
        "regime": brief["regime_flag"],
    }
    history = [h for h in history if h["date"] != brief["date"]]
    history.append(entry)
    history.sort(key=lambda h: h["date"])
    HISTORY_PATH.write_text(
        json.dumps(history, indent=2) + "\n", encoding="utf-8"
    )


def run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}", file=sys.stderr)
    subprocess.run(cmd, check=True, cwd=ROOT)


def git_publish(brief_date: str, *, merge_to_main: bool) -> None:
    branch = f"brief/{brief_date}"
    run(["git", "checkout", "-B", branch])
    run(["git", "add", "-A"])
    run(["git", "commit", "-m", f"brief: {brief_date}"])
    if merge_to_main:
        run(["git", "checkout", "main"])
        run(["git", "merge", "--no-ff", branch, "-m",
             f"Merge brief {brief_date}"])
        run(["git", "push", "origin", "main"])
        run(["git", "branch", "-d", branch])
    else:
        run(["git", "push", "-u", "origin", branch])
        print(
            f"\nPushed branch '{branch}'. Open a PR at:\n"
            f"  https://github.com/Rflorey/domino-watch/compare/main...{branch}?expand=1",
            file=sys.stderr,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Domino Watch brief.")
    parser.add_argument("--commit", action="store_true",
                        help="Commit the brief and push (default: branch + PR).")
    parser.add_argument("--merge", action="store_true",
                        help="With --commit, merge straight to main instead of opening a PR branch.")
    parser.add_argument("--model", default=os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL))
    parser.add_argument("--date", default=None,
                        help="Override the brief date (YYYY-MM-DD). Default: today.")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set. Put it in .env or env.",
              file=sys.stderr)
        return 1

    today = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    spec = load_text(SPEC_PATH)
    schema = load_json(SCHEMA_PATH)
    history = load_json(HISTORY_PATH) if HISTORY_PATH.exists() else []

    brief = call_claude(args.model, spec, schema, history, today)

    # Force the date to match what we asked for, in case the model drifted.
    brief["date"] = today.isoformat()

    validate(brief, schema)

    BRIEFS_DIR.mkdir(parents=True, exist_ok=True)
    out = BRIEFS_DIR / f"{today.isoformat()}.json"
    out.write_text(json.dumps(brief, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}", file=sys.stderr)

    append_history(brief)
    print(f"Appended to {HISTORY_PATH.relative_to(ROOT)}", file=sys.stderr)

    run([sys.executable, str(ROOT / "scripts" / "build.py")])

    if args.commit:
        git_publish(today.isoformat(), merge_to_main=args.merge)
    else:
        print("\nDry run complete. Re-run with --commit to publish.",
              file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
