# New Brief — Operator Instructions (for Claude)

Trigger phrase: "Run today's Domino Watch brief and publish it."

## Steps

1. Read `prompts/daily-brief.md` for the current spec.
2. Read `data/grade-history.json` — note yesterday's grades and regime
   so you can call out what changed.
3. Run `web_search` for each mandatory data pull listed in the spec.
   If a datapoint cannot be retrieved, set its value to `null` in the
   JSON and note "unavailable" in the relevant Stack row note.
4. Compute anchors (US-JP 10Y spread, ¥/bbl, etc.).
5. Determine the four horizon grades and the regime flag.
6. Write `data/briefs/YYYY-MM-DD.json` conforming to
   `data/brief.schema.json`. Use ISO date for `date` and ISO-8601 with
   timezone for `generated_at`.
7. Append today's entry to `data/grade-history.json`:
   `{ "date": "...", "grade_1w": "C", "regime": "yellow" }`
8. Run `python scripts/build.py`. Confirm no validation errors.
9. Show the user the rendered `site/index.html` preview.
10. On user confirmation: `git add`, `git commit -m "brief: YYYY-MM-DD"`,
    `git push`.

## If grades shift from yesterday
Add a one-sentence "what changed" note to `narrative.p1` explaining the
driver.

## If a BOJ / MOF event sits within 14 days
Surface it in `bottom_line` and reference in `horizon_rationale`.
