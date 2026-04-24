"""Build the Domino Watch static site.

Reads structured brief JSON from ``data/briefs/*.json``, validates each
against ``data/brief.schema.json``, and renders Jinja2 templates from
``templates/`` into ``site/``.

Usage (with venv activated):
    python scripts/build.py
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
BRIEFS_DIR = DATA_DIR / "briefs"
TEMPLATES_DIR = ROOT / "templates"
SITE_DIR = ROOT / "site"
ARCHIVE_DIR = SITE_DIR / "archive"
ASSETS_DIR = SITE_DIR / "assets"

SCHEMA_PATH = DATA_DIR / "brief.schema.json"
HISTORY_PATH = DATA_DIR / "grade-history.json"

GRADE_TO_NUM = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}
REGIME_COLOR = {"green": "#3fb950", "yellow": "#d29922", "red": "#f85149"}
STALE_AFTER_DAYS = 1


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_briefs() -> list[dict]:
    briefs = [load_json(p) for p in sorted(BRIEFS_DIR.glob("*.json"))]
    briefs.sort(key=lambda b: b["date"])
    return briefs


def validate_briefs(briefs: list[dict], schema: dict) -> None:
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    for b in briefs:
        for err in validator.iter_errors(b):
            errors.append(f"{b.get('date', '?')}: {err.message} at {list(err.path)}")
    if errors:
        for e in errors:
            print(f"SCHEMA ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def build_sparkline(history: list[dict], width: int = 320, height: int = 60) -> str:
    """Inline-SVG sparkline of the 1w grade over time, with regime-color dots."""
    if not history:
        return ""
    points = []
    for entry in history:
        g = entry.get("grade_1w")
        if g not in GRADE_TO_NUM:
            continue
        points.append((entry["date"], GRADE_TO_NUM[g], entry.get("regime", "yellow")))
    if not points:
        return ""

    pad = 6
    n = len(points)
    if n == 1:
        xs = [width / 2]
    else:
        xs = [pad + i * (width - 2 * pad) / (n - 1) for i in range(n)]
    ys = [
        height - pad - (val - 1) / 4 * (height - 2 * pad)
        for _, val, _ in points
    ]

    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{REGIME_COLOR.get(reg, "#888")}" />'
        for (_, _, reg), x, y in zip(points, xs, ys)
    )
    return (
        f'<svg class="sparkline" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" '
        f'aria-label="1-week grade history">'
        f'<polyline fill="none" stroke="#9aa4b2" stroke-width="1.5" points="{poly}" />'
        f"{dots}"
        f"</svg>"
    )


def days_old(date_str: str, today: dt.date) -> int:
    d = dt.date.fromisoformat(date_str)
    return (today - d).days


def render_brief(env: Environment, brief: dict, styles: str, sparkline_svg: str,
                 today: dt.date, *, is_today: bool) -> str:
    age = days_old(brief["date"], today)
    template = env.get_template("brief.html")
    return template.render(
        brief=brief,
        styles=styles,
        sparkline_svg=sparkline_svg if is_today else "",
        is_today=is_today,
        stale=age >= STALE_AFTER_DAYS and is_today,
        stale_days=age,
    )


def render_archive(env: Environment, briefs: list[dict], styles: str) -> str:
    template = env.get_template("archive-index.html")
    entries = sorted(briefs, key=lambda b: b["date"], reverse=True)
    return template.render(entries=entries, styles=styles)


def main() -> int:
    if not BRIEFS_DIR.exists():
        print(f"No briefs directory at {BRIEFS_DIR}", file=sys.stderr)
        return 1

    schema = load_json(SCHEMA_PATH)
    briefs = load_briefs()
    if not briefs:
        print("No briefs found in data/briefs/. Nothing to build.", file=sys.stderr)
        return 1

    validate_briefs(briefs, schema)

    history = load_json(HISTORY_PATH) if HISTORY_PATH.exists() else []

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    styles = (TEMPLATES_DIR / "styles.css").read_text(encoding="utf-8")
    sparkline_svg = build_sparkline(history)

    SITE_DIR.mkdir(exist_ok=True)
    ARCHIVE_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)

    today = dt.date.today()
    latest = briefs[-1]

    # site/index.html — latest brief
    (SITE_DIR / "index.html").write_text(
        render_brief(env, latest, styles, sparkline_svg, today, is_today=True),
        encoding="utf-8",
    )

    # site/archive/YYYY-MM-DD.html — every brief
    for b in briefs:
        out = ARCHIVE_DIR / f"{b['date']}.html"
        out.write_text(
            render_brief(env, b, styles, "", today, is_today=False),
            encoding="utf-8",
        )

    # site/archive/index.html — listing
    (ARCHIVE_DIR / "index.html").write_text(
        render_archive(env, briefs, styles),
        encoding="utf-8",
    )

    # also drop a copy of styles.css in assets for any stand-alone use
    (ASSETS_DIR / "styles.css").write_text(styles, encoding="utf-8")

    print(f"Built {len(briefs)} brief(s). Latest: {latest['date']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
